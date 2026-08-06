#!/usr/bin/env python3
"""Behavioral tests for scripts/conventions (bead process-kit-ouc).

Every test drives the CLI as a subprocess and asserts observable behavior:
exit codes, JSON payloads, rendered fragment text, and the regen gate
(`render-rule --check`). No internals.

The 20-case spike baseline is ported verbatim from
experiments/profile-spike/demo-cases.sh — same inputs, same expected exit
codes — and runs against the committed profiles/conventions.toml. The one
sanctioned behavior change on top of the baseline: `spike` is an accepted
COMMIT type (Kevin, 2026-08-05). It is still not a branch type.

Run: python3 scripts/tests/test_conventions.py
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CLI = REPO / "scripts" / "conventions"
PROFILE = REPO / "profiles" / "conventions.toml"

BEGIN = "<!-- GENERATED from profiles/conventions.toml — DO NOT EDIT -->"
END = "<!-- END GENERATED from profiles/conventions.toml -->"

FRAGMENT_FILES = {
    "git-conventions": "cursor/rules/operating-model.mdc",
    "close-evidence": "cursor/rules/bead-completion.mdc",
    "defer-convention": "cursor/rules/defer-convention.mdc",
}

# The defer marker, assembled from parts so this file never contains a
# comment-marker-adjacent occurrence defer-lint would match (same idiom as
# the checker and its tests).
D = "defer" + ":"


def run_cli(args, cwd=None, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "CONVENTIONS_PROFILE"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True, text=True, cwd=cwd, env=env,
    )


def extract_region(text):
    # Deliberately independent of the CLI's extractor: a bug there should
    # disagree with this reimplementation, not be mirrored by it.
    lines = text.splitlines()
    begins = [i for i, l in enumerate(lines) if l.strip() == BEGIN]
    ends = [i for i, l in enumerate(lines) if l.strip() == END]
    if len(begins) != 1 or len(ends) != 1 or begins[0] >= ends[0]:
        return None
    return "\n".join(lines[begins[0]:ends[0] + 1])


# --- AC1: the spike's 20 demo cases, same verdicts --------------------------
# (label, expected exit code, argv) — ported from demo-cases.sh.
SPIKE_BASELINE = [
    # commit messages (real, from git log --oneline)
    ("real-commit-chore", 0, ["check-commit",
     "chore: enable validation.on-create warn in kit repo (process-kit-qxc)"]),
    ("real-commit-feat", 0, ["check-commit",
     "feat: tdd-ledger CLI — durable red-then-green evidence + CI verify"]),
    # real commit 0fcdb1d: 87-char summary vs the "under 72" cap — the
    # spike kept it as live proof the prose convention was unenforced.
    ("real-commit-fix-overlong", 1, ["check-commit",
     "fix: packet verifier strip check scans the grid structurally, "
     "not 1800 chars (segnolabs-cga)"]),
    ("bad-type", 1, ["check-commit", "wip: half-done stuff"]),
    ("no-colon-format", 1, ["check-commit", "added loading spinner"]),
    ("summary-too-long", 1, ["check-commit",
     "docs: this summary deliberately rambles on far past the seventy-two "
     "character cap to trip the length check"]),
    # branch names
    ("rule-example-branch", 0, ["check-branch", "feat/gastown-abc-loading-ux"]),
    # `spike` was sanctioned as a COMMIT type only — branches keep rejecting it.
    ("spike-not-a-branch-type", 1, ["check-branch",
     "spike/process-kit-vgz-profile-projection"]),
    ("no-slash", 1, ["check-branch", "main"]),
    ("uppercase-slug", 1, ["check-branch", "fix/Process-Kit-ABC-Thing"]),
    # close reasons (real, from bd show)
    ("real-task-close", 0, ["check-close", "--type", "task",
     "Commit 52b45df, reviewed by coordinator. AC1: docs/README.md Directory "
     "index table covers specs/, research/, refinements/, decisions/. "
     "AC2: glossary gained 7 entries."]),
    ("real-feature-close", 0, ["check-close", "--type", "feature",
     "Commits 515bb21 (impl) + 92589d6 (tier1 fixes) on main. AC1: "
     "record-failing/record-passing append JSONL entries, verify exits 0 "
     "clean / 1 with named reasons."]),
    ("real-spike-close", 0, ["check-close", "--type", "spike",
     "Closed as won't-do/obsolete (Planner decision): the spike's premise "
     "was eliminated by process-kit-amq (commit c816f2e)."]),
    ("real-epic-close", 0, ["check-close", "--type", "epic",
     "All 5 children closed with commit-mapped evidence (815: 52b45df, "
     "opk: ed67eb9). Success criterion 1 met."]),
    ("docs-na-close", 0, ["check-close", "--type", "docs",
     "N/A — documentation update, no verification needed. Commit 52b45df."]),
    ("vague-done", 1, ["check-close", "--type", "feature", "Done"]),
    ("no-commit-ref", 1, ["check-close", "--type", "bug",
     "AC1: fixed the crash, test_login passes now."]),
    ("iou-phrase", 1, ["check-close", "--type", "feature",
     "Commit a1b2c3f. AC1 will be verified later in the PR manual-check pass."]),
    ("sanctioned-deferral", 0, ["check-close", "--type", "feature",
     "Commit a1b2c3f. AC1: spinner renders (verified). AC2 deferred to bead "
     "process-kit-xyz."]),
    ("unknown-bead-type", 1, ["check-close", "--type", "gizmo",
     "Commit a1b2c3f. AC1: done."]),
]


class SpikeBaselineTest(unittest.TestCase):
    def test_baseline_has_exactly_20_cases(self):
        self.assertEqual(len(SPIKE_BASELINE), 20)

    def test_spike_demo_case_verdicts_reproduce(self):
        for label, want, argv in SPIKE_BASELINE:
            with self.subTest(label=label):
                r = run_cli(["--profile", str(PROFILE)] + argv)
                self.assertEqual(r.returncode, want,
                                 f"[{label}] {r.stdout}{r.stderr}")

    # --- AC1: the sanctioned change — spike commit type accepted ---

    def test_spike_commit_type_is_accepted(self):
        r = run_cli(["--profile", str(PROFILE), "check-commit",
                     "spike: probe profile-projection round-trip"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["ok"])
        self.assertEqual(out["violations"], [])

    def test_wip_commit_type_stays_rejected_with_named_code(self):
        r = run_cli(["--profile", str(PROFILE), "check-commit",
                     "wip: half-done stuff"])
        self.assertEqual(r.returncode, 1)
        out = json.loads(r.stdout)
        self.assertFalse(out["ok"])
        self.assertEqual(out["violations"][0]["code"], "commit-type")

    # --- check JSON shape: traceable violations, no exit_code key ---

    def test_check_json_payload_shape(self):
        r = run_cli(["--profile", str(PROFILE), "check-commit",
                     "added loading spinner"])
        out = json.loads(r.stdout)
        for key in ("ok", "check", "subject", "profile", "violations"):
            self.assertIn(key, out)
        self.assertNotIn("exit_code", out)
        self.assertEqual(out["check"], "commit")
        # the resolved profile path is echoed so a wrong-profile verdict
        # is diagnosable from output alone
        self.assertEqual(Path(out["profile"]).resolve(), PROFILE.resolve())
        for v in out["violations"]:
            self.assertIn("code", v)
            self.assertIn("detail", v)

    def test_check_close_reports_missing_element_by_name(self):
        r = run_cli(["--profile", str(PROFILE), "check-close", "--type", "bug",
                     "AC1: fixed the crash, test_login passes now."])
        out = json.loads(r.stdout)
        codes = [v["code"] for v in out["violations"]]
        self.assertIn("close-missing-commit-ref", codes)


class CheckerEdgeCasesTest(unittest.TestCase):
    """Regression tests from the Tier 1 review of process-kit-ouc."""

    def test_empty_summary_with_body_is_rejected(self):
        # `git commit -m "feat: " -m "body"` produces exactly this shape;
        # DOTALL lets (.+) span the body, so the guard must catch it.
        r = run_cli(["--profile", str(PROFILE), "check-commit",
                     "feat: \n\nimplement the loading spinner per AC1"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertIn("commit-empty-summary",
                      [v["code"] for v in out["violations"]])

    def test_multiline_epic_close_reason_passes(self):
        # "children ... closed" spanning a line break is a legitimate close.
        r = run_cli(["--profile", str(PROFILE), "check-close", "--type",
                     "epic",
                     "All 4 children verified individually.\n"
                     "Everything closed with commit-mapped evidence "
                     "(abc: 52b45df)."])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_branch_with_trailing_newline_is_rejected(self):
        # unstripped `git symbolic-ref` output must not pass the anchor
        r = run_cli(["--profile", str(PROFILE), "check-branch",
                     "feat/abc-def\n"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


class RenderRuleTest(unittest.TestCase):
    def render(self, fragment):
        r = run_cli(["--profile", str(PROFILE), "render-rule", fragment])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout.rstrip("\n")

    def test_git_conventions_fragment_is_marker_wrapped(self):
        text = self.render("git-conventions")
        lines = text.splitlines()
        self.assertEqual(lines[0], BEGIN)
        self.assertEqual(lines[-1], END)

    def test_git_conventions_fragment_carries_the_law(self):
        text = self.render("git-conventions")
        self.assertIn("## Git Conventions", text)
        # commit grammar with spike sanctioned
        self.assertIn(
            "- Commit messages: `<type>: <summary>` — types `feat`, `fix`, "
            "`refactor`, `test`, `chore`, `docs`, `spike`; summaries under "
            "72 characters.", text)
        # branch grammar stays spike-free, list now explicit
        self.assertIn(
            "Branch naming: `<type>/<bead-id>-<short-description>` — types "
            "`feat`, `fix`, `refactor`, `test`, `chore`, `docs`.", text)
        # judgment-shaped law preserved verbatim
        self.assertIn(
            "- Commit at logical checkpoints, small and atomic — not one "
            "giant commit at bead close. Never force push shared branches "
            "without explicit user approval.", text)

    def test_close_evidence_fragment_preserves_committed_table_rows(self):
        text = self.render("close-evidence")
        lines = text.splitlines()
        self.assertEqual(lines[0], BEGIN)
        self.assertEqual(lines[-1], END)
        self.assertIn("| Bead type | Required evidence |", text)
        # every row of today's hand-written table, byte-for-byte
        for row in (
            "| Bug | Test output showing bug is reproduced and fixed |",
            "| Feature | Test output or manual verification notes per AC |",
            "| Story | Test output or manual verification per AC (same as feature) |",
            "| Spike | Summary of findings; whether the question was answered |",
            "| Refactor | Build/lint clean, existing behavioral tests pass |",
            "| Chore/config | Brief summary of what was done |",
            '| Docs | "N/A — documentation update, no verification needed" |',
            '| Decision | "N/A — decision record, no verification needed" |',
            '| Milestone | "N/A — milestone marker, verify children are closed" |',
            "| Epic | Verify all children closed (`bd epic close-eligible`), "
            "then confirm each success criterion is met by the closed "
            "children's outcomes. If a criterion is unmet, create a follow-up "
            "bead before closing. |",
        ):
            self.assertIn(row, text)
        # the committed table has no Task row — task stays checker-only
        self.assertNotIn("| Task |", text)

    def test_defer_convention_fragment_carries_the_law(self):
        text = self.render("defer-convention")
        lines = text.splitlines()
        self.assertEqual(lines[0], BEGIN)
        self.assertEqual(lines[-1], END)
        # the grammar template, assembled by the renderer from marker parts
        # and format — every line byte-matches today's hand-written rule
        self.assertIn(
            f"Mark deliberate simplifications with a `{D}` comment:", text)
        self.assertIn(
            f"// {D} <what was simplified>. ceiling: <known limitation>. "
            "upgrade when: <trigger condition>.", text)
        self.assertIn(
            "Language-appropriate comment prefix (`//`, `#`, `/* */`, `--`); "
            "the ceiling and trigger may continue on the following comment "
            "line(s).", text)
        self.assertIn(
            f"**The no-trigger law:** every `{D}` comment MUST include an "
            '"upgrade when:" condition. A deferral without a trigger is just '
            "a TODO with a fancier name. If you can't name when to revisit, "
            "either the simplification is permanent (no comment needed) or "
            "you don't understand the ceiling yet (investigate before "
            "deferring).", text)
        self.assertIn(
            f"Marker choice: `{D}` = deliberate simplification with known "
            "limits (structured — ceiling + trigger required); `TODO` = "
            "unstructured reminder; `FIXME` = actually broken.", text)

    # --- AC2: committed regions byte-match render output ---

    def test_committed_regions_byte_match_render(self):
        for fragment, relfile in FRAGMENT_FILES.items():
            with self.subTest(fragment=fragment):
                committed = extract_region((REPO / relfile).read_text())
                self.assertIsNotNone(
                    committed, f"no GENERATED region in {relfile}")
                self.assertEqual(committed, self.render(fragment))

    def test_render_rule_check_passes_on_this_repo(self):
        # cwd-based resolution: no --profile, run from repo root.
        r = run_cli(["render-rule", "--check"], cwd=REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertTrue(out["ok"])
        self.assertEqual({f["fragment"] for f in out["fragments"]},
                         set(FRAGMENT_FILES))


class RegenGateTest(unittest.TestCase):
    """Seeded-drift behavior of render-rule --check on a fixture repo."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "profiles").mkdir()
        shutil.copy(PROFILE, self.root / "profiles" / "conventions.toml")
        for fragment, relfile in FRAGMENT_FILES.items():
            r = run_cli(["--profile", str(PROFILE), "render-rule", fragment])
            assert r.returncode == 0, r.stdout + r.stderr
            dest = self.root / relfile
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("hand-written head\n\n" + r.stdout
                            + "\nhand-written tail\n")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self):
        r = run_cli(["render-rule", "--check"], cwd=self.root)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload

    def test_clean_fixture_passes(self):
        r, out = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])

    def test_seeded_drift_inside_region_fails_and_names_fragment(self):
        f = self.root / FRAGMENT_FILES["git-conventions"]
        f.write_text(f.read_text().replace("summaries under 72 characters",
                                           "summaries under 720 characters"))
        r, out = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(out["ok"])
        drifted = [x for x in out["fragments"] if x["status"] == "drift"]
        self.assertEqual([x["fragment"] for x in drifted], ["git-conventions"])
        self.assertTrue(drifted[0]["diff"])  # unified diff lines present

    def test_seeded_drift_in_defer_fragment_fails_and_names_it(self):
        f = self.root / FRAGMENT_FILES["defer-convention"]
        f.write_text(f.read_text().replace("fancier name", "fancy name"))
        r, out = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        drifted = [x for x in out["fragments"] if x["status"] == "drift"]
        self.assertEqual([x["fragment"] for x in drifted],
                         ["defer-convention"])

    def test_edit_outside_region_does_not_trip_the_gate(self):
        f = self.root / FRAGMENT_FILES["git-conventions"]
        f.write_text(f.read_text().replace("hand-written tail",
                                           "hand-written tail, edited"))
        r, out = self.check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_end_marker_fails_as_missing_markers(self):
        f = self.root / FRAGMENT_FILES["close-evidence"]
        f.write_text(f.read_text().replace(END, ""))
        r, out = self.check()
        self.assertEqual(r.returncode, 1)
        statuses = {x["fragment"]: x["status"] for x in out["fragments"]}
        self.assertEqual(statuses["close-evidence"], "missing-markers")

    def test_missing_rule_file_fails_as_missing_file(self):
        (self.root / FRAGMENT_FILES["git-conventions"]).unlink()
        r, out = self.check()
        self.assertEqual(r.returncode, 1)
        statuses = {x["fragment"]: x["status"] for x in out["fragments"]}
        self.assertEqual(statuses["git-conventions"], "missing-file")

    def test_profile_edit_without_regen_trips_the_gate(self):
        # The round-trip guarantee: a profile change with no fragment regen
        # must fail CI. Drop spike from commit types in the fixture profile.
        p = self.root / "profiles" / "conventions.toml"
        p.write_text(p.read_text().replace(
            '"docs", "spike"]', '"docs"]'))
        r, out = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)


