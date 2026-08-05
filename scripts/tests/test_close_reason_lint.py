#!/usr/bin/env python3
"""Behavioral tests for scripts/close-reason-lint.

Every test drives the CLI as a subprocess against JSON fixtures (file or
stdin) and asserts observable behavior: exit codes, human/JSON output, and
finding shapes. No internals.

Fixtures mimic the bd JSON surface: `bd list --status=closed --json`
returns an array of bead objects carrying id, issue_type, status,
close_reason, and acceptance_criteria; `bd show <id> --json` returns a
one-element array of the same shape.

Run: python3 scripts/tests/test_close_reason_lint.py
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "close-reason-lint"

GOOD_REASON = "Commit ab34f9e on main. AC1: loading indicator verified. AC2: error state renders."
NO_REF_REASON = "AC1: verified manually. AC2: renders as specified."
NO_AC_REASON = "Done in commit ab34f9e, all good."
BARE_REASON = "Done."


def bead(id="pk-1", issue_type="feature", reason=GOOD_REASON,
         acs="- shows a loading indicator\n- renders the error state",
         status="closed", **extra):
    b = {
        "id": id,
        "title": "fixture bead",
        "issue_type": issue_type,
        "status": status,
        "close_reason": reason,
        "acceptance_criteria": acs,
    }
    b.update(extra)
    return b


def run_cli(args, stdin_text=None):
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        input=stdin_text,
    )


class CloseReasonLintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def lint(self, beads, *extra):
        payload = json.dumps(beads)
        return run_cli(["--json", *extra], stdin_text=payload)

    def lint_json(self, beads, *extra):
        r = self.lint(beads, *extra)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload

    # --- AC: flags closed beads whose reasons lack a commit-ref ---

    def test_reason_without_commit_ref_is_flagged_exit_1(self):
        r, out = self.lint_json([bead(reason=NO_REF_REASON)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(out["ok"])
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["id"], "pk-1")
        self.assertIn("commit-ref", f["missing"])
        self.assertEqual(f["severity"], "error")

    def test_hex_hash_counts_as_commit_ref(self):
        r, out = self.lint_json(
            [bead(reason="Landed in 1920608. AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_pr_url_counts_as_commit_ref(self):
        r, out = self.lint_json([bead(
            reason="See https://github.com/o/r/pull/42 — AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_conventional_branch_name_counts_as_commit_ref(self):
        r, out = self.lint_json([bead(
            reason="On feat/pk-1-loading-state. AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_branch_keyword_form_counts_as_commit_ref(self):
        r, out = self.lint_json([bead(
            reason="Pushed to branch spike-exploration. AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_decimal_word_alone_is_not_a_commit_ref(self):
        # "closed 20260804" is a date, but hex-plausible; the checker is a
        # candidate reporter — what must NOT count is a non-hex word.
        r, out = self.lint_json([bead(
            reason="AC1: verified. Deployed to staging zone.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    # --- AC: flags closed beads whose reasons lack AC-mapping shape ---

    def test_reason_without_ac_mapping_is_flagged_exit_1(self):
        r, out = self.lint_json([bead(reason=NO_AC_REASON)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        f = out["findings"][0]
        self.assertIn("ac-mapping", f["missing"])
        self.assertEqual(f["severity"], "error")

    def test_numbered_ac_reference_counts_as_mapping(self):
        r, out = self.lint_json([bead(
            reason="Commit ab34f9e. AC 1 and AC-2 both verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_acceptance_criteria_phrase_counts_as_mapping(self):
        r, out = self.lint_json([bead(
            reason="Commit ab34f9e. All acceptance criteria verified by test run.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_lowercase_ac_word_fragment_is_not_mapping(self):
        # "acid", "reach", etc. must not satisfy the AC-mapping shape.
        r, out = self.lint_json([bead(
            reason="Commit ab34f9e. Reached acid-test parity each way.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ac-mapping", out["findings"][0]["missing"])

    def test_bead_without_acceptance_criteria_skips_ac_mapping_check(self):
        # Cannot demand mapping to ACs that do not exist.
        r, out = self.lint_json([bead(reason=NO_AC_REASON, acs="")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_missing_both_reports_both_in_one_finding(self):
        r, out = self.lint_json([bead(reason=BARE_REASON)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(sorted(out["findings"][0]["missing"]),
                         ["ac-mapping", "commit-ref"])

    # --- Empty reason ---

    def test_empty_close_reason_is_flagged(self):
        r, out = self.lint_json([bead(reason="")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("close-reason", out["findings"][0]["missing"])

    # --- Exemptions (bead-completion.mdc evidence table) ---

    def test_docs_decision_milestone_epic_are_exempt(self):
        beads = [
            bead(id="pk-d", issue_type="docs",
                 reason="N/A — documentation update, no verification needed"),
            bead(id="pk-x", issue_type="decision",
                 reason="N/A — decision record, no verification needed"),
            bead(id="pk-m", issue_type="milestone",
                 reason="N/A — milestone marker, verify children are closed"),
            bead(id="pk-e", issue_type="epic",
                 reason="All children closed; success criteria met."),
        ]
        r, out = self.lint_json(beads)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["beads_exempt"], 4)
        self.assertEqual(out["beads_checked"], 0)

    def test_chore_missing_commit_ref_is_warning_exit_0(self):
        r, out = self.lint_json([bead(
            issue_type="chore", reason="Swept stale branches.", acs="")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["missing"], ["commit-ref"])
        self.assertEqual(f["severity"], "warning")

    def test_spike_missing_commit_ref_is_warning_exit_0(self):
        r, out = self.lint_json([bead(
            issue_type="spike",
            reason="Question answered: AC1 approach is viable.",
            acs="- is the approach viable?")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["severity"], "warning")

    def test_chore_with_acs_still_gets_ac_mapping_error(self):
        r, out = self.lint_json([bead(
            issue_type="chore", reason="Swept stale branches.",
            acs="- sweep completes")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        f = out["findings"][0]
        self.assertIn("ac-mapping", f["missing"])
        self.assertEqual(f["severity"], "error")

    # --- Input handling ---

    def test_non_closed_beads_are_skipped(self):
        beads = [bead(reason=BARE_REASON, status="open"),
                 bead(id="pk-2", reason=BARE_REASON, status="in_progress")]
        r, out = self.lint_json(beads)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["beads_skipped"], 2)

    def test_single_object_input_is_accepted(self):
        r, out = self.lint_json(bead(reason=BARE_REASON))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)

    def test_input_file_flag(self):
        p = self.root / "closed.json"
        p.write_text(json.dumps([bead(reason=BARE_REASON)]))
        r = run_cli(["--input", str(p), "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(len(out["findings"]), 1)

    def test_missing_input_file_is_io_error_exit_3(self):
        r = run_cli(["--input", str(self.root / "nope.json")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_invalid_json_is_input_error_exit_3(self):
        r = run_cli(["--json"], stdin_text="this is not json")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])

    def test_unknown_flag_is_usage_error_exit_2(self):
        r = run_cli(["--bogus"], stdin_text="[]")
        self.assertEqual(r.returncode, 2)

    # --- Output shapes ---

    def test_json_top_level_shape(self):
        r, out = self.lint_json([bead(), bead(id="pk-2", reason=BARE_REASON)])
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "beads_checked", "beads_exempt", "beads_skipped",
                    "findings"):
            self.assertIn(key, out)
        self.assertNotIn("exit_code", out)
        self.assertEqual(out["beads_checked"], 2)
        f = out["findings"][0]
        for key in ("id", "issue_type", "missing", "severity", "reason"):
            self.assertIn(key, f)

    def test_human_output_names_bead_and_missing_checks(self):
        r = run_cli([], stdin_text=json.dumps([bead(reason=BARE_REASON)]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("pk-1", r.stdout)
        self.assertIn("commit-ref", r.stdout)
        self.assertIn("ac-mapping", r.stdout)

    def test_clean_input_human_output_names_summary(self):
        r = run_cli([], stdin_text=json.dumps([bead()]))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Checked 1", r.stdout)
        self.assertIn("clean", r.stdout)

    def test_help_exits_zero_and_carries_worked_examples(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("bd list --status=closed --json", r.stdout)
        self.assertIn("commit-ref", r.stdout)
        self.assertIn("ac-mapping", r.stdout)
        self.assertIn("exempt", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
