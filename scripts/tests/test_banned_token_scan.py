#!/usr/bin/env python3
"""Behavioral tests for scripts/banned-token-scan.

Every test drives the CLI as a subprocess against tempfile/stdin fixtures
and asserts observable behavior: exit codes, human/JSON output, and finding
shapes. No internals.

Fixture texts assemble each flagged token from parts (J below) so this
file's own source never contains a scannable occurrence — the scanner must
never need to special-case test content (same content-side idiom as
scripts/defer-lint and its tests).

The token catalog is profile-driven (bead process-kit-8dx):
ProfileCatalogTest covers the resolution chain and fallback posture,
DeclaredTokenExclusionTest covers the content-side exclusion contract for
data files (the cross-copy fixture), FallbackParityTest pins built-in
fallback parity structurally and behaviorally.

Run: python3 scripts/tests/test_banned_token_scan.py
"""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "banned-token-scan"
REPO = CLI.parent.parent
PROFILE = REPO / "profiles" / "conventions.toml"

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
W_DAYS = J(("da", "ys"))

# Class keys as the scanner reports them (one is assembled because its
# name embeds a token).
C_TIME = "time-units"
C_TEAM = "team-size"
C_SCHED = W_SCHEDULE + "-framing"
C_EST = "estimation-verbs"

# Declared-token region markers (content-side exclusion contract). The
# ":begin" suffix is joined at runtime so this test file never carries a
# region-opening line at rest — the self-clean test scans this file.
MARK = "banned-token-scan:declared-tokens"
MARK_BEGIN = MARK + ":begin"
MARK_END = MARK + ":end"


def run_cli(args, stdin_text=None, cwd=None, env_extra=None):
    # CONVENTIONS_PROFILE is scrubbed so a profile configured in the
    # developer's environment can never leak a catalog into a fixture run
    # (same hygiene as the other checker suites).
    # NOTE on cwd: runs without an explicit cwd inherit the test runner's
    # directory, so catalog-agnostic tests pick up the DISCOVERED kit
    # profile inside this repo and the built-in fallback outside it. Safe
    # only because FallbackParityTest pins the two catalogs equal — keep
    # that pin, or pass cwd/--profile explicitly.
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


