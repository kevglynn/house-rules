#!/usr/bin/env python3
"""Behavioral tests for the plugin manifests on three surfaces
(process-kit-wsi), plus Claude core packaging contracts (process-kit-i8r):
always-on downgrade documentation, bin/ PATH wrappers, and a consumer-
workspace fixture proving bare checker names resolve without scripts/.

Typed validation (process-kit-5lj) pins official/minimal schemas under
scripts/tests/fixtures/schemas/ and checks them with a stdlib subset
validator — not a hand-maintained top-level field-name whitelist alone.
Claude marketplace also asserts unique plugins[].name (upstream schema
does not); negative fixtures prove wrong types and duplicates fail.

Surfaces and the schema each was verified against (2026-08-07):
  1. .claude-plugin/marketplace.json — Claude Code plugin marketplace.
     Pinned: fixtures/schemas/claude-code-marketplace.min.schema.json
     (subset of https://json.schemastore.org/claude-code-marketplace.json).
     Docs: https://code.claude.com/docs/en/plugin-marketplaces.
  2. .cursor-plugin/plugin.json — Cursor Plugin manifest.
     Pinned: fixtures/schemas/cursor-plugin.min.schema.json
     (typed contract from https://cursor.com/docs/reference/plugins).
  3. plugin.json (repo root) — Agent Plugins open standard.
     Pinned: fixtures/schemas/agent-plugins-plugin.schema.json
     (https://agent-plugins.org/schemas/1.0.0/plugin.schema.json).

Core-plugin contents are DERIVED from profiles/core-manifest.list via
test_core_manifest.parse_manifest — the single source of truth for core
membership — never restated here. Helpers are factored so fixture tests
can prove they flag violations (a checker that passes regardless of
correctness is zero signal).

Run: python3 scripts/tests/test_plugin_manifests.py
"""

import copy
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_core_manifest import MANIFEST as CORE_MANIFEST
from test_core_manifest import parse_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = Path(__file__).resolve().parent / "fixtures" / "schemas"
CLAUDE_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CLAUDE_PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
CURSOR_PLUGIN = REPO_ROOT / ".cursor-plugin" / "plugin.json"
ROOT_PLUGIN = REPO_ROOT / "plugin.json"
BIN_DIR = REPO_ROOT / "bin"

AGENT_PLUGINS_SCHEMA_PATH = SCHEMA_DIR / "agent-plugins-plugin.schema.json"
CLAUDE_MARKETPLACE_SCHEMA_PATH = SCHEMA_DIR / "claude-code-marketplace.min.schema.json"
CURSOR_PLUGIN_SCHEMA_PATH = SCHEMA_DIR / "cursor-plugin.min.schema.json"

# Pinned always-on contract (process-kit-i8r): Claude packages core as
# discoverable commands/skills — explicit downgrade from Cursor alwaysApply.
ALWAYS_ON_DOWNGRADE_RE = re.compile(
    r"discoverable commands/skills.*not always-on policy",
    re.IGNORECASE | re.DOTALL,
)
CORE_CHECKERS = ("defer-lint", "banned-token-scan")

# Claude Code and Cursor both require kebab-case plugin/marketplace names.
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
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
    """Name rule from the Agent Plugins standard (schema pattern + length)."""
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


# ---------------------------------------------------------------------------
# Stdlib JSON Schema subset validator (pinned schemas; no jsonschema dep)
# ---------------------------------------------------------------------------

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
    "null": type(None),
}


class SchemaValidationError(ValueError):
    """Raised when an instance fails a pinned schema check."""


