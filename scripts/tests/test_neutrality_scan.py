#!/usr/bin/env python3
"""Behavioral tests for scripts/neutrality-scan.

AGENTS.md declares neutrality as law: rule and skill content must carry no
project names, people, or project/user-specific parameters, because
`house-rules init` lands that content verbatim in other people's repos. The
law had no checker, which is how four violations shipped — one of them a
private-tool directive sitting in an always-on rule.

Two properties matter more than coverage breadth here, and both are tested
directly rather than inferred:

  1. It fires on real leaks, including ones nobody listed. The
     capitalized-word-plus-MCP heuristic is the only class that catches an
     unlisted tool name, so it is tested against a name that appears in no
     term list.
  2. It does not fire on the kit's own host platforms. Cursor and Claude Code
     appear on nearly every page; a checker that flags them gets switched off
     within a day, and then catches nothing at all. False-positive load is
     the make-or-break risk, so the legitimate forms are pinned as tests.

Run: python3 scripts/tests/test_neutrality_scan.py
"""

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCANNER = REPO_ROOT / "scripts" / "neutrality-scan"
TERMS_PROFILE = REPO_ROOT / "profiles" / "neutrality-terms.toml"

EXIT_CLEAN, EXIT_FINDINGS, EXIT_USAGE, EXIT_ERROR = 0, 1, 2, 3