class ProfileResolutionTest(unittest.TestCase):
    def test_env_var_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp:
            alt = Path(tmp) / "alt.toml"
            alt.write_text(PROFILE.read_text().replace(
                '"docs", "spike"]', '"docs"]'))
            r = run_cli(["check-commit", "spike: probe"],
                        env_extra={"CONVENTIONS_PROFILE": str(alt)})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_flag_beats_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            alt = Path(tmp) / "alt.toml"
            alt.write_text(PROFILE.read_text().replace(
                '"docs", "spike"]', '"docs"]'))
            r = run_cli(["--profile", str(PROFILE), "check-commit",
                         "spike: probe"],
                        env_extra={"CONVENTIONS_PROFILE": str(alt)})
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_upward_search_finds_profile_from_subdirectory(self):
        r = run_cli(["check-commit", "spike: probe"],
                    cwd=REPO / "scripts" / "tests")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_no_profile_anywhere_is_io_error_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run_cli(["check-commit", "feat: x"], cwd=tmp)
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            err = json.loads(r.stderr)
            self.assertFalse(err["ok"])
            self.assertEqual(err["error_kind"], "io")

    def test_malformed_profile_is_io_error_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.toml"
            bad.write_text("[commit\ntypes = not toml")
            r = run_cli(["--profile", str(bad), "check-commit", "feat: x"])
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)