def validate_schema(instance, schema, path="$"):
    """Validate `instance` against a Draft-07 / 2020-12 *subset*.

    Supported keywords: type, required, properties, additionalProperties
    (bool or schema), const, pattern, minLength, maxLength, items (schema),
    anyOf. Enough to exercise the pinned Agent Plugins / Claude / Cursor
    schemas without a pip dependency.
    """
    if "const" in schema and instance != schema["const"]:
        raise SchemaValidationError(
            f"{path}: expected const {schema['const']!r}, got {instance!r}"
        )

    if "type" in schema:
        expected = schema["type"]
        types = expected if isinstance(expected, list) else [expected]

        def _matches(t):
            py = _TYPE_MAP[t]
            if t in ("integer", "number") and isinstance(instance, bool):
                return False  # bool subclasses int
            return isinstance(instance, py)

        if not any(_matches(t) for t in types):
            raise SchemaValidationError(
                f"{path}: expected type {expected!r}, got {type(instance).__name__}"
            )

    if "anyOf" in schema:
        errors = []
        for i, sub in enumerate(schema["anyOf"]):
            try:
                validate_schema(instance, sub, f"{path}/anyOf[{i}]")
                break
            except SchemaValidationError as exc:
                errors.append(str(exc))
        else:
            raise SchemaValidationError(
                f"{path}: matched no anyOf branch ({len(errors)} errors)"
            )

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            raise SchemaValidationError(
                f"{path}: string shorter than minLength {schema['minLength']}"
            )
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            raise SchemaValidationError(
                f"{path}: string longer than maxLength {schema['maxLength']}"
            )
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            raise SchemaValidationError(
                f"{path}: string does not match pattern {schema['pattern']!r}"
            )

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                raise SchemaValidationError(f"{path}: missing required property {key!r}")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                validate_schema(value, props[key], f"{path}.{key}")
            elif "additionalProperties" in schema:
                add = schema["additionalProperties"]
                if add is False:
                    raise SchemaValidationError(
                        f"{path}: additional property {key!r} not allowed"
                    )
                if isinstance(add, dict):
                    validate_schema(value, add, f"{path}.{key}")

    if isinstance(instance, list) and "items" in schema:
        item_schema = schema["items"]
        if isinstance(item_schema, dict):
            for i, item in enumerate(instance):
                validate_schema(item, item_schema, f"{path}[{i}]")


def assert_unique_plugin_names(plugins):
    """Raise SchemaValidationError if plugins[].name duplicates exist.

    Dict-by-name indexing masks duplicates; walk the list explicitly.
    Upstream SchemaStore marketplace schema does not enforce uniqueness.
    """
    if not isinstance(plugins, list):
        raise SchemaValidationError("plugins: expected array")
    seen = {}
    for i, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            raise SchemaValidationError(f"plugins[{i}]: expected object")
        name = entry.get("name")
        if not isinstance(name, str):
            raise SchemaValidationError(f"plugins[{i}].name: expected string")
        if name in seen:
            raise SchemaValidationError(
                f"duplicate plugins[].name {name!r} at indices "
                f"{seen[name]} and {i}"
            )
        seen[name] = i


