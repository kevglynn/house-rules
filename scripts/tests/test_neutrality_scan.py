#!/usr/bin/env python3
"""Behavioral tests for project neutrality in the distributed surface.

AGENTS.md declares neutrality as law: rule and skill content must carry no
project names, people, or project/user-specific parameters, because
`house-rules init` lands that content verbatim in other people's repos.

This module currently covers the **private-tool** class only, via a
structural heuristic rather than a name list: a capitalized word followed
by `MCP`. A list can only catch leaks someone already thought of; the
bigram catches the ones nobody has. It is what would have caught the
`Jawnt MCP` directive that shipped in an always-on rule (process-kit-ei0).

Widening this to the full term-class checker (vendor model names, personal
identifiers, a terms profile, and a `scripts/neutrality-scan` CLI) is
process-kit-pi6; see docs/specs/2026-08-08-project-neutrality-enforcement.md.

Run: python3 scripts/tests/test_neutrality_scan.py
"""

import re
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# The surface `house-rules init` distributes or an agent reads as law.
# Deliberately excludes docs/ (dated historical records, where names are
# correct) and scripts/ (installers legitimately hardcode the repo URL).
DISTRIBUTED_ROOTS = (
    "cursor/rules",
    "claude/rules",
    "skills",
    "templates",
    "global-safety-net",
)

TEXT_SUFFIXES = {".md", ".mdc"}

# A capitalized word immediately preceding `MCP`. Lowercase carriers
# ("an MCP plan", "the MCP tools") and the plural ("query MCPs") are
# generic prose about the protocol, not a named product.
PRIVATE_TOOL_BIGRAM = re.compile(r"\b[A-Z][a-z]+ MCP\b")

# Named products that may legitimately appear in generic content, each with
# the reason it is exempt. An entry is a decision, not a mute button.
ALLOWED_TOOL_NAMES = {
    # e.g. "Figma MCP": "first-party integration the kit documents by name"
}


def distributed_text_files(root):
    """Every Markdown file in the distributed surface, sorted."""
    for rel in DISTRIBUTED_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def find_private_tool_names(root):
    """Return (relpath, lineno, matched_term) for each non-exempt hit."""
    hits = []
    for path in distributed_text_files(root):
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in PRIVATE_TOOL_BIGRAM.finditer(line):
                term = match.group(0)
                if term in ALLOWED_TOOL_NAMES:
                    continue
                hits.append((str(path.relative_to(root)), lineno, term))
    return hits


class TestDistributedSurfaceIsNeutral(unittest.TestCase):
    """The shipped content names no private tool."""

    def test_no_private_tool_names_in_distributed_content(self):
        hits = find_private_tool_names(REPO_ROOT)
        self.assertEqual(
            hits,
            [],
            "distributed content names a private tool; either rewrite it in "
            "capability-level terms and move the specifics to the overlay, or "
            f"add a reasoned ALLOWED_TOOL_NAMES entry: {hits}",
        )


class TestCheckerIsNotVacuous(unittest.TestCase):
    """Fixture negatives: the helper must flag violations, not wave them by."""

    def _write(self, root, relpath, text):
        target = root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_named_private_tool_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "cursor/rules/dirty.mdc",
                "When Jawnt MCP is available, use it for cross-project reads.\n",
            )
            hits = find_private_tool_names(root)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0][2], "Jawnt MCP")

    def test_generic_protocol_prose_is_not_flagged(self):
        # The forms that appear legitimately throughout the kit. A
        # boundary-less or case-insensitive pattern would fire on all of
        # these and the checker would be turned off within a day.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "skills/some-skill/SKILL.md",
                "Voices may query MCPs for evidence.\n"
                "This may be read by an MCP plan tool.\n"
                "Prefer one MCP call over a per-directory loop.\n"
                "Note that the MCP tools are read-only.\n"
                "Anything a CLI already covers where a shell exists.\n",
            )
            self.assertEqual(find_private_tool_names(root), [])

    def test_allowlisted_tool_name_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root, "templates/t.md", "Call the Figma MCP to read the file.\n"
            )
            self.assertEqual(len(find_private_tool_names(root)), 1)
            ALLOWED_TOOL_NAMES["Figma MCP"] = "test fixture"
            try:
                self.assertEqual(find_private_tool_names(root), [])
            finally:
                del ALLOWED_TOOL_NAMES["Figma MCP"]

    def test_claude_projection_is_in_scope(self):
        # A leak fixed only in the canonical .mdc but left in the generated
        # Claude projection still ships to Claude adopters.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "cursor/rules/clean.mdc", "Capability-level prose.\n")
            self._write(root, "claude/rules/stale.md", "Use Jawnt MCP for reads.\n")
            hits = find_private_tool_names(root)
            self.assertEqual(len(hits), 1)
            self.assertIn("claude/rules/stale.md", hits[0][0])


if __name__ == "__main__":
    unittest.main()
