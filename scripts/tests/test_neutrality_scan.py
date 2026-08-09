#!/usr/bin/env python3
"""Behavioral tests for scripts/neutrality-scan.

AGENTS.md declares neutrality as law: rule and skill content must carry no
project names, people, or project/user-specific parameters, because
`house-rules init` lands that content verbatim in other people's repos. The
law had no checker, which is how four violations shipped — one of them a
private-tool directive sitting in an always-on rule.

Three properties matter more than coverage breadth here, and all three are
tested directly rather than inferred:

  1. It fires on real leaks, including ones nobody listed. The
     capitalized-token-plus-MCP heuristic is the only class that catches an
     unlisted tool name, so it is tested against the shapes MCP servers are
     actually named with — not against one hand-picked name that happens to
     fit the pattern that was written for it.
  2. It does not fire on the kit's own host platforms or on generic prose
     about the protocol. False-positive load is the make-or-break risk: a
     checker that cries wolf gets switched off, and then catches nothing.
  3. It has no silent path to "clean". Every way the scanner can decline to
     look at something — an unresolved root, an unreadable file, a file
     asking to be skipped — either fails loudly or does not exist.

Run: python3 scripts/tests/test_neutrality_scan.py
"""

import json
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCANNER = REPO_ROOT / "scripts" / "neutrality-scan"
TERMS_PROFILE = REPO_ROOT / "profiles" / "neutrality-terms.toml"

EXIT_CLEAN, EXIT_FINDINGS, EXIT_USAGE, EXIT_ERROR = 0, 1, 2, 3

DECLARED_ROOTS = tomllib.loads(
    TERMS_PROFILE.read_text(encoding="utf-8"))["scope"]["roots"]


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


def error_payload(stderr):
    """Errors are JSON on stderr in both output modes; parsing it here is
    also the assertion that they are."""
    try:
        return json.loads(stderr)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stderr was not JSON: {exc}\nstderr: {stderr!r}")


def make_tree(tmp):
    """Create every declared scope root.

    Required, not incidental: an unresolvable root is a catalog error, so a
    fixture that creates only the directory it cares about would exercise
    the error path instead of the scan.
    """
    for rel in DECLARED_ROOTS:
        (Path(tmp) / rel).mkdir(parents=True, exist_ok=True)
    return tmp


def write(root, relpath, text):
    target = Path(root) / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(text), encoding="utf-8")
    return target


def classes_of(payload):
    return sorted({f["class"] for f in payload["findings"]})


def terms_of(payload):
    return sorted(f["term"] for f in payload["findings"])


