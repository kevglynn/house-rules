#!/usr/bin/env python3
"""Behavioral tests for scripts/close-reason-lint.

Every test drives the CLI as a subprocess against JSON fixtures (file or
stdin) and asserts observable behavior: exit codes, human/JSON output, and
finding shapes. One deliberate unit-level exception: the structural
fallback-parity pin loads the CLI as a module, because sample-based scans
cannot pin pattern equality (same idiom as test_defer_lint.py).

Fixtures mimic the bd JSON surface: `bd list --status=closed --json`
returns an array of bead objects carrying id, issue_type, status,
close_reason, and acceptance_criteria; `bd show <id> --json` returns a
one-element array of the same shape.

The close-evidence shape (detectors, per-type requires, IOU phrases) is
profile-driven (bead process-kit-ywq): ProfileShapeTest covers the
resolution chain and fallback posture, ReconciledProfilePinsTest pins the
reconciled kit-profile detectors, FallbackParityTest pins built-in
fallback parity structurally and behaviorally.

Run: python3 scripts/tests/test_close_reason_lint.py
"""

import importlib.util
import json
import os
import subprocess
import tempfile
import tomllib
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "close-reason-lint"
REPO = CLI.parent.parent
PROFILE = REPO / "profiles" / "conventions.toml"

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


def run_cli(args, stdin_text=None, cwd=None, env_extra=None):
    # CONVENTIONS_PROFILE is scrubbed so a profile configured in the
    # developer's environment can never leak shape into a fixture run
    # (same hygiene as test_defer_lint.py / test_conventions.py).
    env = {k: v for k, v in os.environ.items() if k != "CONVENTIONS_PROFILE"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        input=stdin_text,
        cwd=cwd,
        env=env,
    )


def alt_close_profile(docs_requires="na_marker"):
    """A minimal-but-complete [close_evidence] profile with detectors, an
    IOU list, and per-type requires that all differ from the kit's, so
    tests can prove the shape comes from the profile, not any built-in."""
    return (
        "schema_version = 1\n"
        'profile = "fixture"\n'
        "\n"
        "[close_evidence]\n"
        'iou_phrases = ["will be verified later", "handshake promise"]\n'
        "iou_exempt = { pattern = 'deferred to bead \\S+',"
        ' flags = ["IGNORECASE"] }\n'
        "\n"
        "[close_evidence.elements.commit_ref]\n"
        'description = "change-record reference"\n'
        "pattern = 'CR-\\d+'\n"
        "\n"
        "[close_evidence.elements.ac_mapping]\n"
        'description = "criterion tag"\n'
        "pattern = '\\bAC\\s*\\d+'\n"
        "\n"
        "[close_evidence.by_type.task]\n"
        'requires = ["commit_ref", "ac_mapping"]\n'
        "\n"
        "[close_evidence.by_type.feature]\n"
        'requires = ["commit_ref", "ac_mapping"]\n'
        "\n"
        # No ref_severity: the default (error) applies — the kit profile's
        # chore softening must be shown to be profile data, not code.
        "[close_evidence.by_type.chore]\n"
        'requires = ["commit_ref"]\n'
        "\n"
        "[close_evidence.by_type.docs]\n"
        f'requires = ["{docs_requires}"]\n'
    )


