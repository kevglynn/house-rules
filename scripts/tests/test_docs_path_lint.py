#!/usr/bin/env python3
"""Behavioral tests for scripts/docs-path-lint.

Every test drives the CLI as a subprocess against tempdir fixtures and
asserts observable behavior: exit codes, human/JSON output, and finding
shapes. No internals.

The flagship fixture reproduces the incident that motivated the checker:
active docs teaching `playbook-init.sh` after the script had been renamed
— a stale reference inside a fenced bash block must be caught with the
file, line, and missing path named.

Run: python3 scripts/tests/test_docs_path_lint.py
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "docs-path-lint"

ALLOW = "docs-path-lint:allow"

STALE_FENCE = (
    "# Quickstart\n"
    "\n"
    "Run the installer:\n"
    "\n"
    "```bash\n"
    "bash ~/process-kit/scripts/playbook-init.sh\n"
    "```\n"
)


def run_cli(args, cwd=None):
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class FixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relpath, content):
        p = self.root / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def scan(self, *extra):
        return run_cli(["--root", str(self.root), *extra])

    def scan_json(self, *extra):
        r = run_cli(["--root", str(self.root), "--json", *extra])
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload


def fenced(*lines, tag="bash"):
    return "```" + tag + "\n" + "\n".join(lines) + "\n```\n"


class DocsPathLintTest(FixtureTest):
    # --- AC: a stale script reference in a fenced block is caught ---

    def test_stale_playbook_init_reference_is_finding_exit_1(self):
        self.write("README.md", STALE_FENCE)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(out["ok"])
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["file"], "README.md")
        self.assertEqual(f["line"], 6)
        self.assertEqual(f["path"], "scripts/playbook-init.sh")
        self.assertIn("playbook-init.sh", f["token"])

    def test_repo_relative_and_dot_slash_references_are_checked(self):
        self.write("README.md", fenced(
            "./scripts/gone-one sync",
            "bash scripts/gone-two.sh",
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(sorted(f["path"] for f in out["findings"]),
                         ["scripts/gone-one", "scripts/gone-two.sh"])

    def test_process_kit_env_idiom_is_resolved(self):
        self.write("README.md", fenced(
            'bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/missing-cli" doctor',
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["path"], "scripts/missing-cli")

    def test_bash_invoked_sh_path_outside_scripts_dir_is_checked(self):
        self.write("README.md", fenced("bash setup/missing.sh"))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["path"], "setup/missing.sh")

    # --- Existing references pass ---

    def test_existing_references_in_all_spellings_are_clean(self):
        self.write("scripts/real.sh", "#!/bin/sh\n")
        self.write("scripts/real-cli", "#!/usr/bin/env python3\n")
        self.write("README.md", fenced(
            "bash ~/process-kit/scripts/real.sh",
            "bash ~/house-rules/scripts/real.sh --check",
            "./scripts/real-cli sync --format cursor",
            "bash scripts/real.sh",
            'bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/real-cli" doctor',
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])
        self.assertEqual(out["findings"], [])
        self.assertGreaterEqual(out["refs_checked"], 5)

    def test_glob_reference_is_counted_skip(self):
        # Globs are skipped, not existence-checked — but counted, so the
        # skip is never silent. Promote to real glob checking when a doc
        # actually fences a glob (none do today).
        self.write("docs/a.md", fenced("shellcheck scripts/*.sh"))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["skips_by_reason"].get("glob"), 1)

    def test_trailing_sentence_punctuation_is_trimmed_from_token(self):
        # "see scripts/real-cli." in a fence comment must not flag the
        # existing script; a genuinely missing path keeps its clean name.
        self.write("scripts/real-cli", "#!/usr/bin/env python3\n")
        self.write("README.md", fenced(
            "# see scripts/real-cli.",
            "echo scripts/gone-two.sh.",
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(out["findings"][0]["path"], "scripts/gone-two.sh")

    # --- Scope: only fenced shell blocks in the doc set are scanned ---

    def test_prose_outside_fences_is_not_scanned(self):
        self.write("README.md",
                   "Run `bash scripts/gone.sh` then scripts/also-gone.\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_markdown_tagged_fence_is_not_scanned(self):
        self.write("README.md", fenced(
            "bash scripts/gone.sh", tag="markdown"))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_fence_tag_with_info_string_attributes_is_scanned(self):
        self.write("README.md", fenced(
            "bash scripts/gone.sh", tag='bash title="setup"'))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["path"], "scripts/gone.sh")

    def test_untagged_fence_with_shellish_first_line_is_scanned(self):
        self.write("README.md", fenced("bash scripts/gone.sh", tag=""))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["path"], "scripts/gone.sh")

    def test_untagged_fence_with_prose_first_line_is_not_scanned(self):
        self.write("README.md", fenced(
            "Sample output mentioning scripts/gone.sh", tag=""))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_list_indented_fence_is_scanned(self):
        self.write("README.md", (
            "1. Clone it:\n"
            "   ```bash\n"
            "   bash scripts/gone.sh\n"
            "   ```\n"
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["line"], 3)

    def test_doc_set_selection(self):
        bad = fenced("bash scripts/gone.sh")
        # In the set: root README/QUICKSTART/WELCOME/AGENTS/CONTRIBUTING,
        # docs/*.md, sandbox/*.md.
        self.write("QUICKSTART.md", bad)
        self.write("AGENTS.md", bad)
        self.write("CONTRIBUTING.md", bad)
        self.write("docs/faq.md", bad)
        self.write("sandbox/WALKTHROUGH.md", bad)
        # Out of the set: nested docs dirs (historical records), other root
        # files, sandbox subdirs, global-safety-net (commands live in
        # tables/blockquotes a fence scanner cannot see).
        self.write("docs/specs/plan.md", bad)
        self.write("CLAUDE.md", bad)
        self.write("sandbox/project/notes.md", bad)
        self.write("global-safety-net/agent-protocol.md", bad)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(sorted(f["file"] for f in out["findings"]),
                         ["AGENTS.md", "CONTRIBUTING.md", "QUICKSTART.md",
                          "docs/faq.md", "sandbox/WALKTHROUGH.md"])
        self.assertEqual(out["files_scanned"], 5)

    # --- Placeholder and outside-repo tokens are skipped ---

    def test_placeholder_tokens_are_skipped(self):
        self.write("README.md", fenced(
            "bash scripts/<your-script>.sh",
            "bash scripts/$SCRIPT_NAME.sh",
            "cp scripts/YYYY-MM-DD-report.sh backups/",
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertGreaterEqual(out["refs_skipped"], 3)

    def test_home_and_absolute_paths_outside_clone_are_skipped(self):
        self.write("README.md", fenced(
            "source ~/.house-rules-aliases.sh",
            "bash /opt/other/tool.sh",
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_urls_are_skipped(self):
        self.write("README.md", fenced(
            "curl -O https://example.com/x/scripts/remote.sh",
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    # --- Allow marker: deliberate exceptions, never silent ---

    def test_allow_marker_suppresses_next_fence_only(self):
        self.write("README.md", (
            f"<!-- {ALLOW} -->\n"
            + fenced("bash scripts/illustrative.sh")
            + fenced("bash scripts/really-gone.sh")
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(out["findings"][0]["path"], "scripts/really-gone.sh")
        self.assertEqual(out["refs_allowed"], 1)

    def test_allow_marker_skips_unscannable_fence_to_next_scannable(self):
        # A ```markdown example fence between the marker and the intended
        # bash fence is never consulted; arming it would silently waste
        # the exception.
        self.write("README.md", (
            f"<!-- {ALLOW} -->\n"
            + fenced("bash scripts/example.sh", tag="markdown")
            + fenced("bash scripts/illustrative.sh")
        ))
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["refs_allowed"], 1)

    def test_embedded_marker_substring_is_inert(self):
        # Whole-token contract, both directions: a longer word carrying
        # the marker as a substring must not arm an exception. The prefix
        # case is the dangerous one — a naive substring match would turn
        # it into allow-everything for the next fence.
        for embedded in (f"{ALLOW}list-of-things", f"x{ALLOW}"):
            with self.subTest(embedded=embedded):
                self.write("README.md", (
                    f"<!-- {embedded} -->\n"
                    + fenced("bash scripts/gone.sh")
                ))
                r, out = self.scan_json()
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertEqual(out["refs_allowed"], 0)

    # --- Output shapes ---

    def test_human_output_names_file_line_and_missing_path(self):
        self.write("README.md", STALE_FENCE)
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertIn("README.md:6", r.stdout)
        self.assertIn("scripts/playbook-init.sh", r.stdout)

    def test_clean_tree_human_output_names_scan_summary(self):
        self.write("README.md", fenced("git status"))
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("clean", r.stdout)

    def test_json_top_level_shape(self):
        # No exit_code key: the process exit code is the contract, matching
        # the sibling checkers' payload shape.
        self.write("README.md", STALE_FENCE)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "root", "files_scanned", "fences_scanned",
                    "fences_skipped", "refs_checked", "refs_allowed",
                    "refs_skipped", "skips_by_reason", "findings"):
            self.assertIn(key, out)
        self.assertNotIn("exit_code", out)
        f = out["findings"][0]
        for key in ("file", "line", "path", "token", "text"):
            self.assertIn(key, f)

    # --- Agent-CLI conventions: stable exit codes ---

    def test_empty_root_is_usage_error_exit_2(self):
        # Pinning the stderr JSON distinguishes "argparse rejected the
        # input" from "the interpreter never ran the program" (a deleted
        # CLI also exits 2) and pins the JSON-on-stderr agent convention.
        r = run_cli(["--root", ""])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["exit_code"], 2)

    def test_nonexistent_root_is_io_error_exit_3(self):
        r = run_cli(["--root", str(self.root / "nope")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_root_with_no_docs_is_io_error_exit_3(self):
        # A mis-pointed --root must not lie green in CI: zero doc files
        # found is an error, not a clean scan.
        r = self.scan()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "io")

    def test_unknown_flag_is_usage_error_exit_2(self):
        r = run_cli(["--bogus"])
        self.assertEqual(r.returncode, 2)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["exit_code"], 2)

    def test_help_exits_zero_and_carries_worked_examples(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("playbook-init.sh", r.stdout)
        self.assertIn(ALLOW, r.stdout)
        self.assertIn("known limitations", r.stdout)


if __name__ == "__main__":
    unittest.main()