class TreeCase(unittest.TestCase):
    """Base for tests that scan a fixture tree with all roots present."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tree = make_tree(self._tmp.name)

    def put(self, relpath, text):
        return write(self.tree, relpath, text)


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
        self.assertTrue(payload["ok"])

    def test_reports_what_it_actually_scanned(self):
        # A scanner that silently resolved zero files would pass the two
        # tests above while checking nothing.
        rc, payload = scan_json()
        self.assertGreater(payload["scanned"], 20, "suspiciously few files scanned")

    def test_every_declared_root_contributed_files(self):
        # Stronger than a total: a single root going empty (renamed
        # directory, wrong suffix list) is invisible in an aggregate count
        # but obvious per root.
        rc, payload = scan_json()
        empty = [r for r, n in payload["coverage"].items() if n == 0]
        self.assertEqual(empty, [], f"declared roots scanned nothing: {empty}")

    def test_the_terms_catalog_does_not_flag_itself(self):
        # The catalog is term-laden by construction and lives under a scanned
        # root. The scanner skips the catalog it loaded, by resolved path.
        rc, payload = scan_json()
        offenders = [f for f in payload["findings"]
                     if "neutrality-terms" in f["file"]]
        self.assertEqual(offenders, [])


class TestFlagsRealLeaks(TreeCase):
    """AC2, positive half: it fires on the classes that shipped."""

    def test_flags_a_vendor_model_name(self):
        self.put("skills/some-skill/SKILL.md",
                 "Paste the prompt into Grok and collect the response.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("vendor_model", classes_of(payload))

    def test_flags_a_vendor_model_in_a_skill_support_file(self):
        # Finding 2 lived in a .py, not a .md. A markdown-only scanner would
        # have missed the exact leak that motivated this checker.
        self.put("skills/some-skill/assemble.py", 'DEFAULT_MODELS = ["Gemini"]\n')
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("vendor_model", classes_of(payload))

    def test_flags_a_leak_in_distributed_ci_workflow_yaml(self):
        # templates/ ships a CI workflow that installs into an adopter's
        # repo. Choosing suffixes by "what did the known leak use" left the
        # most literally-distributed file in the kit unscanned.
        self.put("templates/verify.yml",
                 "      - run: echo 'ask Grok to review'\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("vendor_model", classes_of(payload))

    def test_flags_a_bare_personal_handle(self):
        self.put("profiles/conventions.toml", "# sanctioned by Kevin, 2026-08-05\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("personal", classes_of(payload))

    def test_flags_the_generated_claude_projection(self):
        # A leak fixed in the canonical .mdc but left in the projection still
        # ships to every Claude adopter.
        self.put("cursor/rules/clean.mdc", "Capability-level prose.\n")
        self.put("claude/rules/stale.md", "Use Jawnt MCP for reads.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertEqual(len(payload["findings"]), 1)
        self.assertIn("claude/rules/stale.md", payload["findings"][0]["file"])

    def test_finding_carries_location_and_line(self):
        self.put("templates/t.md", "line one\nline two\nUse Jawnt MCP here.\n")
        rc, payload = scan_json(self.tree)
        f = payload["findings"][0]
        self.assertEqual(f["line"], 3)
        self.assertEqual(f["file"], "templates/t.md")
        self.assertIn("Jawnt", f["text"])


class TestUnlistedToolHeuristic(TreeCase):
    """The only class that catches a name nobody enumerated — so the only
    class whose failure is silent. Tested against how MCP servers are
    actually named, not against one name chosen to fit the pattern."""

    # Real server-name shapes. The original [A-Z][a-z]+ pattern caught
    # exactly one of these five and shipped described as the safety net.
    REAL_SHAPES = [
        ("GitHub MCP", "internal capital"),
        ("AWS MCP", "all caps"),
        ("Chrome DevTools MCP", "multi-word with internal capital"),
        ("OpenAI MCP", "camel case"),
        ("S3 MCP", "digit in the name"),
    ]

    def test_catches_every_real_server_name_shape(self):
        missed = []
        for name, shape in self.REAL_SHAPES:
            with tempfile.TemporaryDirectory() as tmp:
                make_tree(tmp)
                write(tmp, "cursor/rules/leaky.mdc",
                      f"Use {name} for cross-project reads.\n")
                rc, payload = scan_json(tmp)
                if rc != EXIT_FINDINGS or name not in terms_of(payload):
                    missed.append(f"{name} ({shape})")
        self.assertEqual(missed, [], f"heuristic missed real names: {missed}")

    def test_the_reported_term_is_the_tool_name_alone(self):
        # The term is what a maintainer copies into an allowlist entry. A
        # match that swallows the sentence's opening verb ("Use GitHub MCP")
        # produces an allowlist entry that is wrong the moment the sentence
        # is reworded.
        self.put("cursor/rules/leaky.mdc", "Use GitHub MCP for repo reads.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(terms_of(payload), ["GitHub MCP"])

    def test_an_unlisted_name_is_caught_at_all(self):
        self.put("cursor/rules/leaky.mdc",
                 "When Frobnitz MCP is available, prefer it.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("Frobnitz MCP", terms_of(payload))


class TestOverlapPrecedence(TreeCase):
    """One leak, one finding — reported as the class with the right remedy."""

    def test_a_listed_name_outranks_the_heuristic_that_contains_it(self):
        # "Jawnt MCP" matches both the listed private-tool name and the
        # structural bigram. The listed class must win: its remedy says the
        # name is never legitimate, while the heuristic's offers "allowlist
        # it with a reason" — the wrong advice for a name on the list.
        self.put("cursor/rules/leaky.mdc", "Use Jawnt MCP for reads.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(len(payload["findings"]), 1)
        self.assertEqual(payload["findings"][0]["class"], "private_tool")

    def test_two_distinct_leaks_on_one_line_both_report(self):
        # Dedupe is overlap-based, not "one finding per line".
        self.put("cursor/rules/leaky.mdc", "Ask Grok, then ask Gemini.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(terms_of(payload), ["Gemini", "Grok"])


class TestHostPlatformsAreNotFlagged(TreeCase):
    """AC2, negative half. The kit's two declared host platforms are out of
    the vendor class by design; flagging them makes the checker unusable."""

    def test_cursor_and_claude_code_prose_is_clean(self):
        self.put("cursor/rules/hosts.mdc", """\
            Cursor keeps alwaysApply: true for this rule.
            Claude Code has no equivalent, so core rules ship as skills.
            Rules live in .cursor/rules/ and .claude/rules/.
            Claude Code reads .claude/skills/; Cursor reads .cursor/skills/.
            """)
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"host-platform prose flagged:\n{out}")

    def test_host_platform_mcp_references_are_clean(self):
        # Widening the heuristic to catch "GitHub MCP" also makes it catch
        # "Cursor MCP", which appears legitimately throughout the kit.
        self.put("skills/s/SKILL.md", """\
            The Cursor MCP catalog lists configured servers.
            Claude Code MCP servers are configured per project.
            """)
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"host-platform MCP prose flagged:\n{out}")

    def test_generic_protocol_prose_is_clean(self):
        # Lowercase carriers, the plural, and a capitalized sentence-opener
        # in front of a bare "MCP" are prose about the protocol, not a named
        # product.
        self.put("skills/s/SKILL.md", """\
            Voices may query MCPs for evidence.
            An MCP plan is one way to do this.
            This may be read by an MCP tool.
            Prefer one MCP call over a per-directory loop.
            Note that the MCP tools are read-only.
            """)
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"generic MCP prose flagged:\n{out}")

    def test_canonical_repo_url_is_not_personal_attribution(self):
        # The clone URL carries the maintainer's handle and is load-bearing:
        # agents tell users to run it. Exempted by context, not by pinning
        # line numbers that move.
        self.put("global-safety-net/proto.md",
                 "Clone it with: `git clone https://github.com/kevglynn/house-rules ~/x`\n")
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"canonical repo URL flagged:\n{out}")

    def test_the_same_handle_outside_a_url_is_still_flagged(self):
        # The exemption must be the URL context, not the handle itself —
        # otherwise it is a mute button on the whole personal class.
        self.put("global-safety-net/proto.md", "Ask kevglynn before changing this.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("personal", classes_of(payload))

    def test_only_a_full_scheme_qualified_url_earns_the_exemption(self):
        # The exemption is what makes the handle legitimate, so its shape is
        # the security boundary. Anchored at the scheme and closed at the
        # repo segment, it covers the canonical clone URL and nothing looser.
        #
        # This narrows real behavior: a scheme-less "github.com/owner/repo"
        # mention now flags. That is the intended trade — the kit writes the
        # clone URL in full, and the looser form was exemption surface with
        # no caller.
        self.put("global-safety-net/proto.md",
                 "Docs live at github.com/kevglynn/house-rules for reference.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS,
                         "a scheme-less fragment earned the URL exemption")
        self.assertIn("personal", classes_of(payload))


class TestNoSilentCleanPath(TreeCase):
    """Every way the scanner can decline to look at something must fail
    loudly. A green gate over an unscanned tree is the failure mode this
    checker exists to prevent, in its own implementation."""

    def test_no_in_file_marker_can_suppress_scanning(self):
        # An earlier draft honored a declared-terms region readable from
        # file content. Any scanned file could therefore open a region and
        # silence the rest of itself while the gate stayed green — and an
        # unterminated region silenced everything after it.
        self.put("cursor/rules/sneaky.mdc",
                 "# neutrality-scan:declared-terms:begin\n"
                 "Use Frobnitz MCP always.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS,
                         "a file suppressed its own scanning")
        self.assertIn("Frobnitz MCP", terms_of(payload))

    def test_an_unresolvable_scope_root_is_an_error_not_a_pass(self):
        # Rename a scanned directory and the old behavior was to skip it in
        # silence — indistinguishable from a root that resolved and was
        # clean, forever.
        catalog = TERMS_PROFILE.read_text(encoding="utf-8").replace(
            '"templates",', '"templates-renamed",')
        prof = Path(self.tree) / "renamed.toml"
        prof.write_text(catalog, encoding="utf-8")
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)
        self.assertIn("templates-renamed", err)

    def test_an_undecodable_byte_does_not_skip_the_rest_of_the_file(self):
        # Skipping on UnicodeDecodeError meant one stray byte made a whole
        # file report clean.
        p = Path(self.tree) / "cursor" / "rules" / "mixed.mdc"
        p.write_bytes(b"intro\n\xff\xfe binary-ish\nUse Frobnitz MCP always.\n")
        rc, payload = scan_json(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("Frobnitz MCP", terms_of(payload))

    def test_an_absolute_scope_root_is_rejected(self):
        # Path(root) / "/etc" is "/etc": an absolute root silently discards
        # --root, escapes the tree under scan, and then dies in relative_to
        # with an exit code that collides with "findings found".
        catalog = TERMS_PROFILE.read_text(encoding="utf-8").replace(
            '"templates",', '"/etc",')
        prof = Path(self.tree) / "abs.toml"
        prof.write_text(catalog, encoding="utf-8")
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)
        self.assertIn("relative", err)

    def test_a_traversal_scope_root_is_rejected(self):
        catalog = TERMS_PROFILE.read_text(encoding="utf-8").replace(
            '"templates",', '"../elsewhere",')
        prof = Path(self.tree) / "trav.toml"
        prof.write_text(catalog, encoding="utf-8")
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)

    def test_a_class_without_a_remedy_is_rejected(self):
        # The remedy is the only actionable content in a finding.
        catalog = TERMS_PROFILE.read_text(encoding="utf-8")
        catalog += '\n[classes.mystery]\nentries = ["Frobnitz"]\n'
        prof = Path(self.tree) / "noremedy.toml"
        prof.write_text(catalog, encoding="utf-8")
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)
        self.assertIn("remedy", err)

    def test_a_bare_string_where_a_list_belongs_is_rejected(self):
        # A string is iterable: `entries = "Grok"` would silently compile one
        # matcher per character and match almost nothing.
        catalog = TERMS_PROFILE.read_text(encoding="utf-8")
        catalog += ('\n[classes.mystery]\nremedy = "rewrite it"\n'
                    'entries = "Frobnitz"\n')
        prof = Path(self.tree) / "barestring.toml"
        prof.write_text(catalog, encoding="utf-8")
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)
        self.assertIn("list", err)


class TestScopeBoundary(TreeCase):
    """Out-of-scope trees are where names are correct and load-bearing."""

    def test_docs_are_not_scanned(self):
        # docs/specs and docs/reviews are dated records that must name the
        # problem to describe it — including this epic's own spec.
        self.put("docs/specs/s.md", "DEFAULT_MODELS = Grok, Gemini, GPT\n")
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"docs/ was scanned:\n{out}")

    def test_scripts_are_not_scanned(self):
        self.put("scripts/init.sh",
                 "echo 'clone https://github.com/kevglynn/house-rules'\n")
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_CLEAN, f"scripts/ was scanned:\n{out}")


class TestAllowlist(TreeCase):
    """An exemption is a recorded decision, not a mute button."""

    def _profile_with_allow(self, body):
        base = TERMS_PROFILE.read_text(encoding="utf-8")
        p = Path(self.tree) / "custom-terms.toml"
        p.write_text(base + textwrap.dedent(body), encoding="utf-8")
        return p

    def test_allowlisted_term_with_a_reason_is_exempt(self):
        self.put("templates/t.md", "Call the Figma MCP to read the file.\n")
        rc, _, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS, "precondition: term must flag first")
        prof = self._profile_with_allow("""
            [[allow]]
            term = "Figma MCP"
            reason = "first-party integration the kit documents by name"
            """)
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_CLEAN, f"allowlist ignored:\n{out}\n{err}")

    def test_allowlist_entry_without_a_reason_is_a_profile_error(self):
        # The required reason is the whole point: an unexplained exemption is
        # indistinguishable from someone silencing a real leak.
        self.put("templates/t.md", "Call the Figma MCP to read the file.\n")
        prof = self._profile_with_allow("""
            [[allow]]
            term = "Figma MCP"
            """)
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)
        self.assertIn("reason", (out + err).lower())

    def test_allowlist_reason_may_not_be_blank(self):
        self.put("templates/t.md", "Call the Figma MCP to read the file.\n")
        prof = self._profile_with_allow("""
            [[allow]]
            term = "Figma MCP"
            reason = "   "
            """)
        rc, out, err = run_scan(self.tree, "--profile", str(prof))
        self.assertEqual(rc, EXIT_ERROR)


class TestInterfaceContract(TreeCase):
    """Exit codes and payload shape agents dispatch on."""

    def test_usage_error_exits_2_with_the_family_envelope(self):
        rc, out, err = run_scan(None, "--no-such-flag")
        self.assertEqual(rc, EXIT_USAGE)
        payload = error_payload(err)
        # Key names match defer-lint / close-reason-lint / banned-token-scan
        # so one wrapper can read errors from all of them.
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["exit_code"], EXIT_USAGE)
        self.assertIn("error", payload)
        self.assertIn("error_kind", payload)

    def test_unreadable_profile_exits_3_with_a_json_error(self):
        rc, out, err = run_scan(None, "--profile", "/nonexistent/terms.toml")
        self.assertEqual(rc, EXIT_ERROR)
        payload = error_payload(err)
        self.assertEqual(payload["error_kind"], "catalog")

    def test_invalid_profile_exits_3(self):
        bad = Path(self.tree) / "bad.toml"
        bad.write_text("this is not = = valid toml\n", encoding="utf-8")
        rc, _, err = run_scan(None, "--profile", str(bad))
        self.assertEqual(rc, EXIT_ERROR)
        error_payload(err)

    def test_errors_are_json_on_stderr_even_in_json_mode(self):
        # An agent running --json must never get a traceback on stdout or a
        # bare exit code it cannot distinguish from "findings found".
        rc, out, err = run_scan(None, "--json", "--profile", "/nonexistent.toml")
        self.assertEqual(rc, EXIT_ERROR)
        self.assertEqual(out.strip(), "")
        error_payload(err)

    def test_json_payload_carries_the_documented_keys(self):
        self.put("templates/t.md", "Use Frobnitz MCP here.\n")
        rc, payload = scan_json(self.tree)
        for key in ("ok", "findings", "scanned", "coverage", "profile", "roots"):
            self.assertIn(key, payload)
        self.assertFalse(payload["ok"])
        for key in ("file", "line", "class", "term", "text"):
            self.assertIn(key, payload["findings"][0])

    def test_the_remedy_is_always_printed_not_hidden_behind_a_flag(self):
        self.put("templates/t.md", "Use Frobnitz MCP here.\n")
        rc, out, _ = run_scan(self.tree)
        self.assertEqual(rc, EXIT_FINDINGS)
        self.assertIn("private_tool_heuristic", out)
        self.assertIn("overlay", out.lower())

    def test_finding_text_is_capped(self):
        # A single-line generated file would otherwise put its whole contents
        # into every finding, and into the JSON payload once per finding.
        self.put("templates/t.md", "x" * 5000 + " Use Frobnitz MCP here.\n")
        rc, payload = scan_json(self.tree)
        self.assertLessEqual(len(payload["findings"][0]["text"]), 200)

    def test_help_names_the_heuristic_limitation(self):
        # The heuristic's blind spot is the thing a reader most needs to know
        # before trusting a clean result.
        rc, out, _ = run_scan(None, "--help")
        self.assertEqual(rc, EXIT_CLEAN)
        self.assertIn("neutrality", out.lower())
        self.assertIn("limitation", out.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
