#!/usr/bin/env python3
"""Behavioral tests for scripts/banned-token-scan.

Every test drives the CLI as a subprocess against tempfile/stdin fixtures
and asserts observable behavior: exit codes, human/JSON output, and finding
shapes. No internals.

Fixture texts assemble each flagged token from parts (J below) so this
file's own source never contains a scannable occurrence — the scanner must
never need to special-case test content (same content-side idiom as
scripts/defer-lint and its tests).

Run: python3 scripts/tests/test_banned_token_scan.py
"""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "banned-token-scan"

# Assembled so no literal banned token appears in this file at rest.
J = "".join
W_WEEKS = J(("wee", "ks"))
W_HOURS = J(("hou", "rs"))
W_SPRINTS = J(("spri", "nts"))
W_STORY_POINTS = J(("story poi", "nts"))
W_TWO_ENGINEERS = J(("two engi", "neers"))
W_SMALL_TEAM = J(("small te", "am"))
W_TEAM_OF = J(("team o", "f"))
W_TIMELINE = J(("time", "line"))
W_SCHEDULE = J(("sched", "ule"))
W_AMBITIOUS = J(("ambi", "tious"))
W_ON_TRACK = J(("on tra", "ck"))
W_ETA = J(("ET", "A"))
W_QUICK_WIN = J(("quick w", "in"))
W_BALLPARK = J(("ball", "park"))
W_I_ESTIMATE = J(("I esti", "mate"))
W_ROUGH_ESTIMATE = J(("rough esti", "mate"))
W_ROUGHLY = J(("roug", "hly"))

# Class keys as the scanner reports them (one is assembled because its
# name embeds a token).
C_TIME = "time-units"
C_TEAM = "team-size"
C_SCHED = W_SCHEDULE + "-framing"
C_EST = "estimation-verbs"


def run_cli(args, stdin_text=None):
    return subprocess.run(
        ["python3", str(CLI)] + args,
        capture_output=True,
        text=True,
        input=stdin_text,
    )


