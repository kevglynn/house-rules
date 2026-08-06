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

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
import tomllib
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "defer-lint"
PROFILE = CLI.parent.parent / "profiles" / "conventions.toml"

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


def run_cli(args, cwd=None, env_extra=None, cli=None):
    # CONVENTIONS_PROFILE is scrubbed so a profile configured in the
    # developer's environment can never leak grammar into a fixture run.
    env = {k: v for k, v in os.environ.items() if k != "CONVENTIONS_PROFILE"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["python3", str(cli or CLI)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def alt_defer_profile(marker_word):
    """A minimal-but-complete [defer] profile with a custom marker word.

    source_exts is deliberately narrowed to .py so tests can also prove the
    scanned file set comes from the profile, not from any built-in list.
    """
    return (
        "schema_version = 1\n"
        'profile = "fixture"\n'
        "\n"
        "[defer]\n"
        f'marker_word = "{marker_word}"\n'
        'marker_suffix = ":"\n'
        "\n"
        "[defer.scan]\n"
        "marker_line_prefixes = ['#+', '//+']\n"
        "continuation_prefixes = ['#+', '//+']\n"
        'skip_dirs = [".git"]\n'
        "extra_filenames = []\n"
        'source_exts = [".py"]\n'
        "\n"
        '[defer.clauses."upgrade-when"]\n'
        "pattern = 'upgrade\\s+when:'\n"
        'flags = ["IGNORECASE"]\n'
        'severity = "error"\n'
        "\n"
        "[defer.clauses.ceiling]\n"
        "pattern = 'ceiling:'\n"
        'flags = ["IGNORECASE"]\n'
        'severity = "warning"\n'
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

    def scan(self, *extra, env_extra=None):
        return run_cli(["--root", str(self.root), *extra],
                       env_extra=env_extra)

    def scan_json(self, *extra, env_extra=None):
        r = run_cli(["--root", str(self.root), "--json", *extra],
                    env_extra=env_extra)
        payload = json.loads(r.stdout) if r.stdout.strip() else None
        return r, payload


class DeferLintTest(FixtureTest):
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
        r = run_cli(["--root", str(self.root), "--json"], cli=dest)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["findings"], [])

    def test_kit_copy_scanning_tree_with_distributed_copy_is_clean(self):
        # The kit's own copy is routinely invoked against bootstrapped target
        # repos that carry a distributed copy at scripts/defer-lint — and,
        # post-distribution, the profile data file next to it. Both are
        # different paths from the running copy's own — the exclusion
        # contract must hold by content, not path identity.
        dest = self.root / "scripts" / "defer-lint"
        dest.parent.mkdir(parents=True)
        shutil.copy(CLI, dest)
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR)
        profile_dest = self.root / "profiles" / "conventions.toml"
        profile_dest.parent.mkdir(parents=True)
        shutil.copy(PROFILE, profile_dest)
        r, out = self.scan_json()  # runs the ORIGINAL CLI over self.root
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(
            [f for f in out["findings"]
             if f["file"] in ("scripts/defer-lint",
                              "profiles/conventions.toml")],
            [],
        )

    def test_profile_data_file_does_not_trip_the_scanner(self):
        # Exclusion contract (design doc): the profile that CARRIES the
        # defer grammar is itself a scanned .toml source file; its grammar
        # strings must be clean by construction — no line may hold a
        # comment-prefix-adjacent marker occurrence.
        dest = self.root / "profiles" / "conventions.toml"
        dest.parent.mkdir(parents=True)
        shutil.copy(PROFILE, dest)
        self.write("ok.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["findings"], [])
        self.assertEqual(out["defer_comments"], 0)

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
        for key in ("ok", "root", "grammar_source", "files_scanned",
                    "files_skipped", "defer_comments", "findings"):
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


class ProfileGrammarTest(FixtureTest):
    """AC: the defer grammar lives in profiles/conventions.toml and
    defer-lint reads it at runtime — marker word, clause requirements, and
    the scanned file set all come from the profile when one is present."""

    def test_discovered_profile_marker_drives_the_scan(self):
        # A profile at <root>/profiles/conventions.toml is discovered from
        # the scan root; its marker word replaces the built-in one, so the
        # D-marker comment below must NOT register as a defer.
        self.write("profiles/conventions.toml", alt_defer_profile("postpone"))
        self.write("a.py", "# postpone: quick hack.\n" + BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(out["defer_comments"], 1)
        self.assertEqual(len(out["findings"]), 1)
        f = out["findings"][0]
        self.assertEqual(f["missing"], ["upgrade-when", "ceiling"])
        self.assertEqual(f["severity"], "error")
        self.assertIn("postpone:", f["text"])

    def test_profile_scanned_file_set_drives_file_selection(self):
        # The fixture profile narrows source_exts to .py — the .js file
        # must not be scanned at all.
        self.write("profiles/conventions.toml", alt_defer_profile("postpone"))
        self.write("bad.js", "// postpone: no clauses at all.\n")
        self.write("ok.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(out["files_scanned"], 1)
        self.assertEqual(out["defer_comments"], 0)

    def test_env_profile_is_honored(self):
        with tempfile.TemporaryDirectory() as tmp:
            alt = Path(tmp) / "alt.toml"
            alt.write_text(alt_defer_profile("postpone"))
            self.write("a.py", "# postpone: quick hack.\n")
            r, out = self.scan_json(
                env_extra={"CONVENTIONS_PROFILE": str(alt)})
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("upgrade-when", out["findings"][0]["missing"])

    def test_profile_flag_beats_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            flag_profile = Path(tmp) / "flag.toml"
            flag_profile.write_text(alt_defer_profile("postpone"))
            env_profile = Path(tmp) / "env.toml"
            env_profile.write_text(alt_defer_profile("shelve"))
            self.write("a.py", "# postpone: quick hack.\n")
            env = {"CONVENTIONS_PROFILE": str(env_profile)}
            # env alone: shelve grammar, the postpone line is not a defer
            r, out = self.scan_json(env_extra=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(out["defer_comments"], 0)
            # flag wins: postpone grammar flags it
            r, out = self.scan_json("--profile", str(flag_profile),
                                    env_extra=env)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertEqual(out["defer_comments"], 1)

    def test_malformed_discovered_profile_is_io_error_exit_3(self):
        # A profile that is present but unreadable must fail loudly, never
        # silently fall back — corruption would otherwise hide grammar.
        self.write("profiles/conventions.toml", "[defer\nnot toml at all")
        self.write("a.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIsNone(out)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "io")

    def test_incomplete_defer_section_is_profile_error_exit_3(self):
        self.write("profiles/conventions.toml",
                   'schema_version = 1\n[defer]\nmarker_word = "defer"\n')
        self.write("a.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertFalse(err["ok"])
        self.assertEqual(err["error_kind"], "profile")

    def test_discovered_profile_without_defer_section_falls_back(self):
        # A DISCOVERED conventions profile that predates the [defer]
        # section simply does not parameterize this checker — built-in
        # grammar applies, and the payload says so.
        self.write("profiles/conventions.toml", "schema_version = 1\n")
        self.write("a.py", BAD_NO_TRIGGER)
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("upgrade-when", out["findings"][0]["missing"])
        self.assertEqual(out["grammar_source"], "built-in fallback")

    def test_explicit_profile_without_defer_section_is_error_exit_3(self):
        # Explicit selection is loud: the caller named a grammar source
        # that has no grammar — silent fallback would hide the mistake.
        with tempfile.TemporaryDirectory() as tmp:
            alt = Path(tmp) / "alt.toml"
            alt.write_text("schema_version = 1\n")
            self.write("a.py", BAD_NO_TRIGGER)
            r, out = self.scan_json("--profile", str(alt))
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            err = json.loads(r.stderr)
            self.assertFalse(err["ok"])
            self.assertEqual(err["error_kind"], "profile")

    def test_clauses_as_array_of_tables_is_profile_error_exit_3(self):
        # [[defer.clauses]] parses as a list, not a table of named clause
        # tables — must be a profile error, not a crash.
        bad = alt_defer_profile("postpone").replace(
            '[defer.clauses."upgrade-when"]', '[[defer.clauses]]').replace(
            "[defer.clauses.ceiling]", "[[defer.clauses]]")
        self.write("profiles/conventions.toml", bad)
        self.write("a.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "profile")

    def test_non_string_comment_prefix_is_profile_error_exit_3(self):
        bad = alt_defer_profile("postpone").replace(
            "marker_line_prefixes = ['#+', '//+']",
            "marker_line_prefixes = ['#+', 3]")
        self.write("profiles/conventions.toml", bad)
        self.write("a.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        err = json.loads(r.stderr)
        self.assertEqual(err["error_kind"], "profile")

    def test_grammar_source_names_the_discovered_profile(self):
        self.write("profiles/conventions.toml", alt_defer_profile("postpone"))
        self.write("a.py", "x = 1\n")
        r, out = self.scan_json()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(
            out["grammar_source"].endswith("conventions.toml"),
            out["grammar_source"])
        self.assertIn("[grammar:", self.scan().stdout)

    def test_fallback_parity_with_kit_profile_grammar(self):
        # Drift guard, not red-proof: the built-in fallback and the kit
        # profile's [defer] section must produce identical scans over a
        # fixture that exercises markers, clauses (both severities and
        # near-miss trigger text), prefixes, skip dirs, extra filenames,
        # and extensions.
        self.write("a.py", GOOD_ONE_LINE + BAD_NO_TRIGGER)
        self.write("b.sql", f"-- {D} full scan. ceiling: x. upgrade when: y.\n")
        self.write("c.css", f"/* {D} magic number. ceiling: x. upgrade when: y. */\n")
        self.write(
            "d.java",
            f"/* {D} sync call. ceiling: blocks the event loop.\n"
            " * upgrade when: p99 latency matters. */\n",
        )
        self.write("Makefile", BAD_CEILING_ONLY)
        # Warning-only path: a loosened profile severity would diverge here.
        self.write("f.py", BAD_TRIGGER_ONLY)
        # Near-miss trigger text: a loosened upgrade-when pattern (e.g. bare
        # "upgrade") would stop flagging these under one grammar only.
        self.write("g.py", f"# {D} near miss. ceiling: x. we may upgrade later.\n")
        self.write("h.py", f"# {D} near miss. ceiling: x. upgrade sometime: y.\n")
        self.write("bin/tool", "#!/usr/bin/env python3\n" + BAD_NO_TRIGGER)
        self.write("e.toml", f"# {D} toml file. ceiling: x. upgrade when: y.\n")
        self.write("node_modules/pkg/i.js", f"// {D} vendored, skipped.\n")
        r_fallback, out_fallback = self.scan_json()
        r_profile, out_profile = self.scan_json(
            env_extra={"CONVENTIONS_PROFILE": str(PROFILE)})
        self.assertEqual(r_fallback.returncode, r_profile.returncode,
                         r_fallback.stdout + r_profile.stdout
                         + r_fallback.stderr + r_profile.stderr)
        # grammar_source is the one legitimate difference between the runs.
        self.assertEqual(out_fallback.pop("grammar_source"),
                         "built-in fallback")
        self.assertTrue(out_profile.pop("grammar_source")
                        .endswith("conventions.toml"))
        self.assertEqual(out_fallback, out_profile)
        self.assertGreater(out_fallback["defer_comments"], 0)
        # The fixture genuinely exercises both severity paths.
        severities = {f["severity"] for f in out_fallback["findings"]}
        self.assertEqual(severities, {"error", "warning"})

    def test_fallback_structurally_matches_kit_profile_section(self):
        # Structural pin, complementing the behavioral parity scan above:
        # every checker-consumed key of the built-in fallback must equal
        # the kit profile's [defer] section, so severity flips, pattern
        # loosening, or list edits on either side cannot drift silently.
        # (Deliberate unit-level exception to the subprocess-only style —
        # sample-based scans cannot pin pattern equality.)
        loader = SourceFileLoader("defer_lint_module", str(CLI))
        spec = importlib.util.spec_from_loader("defer_lint_module", loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        fallback = mod.FALLBACK_DEFER
        with open(PROFILE, "rb") as f:
            section = tomllib.load(f)["defer"]
        self.assertEqual(fallback["marker_word"], section["marker_word"])
        self.assertEqual(fallback["marker_suffix"], section["marker_suffix"])
        # Clause names, order, and full checker-consumed entries.
        self.assertEqual(list(fallback["clauses"]), list(section["clauses"]))
        for name, entry in fallback["clauses"].items():
            profile_entry = section["clauses"][name]
            for key in ("pattern", "flags", "severity"):
                self.assertEqual(entry[key], profile_entry[key],
                                 f"clauses.{name}.{key} drifted")
        for key in ("marker_line_prefixes", "continuation_prefixes",
                    "skip_dirs", "extra_filenames", "source_exts"):
            self.assertEqual(fallback["scan"][key], section["scan"][key],
                             f"scan.{key} drifted")


if __name__ == "__main__":
    unittest.main()
