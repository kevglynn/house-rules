#!/usr/bin/env python3
"""Behavioral tests for scripts/defer-lint.

Every test drives the CLI as a subprocess against tempdir fixtures and
asserts observable behavior: exit codes, human/JSON output, and finding
shapes. No internals.

Fixture texts build the marker from parts (D below) so this file's own
source never contains a comment-marker-adjacent defer string — the checker
must never need to special-case test content.

Run: python3 scripts/tests/test_defer_lint.py
"""

import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "defer-lint"

# Assembled so the literal comment-marker + marker-word sequence never
# appears in this file at rest (path/fixture exclusion, not content
# special-casing, is how the checker itself stays clean).
D = "defer" + ":"

GOOD_ONE_LINE = f"# {D} in-memory cache. ceiling: lost on restart. upgrade when: sessions must survive deploys.\n"
GOOD_TWO_LINE = (
    f"# {D} global lock on config reload. ceiling: blocks requests (~50ms).\n"
    "# upgrade when: reload frequency exceeds 1/minute.\n"
)
BAD_NO_TRIGGER = f"# {D} simplified validation.\n"
BAD_CEILING_ONLY = f"# {D} in-memory cache. ceiling: lost on restart.\n"
BAD_TRIGGER_ONLY = f"# {D} naive retry. upgrade when: upstream starts throttling.\n"


def run_cli(args, cwd=None):
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class DeferLintTest(unittest.TestCase):
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

    # --- AC: flags defer comments lacking an upgrade-when clause ---

    def test_no_trigger_defer_is_violation_exit_1(self):
        self.write("src/a.py", "x = 1\n" + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(out["ok"])
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["file"], "src/a.py")
        self.assertEqual(f["line"], 2)
        self.assertIn("upgrade-when", f["missing"])
        self.assertEqual(f["severity"], "error")

    def test_ceiling_without_trigger_is_still_violation(self):
        self.write("a.py", BAD_CEILING_ONLY)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)
        self.assertEqual(out["findings"][0]["missing"], ["upgrade-when"])

    # --- AC: complete defers pass, including multi-line continuation ---

    def test_complete_one_line_defer_is_clean_exit_0(self):
        self.write("a.py", GOOD_ONE_LINE)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["defer_comments"], 1)

    def test_two_line_defer_with_trigger_on_continuation_is_clean(self):
        # The rule's own canonical examples are two-line comments; a naive
        # single-line check false-positives on them.
        self.write("a.py", "x = 1\n" + GOOD_TWO_LINE + "y = 2\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_multi_line_defer_still_missing_trigger_is_violation(self):
        self.write(
            "a.py",
            f"# {D} naive approach. ceiling: slow on big inputs.\n"
            "# profiled once, looked fine.\n"
            "x = 1\n",
        )
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)
        self.assertIn("upgrade-when", out["findings"][0]["missing"])

    def test_continuation_stops_at_non_comment_line(self):
        # The trigger appearing in later CODE must not rescue the defer.
        self.write(
            "a.py",
            BAD_NO_TRIGGER + 'x = "upgrade when: never, this is code"\n',
        )
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)

    # --- Missing ceiling: lesser severity, does not fail the scan ---

    def test_missing_ceiling_only_is_warning_exit_0(self):
        self.write("a.py", BAD_TRIGGER_ONLY)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["missing"], ["ceiling"])
        self.assertEqual(f["severity"], "warning")

    # --- Comment syntaxes ---

    def test_slash_slash_and_dashes_and_block_comments(self):
        self.write("a.js", f"// {D} shortcut. ceiling: x. upgrade when: y.\n")
        self.write("b.sql", f"-- {D} full scan. ceiling: x. upgrade when: y.\n")
        self.write("c.css", f"/* {D} magic number. ceiling: x. upgrade when: y. */\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 3)
        self.assertEqual(out["findings"], [])

    def test_block_comment_continuation_without_star_prefix(self):
        self.write(
            "a.c",
            f"/* {D} fixed buffer. ceiling: 4k payloads.\n"
            "   upgrade when: payloads exceed 4k in prod. */\n",
        )
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_star_prefixed_block_continuation(self):
        self.write(
            "a.java",
            f"/* {D} sync call. ceiling: blocks the event loop.\n"
            " * upgrade when: p99 latency matters. */\n",
        )
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_bad_defer_in_slash_comment_is_flagged(self):
        self.write("a.ts", f"// {D} no trigger here at all.\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)

    # --- File selection ---

    def test_skips_git_and_node_modules(self):
        self.write(".git/hooks/x.py", BAD_NO_TRIGGER)
        self.write("node_modules/pkg/i.js", f"// {D} vendored.\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_skips_binary_files(self):
        p = self.root / "blob.py"
        p.write_bytes(b"\x00\x01" + BAD_NO_TRIGGER.encode())
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_markdown_prose_is_not_scanned(self):
        # Rule/docs files quote bad examples in fences; those are prose.
        self.write("README.md", BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_extensionless_file_with_shebang_is_scanned(self):
        self.write("bin/tool", "#!/usr/bin/env python3\n" + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["file"], "bin/tool")

    def test_exclude_flag_skips_path(self):
        self.write("gen/out.py", BAD_NO_TRIGGER)
        r, out = self.scan_json("--exclude", "gen")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_checker_excludes_its_own_running_copy(self):
        # The CLI's --help epilog carries worked bad examples; a copy of the
        # checker inside the scanned tree must not flag itself.
        dest = self.root / "scripts" / "defer-lint"
        dest.parent.mkdir(parents=True)
        shutil.copy(CLI, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR)
        r = subprocess.run(
            ["python3", str(dest), "--root", str(self.root), "--json"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])

    # --- Output shapes ---

    def test_human_output_names_file_line_and_missing_clause(self):
        self.write("src/a.py", BAD_NO_TRIGGER)
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertIn("src/a.py:1", r.stdout)
        self.assertIn("upgrade-when", r.stdout)

    def test_clean_tree_human_output_exit_0(self):
        self.write("a.py", "x = 1\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_json_top_level_shape(self):
        self.write("a.py", GOOD_ONE_LINE + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "root", "files_scanned", "defer_comments",
                    "findings", "exit_code"):
            self.assertIn(key, out)
        self.assertEqual(out["exit_code"], 1)
        self.assertEqual(out["defer_comments"], 2)
        f = out["findings"][0]
        for key in ("file", "line", "text", "missing", "severity"):
            self.assertIn(key, f)
        self.assertIn(D, f["text"])

    # --- Agent-CLI conventions: stable exit codes ---

    def test_empty_root_is_usage_error_exit_2(self):
        r = run_cli(["--root", ""])
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_nonexistent_root_is_io_error_exit_3(self):
        r = run_cli(["--root", str(self.root / "nope")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_root_that_is_a_file_is_io_error_exit_3(self):
        p = self.write("f.py", "x = 1\n")
        r = run_cli(["--root", str(p)])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_unknown_flag_is_usage_error_exit_2(self):
        r = run_cli(["--bogus"])
        self.assertEqual(r.returncode, 2)

    def test_help_exits_zero_and_carries_worked_examples(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("upgrade when:", r.stdout)
        self.assertIn("ceiling:", r.stdout)
        self.assertIn("TODO", r.stdout)  # marker comparison lives here now
        self.assertIn("FIXME", r.stdout)


if __name__ == "__main__":
    unittest.main()