# A minimal-but-complete [tokens] profile whose single class, token, and
# exclude marker differ from the kit's, so tests can prove the catalog —
# marker included — comes from the profile, not any built-in. Render-only
# keys (rule_label, rule_items, rule_note) are deliberately absent — the
# checker must not require them.
ALT_MARK = "fixture-scan:declared-tokens"
ALT_TOKENS_PROFILE = (
    "schema_version = 1\n"
    'profile = "fixture"\n'
    "\n"
    "[tokens]\n"
    f'exclude_marker = "{ALT_MARK}"\n'
    "\n"
    "[tokens.classes.jargon]\n"
    'report_as = "jargon-units"\n'
    "entries = [\n"
    "  { display = \"flubber\", pattern = '\\bflubber\\b',"
    ' flags = ["IGNORECASE"] },\n'
    "]\n"
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

    def test_every_catalog_token_is_flagged_with_its_class(self):
        # Catalog-membership pin: one canonical fixture per token, so a
        # silently dropped catalog entry fails exactly one subTest.
        cases = [
            (C_TIME, J(("hou", "rs"))), (C_TIME, J(("da", "ys"))),
            (C_TIME, W_WEEKS), (C_TIME, J(("mon", "ths"))),
            (C_TIME, J(("quar", "ters"))), (C_TIME, W_SPRINTS),
            (C_TIME, "man-" + J(("hou", "rs"))),
            (C_TIME, "person-" + J(("hou", "rs"))),
            (C_TIME, "engineer-" + J(("hou", "rs"))),
            (C_TIME, "dev-" + J(("hou", "rs"))),
            (C_TIME, W_STORY_POINTS),
            (C_TEAM, J(("one dev", "eloper"))), (C_TEAM, J(("a dev", "eloper"))),
            (C_TEAM, "3 " + J(("engin", "eers"))), (C_TEAM, W_SMALL_TEAM),
            (C_TEAM, W_TEAM_OF + " 3"),
            (C_TEAM, J(("with more peo", "ple"))),
            (C_TEAM, J(("engineering te", "am"))),
            (C_SCHED, W_TIMELINE), (C_SCHED, W_SCHEDULE),
            (C_SCHED, W_AMBITIOUS), (C_SCHED, J(("aggres", "sive"))),
            (C_SCHED, W_ON_TRACK), (C_SCHED, W_ETA),
            (C_SCHED, J(("by EO", "D"))), (C_SCHED, J(("by end of wee", "k"))),
            (C_SCHED, J(("takes a whi", "le"))), (C_SCHED, J(("takes lo", "ng"))),
            (C_SCHED, W_QUICK_WIN),
            (C_EST, W_I_ESTIMATE), (C_EST, "I'd " + J(("esti", "mate"))),
            (C_EST, W_ROUGH_ESTIMATE), (C_EST, W_BALLPARK),
            (C_EST, f"{W_ROUGHLY} 3 " + W_WEEKS),
        ]
        self.assertEqual(len(cases), 34)
        for cls, phrase in cases:
            with self.subTest(token=phrase):
                r, out = self.scan_json(f"the plan needs {phrase} overall\n")
                self.assertEqual(r.returncode, 1,
                                 f"{phrase}: {r.stdout}{r.stderr}")
                self.assertIn(cls, self.classes_hit(out))

    def test_phrase_whitespace_runs_are_normalized(self):
        # Multi-word tokens must match across double spaces / odd wrapping,
        # including inside the composed team-of-N pattern.
        double = W_TEAM_OF.replace(" ", "  ")
        r, out = self.scan_json(f"a {double}  3 could do it\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn(C_TEAM, self.classes_hit(out))

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

    def test_missing_file_is_io_error_exit_3(self):
        r = run_cli([str(self.root / "nope.md")])
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_unknown_flag_is_usage_error_exit_2(self):
        # The JSON-on-stderr contract must hold for usage errors too, not
        # just I/O errors — exit code 2 alone is what stock argparse gives.
        r = run_cli(["--bogus"], stdin_text="x\n")
        self.assertEqual(r.returncode, 2)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["exit_code"], 2)

    def test_unicode_text_is_scanned(self):
        r, out = self.scan_json(f"café naïve — take 2 {W_WEEKS}\n")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["line"], 1)

    def test_empty_stdin_is_clean_exit_0(self):
        r, out = self.scan_json("")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])

    # --- Content self-matching: the scanner's own source stays clean ---

    def test_scanning_own_source_file_is_clean(self):
        # Any copy of the scanner (kit or distributed) fed to itself must
        # report zero hits: every token in its source is assembled from
        # parts, never present at rest. files_scanned pins that the file
        # was actually read, not name-skipped.
        r = run_cli([str(CLI), "--json"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["files_scanned"], 1)

    def test_token_laden_file_named_like_the_scanner_is_still_flagged(self):
        # The self-clean guarantee is content-side, never path or filename
        # special-casing (defer-lint cross-copy precedent).
        p = self.write("banned-token-scan", f"take 2 {W_WEEKS}\n")
        r = run_cli([str(p), "--json"])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(len(out["findings"]), 1)

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

    def scan_json(self, stdin_text=None, args=(), cwd=None, env_extra=None):
        r = run_cli(["--json", *args], stdin_text=stdin_text, cwd=cwd,
                    env_extra=env_extra)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload


class ProfileCatalogTest(ProfileFixtureTest):
    """AC1: the token catalog lives in profiles/conventions.toml and the
    scanner reads it at runtime. Resolution chain and fallback posture
    follow the standalone-checker standard (defer-lint / close-reason-lint
    precedent): --profile > CONVENTIONS_PROFILE > upward walk from cwd;
    profile-less trees and DISCOVERED profiles without the section fall
    back; EXPLICIT selection missing the section is loud."""

    def test_profile_flag_drives_the_catalog(self):
        # Under the alt profile "flubber" is the only token — the kit
        # catalog's tokens must NOT flag; under the kit profile, reverse.
        alt = self.write("alt.toml", ALT_TOKENS_PROFILE)
        text = f"pure flubber, take 2 {W_WEEKS}\n"
        r, out = self.scan_json(text, args=["--profile", str(alt)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual([f["class"] for f in out["findings"]],
                         ["jargon-units"])
        self.assertEqual(out["findings"][0]["token"], "flubber")
        r, out = self.scan_json(text, args=["--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual([f["class"] for f in out["findings"]], [C_TIME])

    def test_env_profile_is_honored(self):
        alt = self.write("alt.toml", ALT_TOKENS_PROFILE)
        r, out = self.scan_json(
            "pure flubber\n", env_extra={"CONVENTIONS_PROFILE": str(alt)})
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["token"], "flubber")
        self.assertTrue(out["grammar_source"].endswith("alt.toml"),
                        out["grammar_source"])

    def test_profile_flag_beats_env(self):
        alt = self.write("alt.toml", ALT_TOKENS_PROFILE)
        env = {"CONVENTIONS_PROFILE": str(alt)}
        # env alone: the alt catalog flags flubber
        r, out = self.scan_json("pure flubber\n", env_extra=env)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        # flag wins: the kit catalog has no flubber entry
        r, out = self.scan_json("pure flubber\n",
                                args=["--profile", str(PROFILE)],
                                env_extra=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertTrue(out["grammar_source"].endswith("conventions.toml"),
                        out["grammar_source"])

    def test_discovered_profile_drives_the_catalog(self):
        # A profile at <cwd>/profiles/conventions.toml is discovered from
        # the invoker's directory (stdin/files tool with no --root — the
        # close-reason-lint anchor).
        self.write("profiles/conventions.toml", ALT_TOKENS_PROFILE)
        r, out = self.scan_json("pure flubber\n", cwd=str(self.root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["token"], "flubber")
        self.assertTrue(out["grammar_source"].endswith("conventions.toml"),
                        out["grammar_source"])

    def test_discovered_profile_without_tokens_section_falls_back(self):
        # A DISCOVERED conventions profile that predates the [tokens]
        # section simply does not parameterize this checker — the built-in
        # catalog applies, and the payload says so.
        self.write("profiles/conventions.toml", "schema_version = 1\n")
        r, out = self.scan_json(f"take 2 {W_WEEKS}\n", cwd=str(self.root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["findings"][0]["class"], C_TIME)
        self.assertEqual(out["grammar_source"], "built-in fallback")

    def test_no_profile_anywhere_falls_back(self):
        (self.root / ".git").mkdir()  # stop the upward walk at the fixture
        r, out = self.scan_json(f"take 2 {W_WEEKS}\n", cwd=str(self.root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["grammar_source"], "built-in fallback")
        r, out = self.scan_json("all clear\n", cwd=str(self.root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_explicit_profile_without_tokens_section_is_error_exit_3(self):
        # Explicit selection is loud: the caller named a catalog source
        # that has no catalog — silent fallback would hide the mistake.
        empty = self.write("empty.toml", "schema_version = 1\n")
        for label, extra, env_extra in (
                ("flag", ["--profile", str(empty)], None),
                ("env", [], {"CONVENTIONS_PROFILE": str(empty)})):
            with self.subTest(source=label):
                r = run_cli(["--json", *extra], stdin_text="x\n",
                            env_extra=env_extra)
                self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
                err = json.loads(r.stderr)
                self.assertFalse(err["ok"])
                self.assertEqual(err["error_kind"], "profile")

    def test_malformed_profile_is_io_error_exit_3(self):
        # A profile that is present but unreadable must fail loudly, never
        # silently fall back — corruption would otherwise hide the catalog.
        bad = self.write("bad.toml", "[tokens\nnot toml at all")
        r = run_cli(["--json", "--profile", str(bad)], stdin_text="x\n")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_incomplete_tokens_section_is_profile_error_exit_3(self):
        partial = self.write(
            "partial.toml",
            "schema_version = 1\n[tokens]\nexclude_marker = \"x\"\n")
        r = run_cli(["--json", "--profile", str(partial)], stdin_text="x\n")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "profile")

    def test_bad_entry_shape_is_profile_error_exit_3(self):
        bad = self.write("bad-entry.toml", ALT_TOKENS_PROFILE.replace(
            "pattern = '\\bflubber\\b'", "pattern = 3"))
        r = run_cli(["--json", "--profile", str(bad)], stdin_text="x\n")
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "profile")

    def test_grammar_source_names_the_discovered_profile(self):
        # The JSON grammar_source key is pinned by the contract test below;
        # this covers the human-output echo only.
        r = run_cli([], stdin_text="all clear\n", cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[grammar:", r.stdout)

    def test_json_contract_gains_additive_keys_only(self):
        # Additive keys only (grammar_source + the region-suppression
        # counters) — the rest of the payload shape is consumed by target
        # repos and must not change.
        r, out = self.scan_json(f"take 2 {W_WEEKS}\n",
                                args=["--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1)
        self.assertEqual(set(out),
                         {"ok", "files_scanned", "findings", "grammar_source",
                          "excluded_regions", "unterminated_regions"})


class DeclaredTokenExclusionTest(ProfileFixtureTest):
    """AC2: the content-side exclusion contract for data files. A region
    bracketed by the declared-token marker lines is catalog DATA — the
    scanner suppresses matching there, in the kit profile and in every
    distributed copy, at any path. Real prose keeps flagging."""

    def test_kit_profile_copy_at_any_path_does_not_self_flag(self):
        # Cross-copy direction 1: distributed profile copies — at the
        # conventional path AND at an arbitrary name — are scan-clean.
        # files_scanned pins the copies were actually read, never
        # name-skipped (the contract is content-side, not path-side).
        copies = []
        for rel in ("profiles/conventions.toml", "data/renamed-copy.toml"):
            dest = self.root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(PROFILE, dest)
            copies.append(str(dest))
        r = run_cli([*copies, "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["files_scanned"], 2)

    def test_profile_copy_is_clean_under_fallback_grammar_too(self):
        # The contract must hold whatever the ACTIVE grammar is: a
        # fallback-grammar run over a tree carrying a distributed profile
        # copy must not flag the copy.
        dest = self.write("stash/profile-copy.toml", "")
        shutil.copy(PROFILE, dest)
        with tempfile.TemporaryDirectory() as elsewhere:
            (Path(elsewhere) / ".git").mkdir()  # profile-less cwd
            r = run_cli([str(dest), "--json"], cwd=elsewhere)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["files_scanned"], 1)

    def test_declared_region_suppresses_only_the_region(self):
        # Both directions in one file: hits before and after the region
        # still flag; catalog-shaped content inside it does not. A token on
        # the begin-marker line itself pins the documented contract that
        # marker lines are part of the region.
        p = self.write("doc.md", (
            f"take 2 {W_WEEKS} to assess\n"
            f"{MARK_BEGIN} catalog data {W_BALLPARK}\n"
            f"{W_TIMELINE} {W_BALLPARK}\n"
            f"pattern = '\\b{W_WEEKS}\\b'\n"
            f"{MARK_END}\n"
            f"the {W_TIMELINE} slipped\n"))
        r = run_cli([str(p), "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(sorted((f["line"], f["token"])
                                for f in out["findings"]),
                         [(1, W_WEEKS), (6, W_TIMELINE)])
        self.assertEqual(out["excluded_regions"], 1)
        self.assertEqual(out["unterminated_regions"], 0)

    def test_profile_exclude_marker_drives_suppression(self):
        # The active profile's marker — not the kit's — is the exclusion
        # contract. A region bracketed by the alt profile's marker
        # suppresses that profile's token; the kit marker means nothing
        # under the alt profile (its region does NOT suppress).
        alt = self.write("alt.toml", ALT_TOKENS_PROFILE)
        theirs = self.write("theirs.md",
                            f"{ALT_MARK}:begin\nflubber\n{ALT_MARK}:end\n")
        r = run_cli([str(theirs), "--json", "--profile", str(alt)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(json.loads(r.stdout)["excluded_regions"], 1)
        ours = self.write("ours.md",
                          f"{MARK_BEGIN}\nflubber\n{MARK_END}\n")
        r = run_cli([str(ours), "--json", "--profile", str(alt)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([f["token"] for f in out["findings"]], ["flubber"])
        self.assertEqual(out["excluded_regions"], 0)

    def test_same_line_begin_end_pair_is_a_one_line_region(self):
        # A begin+end pair on one line suppresses that line only —
        # scanning resumes on the next line instead of running to EOF.
        p = self.write("doc.md",
                       f"{MARK_BEGIN} {W_WEEKS} {MARK_END}\n"
                       f"take 2 {W_WEEKS}\n")
        r = run_cli([str(p), "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([(f["line"], f["token"]) for f in out["findings"]],
                         [(2, W_WEEKS)])
        self.assertEqual(out["excluded_regions"], 1)
        self.assertEqual(out["unterminated_regions"], 0)

    def test_marker_superstring_does_not_open_a_region(self):
        # A marker embedded in a longer word is inert — it must not open
        # a region and swallow the rest of the file.
        p = self.write("doc.md",
                       f"see the {MARK_BEGIN}ner-notes\n"
                       f"take 2 {W_WEEKS}\n")
        r = run_cli([str(p), "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([(f["line"], f["token"]) for f in out["findings"]],
                         [(2, W_WEEKS)])
        self.assertEqual(out["excluded_regions"], 0)

    def test_unterminated_region_excludes_to_eof(self):
        # Documented ceiling: a begin marker with no end marker excludes
        # the rest of that source (accident hazard, not adversary defense).
        # The unterminated_regions counter surfaces the accident.
        r, out = self.scan_json(f"{MARK_BEGIN}\ntake 2 {W_WEEKS}\n",
                                args=["--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["excluded_regions"], 1)
        self.assertEqual(out["unterminated_regions"], 1)

    def test_region_state_does_not_leak_across_files(self):
        # An unterminated region in one file must not swallow the next.
        a = self.write("a.md", f"{MARK_BEGIN}\n{W_TIMELINE}\n")
        b = self.write("b.md", f"take 2 {W_WEEKS}\n")
        r = run_cli([str(a), str(b), "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual([(f["file"], f["token"]) for f in out["findings"]],
                         [(str(b), W_WEEKS)])

    def test_real_prose_still_flags_under_the_profile_catalog(self):
        # Cross-copy direction 2, stated explicitly against the profile
        # grammar: ordinary prose with real hits keeps flagging.
        p = self.write("notes.md", f"this needs a {W_SMALL_TEAM} and "
                                   f"{W_ROUGHLY} 3 {W_WEEKS}\n")
        r = run_cli([str(p), "--json", "--profile", str(PROFILE)])
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        classes = {f["class"] for f in out["findings"]}
        self.assertEqual(classes, {C_TEAM, C_EST, C_TIME})


class FallbackParityTest(ProfileFixtureTest):
    """AC1: the built-in fallback catalog stays pinned to the profile —
    structurally on every checker-consumed key, and behaviorally over a
    fixture exercising every class, both flag postures, overlap dedupe,
    composed patterns, and the declared-token region."""

    def test_fallback_structurally_matches_kit_profile_section(self):
        # Structural pin, complementing the behavioral parity scan below:
        # pattern loosening, flag flips, entry reordering, or list edits
        # on either side cannot drift silently. (Deliberate unit-level
        # exception to the subprocess-only style — sample-based scans
        # cannot pin pattern equality; same idiom as the other suites.)
        loader = SourceFileLoader("banned_token_scan_module", str(CLI))
        spec = importlib.util.spec_from_loader(
            "banned_token_scan_module", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        fallback = mod.FALLBACK_TOKENS
        with open(PROFILE, "rb") as f:
            section = tomllib.load(f)["tokens"]
        self.assertEqual(fallback["exclude_marker"],
                         section["exclude_marker"])
        # Class group names AND order (matcher order is behavior: overlap
        # dedupe keeps the first-matched span per class).
        self.assertEqual(list(fallback["classes"]), list(section["classes"]))
        for group, cls in fallback["classes"].items():
            prof_cls = section["classes"][group]
            self.assertEqual(cls["report_as"], prof_cls["report_as"],
                             f"classes.{group}.report_as drifted")
            self.assertEqual(len(cls["entries"]), len(prof_cls["entries"]),
                             f"classes.{group} entry count drifted")
            for i, (fe, pe) in enumerate(zip(cls["entries"],
                                             prof_cls["entries"])):
                for key in ("display", "pattern"):
                    self.assertEqual(fe[key], pe[key],
                                     f"classes.{group}[{i}].{key} drifted")
                self.assertEqual(fe.get("flags", []), pe.get("flags", []),
                                 f"classes.{group}[{i}].flags drifted")
        # The catalog is genuinely the full 34-token set.
        self.assertEqual(sum(len(c["entries"])
                             for c in fallback["classes"].values()), 34)

    def test_fallback_displays_carry_no_regex_metacharacters(self):
        # _word_pat interpolates displays into patterns without re.escape
        # (escaping would break the byte-parity with the profile's pattern
        # strings above). That is safe only while displays stay free of
        # regex metacharacters — this pins the premise.
        loader = SourceFileLoader("banned_token_scan_meta_pin", str(CLI))
        spec = importlib.util.spec_from_loader(
            "banned_token_scan_meta_pin", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        forbidden = set(".^$*+?{}[]()|\\")
        for group, cls in mod.FALLBACK_TOKENS["classes"].items():
            for entry in cls["entries"]:
                self.assertFalse(
                    set(entry["display"]) & forbidden,
                    f"classes.{group} display {entry['display']!r} carries "
                    "a regex metacharacter — _word_pat does not escape")

    def test_fallback_behavioral_parity_with_kit_profile(self):
        # Every class, the case-sensitive entry both ways, dedupe,
        # composed patterns, and region suppression — identical verdicts
        # from the kit profile and the built-in fallback.
        text = (
            f"budget: 12 person-{W_HOURS} plus 3 {W_HOURS}\n"
            f"a {W_TEAM_OF} 3 could; {W_TWO_ENGINEERS} might\n"
            f"{W_ROUGHLY} 3 {W_WEEKS} of slack\n"
            f"the {W_ETA} is unclear; the {W_ETA.lower()} squared term\n"
            f"{W_TIMELINE} {W_AMBITIOUS} {W_QUICK_WIN}\n"
            f"{W_I_ESTIMATE} {W_BALLPARK}\n"
            f"{MARK_BEGIN} declared data\n"
            f"{W_SCHEDULE} {W_SPRINTS}\n"
            f"{MARK_END}\n"
            f"tail {W_DAYS}\n"
        )
        (self.root / ".git").mkdir()  # profile-less tree → fallback
        r_fb, out_fb = self.scan_json(text, cwd=str(self.root))
        r_prof, out_prof = self.scan_json(
            text, args=["--profile", str(PROFILE)])
        self.assertEqual(r_fb.returncode, r_prof.returncode,
                         r_fb.stdout + r_prof.stdout
                         + r_fb.stderr + r_prof.stderr)
        # grammar_source is the one legitimate difference between the runs.
        self.assertEqual(out_fb.pop("grammar_source"), "built-in fallback")
        self.assertTrue(out_prof.pop("grammar_source")
                        .endswith("conventions.toml"))
        self.assertEqual(out_fb, out_prof)
        # The fixture genuinely exercises all four classes and the region.
        classes = {f["class"] for f in out_fb["findings"]}
        self.assertEqual(classes, {C_TIME, C_TEAM, C_SCHED, C_EST})
        self.assertNotIn(8, [f["line"] for f in out_fb["findings"]])


if __name__ == "__main__":
    unittest.main()