def run_scan(root=None, *args):
    """Run the scanner over `root` (default: the real repo). Returns
    (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(SCANNER)]
    if root is not None:
        cmd += ["--root", str(root)]
    cmd += list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return proc.returncode, proc.stdout, proc.stderr


def scan_json(root=None, *args):
    """Run with --json and return (returncode, parsed payload)."""
    rc, out, err = run_scan(root, "--json", *args)
    try:
        return rc, json.loads(out)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"--json emitted unparseable stdout (rc={rc}): {exc}\n"
            f"stdout: {out!r}\nstderr: {err!r}"
        )


def write(root, relpath, text):
    target = Path(root) / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(text), encoding="utf-8")
    return target


def classes_of(payload):
    return sorted({f["class"] for f in payload["findings"]})


def terms_of(payload):
    return sorted(f["term"] for f in payload["findings"])


class TestRealSurfaceIsClean(unittest.TestCase):
    """AC1: the distributed surface reports zero findings and exits 0."""

    def test_exits_clean_on_the_real_repo(self):
        rc, out, err = run_scan()
        self.assertEqual(
            rc, EXIT_CLEAN,
            f"the distributed surface has neutrality findings:\n{out}\n{err}",
        )

    def test_json_findings_list_is_empty(self):
        rc, payload = scan_json()
        self.assertEqual(payload["findings"], [])
        self.assertEqual(rc, EXIT_CLEAN)

    def test_reports_what_it_actually_scanned(self):
        # A scanner that silently resolved zero files would pass the two
        # tests above while checking nothing.
        rc, payload = scan_json()
        self.assertGreater(payload["scanned"], 20, "suspiciously few files scanned")

    def test_the_terms_profile_does_not_flag_itself(self):
        # The catalog is term-laden by construction. Without the declared-
        # terms region contract every entry in it is a finding, and the
        # checker cannot run on its own repo at all.
        rc, payload = scan_json()
        offenders = [f for f in payload["findings"]
                     if "neutrality-terms" in f["file"]]
        self.assertEqual(offenders, [])


class TestFlagsRealLeaks(unittest.TestCase):
    """AC2, positive half: it fires on the classes that shipped."""

    def test_flags_an_unlisted_capitalized_mcp_bigram(self):
        # The class that earns its keep: this name is in no term list.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "cursor/rules/leaky.mdc",
                  "When Jawnt MCP is available, prefer it for cross-project reads.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("Jawnt MCP", terms_of(payload))
            self.assertIn("private_tool_heuristic", classes_of(payload))

    def test_flags_a_vendor_model_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "skills/some-skill/SKILL.md",
                  "Paste the prompt into Grok and collect the response.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("vendor_model", classes_of(payload))

    def test_flags_a_vendor_model_in_a_skill_support_file(self):
        # Finding 2 lived in a .py, not a .md. A markdown-only scanner would
        # have missed the exact leak that motivated this checker.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "skills/some-skill/assemble.py",
                  'DEFAULT_MODELS = ["Gemini"]\n')
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("vendor_model", classes_of(payload))

    def test_flags_a_bare_personal_handle(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "profiles/conventions.toml",
                  "# sanctioned by Kevin, 2026-08-05\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("personal", classes_of(payload))

    def test_flags_the_generated_claude_projection(self):
        # A leak fixed in the canonical .mdc but left in the projection still
        # ships to every Claude adopter.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "cursor/rules/clean.mdc", "Capability-level prose.\n")
            write(tmp, "claude/rules/stale.md", "Use Jawnt MCP for reads.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertEqual(len(payload["findings"]), 1)
            self.assertIn("claude/rules/stale.md", payload["findings"][0]["file"])

    def test_one_leak_reports_once_as_its_most_specific_class(self):
        # "Jawnt MCP" matches both the listed private-tool name and the
        # structural bigram. Reporting both would say nothing the wider match
        # did not, and would double the apparent finding count.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "cursor/rules/leaky.mdc", "Use Jawnt MCP for reads.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(len(payload["findings"]), 1)
            self.assertEqual(payload["findings"][0]["term"], "Jawnt MCP")
            self.assertEqual(payload["findings"][0]["class"],
                             "private_tool_heuristic")

    def test_two_distinct_leaks_on_one_line_both_report(self):
        # Dedupe must be containment-based, not "one finding per line".
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "cursor/rules/leaky.mdc", "Ask Grok, then ask Gemini.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(terms_of(payload), ["Gemini", "Grok"])

    def test_finding_carries_location_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md",
                  "line one\nline two\nUse Jawnt MCP here.\n")
            rc, payload = scan_json(tmp)
            f = payload["findings"][0]
            self.assertEqual(f["line"], 3)
            self.assertEqual(f["file"], "templates/t.md")
            self.assertIn("Jawnt MCP", f["text"])


class TestHostPlatformsAreNotFlagged(unittest.TestCase):
    """AC2, negative half. The kit's two declared host platforms are out of
    the vendor class by design; flagging them makes the checker unusable."""

    def test_cursor_and_claude_code_prose_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "cursor/rules/hosts.mdc", """\
                Cursor keeps alwaysApply: true for this rule.
                Claude Code has no equivalent, so core rules ship as skills.
                Rules live in .cursor/rules/ and .claude/rules/.
                Claude Code reads .claude/skills/; Cursor reads .cursor/skills/.
                """)
            rc, out, err = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"host-platform prose flagged:\n{out}")

    def test_generic_protocol_prose_is_clean(self):
        # Lowercase carriers and the plural are prose about the protocol, not
        # a named product. A case-insensitive or boundary-less heuristic
        # fires on all of these.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "skills/s/SKILL.md", """\
                Voices may query MCPs for evidence.
                This may be read by an MCP plan tool.
                Prefer one MCP call over a per-directory loop.
                Note that the MCP tools are read-only.
                """)
            rc, out, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"generic MCP prose flagged:\n{out}")

    def test_canonical_repo_url_is_not_personal_attribution(self):
        # The clone URL carries the maintainer's handle and is load-bearing:
        # agents tell users to run it. Exempted by context, not by pinning
        # six line numbers that move.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "global-safety-net/proto.md",
                  "Clone it with: `git clone https://github.com/kevglynn/house-rules ~/x`\n")
            rc, out, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"canonical repo URL flagged:\n{out}")

    def test_the_same_handle_outside_a_url_is_still_flagged(self):
        # The exemption must be the URL context, not the handle itself —
        # otherwise it is a mute button on the whole personal class.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "global-safety-net/proto.md",
                  "Ask kevglynn before changing this.\n")
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("personal", classes_of(payload))


class TestScopeBoundary(unittest.TestCase):
    """Out-of-scope trees are where names are correct and load-bearing."""

    def test_docs_are_not_scanned(self):
        # docs/specs and docs/reviews are dated records that must name the
        # problem to describe it — including this epic's own spec.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "docs/specs/s.md", "DEFAULT_MODELS = Grok, Gemini, GPT\n")
            rc, out, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"docs/ was scanned:\n{out}")

    def test_scripts_are_not_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "scripts/init.sh",
                  "echo 'clone https://github.com/kevglynn/house-rules'\n")
            rc, out, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"scripts/ was scanned:\n{out}")


class TestAllowlist(unittest.TestCase):
    """An exemption is a recorded decision, not a mute button."""

    def _profile_with_allow(self, tmp, body):
        base = TERMS_PROFILE.read_text(encoding="utf-8")
        p = Path(tmp) / "custom-terms.toml"
        p.write_text(base + textwrap.dedent(body), encoding="utf-8")
        return p

    def test_allowlisted_term_with_a_reason_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md", "Call the Figma MCP to read the file.\n")
            rc, _, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_FINDINGS, "precondition: term must flag first")
            prof = self._profile_with_allow(tmp, """
                [[allow]]
                term = "Figma MCP"
                reason = "first-party integration the kit documents by name"
                """)
            rc, out, err = run_scan(tmp, "--profile", str(prof))
            self.assertEqual(rc, EXIT_CLEAN, f"allowlist ignored:\n{out}\n{err}")

    def test_allowlist_entry_without_a_reason_is_a_profile_error(self):
        # The required reason is the whole point: an unexplained exemption is
        # indistinguishable from someone silencing a real leak.
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md", "Call the Figma MCP to read the file.\n")
            prof = self._profile_with_allow(tmp, """
                [[allow]]
                term = "Figma MCP"
                """)
            rc, out, err = run_scan(tmp, "--profile", str(prof))
            self.assertEqual(rc, EXIT_ERROR)
            self.assertIn("reason", (out + err).lower())

    def test_allowlist_reason_may_not_be_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md", "Call the Figma MCP to read the file.\n")
            prof = self._profile_with_allow(tmp, """
                [[allow]]
                term = "Figma MCP"
                reason = "   "
                """)
            rc, out, err = run_scan(tmp, "--profile", str(prof))
            self.assertEqual(rc, EXIT_ERROR)


class TestDeclaredTermsRegion(unittest.TestCase):
    """The data-file self-matching contract, same idiom as banned-token-scan."""

    def test_terms_inside_a_declared_region_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = "neutrality-scan:declared-terms"
            write(tmp, "profiles/some-catalog.toml", f"""\
                # {marker}:begin
                entries = ["Grok", "Gemini"]
                # {marker}:end
                """)
            rc, out, _ = run_scan(tmp)
            self.assertEqual(rc, EXIT_CLEAN, f"declared region not honored:\n{out}")

    def test_terms_outside_the_region_are_still_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = "neutrality-scan:declared-terms"
            write(tmp, "profiles/some-catalog.toml", f"""\
                # {marker}:begin
                entries = ["Grok"]
                # {marker}:end
                note = "also ask Gemini"
                """)
            rc, payload = scan_json(tmp)
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertEqual(terms_of(payload), ["Gemini"])


class TestInterfaceContract(unittest.TestCase):
    """Exit codes and payload shape agents dispatch on."""

    def test_usage_error_exits_2(self):
        rc, _, _ = run_scan(None, "--no-such-flag")
        self.assertEqual(rc, EXIT_USAGE)

    def test_unreadable_profile_exits_3(self):
        rc, _, _ = run_scan(None, "--profile", "/nonexistent/terms.toml")
        self.assertEqual(rc, EXIT_ERROR)

    def test_invalid_profile_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.toml"
            bad.write_text("this is not = = valid toml\n", encoding="utf-8")
            rc, _, _ = run_scan(None, "--profile", str(bad))
            self.assertEqual(rc, EXIT_ERROR)

    def test_json_payload_carries_the_documented_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md", "Use Jawnt MCP here.\n")
            rc, payload = scan_json(tmp)
            for key in ("findings", "scanned", "profile", "roots"):
                self.assertIn(key, payload)
            for key in ("file", "line", "class", "term", "text"):
                self.assertIn(key, payload["findings"][0])

    def test_explain_names_the_class_and_the_remedy(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "templates/t.md", "Use Jawnt MCP here.\n")
            rc, out, _ = run_scan(tmp, "--explain")
            self.assertEqual(rc, EXIT_FINDINGS)
            self.assertIn("private_tool_heuristic", out)
            self.assertIn("overlay", out.lower())

    def test_help_exits_clean(self):
        rc, out, _ = run_scan(None, "--help")
        self.assertEqual(rc, EXIT_CLEAN)
        self.assertIn("neutrality", out.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
