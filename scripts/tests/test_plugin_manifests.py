#!/usr/bin/env python3
"""Behavioral tests for the plugin manifests on three surfaces
(process-kit-wsi).

Surfaces and the schema each was verified against (2026-08-07):
  1. .claude-plugin/marketplace.json — Claude Code plugin marketplace.
     Docs: https://code.claude.com/docs/en/plugin-marketplaces and
     https://code.claude.com/docs/en/plugins-reference. Required fields:
     name, owner.name, plugins; each entry requires name + source. A
     marketplace-root source ("./") with strict: false makes the entry
     the complete component definition, and a component-declaring
     .claude-plugin/plugin.json alongside it would be a load conflict.
  2. .cursor-plugin/plugin.json — Cursor Plugin manifest.
     Docs: https://cursor.com/docs/reference/plugins. Required field:
     name (lowercase kebab-case); rules/skills accept path arrays;
     paths must be relative with no ".." traversal.
  3. plugin.json (repo root) — Agent Plugins open standard.
     Docs: https://agent-plugins.org/plugin-authors/manifest. Required:
     $schema + name; the top-level field set is closed; names are 1-64
     chars of lowercase alnum/hyphen/period with alnum ends and no
     "--" or "..".

Core-plugin contents are DERIVED from profiles/core-manifest.list via
test_core_manifest.parse_manifest — the single source of truth for core
membership — never restated here. Helpers are factored so fixture tests
can prove they flag violations (a checker that passes regardless of
correctness is zero signal).

Run: python3 scripts/tests/test_plugin_manifests.py
"""

import json
import re
import unittest
from pathlib import Path

from test_core_manifest import MANIFEST as CORE_MANIFEST
from test_core_manifest import parse_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLAUDE_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR_PLUGIN = REPO_ROOT / ".cursor-plugin" / "plugin.json"
ROOT_PLUGIN = REPO_ROOT / "plugin.json"

