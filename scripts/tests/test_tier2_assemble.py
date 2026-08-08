#!/usr/bin/env python3
"""Behavioral tests for skills/tier2-handoff/assemble.py.

The property under test is project- and vendor-neutrality. The skill ships
to third-party repos, and the assembler is the one place in the kit that
asserted a concrete reviewer lineup: with no spec `models` field it emitted
"Paste everything below this line into each external model (Grok, Gemini,
GPT)." Vendor names age faster than anything else in the kit, and a
distributed skill telling someone to use three specific vendors is
project-specific configuration masquerading as generic guidance.

So: with no lineup supplied, the prompt describes reviewer archetypes (the
pattern skills/council already uses); with one supplied, it renders exactly
what the caller asked for.

Also pins the determinism guarantee the skill's whole design rests on —
identical spec in, byte-identical prompt out — since a checker that only
looked at wording would miss a regression that made the output depend on
dict ordering or the clock.

Run: python3 scripts/tests/test_tier2_assemble.py
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSEMBLE = REPO_ROOT / "skills" / "tier2-handoff" / "assemble.py"
SKILL_MD = REPO_ROOT / "skills" / "tier2-handoff" / "SKILL.md"

# Model and vendor names that must not appear in a prompt the caller did not
# ask to be vendor-specific. Deliberately broader than the three that were
# hardcoded: the fix is "name no vendor", not "name three fewer vendors".
VENDOR_NAMES = [
    "Grok", "Gemini", "GPT", "Claude", "Codex", "Copilot",
    "OpenAI", "Anthropic", "Google", "xAI", "Meta",
    "Llama", "Mistral", "DeepSeek", "Qwen", "Kimi", "o1", "o3",
]

MINIMAL_SPEC = {
    "subject": "token bucket",
    "bead_id": "test-000",
    "language": "Rust",
    "artifact_noun": "rate-limiter module",
    "focus": "Any path that returns a token when the bucket is empty.",
    "context": "A token-bucket rate limiter behind a trait.",
    "files": ["subject.rs"],
}


def run_assemble(spec, extra_args=()):
    """Run the assembler on `spec` in a throwaway root, return stdout."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "subject.rs").write_text("fn take() -> bool { true }\n", encoding="utf-8")
        spec_path = root / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(ASSEMBLE), "--spec", str(spec_path),
             "--root", str(root), "--out", "-", *extra_args],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"assemble.py exited {proc.returncode}: {proc.stderr}"
            )
        return proc.stdout


def vendors_in(text):
    """Vendor names present in `text`, matched case-sensitively on word-ish
    boundaries so 'GPT' hits but 'gpt' inside a path does not, and 'Meta'
    hits but 'metadata' does not."""
    import re
    found = []
    for name in VENDOR_NAMES:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", text):
            found.append(name)
    return found


class TestNoLineupIsVendorNeutral(unittest.TestCase):
    """AC1: no overlay, no spec models → no vendor named, archetypes instead."""

    def setUp(self):
        self.doc = run_assemble(MINIMAL_SPEC)

    def test_names_no_vendor(self):
        found = vendors_in(self.doc)
        self.assertEqual(
            found, [],
            f"prompt names vendor(s) {found} though the spec supplied no models",
        )

    def test_describes_archetypes_instead(self):
        # The council skill's wording: capability and family, not brand.
        self.assertIn("different family", self.doc)
        self.assertRegex(self.doc, r"strongest[^.]*reasoning model")

    def test_forbids_inventing_a_model_name(self):
        # Without this, an agent resolving an archetype will happily emit a
        # slug that does not exist in its environment.
        self.assertIn("invent", self.doc.lower())

    def test_paste_instruction_survives(self):
        # De-vendoring must not cost the operator the actual instruction.
        self.assertIn("Paste everything below this line", self.doc)
        self.assertIn("hand them back for triage", self.doc)

    def test_exploit_prompt_is_also_vendor_neutral(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "exploit.md"
            run_assemble(MINIMAL_SPEC, ("--exploit-out", str(out)))
            found = vendors_in(out.read_text(encoding="utf-8"))
        self.assertEqual(found, [], f"exploit prompt names vendor(s) {found}")


class TestExplicitLineupIsHonored(unittest.TestCase):
    """AC2: a spec models field still renders an explicit named lineup."""

    def test_named_models_appear_verbatim(self):
        spec = dict(MINIMAL_SPEC, models=["Grok", "Gemini"])
        doc = run_assemble(spec)
        self.assertIn("Grok, Gemini", doc)

    def test_named_models_replace_the_archetype_wording(self):
        spec = dict(MINIMAL_SPEC, models=["Codex"])
        doc = run_assemble(spec)
        self.assertIn("Codex", doc)
        self.assertNotIn("different family", doc)

    def test_single_model_reads_naturally(self):
        doc = run_assemble(dict(MINIMAL_SPEC, models=["Codex"]))
        self.assertNotIn("(, )", doc)
        self.assertNotIn("Codex, ", doc)


class TestSourceAndDocsCarryNoLineup(unittest.TestCase):
    """The default must not survive anywhere as dormant configuration."""

    def test_assembler_source_hardcodes_no_vendor(self):
        src = ASSEMBLE.read_text(encoding="utf-8")
        # The docstring documents the `models` field; it must not document a
        # vendor lineup as its default.
        found = vendors_in(src)
        self.assertEqual(
            found, [],
            f"assemble.py source still carries vendor name(s) {found}",
        )

    def test_skill_overlay_table_default_is_vendor_neutral(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("|") and "`models`" in line:
                found = vendors_in(line)
                self.assertEqual(
                    found, [],
                    f"SKILL.md overlay default names vendor(s) {found}: {line}",
                )
                break
        else:
            self.fail("no `models` row found in the SKILL.md overlay table")


class TestDeterminism(unittest.TestCase):
    """The assembler's reason for existing: same spec in, same bytes out."""

    def test_repeated_runs_are_byte_identical(self):
        a = run_assemble(MINIMAL_SPEC)
        b = run_assemble(MINIMAL_SPEC)
        self.assertEqual(a, b)

    def test_key_order_does_not_change_output(self):
        reordered = dict(reversed(list(MINIMAL_SPEC.items())))
        self.assertEqual(run_assemble(MINIMAL_SPEC), run_assemble(reordered))


class TestVendorMatcherItself(unittest.TestCase):
    """A detector that never fires would make every test above vacuous."""

    def test_matcher_finds_a_planted_name(self):
        self.assertEqual(vendors_in("send it to GPT and Grok"), ["Grok", "GPT"])

    def test_matcher_ignores_substrings_and_case(self):
        self.assertEqual(vendors_in("metadata about a gpt-ish claude-like thing"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