class TestClaudeMarketplace(unittest.TestCase):
    """.claude-plugin/marketplace.json satisfies the vendor schema and
    the core/full tier contract."""

    def setUp(self):
        self.assertTrue(CLAUDE_MARKETPLACE.is_file(), "marketplace.json missing")
        self.doc = load_json(CLAUDE_MARKETPLACE)
        self.schema = load_json(CLAUDE_MARKETPLACE_SCHEMA_PATH)
        # Uniqueness before dict-by-name (which would mask duplicates).
        assert_unique_plugin_names(self.doc["plugins"])
        self.entries = {p["name"]: p for p in self.doc["plugins"]}

    def test_matches_pinned_marketplace_schema(self):
        validate_schema(self.doc, self.schema)
        self.assertIn("json.schemastore.org/claude-code-marketplace", self.schema["$comment"])

    def test_plugin_names_are_unique(self):
        names = [p["name"] for p in self.doc["plugins"]]
        self.assertEqual(len(names), len(set(names)))

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

    def test_core_always_on_contract_is_explicit_downgrade(self):
        # Loader-level pin: marketplace description states the Claude
        # always-on downgrade, and delivery is commands[] (not hooks /
        # alwaysApply). A description that still claims always-on or
        # omits the downgrade fails this fixture.
        core = self.entries["house-rules-core"]
        self.assertRegex(core["description"], ALWAYS_ON_DOWNGRADE_RE)
        self.assertIn("commands", core)
        self.assertGreater(len(core["commands"]), 0)
        self.assertNotIn("hooks", core)
        # Claude projections strip alwaysApply; none may reintroduce it.
        for cmd in core["commands"]:
            text = (REPO_ROOT / normalize(cmd)).read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r"(?m)^alwaysApply:\s*true\s*$",
                f"{cmd} must not claim alwaysApply",
            )
        upgrade = (REPO_ROOT / "claude/rules/core-upgrade-offer.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("always-on downgrade", upgrade.lower())
        self.assertIn("discoverable commands", upgrade.lower())

    def test_core_bin_wrappers_exist_for_checkers(self):
        # Claude puts plugin bin/ on the Bash PATH; wrappers must exist
        # for every core CLI basename while scripts/ remains for local init.
        _, _, _, clis = core_expectations()
        for cli in clis:
            name = Path(cli).name
            wrapper = BIN_DIR / name
            self.assertTrue(
                wrapper.is_file() and os.access(wrapper, os.X_OK),
                f"missing executable bin/{name} for core CLI {cli}",
            )
            self.assertTrue(
                (REPO_ROOT / cli).is_file(),
                f"local-init path {cli} must still exist",
            )


class TestClaudeConsumerWorkspace(unittest.TestCase):
    """Plugin-style install: bin/ on PATH, no scripts/ in the consumer cwd."""

    def test_core_checkers_resolve_via_bin_on_path(self):
        self.assertTrue(BIN_DIR.is_dir(), "bin/ missing — plugin PATH surface")
        # Strip kit scripts/ from PATH so a bare name cannot accidentally
        # resolve via a developer PATH that already includes scripts/.
        path_parts = [
            p
            for p in os.environ.get("PATH", "").split(os.pathsep)
            if p and Path(p).resolve() != (REPO_ROOT / "scripts").resolve()
        ]
        env = {**os.environ, "PATH": os.pathsep.join([str(BIN_DIR), *path_parts])}
        with tempfile.TemporaryDirectory() as consumer:
            consumer_path = Path(consumer)
            # Relative scripts/ citation fails in a consumer with no kit tree.
            try:
                missing = subprocess.run(
                    ["scripts/defer-lint", "--help"],
                    cwd=consumer_path,
                    env=env,
                    capture_output=True,
                    text=True,
                )
            except FileNotFoundError:
                missing = None  # absolute failure to resolve — expected
            if missing is not None:
                self.assertNotEqual(
                    missing.returncode,
                    0,
                    "scripts/defer-lint must not resolve in a bare consumer cwd",
                )
            for name in CORE_CHECKERS:
                result = subprocess.run(
                    [name, "--help"],
                    cwd=consumer_path,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{name} --help failed from consumer cwd: {result.stderr}",
                )
                self.assertIn(name, result.stdout)

    def test_claude_projections_teach_bare_checker_names(self):
        # Claude projections prefer bare bin/ names; scripts/ is fallback.
        cases = {
            "claude/rules/defer-convention.md": "defer-lint",
            "claude/rules/agent-identity.md": "banned-token-scan",
        }
        for rel, name in cases.items():
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertRegex(
                text,
                rf"\*\*Checker:\*\* `{re.escape(name)}`",
                f"{rel} must lead with bare `{name}`",
            )
            self.assertIn(
                f"scripts/{name}",
                text,
                f"{rel} must keep scripts/ fallback for local installs",
            )


class TestCursorPlugin(unittest.TestCase):
    """.cursor-plugin/plugin.json carries the core tier per the Cursor
    Plugin schema."""

    def setUp(self):
        self.assertTrue(CURSOR_PLUGIN.is_file(), "cursor plugin.json missing")
        self.doc = load_json(CURSOR_PLUGIN)
        self.schema = load_json(CURSOR_PLUGIN_SCHEMA_PATH)

    def test_matches_pinned_cursor_schema(self):
        validate_schema(self.doc, self.schema)
        self.assertIn("cursor.com/docs/reference/plugins", self.schema["$comment"])

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
        self.schema = load_json(AGENT_PLUGINS_SCHEMA_PATH)

    def test_matches_pinned_agent_plugins_schema(self):
        # Full official schema pinned under fixtures/schemas/ — closed
        # top-level set via additionalProperties: false, not a local whitelist.
        self.assertEqual(self.schema["$id"], AGENT_PLUGINS_SCHEMA)
        validate_schema(self.doc, self.schema)

    def test_required_schema_and_name(self):
        self.assertEqual(self.doc["$schema"], AGENT_PLUGINS_SCHEMA)
        self.assertTrue(agent_plugins_name_ok(self.doc["name"]))

    def test_standard_discovers_skills_from_skills_dir(self):
        # The standard has no component-path fields; skills load from
        # skills/. The layout the manifest relies on must exist.
        skill_dirs = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skill_dirs), 0)