# Claude Code and Cursor both require kebab-case plugin/marketplace names.
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# The Agent Plugins manifest schema is closed: unknown top-level fields
# are schema violations (agent-plugins.org/plugin-authors/manifest).
AGENT_PLUGINS_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
AGENT_PLUGINS_NAME = re.compile(r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$|^[a-z0-9]$")

# Beads-workflow members the full plugin must cover (names verified
# against claude/rules/ and skills/ in this tree).
FULL_PLUGIN_RULES = [
    "claude/rules/session-lifecycle.md",
    "claude/rules/operating-model.md",
    "claude/rules/bead-completion.md",
    "claude/rules/beads-quality.md",
]
FULL_PLUGIN_SKILLS = [
    "skills/bead-authoring",
    "skills/graph-planning",
]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def agent_plugins_name_ok(name):
    """Name rule from the Agent Plugins standard."""
    if not isinstance(name, str) or not 1 <= len(name) <= 64:
        return False
    if "--" in name or ".." in name:
        return False
    return bool(AGENT_PLUGINS_NAME.match(name))


def normalize(declared):
    """Manifest path ("./skills/foo" or "skills/foo/") -> repo-relative."""
    return declared[2:].rstrip("/") if declared.startswith("./") else declared.rstrip("/")


def bad_paths(declared_paths, root):
    """Return declared paths that are absolute, traverse with '..', or
    don't exist in the tree. Vendor rule shared by all three surfaces."""
    bad = []
    for declared in declared_paths:
        p = Path(normalize(declared))
        if p.is_absolute() or ".." in p.parts or not (root / p).exists():
            bad.append(declared)
    return bad


def declared_covers(declared_paths, member, root):
    """True if a declared path names `member` directly or is a directory
    ancestor of it (Claude Code scans declared directories)."""
    target = (root / member).resolve()
    for declared in declared_paths:
        p = (root / normalize(declared)).resolve()
        if p == target or p in target.parents:
            return True
    return False


def core_expectations():
    """Derive per-surface expected paths from the core manifest."""
    entries = parse_manifest(CORE_MANIFEST.read_text(encoding="utf-8"))
    skills = {"./" + p for k, p in entries if k == "skill"}
    rules_mdc = {"./" + p for k, p in entries if k == "rule"}
    # Each rule has a generated claude/rules/<name>.md projection
    # (frontmatter stripped, .mdc -> .md) — the Claude-flavored package
    # derives those paths from the rule entries.
    rules_md = {
        "./claude/rules/" + Path(p).stem + ".md" for k, p in entries if k == "rule"
    }
    clis = {p for k, p in entries if k == "cli"}
    return skills, rules_mdc, rules_md, clis


class TestClaudeMarketplace(unittest.TestCase):
    """.claude-plugin/marketplace.json satisfies the vendor schema and
    the core/full tier contract."""

    def setUp(self):
        self.assertTrue(CLAUDE_MARKETPLACE.is_file(), "marketplace.json missing")
        self.doc = load_json(CLAUDE_MARKETPLACE)
        self.entries = {p["name"]: p for p in self.doc["plugins"]}

    def test_required_marketplace_fields(self):
        self.assertRegex(self.doc["name"], KEBAB)
        self.assertIsInstance(self.doc["owner"], dict)
        self.assertIsInstance(self.doc["owner"]["name"], str)
        self.assertIsInstance(self.doc["plugins"], list)

    def test_two_plugins_core_and_full(self):
        self.assertEqual(
            set(self.entries), {"house-rules-core", "house-rules-full"}
        )
        for entry in self.entries.values():
            self.assertRegex(entry["name"], KEBAB)
            # Marketplace-root source with strict: false is the pattern
            # this repo uses: the entry is the complete definition.
            self.assertEqual(entry["source"], "./")
            self.assertIs(entry["strict"], False)

    def test_no_conflicting_plugin_json(self):
        # With strict: false, a component-declaring
        # .claude-plugin/plugin.json makes the plugin fail to load.
        self.assertFalse(CLAUDE_PLUGIN_JSON.exists())

    def test_core_contents_derive_from_core_manifest(self):
        skills, _, rules_md, clis = core_expectations()
        core = self.entries["house-rules-core"]
        self.assertEqual(set(core["skills"]), skills)
        self.assertEqual(set(core["commands"]), rules_md)
        # CLIs travel because the entry's source is the marketplace root:
        # every core CLI must exist, executable, at its manifest path.
        import os

        for cli in clis:
            target = REPO_ROOT / cli
            self.assertTrue(
                target.is_file() and os.access(target, os.X_OK),
                f"core CLI not packaged at {cli}",
            )

    def test_full_covers_beads_workflow_surface(self):
        full = self.entries["house-rules-full"]
        for member in FULL_PLUGIN_SKILLS:
            self.assertTrue(
                declared_covers(full["skills"], member, REPO_ROOT),
                f"full plugin does not cover {member}",
            )
        for member in FULL_PLUGIN_RULES:
            self.assertTrue(
                declared_covers(full["commands"], member, REPO_ROOT),
                f"full plugin does not cover {member}",
            )

    def test_every_declared_path_exists(self):
        declared = []
        for entry in self.entries.values():
            declared += entry.get("skills", []) + entry.get("commands", [])
        self.assertEqual(bad_paths(declared, REPO_ROOT), [])


class TestCursorPlugin(unittest.TestCase):
    """.cursor-plugin/plugin.json carries the core tier per the Cursor
    Plugin schema."""

    def setUp(self):
        self.assertTrue(CURSOR_PLUGIN.is_file(), "cursor plugin.json missing")
        self.doc = load_json(CURSOR_PLUGIN)

    def test_required_name_field(self):
        self.assertEqual(self.doc["name"], "house-rules-core")
        self.assertRegex(self.doc["name"], KEBAB)

    def test_core_contents_derive_from_core_manifest(self):
        skills, rules_mdc, _, _ = core_expectations()
        self.assertEqual(set(self.doc["rules"]), rules_mdc)
        self.assertEqual(set(self.doc["skills"]), skills)

    def test_every_declared_path_exists(self):
        declared = self.doc["rules"] + self.doc["skills"]
        self.assertEqual(bad_paths(declared, REPO_ROOT), [])


class TestRootAgentPlugin(unittest.TestCase):
    """Root plugin.json conforms to the Agent Plugins standard."""

    def setUp(self):
        self.assertTrue(ROOT_PLUGIN.is_file(), "root plugin.json missing")
        self.doc = load_json(ROOT_PLUGIN)

    def test_required_schema_and_name(self):
        self.assertEqual(self.doc["$schema"], AGENT_PLUGINS_SCHEMA)
        self.assertTrue(agent_plugins_name_ok(self.doc["name"]))

    def test_schema_is_closed(self):
        unknown = set(self.doc) - AGENT_PLUGINS_FIELDS
        self.assertEqual(unknown, set(), f"unknown top-level fields: {unknown}")

    def test_standard_discovers_skills_from_skills_dir(self):
        # The standard has no component-path fields; skills load from
        # skills/. The layout the manifest relies on must exist.
        skill_dirs = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skill_dirs), 0)


class TestCheckersAreNotVacuous(unittest.TestCase):
    """Fixture negatives: the helpers must flag violations."""

    def test_kebab_rejects_invalid_names(self):
        for bad in ("Bad_Name", "has space", "-lead", "trail-", "UPPER"):
            self.assertNotRegex(bad, KEBAB)
        self.assertRegex("house-rules-core", KEBAB)

    def test_agent_plugins_name_rule(self):
        for bad in ("My-Plugin", "-start", "has--double", "too.many..dots", "a" * 65):
            self.assertFalse(agent_plugins_name_ok(bad), bad)
        for good in ("house-rules", "acme.tools", "lint3r"):
            self.assertTrue(agent_plugins_name_ok(good), good)

    def test_bad_paths_flags_absolute_traversal_and_missing(self):
        flagged = bad_paths(
            ["/etc/passwd", "./../outside", "./does/not/exist"], REPO_ROOT
        )
        self.assertEqual(len(flagged), 3)
        self.assertEqual(bad_paths(["./skills"], REPO_ROOT), [])

    def test_declared_covers_rejects_uncovered_member(self):
        self.assertFalse(
            declared_covers(["./skills/graybeard-review"], "skills/bead-authoring", REPO_ROOT)
        )
        self.assertTrue(
            declared_covers(["./skills/"], "skills/bead-authoring", REPO_ROOT)
        )


if __name__ == "__main__":
    unittest.main()