class CliConventionsTest(unittest.TestCase):
    def assert_json_usage_error(self, r):
        # exit 2 alone is what stock argparse (or a missing CLI) produces;
        # the agent contract is JSON on stderr with error_kind "usage".
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "usage")

    def test_unknown_flag_is_usage_error_exit_2(self):
        self.assert_json_usage_error(run_cli(["--bogus"]))

    def test_check_close_without_type_is_usage_error_exit_2(self):
        self.assert_json_usage_error(
            run_cli(["--profile", str(PROFILE), "check-close", "reason only"]))

    def test_unknown_fragment_is_usage_error_naming_known_ones(self):
        r = run_cli(["--profile", str(PROFILE), "render-rule", "nonesuch"])
        self.assert_json_usage_error(r)
        err = json.loads(r.stderr)
        self.assertIn("git-conventions", err["error"])

    def test_render_rule_without_fragment_or_check_is_usage_error(self):
        self.assert_json_usage_error(
            run_cli(["--profile", str(PROFILE), "render-rule"]))

    def test_render_rule_fragment_plus_check_is_usage_error(self):
        # a fragment name alongside --check must not be silently ignored —
        # a whole-repo pass must not be misread as a single-fragment pass
        self.assert_json_usage_error(
            run_cli(["--profile", str(PROFILE), "render-rule",
                     "git-conventions", "--check"]))

    def test_help_exits_zero_and_names_subcommands(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        for name in ("check-commit", "check-branch", "check-close",
                     "render-rule"):
            self.assertIn(name, r.stdout)


if __name__ == "__main__":
    unittest.main()
