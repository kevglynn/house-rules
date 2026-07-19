#!/usr/bin/env python3
"""Behavioral tests for scripts/tdd-ledger.

Every test drives the CLI as a subprocess and asserts observable behavior:
exit codes, JSON stdout/stderr, and ledger file contents. No internals.

Run: python3 scripts/tests/test_tdd_ledger.py
"""

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "tdd-ledger"


def run_cli(args, cwd=None, env_extra=None):
    env = os.environ.copy()
    # Isolate from any real ledger config in the invoking environment.
    env.pop("TDD_LEDGER_PATH", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def read_ledger(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


class TddLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.ledger = self.dir / "ledger.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, event, test_id, bead=None, output=None, ledger=None):
        cmd = {"red": "record-failing", "green": "record-passing"}[event]
        args = [cmd, "--test-id", test_id, "--ledger", str(ledger or self.ledger)]
        if bead:
            args += ["--bead", bead]
        if output is not None:
            args += ["--output", output]
        return run_cli(args, cwd=self.dir)

    def verify(self, ledger=None):
        return run_cli(["verify", "--ledger", str(ledger or self.ledger)], cwd=self.dir)

    # --- AC1: record commands append entries with the required shape ---

    def test_record_failing_appends_red_entry(self):
        r = self.record("red", "test_login", bead="kit-abc", output="AssertionError: boom")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["ok"])
        entries = read_ledger(self.ledger)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["event"], "red")
        self.assertEqual(e["test_id"], "test_login")
        self.assertEqual(e["bead"], "kit-abc")
        expected_digest = hashlib.sha256(b"AssertionError: boom").hexdigest()
        self.assertEqual(e["output_digest"], expected_digest)
        self.assertIn("commit", e)
        self.assertIn("ts", e)

    def test_record_passing_appends_green_entry(self):
        self.record("red", "test_login")
        r = self.record("green", "test_login", output="2 passed")
        self.assertEqual(r.returncode, 0, r.stderr)
        entries = read_ledger(self.ledger)
        self.assertEqual([e["event"] for e in entries], ["red", "green"])

    def test_output_is_digested_as_literal_even_if_it_names_a_file(self):
        # Review finding: file-vs-literal sniffing silently digested the wrong
        # bytes when a short literal happened to name an existing file.
        # Contract is literal-only; file callers use --output "$(cat log)".
        out_file = self.dir / "pass"
        out_file.write_text("file contents that must NOT be digested\n")
        r = self.record("red", "test_x", output="pass")
        self.assertEqual(r.returncode, 0, r.stderr)
        e = read_ledger(self.ledger)[0]
        self.assertEqual(e["output_digest"], hashlib.sha256(b"pass").hexdigest())

    # --- AC1: verify invariants ---

    def test_verify_clean_ledger_exits_zero(self):
        self.record("red", "test_a", output="fail")
        self.record("green", "test_a", output="pass")
        r = self.verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["ok"])
        self.assertEqual(out["violations"], [])

    def test_verify_missing_ledger_exits_zero(self):
        r = self.verify(ledger=self.dir / "does-not-exist.jsonl")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(json.loads(r.stdout)["ok"])

    def test_green_without_red_is_violation(self):
        self.record("green", "test_never_failed", output="pass")
        r = self.verify()
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertFalse(out["ok"])
        reasons = [v["reason"] for v in out["violations"]]
        self.assertIn("green-without-red", reasons)
        # The violation names the offending entry.
        self.assertEqual(
            out["violations"][0]["entry"]["test_id"], "test_never_failed"
        )

    def test_red_after_green_is_missing_red_violation(self):
        # Red exists but only AFTER the green — ordering violation.
        self.record("green", "test_b", output="pass")
        self.record("red", "test_b", output="fail")
        r = self.verify()
        self.assertEqual(r.returncode, 1)
        reasons = [v["reason"] for v in json.loads(r.stdout)["violations"]]
        self.assertIn("missing-red", reasons)

    def test_bead_mismatch_between_red_and_green_is_violation(self):
        self.record("red", "test_c", bead="kit-111", output="fail")
        self.record("green", "test_c", bead="kit-222", output="pass")
        r = self.verify()
        self.assertEqual(r.returncode, 1)
        reasons = [v["reason"] for v in json.loads(r.stdout)["violations"]]
        self.assertIn("id-mismatch", reasons)

    def test_malformed_ledger_line_is_violation_not_crash(self):
        self.ledger.write_text('{"event": "red", "test_id": "t"}\nnot json\n')
        r = self.verify()
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertFalse(out["ok"])
        reasons = [v["reason"] for v in out["violations"]]
        self.assertIn("malformed-entry", reasons)
        # The valid line on the same ledger is still processed.
        self.assertEqual(out["entries"], 1)

    def test_non_utf8_ledger_line_is_malformed_violation_not_crash(self):
        with open(self.ledger, "wb") as f:
            f.write(b'{"event": "red", "test_id": "t"}\n')
            f.write(b"\xff\xfe garbage bytes\n")
        r = self.verify()
        self.assertEqual(r.returncode, 1, r.stderr)
        out = json.loads(r.stdout)
        reasons = [v["reason"] for v in out["violations"]]
        self.assertIn("malformed-entry", reasons)
        self.assertEqual(out["entries"], 1)

    # --- Idempotency ---

    def test_duplicate_record_is_noop(self):
        r1 = self.record("red", "test_dup", output="same output")
        r2 = self.record("red", "test_dup", output="same output")
        self.assertEqual(r1.returncode, 0)
        self.assertEqual(r2.returncode, 0)
        self.assertTrue(json.loads(r2.stdout).get("skipped"))
        self.assertEqual(len(read_ledger(self.ledger)), 1)

    def test_different_output_is_not_a_duplicate(self):
        self.record("red", "test_dup2", output="first failure")
        self.record("red", "test_dup2", output="second failure")
        self.assertEqual(len(read_ledger(self.ledger)), 2)

    def test_same_failure_different_bead_is_recorded_not_skipped(self):
        # Review finding: dedup excluded bead while verify matched on it,
        # so a re-record under a new bead was silently dropped and later
        # produced a false id-mismatch.
        self.record("red", "test_moved", bead="kit-1", output="fail")
        r = self.record("red", "test_moved", bead="kit-2", output="fail")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout).get("skipped"))
        self.assertEqual(len(read_ledger(self.ledger)), 2)
        self.record("green", "test_moved", bead="kit-2", output="pass")
        v = self.verify()
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)

    # --- Ledger path resolution ---

    def test_default_ledger_path_is_repo_root_with_real_commit(self):
        # Review finding: the no-flag/no-env default is the exact invocation
        # CI uses, and it was untested — a resolution regression would
        # silently neuter the gate (missing ledger verifies clean).
        repo = self.dir / "repo"
        subdir = repo / "src"
        subdir.mkdir(parents=True)
        env = {
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
        }
        for cmd in (["git", "init", "-q"],
                    ["git", "commit", "-q", "--allow-empty", "-m", "x"]):
            subprocess.run(cmd, cwd=repo, env={**os.environ, **env},
                           capture_output=True, check=True)
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        r = run_cli(["record-failing", "--test-id", "test_d", "--output", "x"],
                    cwd=subdir)
        self.assertEqual(r.returncode, 0, r.stderr)
        default_ledger = repo / ".tdd-ledger.jsonl"
        self.assertTrue(default_ledger.exists(),
                        "ledger must land at the git repo root")
        e = read_ledger(default_ledger)[0]
        self.assertEqual(e["commit"], head)
        # Pin the CI invocation end-to-end: bare `verify` from inside the
        # repo must find the same ledger (a red-only ledger is clean).
        v = run_cli(["verify"], cwd=subdir)
        self.assertEqual(v.returncode, 0, v.stdout + v.stderr)
        self.assertEqual(json.loads(v.stdout)["entries"], 1)

    def test_env_var_overrides_default_ledger_path(self):
        env_ledger = self.dir / "env-ledger.jsonl"
        r = run_cli(
            ["record-failing", "--test-id", "test_env", "--output", "x"],
            cwd=self.dir,
            env_extra={"TDD_LEDGER_PATH": str(env_ledger)},
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(env_ledger.exists())

    # --- Agent-CLI conventions ---

    def test_usage_error_exits_2_with_json_on_stderr(self):
        r = run_cli(["record-failing"], cwd=self.dir)  # missing --test-id
        self.assertEqual(r.returncode, 2)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])

    def test_empty_test_id_is_usage_error(self):
        # Realistic trigger: an unset shell variable (--test-id "$TEST_ID")
        # would otherwise record evidence identifying no test.
        r = self.record("red", "", output="x")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(json.loads(r.stderr)["ok"])

    def test_empty_ledger_flag_is_usage_error(self):
        # --ledger "" must not silently fall through to the default path.
        r = run_cli(["verify", "--ledger", ""], cwd=self.dir)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertFalse(json.loads(r.stderr)["ok"])

    def test_unreadable_ledger_is_json_io_error_not_traceback(self):
        # Review finding: I/O failures leaked tracebacks with exit 1 —
        # indistinguishable from a TDD violation to the CI gate.
        r = run_cli(["verify", "--ledger", str(self.dir)], cwd=self.dir)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_record_into_parent_that_is_a_file_is_json_io_error(self):
        blocker = self.dir / "notadir"
        blocker.write_text("i am a file")
        r = self.record("red", "test_e", output="x",
                        ledger=blocker / "ledger.jsonl")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_help_exits_zero(self):
        r = run_cli(["--help"], cwd=self.dir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("verify", r.stdout)


if __name__ == "__main__":
    unittest.main()