class TestSchemaNegatives(unittest.TestCase):
    """Temp-mutated JSON fixtures: wrong types and duplicate names fail."""

    @classmethod
    def setUpClass(cls):
        cls.marketplace = load_json(CLAUDE_MARKETPLACE)
        cls.marketplace_schema = load_json(CLAUDE_MARKETPLACE_SCHEMA_PATH)
        cls.agent = load_json(ROOT_PLUGIN)
        cls.agent_schema = load_json(AGENT_PLUGINS_SCHEMA_PATH)
        cls.cursor = load_json(CURSOR_PLUGIN)
        cls.cursor_schema = load_json(CURSOR_PLUGIN_SCHEMA_PATH)

    def test_marketplace_rejects_skills_as_string(self):
        doc = copy.deepcopy(self.marketplace)
        doc["plugins"][0]["skills"] = "./skills/graybeard-review"  # must be array
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.marketplace_schema)
        self.assertIn("skills", str(ctx.exception))

    def test_marketplace_rejects_strict_as_string(self):
        doc = copy.deepcopy(self.marketplace)
        doc["plugins"][0]["strict"] = "false"
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.marketplace_schema)
        self.assertIn("strict", str(ctx.exception))

    def test_marketplace_rejects_owner_name_as_number(self):
        doc = copy.deepcopy(self.marketplace)
        doc["owner"]["name"] = 42
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.marketplace_schema)
        self.assertIn("owner.name", str(ctx.exception))

    def test_marketplace_rejects_duplicate_plugin_names(self):
        doc = copy.deepcopy(self.marketplace)
        dup = copy.deepcopy(doc["plugins"][0])
        doc["plugins"].append(dup)  # same name, second entry
        with self.assertRaises(SchemaValidationError) as ctx:
            assert_unique_plugin_names(doc["plugins"])
        self.assertIn("duplicate", str(ctx.exception).lower())
        self.assertIn(dup["name"], str(ctx.exception))
        # Dict-by-name would silently collapse to one entry — prove the trap.
        collapsed = {p["name"]: p for p in doc["plugins"]}
        self.assertEqual(len(collapsed), len(doc["plugins"]) - 1)

    def test_agent_plugins_rejects_keywords_as_string(self):
        doc = copy.deepcopy(self.agent)
        doc["keywords"] = "rules,skills"
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.agent_schema)
        self.assertIn("keywords", str(ctx.exception))

    def test_agent_plugins_rejects_unknown_top_level_field(self):
        doc = copy.deepcopy(self.agent)
        doc["skills"] = ["./skills/"]  # closed schema — not a top-level field
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.agent_schema)
        self.assertIn("additional property", str(ctx.exception).lower())

    def test_agent_plugins_rejects_author_as_string(self):
        doc = copy.deepcopy(self.agent)
        doc["author"] = "Kevin Glynn"
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.agent_schema)
        self.assertIn("author", str(ctx.exception))

    def test_cursor_rejects_rules_as_object(self):
        doc = copy.deepcopy(self.cursor)
        doc["rules"] = {"path": "./cursor/rules/"}
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_schema(doc, self.cursor_schema)
        self.assertIn("rules", str(ctx.exception))


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

    def test_pinned_schemas_exist_and_cite_upstream(self):
        for path in (
            AGENT_PLUGINS_SCHEMA_PATH,
            CLAUDE_MARKETPLACE_SCHEMA_PATH,
            CURSOR_PLUGIN_SCHEMA_PATH,
        ):
            self.assertTrue(path.is_file(), f"missing pinned schema {path}")
        ap = load_json(AGENT_PLUGINS_SCHEMA_PATH)
        self.assertEqual(ap["$id"], AGENT_PLUGINS_SCHEMA)
        self.assertIs(ap["additionalProperties"], False)


if __name__ == "__main__":
    unittest.main()