class BannedTokenScanTest(unittest.TestCase):
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

    def scan_json(self, text):
        r = run_cli(["--json"], stdin_text=text)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload

    def classes_hit(self, out):
        return {f["class"] for f in out["findings"]}

    # --- AC: reports hits for each of the four token classes ---

    def test_time_unit_hit_is_reported(self):
        r, out = self.scan_json(f"this will take 6 {W_WEEKS} to build\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertFalse(out["ok"])
        f = out["findings"][0]
        self.assertEqual(f["class"], C_TIME)
        self.assertEqual(f["token"], W_WEEKS)
        self.assertEqual(f["line"], 1)

    def test_team_size_hit_is_reported(self):
        r, out = self.scan_json(f"you'd need {W_TWO_ENGINEERS} for this\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(C_TEAM, self.classes_hit(out))

    def test_schedule_framing_hit_is_reported(self):
        r, out = self.scan_json(f"the {W_TIMELINE} is {W_AMBITIOUS}\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(self.classes_hit(out), {C_SCHED})
        self.assertEqual(len(out["findings"]), 2)

    def test_estimation_verb_hit_is_reported(self):
        r, out = self.scan_json(f"a {W_BALLPARK} figure: plenty\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(C_EST, self.classes_hit(out))

    def test_phrase_tokens_are_matched(self):
        text = (f"we are {W_ON_TRACK} for launch\n"
                f"{W_I_ESTIMATE} this is fine\n"
                f"a {W_ROUGH_ESTIMATE} says so\n"
                f"call it a {W_QUICK_WIN}\n"
                f"{W_STORY_POINTS}: 5\n")
        r, out = self.scan_json(text)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 5)
        self.assertEqual(self.classes_hit(out), {C_SCHED, C_EST, C_TIME})

    def test_team_of_number_is_matched_but_team_of_words_is_not(self):
        r, out = self.scan_json(f"a {W_TEAM_OF} 3 could do it\n"
                                f"a {W_TEAM_OF} reviewers signed off\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len(out["findings"]), 1)
        self.assertEqual(out["findings"][0]["line"], 1)
        self.assertEqual(out["findings"][0]["class"], C_TEAM)

    def test_roughly_n_units_reports_estimation_class_too(self):
        r, out = self.scan_json(f"{W_ROUGHLY} 3 {W_HOURS} of compute\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(C_EST, self.classes_hit(out))
        self.assertIn(C_TIME, self.classes_hit(out))

    # --- Matching discipline ---

    def test_clean_text_is_exit_0(self):
        r, out = self.scan_json(
            "scope: three files, two integration points.\n"
            "risk: the parser has unknown edge cases.\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(out["ok"])
        self.assertEqual(out["findings"], [])

    def test_matching_is_case_insensitive(self):
        r, out = self.scan_json(f"{W_WEEKS.capitalize()} of effort\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["class"], C_TIME)

    def test_eta_is_uppercase_only(self):
        # Lowercase "eta" is a Greek letter / word fragment; only the
        # uppercase acronym is the banned usage.
        r1, out1 = self.scan_json(f"the {W_ETA} is unclear\n")
        self.assertEqual(r1.returncode, 1, r1.stdout + r1.stderr)
        r2, out2 = self.scan_json(f"the {W_ETA.lower()} squared term\n")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    def test_word_boundaries_prevent_substring_hits(self):
        # A word that merely embeds a token must not be flagged.
        r, out = self.scan_json(
            f"the {W_SCHEDULE}r daemon ran; ware{W_HOURS}ing continues\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    def test_compound_unit_reports_one_finding_not_two(self):
        # "person-<unit>" embeds the bare unit; overlapping spans in the
        # same class must be deduped to the longest token.
        r, out = self.scan_json(f"budget: 12 person-{W_HOURS}\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        time_hits = [f for f in out["findings"] if f["class"] == C_TIME]
        self.assertEqual(len(time_hits), 1)
        self.assertEqual(time_hits[0]["token"], f"person-{W_HOURS}")

    # --- Input handling ---

    def test_scans_named_files_with_lines(self):
        self.write("a.md", f"fine line\ntake 2 {W_WEEKS}\n")
        self.write("b.md", f"{W_SMALL_TEAM} needed\n")
        r = run_cli([str(self.root / "a.md"), str(self.root / "b.md"),
                     "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["files_scanned"], 2)
        by_file = {(f["file"], f["line"]) for f in out["findings"]}
        self.assertIn((str(self.root / "a.md"), 2), by_file)
        self.assertIn((str(self.root / "b.md"), 1), by_file)

    def test_stdin_findings_use_stdin_marker(self):
        r, out = self.scan_json(f"take 2 {W_WEEKS}\n")
        self.assertEqual(out["findings"][0]["file"], "<stdin>")

    def test_dash_reads_stdin(self):
        r = run_cli(["-", "--json"], stdin_text=f"take 2 {W_WEEKS}\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_missing_file_is_io_error_exit_3(self):
        r = run_cli([str(self.root / "nope.md")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_unknown_flag_is_usage_error_exit_2(self):
        r = run_cli(["--bogus"], stdin_text="x\n")
        self.assertEqual(r.returncode, 2)

    # --- Content self-matching: the scanner's own source stays clean ---

    def test_scanning_own_source_file_is_clean(self):
        # Any copy of the scanner (kit or distributed) fed to itself must
        # report zero hits: every token in its source is assembled from
        # parts, never present at rest.
        r = run_cli([str(CLI), "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])

    def test_scanning_this_test_file_is_clean(self):
        r = run_cli([str(Path(__file__).resolve()), "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])

    # --- Output shapes ---

    def test_json_top_level_shape(self):
        r, out = self.scan_json(f"take 2 {W_WEEKS}\n")
        self.assertEqual(r.returncode, 1)
        for key in ("ok", "files_scanned", "findings"):
            self.assertIn(key, out)
        self.assertNotIn("exit_code", out)
        f = out["findings"][0]
        for key in ("file", "line", "class", "token", "text"):
            self.assertIn(key, f)

    def test_human_output_names_file_line_class_and_token(self):
        p = self.write("a.md", f"take 2 {W_WEEKS}\n")
        r = run_cli([str(p)])
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"{p}:1", r.stdout)
        self.assertIn(C_TIME, r.stdout)
        self.assertIn(W_WEEKS, r.stdout)

    def test_clean_human_output_names_summary(self):
        r = run_cli([], stdin_text="all clear here\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("clean", r.stdout)

    def test_help_exits_zero_names_classes_and_judgment_boundary(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        for cls in (C_TIME, C_TEAM, C_SCHED, C_EST):
            self.assertIn(cls, r.stdout)
        # The reporter explicitly does NOT judge the rule's exceptions.
        self.assertIn("not regressions", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