class CloseReasonLintTest(unittest.TestCase):
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

    def test_all_letter_hex_word_is_not_a_commit_ref(self):
        # Near-miss guard: 7+ chars of pure hex alphabet with no digit is
        # an English word, not a hash.
        r, out = self.lint_json([bead(
            reason="AC1: verified. Config was effaced deliberately.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_file_path_is_not_a_commit_ref(self):
        # docs/... and test/... file paths collide with the branch-type
        # alternation; a dotted or hyphenless slug is a path, not a branch.
        for path in ("docs/specs/plan.md", "test/utils.py"):
            with self.subTest(path=path):
                r, out = self.lint_json([bead(
                    reason=f"AC1: verified via {path} walkthrough.")])
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_branch_keyword_followed_by_prose_is_not_a_ref(self):
        # "the branch after merge" cites no branch; the keyword form only
        # counts when followed by a branch-shaped name.
        r, out = self.lint_json([bead(
            reason="Deleted the branch after merge. AC1: verified.")])
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

    def test_standalone_lowercase_ac_word_is_not_mapping(self):
        # Word-bounded lowercase "ac" (the English fragment, e.g. an AC
        # unit) must not satisfy the shape — the token rule is case-
        # sensitive by design.
        r, out = self.lint_json([bead(
            reason="Commit ab34f9e. Fixed the ac unit wiring.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ac-mapping", out["findings"][0]["missing"])

    def test_singular_acceptance_criterion_phrase_counts_as_mapping(self):
        r, out = self.lint_json([bead(
            reason="Commit ab34f9e. The single acceptance criterion is verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

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

    def test_task_and_untyped_beads_are_checked_not_exempt(self):
        # "task" is also the fallback for a missing issue_type; neither may
        # silently join the exemption table.
        beads = [
            bead(id="pk-t", issue_type="task", reason=BARE_REASON, acs=""),
            {"id": "pk-u", "status": "closed", "close_reason": BARE_REASON},
        ]
        r, out = self.lint_json(beads)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 2)
        for f in out["findings"]:
            self.assertEqual(f["severity"], "error")
            self.assertIn("commit-ref", f["missing"])

    # --- Input handling ---

    def test_non_closed_beads_are_skipped(self):
        beads = [bead(reason=BARE_REASON, status="open"),
                 bead(id="pk-2", reason=BARE_REASON, status="in_progress")]
        r, out = self.lint_json(beads)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["beads_skipped"], 2)

    def test_status_matching_is_case_insensitive(self):
        r, out = self.lint_json([bead(reason=BARE_REASON, status="Closed")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)

    def test_single_object_input_is_accepted(self):
        r, out = self.lint_json(bead(reason=BARE_REASON))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)

    def test_invalid_json_is_input_error_exit_3(self):
        r = run_cli(["--json"], stdin_text="this is not json")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])

    def test_empty_stdin_is_input_error_exit_3(self):
        r = run_cli(["--json"], stdin_text="")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_scalar_json_is_input_error_exit_3(self):
        r = run_cli(["--json"], stdin_text='"hello"')
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])

    def test_non_dict_array_entry_is_input_error_exit_3(self):
        r = run_cli(["--json"], stdin_text="[42]")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)

    def test_empty_array_is_clean_exit_0(self):
        r, out = self.lint_json([])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["beads_checked"], 0)

    def test_unknown_flag_is_usage_error_exit_2(self):
        # The JSON-on-stderr contract must hold for usage errors too, not
        # just I/O errors — exit code 2 alone is what stock argparse gives.
        r = run_cli(["--bogus"], stdin_text="[]")
        self.assertEqual(r.returncode, 2)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["exit_code"], 2)

    # --- Output shapes ---

    def test_json_top_level_shape(self):
        r, out = self.lint_json([bead(), bead(id="pk-2", reason=BARE_REASON)])
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "beads_checked", "beads_exempt", "beads_skipped",
                    "findings", "grammar_source"):
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


class ProfileFixtureTest(unittest.TestCase):
    """Shared tempdir + JSON-run helpers for the profile-driven tests."""

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

    def lint_json(self, beads, *extra, cwd=None, env_extra=None):
        r = run_cli(["--json", *extra], stdin_text=json.dumps(beads),
                    cwd=cwd, env_extra=env_extra)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload


class ProfileShapeTest(ProfileFixtureTest):
    """AC1: detectors, per-type requires, and the IOU list are read from
    profiles/conventions.toml. Resolution chain and fallback posture follow
    the standalone-checker standard (defer-lint precedent): --profile >
    CONVENTIONS_PROFILE > upward walk from cwd; profile-less trees and
    DISCOVERED profiles without the section fall back; EXPLICIT selection
    missing the section is loud."""

    def test_profile_flag_drives_detectors(self):
        # Under the alt profile CR-9 is a commit-ref shape and "AC 1" an
        # AC tag; under the kit profile CR-9 is nothing.
        alt = self.write("alt.toml", alt_close_profile())
        beads = [bead(reason="Change record CR-9 shipped. AC 1 verified.")]
        r, out = self.lint_json(beads, "--profile", str(alt))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        r, out = self.lint_json(beads, "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_profile_requires_drive_exemption(self):
        # A type whose requires name na_marker (or children_closed) has no
        # commit/AC shape for this checker to demand — it is exempt. Flip
        # docs' requires to commit_ref and the same bead gets checked.
        alt_exempt = self.write("exempt.toml", alt_close_profile())
        alt_checked = self.write(
            "checked.toml", alt_close_profile(docs_requires="commit_ref"))
        beads = [bead(issue_type="docs",
                      reason="Tidied the handbook wording.", acs="")]
        r, out = self.lint_json(beads, "--profile", str(alt_exempt))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["beads_exempt"], 1)
        self.assertEqual(out["beads_checked"], 0)
        r, out = self.lint_json(beads, "--profile", str(alt_checked))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["beads_checked"], 1)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_profile_iou_list_drives_verdict(self):
        # The reason satisfies BOTH detector sets; only the alt profile's
        # extra IOU phrase separates the verdicts.
        alt = self.write("alt.toml", alt_close_profile())
        beads = [bead(
            reason="Commit ab34f9e CR-9. AC1 verified. handshake promise.")]
        r, out = self.lint_json(beads, "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        r, out = self.lint_json(beads, "--profile", str(alt))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        f = out["findings"][0]
        self.assertIn("handshake promise", f["iou"])
        self.assertEqual(f["severity"], "error")

    def test_profile_ref_severity_is_profile_data(self):
        # The kit profile softens chore's missing commit-ref to a warning
        # via ref_severity; the alt profile omits the key, so the default
        # (error) applies — severity is data, not code.
        alt = self.write("alt.toml", alt_close_profile())
        beads = [bead(issue_type="chore",
                      reason="Swept stale branches.", acs="")]
        r, out = self.lint_json(beads, "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["severity"], "warning")
        r, out = self.lint_json(beads, "--profile", str(alt))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["severity"], "error")

    def test_env_profile_is_honored(self):
        alt = self.write("alt.toml", alt_close_profile())
        beads = [bead(reason="Change record CR-9 shipped. AC 1 verified.")]
        r, out = self.lint_json(
            beads, env_extra={"CONVENTIONS_PROFILE": str(alt)})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertTrue(out["grammar_source"].endswith("alt.toml"),
                        out["grammar_source"])

    def test_profile_flag_beats_env(self):
        alt = self.write("alt.toml", alt_close_profile())
        beads = [bead(reason="Commit ab34f9e on main. AC1: verified.")]
        env = {"CONVENTIONS_PROFILE": str(alt)}
        # env alone: the alt grammar rejects a plain hex hash
        r, out = self.lint_json(beads, env_extra=env)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        # flag wins: kit profile accepts it
        r, out = self.lint_json(beads, "--profile", str(PROFILE),
                                env_extra=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["grammar_source"].endswith("conventions.toml"),
                        out["grammar_source"])

    def test_malformed_profile_is_io_error_exit_3(self):
        # A profile that is present but unreadable must fail loudly, never
        # silently fall back — corruption would otherwise hide the shape.
        bad = self.write("bad.toml", "[close_evidence\nnot toml at all")
        r = run_cli(["--json", "--profile", str(bad)], stdin_text="[]")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_explicit_profile_without_section_is_error_exit_3(self):
        # Explicit selection is loud: the caller named a shape source that
        # has no shape — silent fallback would hide the mistake.
        empty = self.write("empty.toml", "schema_version = 1\n")
        for label, extra, env_extra in (
                ("flag", ["--profile", str(empty)], None),
                ("env", [], {"CONVENTIONS_PROFILE": str(empty)})):
            with self.subTest(source=label):
                r = run_cli(["--json", *extra], stdin_text="[]",
                            env_extra=env_extra)
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                err = json.loads(r.stderr)
                self.assertFalse(err["ok"])
                self.assertEqual(err["error_kind"], "profile")

    def test_incomplete_close_evidence_section_is_profile_error_exit_3(self):
        partial = self.write(
            "partial.toml",
            "schema_version = 1\n[close_evidence]\niou_phrases = []\n")
        r = run_cli(["--json", "--profile", str(partial)], stdin_text="[]")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "profile")

    def test_discovered_profile_without_section_falls_back(self):
        # A DISCOVERED conventions profile that predates the
        # [close_evidence] section simply does not parameterize this
        # checker — the built-in shape applies, and the payload says so.
        self.write("profiles/conventions.toml", "schema_version = 1\n")
        r, out = self.lint_json([bead(reason=BARE_REASON)],
                                cwd=str(self.root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(sorted(out["findings"][0]["missing"]),
                         ["ac-mapping", "commit-ref"])
        self.assertEqual(out["grammar_source"], "built-in fallback")

    def test_no_profile_anywhere_falls_back(self):
        (self.root / ".git").mkdir()  # stop the upward walk at the fixture
        r, out = self.lint_json([bead()], cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["grammar_source"], "built-in fallback")
        r, out = self.lint_json([bead(reason=BARE_REASON)],
                                cwd=str(self.root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_grammar_source_names_the_discovered_profile(self):
        r, out = self.lint_json([bead()], cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["grammar_source"].endswith("conventions.toml"),
                        out["grammar_source"])
        r = run_cli([], stdin_text=json.dumps([bead()]), cwd=str(REPO))
        self.assertIn("[grammar:", r.stdout)


class IouPhraseTest(ProfileFixtureTest):
    """The IOU-phrase ban (bead-completion: do not defer AC verification)
    now reaches the stream linter via the profile's iou_phrases list."""

    def test_iou_phrase_is_flagged_error(self):
        r, out = self.lint_json(
            [bead(reason="Commit ab34f9e. AC1: done. "
                         "AC2 will be verified later.")],
            "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        f = out["findings"][0]
        self.assertEqual(f["missing"], [])
        self.assertIn("will be verified later", f["iou"])
        self.assertEqual(f["severity"], "error")

    def test_sanctioned_deferral_is_not_flagged(self):
        # "deferred to bead <id>" is the one sanctioned deferral form —
        # iou_exempt scrubs it before the phrase scan.
        r, out = self.lint_json(
            [bead(reason="Commit ab34f9e. AC1: done. "
                         "AC2 deferred to bead pk-99.")],
            "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_iou_on_soft_type_is_error_not_warning(self):
        # chore's missing commit-ref softens to a warning, but an IOU
        # phrase is a violation regardless of type.
        r, out = self.lint_json(
            [bead(issue_type="chore", acs="",
                  reason="Swept stale branches. Will be verified later.")],
            "--profile", str(PROFILE))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        f = out["findings"][0]
        self.assertEqual(f["severity"], "error")
        self.assertIn("will be verified later", f["iou"])

    def test_human_output_names_iou_phrase(self):
        r = run_cli(["--profile", str(PROFILE)], stdin_text=json.dumps(
            [bead(reason="Commit ab34f9e. AC1: done. "
                         "AC2 will be verified later.")]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("IOU", r.stdout)
        self.assertIn("will be verified later", r.stdout)


class ReconciledProfilePinsTest(ProfileFixtureTest):
    """AC4: the profile's close_evidence detectors are reconciled toward
    the production detectors — digit-requiring hash, branch-shaped token,
    all PR/MR URL forms, case-sensitive AC detection (case-insensitive
    alternatives via inline (?i:...) groups). Every pin runs the CLI with
    --profile <kit profile> so the profile data path is what's tested."""

    def pin(self, beads):
        return self.lint_json(beads, "--profile", str(PROFILE))

    def test_all_letter_hex_word_is_not_a_hash(self):
        r, out = self.pin([bead(
            reason="AC1: verified. Config was effaced deliberately.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_digit_bearing_hash_counts(self):
        r, out = self.pin([bead(reason="Landed in 1920608. AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_branch_prose_is_not_a_ref(self):
        r, out = self.pin([bead(
            reason="Deleted the branch after merge. AC1: verified.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("commit-ref", out["findings"][0]["missing"])

    def test_all_pr_url_forms_count(self):
        for form in ("pull", "pulls", "pull-requests", "merge_requests"):
            with self.subTest(form=form):
                r, out = self.pin([bead(
                    reason=f"See https://forge.example/o/r/{form}/42 "
                           "— AC1: verified.")])
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(out["findings"], [])

    def test_lowercase_ac_prose_is_not_mapping(self):
        r, out = self.pin([bead(
            reason="Commit ab34f9e. Fixed the ac unit wiring.")])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ac-mapping", out["findings"][0]["missing"])

    def test_uppercase_acceptance_phrase_still_counts(self):
        # The phrase alternative keeps production's IGNORECASE via an
        # inline (?i:...) group — the flag-mix decision under test.
        r, out = self.pin([bead(
            reason="Commit ab34f9e. ACCEPTANCE CRITERIA all verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_branch_keyword_stays_case_insensitive(self):
        # Same inline-group decision on the branch-keyword alternative.
        r, out = self.pin([bead(
            reason="Branch: hotfix-rollout deployed. AC1: verified.")])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])


class FallbackParityTest(ProfileFixtureTest):
    """AC1: the built-in fallback subset stays pinned to the profile —
    structurally on every checker-consumed key, and behaviorally over a
    fixture exercising every element detector and severity path."""

    def test_fallback_structurally_matches_kit_profile_section(self):
        # Structural pin, complementing the behavioral parity scan below:
        # pattern loosening, severity flips, or list edits on either side
        # cannot drift silently. (Deliberate unit-level exception to the
        # subprocess-only style — sample-based scans cannot pin pattern
        # equality; same idiom as test_defer_lint.py.)
        loader = SourceFileLoader("close_reason_lint_module", str(CLI))
        spec = importlib.util.spec_from_loader(
            "close_reason_lint_module", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        fallback = mod.FALLBACK_CLOSE_EVIDENCE
        with open(PROFILE, "rb") as f:
            section = tomllib.load(f)["close_evidence"]
        # Detectors the checker compiles: pattern and flags, byte-equal.
        for element in ("commit_ref", "ac_mapping"):
            fb, prof = fallback["elements"][element], section["elements"][element]
            self.assertEqual(fb["pattern"], prof["pattern"],
                             f"elements.{element}.pattern drifted")
            self.assertEqual(fb.get("flags", []), prof.get("flags", []),
                             f"elements.{element}.flags drifted")
        # Type set (and order), per-type requires, per-type ref_severity.
        self.assertEqual(list(fallback["by_type"]), list(section["by_type"]))
        for name, entry in fallback["by_type"].items():
            profile_entry = section["by_type"][name]
            self.assertEqual(entry["requires"], profile_entry["requires"],
                             f"by_type.{name}.requires drifted")
            self.assertEqual(entry.get("ref_severity", "error"),
                             profile_entry.get("ref_severity", "error"),
                             f"by_type.{name}.ref_severity drifted")
        # IOU phrase list and the sanctioned-deferral exemption.
        self.assertEqual(fallback["iou_phrases"], section["iou_phrases"])
        self.assertEqual(fallback["iou_exempt"]["pattern"],
                         section["iou_exempt"]["pattern"])
        self.assertEqual(fallback["iou_exempt"].get("flags", []),
                         section["iou_exempt"].get("flags", []))

    def test_fallback_behavioral_parity_with_kit_profile(self):
        # Every element detector alternative, both severities, exemption,
        # skip, IOU hit and IOU exemption — identical verdicts from the
        # kit profile and the built-in fallback.
        beads = [
            bead(id="hash", reason=GOOD_REASON),
            bead(id="mr-url", reason="See https://f.example/o/r/"
                 "merge_requests/7 — AC1: verified."),
            bead(id="branch-slug",
                 reason="On feat/pk-1-loading-state. AC1: verified."),
            bead(id="branch-kw",
                 reason="Pushed to branch spike-exploration. AC1: verified."),
            bead(id="effaced",
                 reason="AC1: verified. Config was effaced deliberately."),
            bead(id="branch-prose",
                 reason="Deleted the branch after merge. AC1: verified."),
            bead(id="lower-ac",
                 reason="Commit ab34f9e. Fixed the ac unit wiring."),
            bead(id="empty", reason=""),
            bead(id="chore-soft", issue_type="chore",
                 reason="Swept stale branches.", acs=""),
            bead(id="spike-soft", issue_type="spike",
                 reason="Question answered: AC1 approach is viable.",
                 acs="- is the approach viable?"),
            bead(id="chore-acs", issue_type="chore",
                 reason="Swept stale branches.", acs="- sweep completes"),
            bead(id="docs-x", issue_type="docs", reason="N/A — docs."),
            bead(id="decision-x", issue_type="decision", reason="N/A."),
            bead(id="milestone-x", issue_type="milestone", reason="N/A."),
            bead(id="epic-x", issue_type="epic",
                 reason="All children closed."),
            bead(id="iou", reason="Commit ab34f9e. AC1: done. "
                 "AC2 will be verified later."),
            bead(id="iou-exempt", reason="Commit ab34f9e. AC1: done. "
                 "AC2 deferred to bead pk-9."),
            bead(id="open-skip", reason=BARE_REASON, status="open"),
            bead(id="unknown-type", issue_type="gizmo", reason=BARE_REASON),
        ]
        (self.root / ".git").mkdir()  # profile-less tree → fallback
        r_fb, out_fb = self.lint_json(beads, cwd=str(self.root))
        r_prof, out_prof = self.lint_json(beads, "--profile", str(PROFILE))
        self.assertEqual(r_fb.returncode, r_prof.returncode,
                         r_fb.stdout + r_prof.stdout
                         + r_fb.stderr + r_prof.stderr)
        # grammar_source is the one legitimate difference between the runs.
        self.assertEqual(out_fb.pop("grammar_source"), "built-in fallback")
        self.assertTrue(out_prof.pop("grammar_source")
                        .endswith("conventions.toml"))
        self.assertEqual(out_fb, out_prof)
        # The fixture genuinely exercises every counting + severity path.
        self.assertGreater(out_fb["beads_exempt"], 0)
        self.assertGreater(out_fb["beads_skipped"], 0)
        severities = {f["severity"] for f in out_fb["findings"]}
        self.assertEqual(severities, {"error", "warning"})
        self.assertTrue(any(f["iou"] for f in out_fb["findings"]))


if __name__ == "__main__":
    unittest.main()
