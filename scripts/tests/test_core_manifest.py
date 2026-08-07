#!/usr/bin/env python3
"""Behavioral tests for profiles/core-manifest.list — the house-rules-core
content list.

Asserts the three durable properties the core tier depends on:
  1. the manifest exists and parses (kind|path lines, known kinds),
  2. every listed path exists in the expected shape (rule file, skill dir
     with SKILL.md, executable CLI),
  3. every listed rule file and every .md in a listed skill dir is free
     of bd/bead/beads references — the core-tier promise is zero
     workflow nagging.

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

# The core-tier cleanliness pattern: no `bd` as a word, no `bead`/`beads`
# as a word (singular included — "claim the bead" is workflow language even
# though the AC's literal grep only named the plural). Case-insensitive.
BD_PATTERN = re.compile(r"\bbd\b|\bbeads?\b", re.IGNORECASE)


def parse_manifest(text):
    """Parse manifest text into (kind, path) tuples.

    Raises ValueError on a malformed line (missing '|', unknown kind,
    absolute or ..-traversal path, duplicate entry) so a bad manifest fails
    loudly rather than resolving against whatever exists on the machine.
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
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"line {lineno}: path must be repo-relative: {path!r}")
        if (kind, path) in entries:
            raise ValueError(f"line {lineno}: duplicate entry: {line!r}")
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
    """Files whose text must be bd/beads-clean.

    A skill entry denotes the whole directory, so every .md in it is
    checked — SKILL.md plus any companion files a skill grows later.
    """
    targets = []
    for kind, path in entries:
        if kind == "rule":
            targets.append(root / path)
        elif kind == "skill":
            targets.extend(sorted((root / path).rglob("*.md")))
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

    def test_required_core_members_present(self):
        # The full shipped set: the AC-named members plus graybeard-playbook
        # (the family's rule per graybeard-help's own table) and the
        # prose-voice skill (hard dependency of the prose-voice rule) —
        # deleting either breaks the manifest's cross-reference-closure
        # invariant, so the pin covers all 12 entries.
        required = {
            ("rule", "cursor/rules/agent-identity.mdc"),
            ("rule", "cursor/rules/defer-convention.mdc"),
            ("rule", "cursor/rules/prose-voice.mdc"),
            ("rule", "cursor/rules/parallel-subagent-safety.mdc"),
            ("rule", "cursor/rules/graybeard-playbook.mdc"),
            ("skill", "skills/graybeard-review"),
            ("skill", "skills/graybeard-audit"),
            ("skill", "skills/graybeard-debt"),
            ("skill", "skills/graybeard-help"),
            ("skill", "skills/prose-voice"),
            ("cli", "scripts/defer-lint"),
            ("cli", "scripts/banned-token-scan"),
        }
        self.assertLessEqual(
            required,
            set(self.entries),
            "manifest is missing required core members",
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

    def test_parse_rejects_absolute_traversal_and_duplicate_paths(self):
        # Path(root) / "/usr/bin/env" silently discards root — a typo'd
        # absolute entry would resolve against the test machine's
        # filesystem and pass. Traversal and duplicates likewise fail loud.
        with self.assertRaises(ValueError):
            parse_manifest("cli|/usr/bin/env\n")
        with self.assertRaises(ValueError):
            parse_manifest("rule|../outside/rule.mdc\n")
        with self.assertRaises(ValueError):
            parse_manifest("cli|scripts/defer-lint\ncli|scripts/defer-lint\n")

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
                "Beads is the source of truth.\n"
                "Claim the bead before starting.\n",
                encoding="utf-8",
            )
            hits = find_unclean([("rule", "cursor/rules/dirty.mdc")], root)
            self.assertEqual(len(hits), 3)

    def test_clean_rule_produces_no_hits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rules = root / "cursor" / "rules"
            rules.mkdir(parents=True)
            # Word-boundary negatives that would trip a boundary-less
            # pattern: "subdirectory" and "lambda" contain the bd
            # substring; "beadwork" starts with bead but is one word.
            (rules / "clean.mdc").write_text(
                "Check the subdirectory for lambda helpers; beadwork"
                " metaphors are fine.\n",
                encoding="utf-8",
            )
            self.assertEqual(
                find_unclean([("rule", "cursor/rules/clean.mdc")], root), []
            )

    def test_dirty_skill_companion_file_is_flagged(self):
        # A skill entry denotes the directory: a clean SKILL.md must not
        # shield a companion .md carrying workflow references.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "some-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("Clean text.\n", encoding="utf-8")
            (skill / "references.md").write_text(
                "Track it with bd create.\n", encoding="utf-8"
            )
            hits = find_unclean([("skill", "skills/some-skill")], root)
            self.assertEqual(len(hits), 1)
            self.assertIn("references.md", hits[0][0])


if __name__ == "__main__":
    unittest.main()
