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

    def test_near_miss_trigger_text_is_still_violation(self):
        # Mutation guard: a detector looser than the full "upgrade when:"
        # phrase (bare word, or missing colon) must NOT pass these.
        self.write("a.py", f"# {D} old client. ceiling: misses fields. should upgrade eventually.\n")
        self.write("b.py", f"# {D} raw sql. ceiling: injection-prone. upgrade when we get time.\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 2)
        for f in out["findings"]:
            self.assertIn("upgrade-when", f["missing"])

    def test_uppercase_clauses_are_recognized(self):
        # Continuation lines plausibly start capitalized; matching is
        # case-insensitive by design.
        self.write(
            "a.py",
            f"# {D} single retry. Ceiling: transient failures surface.\n"
            "# Upgrade when: flake rate exceeds 1%.\n",
        )
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["defer_comments"], 1)

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

    def test_plain_string_mention_without_marker_is_not_a_defer(self):
        # The comment-marker requirement keeps prose/log strings that merely
        # mention the convention out of the scan.
        self.write("a.py", f'msg = "{D} plain mention, no comment marker"\n')
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_symlinked_dir_and_file_are_not_followed(self):
        # Payload lives under .git (never scanned directly); symlinks to it
        # from scanned space must not resurrect it.
        payload = self.write(".git/payload/bad.py", BAD_NO_TRIGGER)
        os.symlink(payload.parent, self.root / "linkdir")
        os.symlink(payload, self.root / "linkfile.py")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 0)

    def test_makefile_and_dockerfile_are_scanned(self):
        self.write("Makefile", BAD_NO_TRIGGER)
        self.write("Dockerfile", BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 2)

    def test_unreadable_binary_files_are_counted_as_skipped(self):
        # A scan that silently drops files can report "clean" on a tree it
        # mostly failed to read; the JSON must expose the skip count.
        p = self.root / "blob.py"
        p.write_bytes(b"\x00\x01" + BAD_NO_TRIGGER.encode())
        self.write("ok.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["files_skipped"], 1)
        self.assertEqual(out["files_scanned"], 1)

    def test_extensionless_file_with_shebang_is_scanned(self):
        self.write("bin/tool", "#!/usr/bin/env python3\n" + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["file"], "bin/tool")

    def test_running_copy_scanning_its_own_tree_is_clean(self):
        # A distributed copy scanning the tree it lives in must not flag
        # its own --help examples or regex source.
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

    def test_kit_copy_scanning_tree_with_distributed_copy_is_clean(self):
        # The kit's own copy is routinely invoked against bootstrapped target
        # repos that carry a distributed copy at scripts/defer-lint. That copy
        # is a different path from the running one — the exclusion contract
        # must hold by content, not path identity.
        dest = self.root / "scripts" / "defer-lint"
        dest.parent.mkdir(parents=True)
        shutil.copy(CLI, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR)
        r, out = self.scan_json()  # runs the ORIGINAL CLI over self.root
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(
            [f for f in out["findings"] if f["file"] == "scripts/defer-lint"],
            [],
        )

    # --- Output shapes ---

    def test_human_output_names_file_line_and_missing_clause(self):
        self.write("src/a.py", BAD_NO_TRIGGER)
        r = self.scan()
        self.assertEqual(r.returncode, 1)
        self.assertIn("src/a.py:1", r.stdout)
        self.assertIn("upgrade-when", r.stdout)

    def test_clean_tree_human_output_names_scan_summary(self):
        self.write("a.py", "x = 1\n")
        r = self.scan()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Scanned 1 files", r.stdout)
        self.assertIn("clean", r.stdout)

    def test_json_top_level_shape(self):
        # No exit_code key: the process exit code is the contract, matching
        # tdd-ledger's payload shape.
        self.write("a.py", GOOD_ONE_LINE + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "root", "files_scanned", "files_skipped",
                    "defer_comments", "findings"):
            self.assertIn(key, out)
        self.assertNotIn("exit_code", out)
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
