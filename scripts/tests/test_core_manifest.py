#!/usr/bin/env python3
"""Behavioral tests for profiles/core-manifest.list — the house-rules-core
content list.

Asserts the three durable properties the core tier depends on:
  1. the manifest exists and parses (kind|path lines, known kinds),
  2. every listed path exists in the expected shape (rule file, skill dir
     with SKILL.md, executable CLI),
  3. every listed rule file and skill SKILL.md is free of bd/beads
     references — the core-tier promise is zero workflow nagging.

Checks are factored as helpers so fixture tests can prove they actually
flag violations (a checker that passes regardless of correctness is zero
signal).

Run: python3 scripts/tests/test_core_manifest.py
"""

import os
import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO_ROOT / "profiles" / "core-manifest.list"

KNOWN_KINDS = {"rule", "skill", "cli"}

# The core-tier cleanliness pattern from the acceptance criteria: no `bd`
# as a word, no `beads`. Case-insensitive.
BD_PATTERN = re.compile(r"\bbd\b|beads", re.IGNORECASE)


def parse_manifest(text):
    """Parse manifest text into (kind, path) tuples.

    Raises ValueError on a malformed line (missing '|' or unknown kind) so
    a bad manifest fails loudly rather than being silently skipped.
    """
    entries = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            raise ValueError(f"line {lineno}: no '|' separator: {line!r}")
        kind, path = line.split("|", 1)
        if kind not in KNOWN_KINDS:
            raise ValueError(f"line {lineno}: unknown kind {kind!r}")
        if not path:
            raise ValueError(f"line {lineno}: empty path")
        entries.append((kind, path))
    return entries


def find_missing(entries, root):
    """Return entries whose path does not exist in the expected shape."""
    missing = []
    for kind, path in entries:
        target = root / path
        if kind == "rule":
            ok = target.is_file()
        elif kind == "skill":
            ok = target.is_dir() and (target / "SKILL.md").is_file()
        else:  # cli
            ok = target.is_file() and os.access(target, os.X_OK)
        if not ok:
            missing.append((kind, path))
    return missing


def grep_targets(entries, root):
    """Files whose text must be bd/beads-clean: rule files and skill SKILL.md."""
    targets = []
    for kind, path in entries:
        if kind == "rule":
            targets.append(root / path)
        elif kind == "skill":
            targets.append(root / path / "SKILL.md")
    return targets


def find_unclean(entries, root):
    """Return (file, lineno, line) for every bd/beads hit in grep targets."""
    hits = []
    for target in grep_targets(entries, root):
        for lineno, line in enumerate(
            target.read_text(encoding="utf-8").splitlines(), 1
        ):
            if BD_PATTERN.search(line):
                hits.append((str(target.relative_to(root)), lineno, line.strip()))
    return hits


class TestRealManifest(unittest.TestCase):
    """The shipped manifest satisfies the core-tier acceptance criteria."""

    def setUp(self):
        self.assertTrue(
            MANIFEST.is_file(),
            f"core manifest missing at {MANIFEST.relative_to(REPO_ROOT)}",
        )
        self.entries = parse_manifest(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_nonempty_and_well_formed(self):
        self.assertGreater(len(self.entries), 0, "manifest lists nothing")

    def test_required_core_members_present(self):
        # Pinned by the bead's acceptance criteria.
        required = {
            ("rule", "cursor/rules/agent-identity.mdc"),
            ("rule", "cursor/rules/defer-convention.mdc"),
            ("rule", "cursor/rules/prose-voice.mdc"),
            ("rule", "cursor/rules/parallel-subagent-safety.mdc"),
            ("skill", "skills/graybeard-review"),
            ("skill", "skills/graybeard-audit"),
            ("skill", "skills/graybeard-debt"),
            ("skill", "skills/graybeard-help"),
            ("cli", "scripts/defer-lint"),
            ("cli", "scripts/banned-token-scan"),
        }
        self.assertLessEqual(
            required,
            set(self.entries),
            "manifest is missing AC-required core members",
        )

    def test_every_listed_path_exists(self):
        self.assertEqual(find_missing(self.entries, REPO_ROOT), [])

    def test_core_rules_and_skills_are_bd_clean(self):
        hits = find_unclean(self.entries, REPO_ROOT)
        self.assertEqual(
            hits, [], "core-listed files contain bd/beads references: " f"{hits}"
        )


class TestCheckersAreNotVacuous(unittest.TestCase):
    """Fixture negatives: the helpers must flag violations, not wave them by."""

    def test_parse_rejects_unknown_kind_and_malformed_line(self):
        with self.assertRaises(ValueError):
            parse_manifest("hook|scripts/some-hook\n")
        with self.assertRaises(ValueError):
            parse_manifest("cursor/rules/agent-identity.mdc\n")

    def test_missing_path_is_flagged(self):
        entries = [("rule", "cursor/rules/does-not-exist.mdc")]
        self.assertEqual(find_missing(entries, REPO_ROOT), entries)

    def test_skill_dir_without_skill_md_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "empty-skill").mkdir(parents=True)
            entries = [("skill", "skills/empty-skill")]
            self.assertEqual(find_missing(entries, root), entries)

    def test_bd_referencing_rule_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "cursor" / "rules"
            rules.mkdir(parents=True)
            (rules / "dirty.mdc").write_text(
                "Run bd ready to find the next task.\n"
                "Beads is the source of truth.\n",
                encoding="utf-8",
            )
            hits = find_unclean([("rule", "cursor/rules/dirty.mdc")], root)
            self.assertEqual(len(hits), 2)

    def test_clean_rule_produces_no_hits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "cursor" / "rules"
            rules.mkdir(parents=True)
            # "bead" singular and "embedded" must NOT trip the word-boundary
            # pattern; only `bd` as a word or `beads` count.
            (rules / "clean.mdc").write_text(
                "A bead description is out of scope. Embedded text is fine.\n",
                encoding="utf-8",
            )
            self.assertEqual(
                find_unclean([("rule", "cursor/rules/clean.mdc")], root), []
            )


if __name__ == "__main__":
    unittest.main()
