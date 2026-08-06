#!/usr/bin/env python3
"""Behavioral tests for the packet skill's render.py --verify checks.

Every test drives render.py as a subprocess against a synthetic packet and
asserts observable behavior: exit code and the WARN/ERROR lines on stderr.
No internals.

Run: python3 skills/packet/tests/test_render_verify.py
"""

import subprocess
import tempfile
import unittest
from pathlib import Path

RENDER = Path(__file__).resolve().parent.parent / "render.py"


def verify(md_text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(md_text)
        path = f.name
    try:
        return subprocess.run(
            ["python3", str(RENDER), "--in", path, "--verify"],
            capture_output=True,
            text=True,
        )
    finally:
        Path(path).unlink()


def packet(grid_rows, strip_placement):
    """A minimal blueprint-conformant packet.

    strip_placement: "after-grid" (the shipped template order),
    "before-grid" (the placement the live packet used), or "absent".
    """
    rows = "\n".join(
        f"| checklist item {i} | **SHIPPED** — evidence prose for row {i}, "
        f"padded with linked detail to make grid rows realistically wide |"
        for i in range(grid_rows)
    )
    grid = f"| Your checklist item | Status |\n|---|---|\n{rows}\n"
    strip = "> **1 deliberate divergence from your plan text:** example.\n"
    glance = {
        "after-grid": grid + "\n" + strip,
        "before-grid": strip + "\n" + grid,
        "absent": grid,
    }[strip_placement]
    return (
        "# Gate N — packet\n\n"
        "## Status at a glance\n\n"
        f"{glance}\n"
        "## Receipts\n\n"
        "**Proof one** — [link](#status-at-a-glance)\n\n"
        "**Proof two** — [link](#status-at-a-glance)\n\n"
        "**Proof three** — [link](#status-at-a-glance)\n\n"
        "## FAQ\n\n"
        "**One question?**\n\nOne answer.\n"
    )


STRIP_WARN = "no divergence strip"


class RenderVerifyStripTest(unittest.TestCase):
    def test_template_order_with_long_grid_does_not_warn(self):
        # The bug: a fixed 1800-char scan window pushed a
        # template-conformant strip out of range once grid rows carried
        # rich evidence. 40 realistic rows ≈ 5KB of table.
        result = verify(packet(grid_rows=40, strip_placement="after-grid"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(STRIP_WARN, result.stderr)

    def test_template_order_with_short_grid_does_not_warn(self):
        result = verify(packet(grid_rows=2, strip_placement="after-grid"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(STRIP_WARN, result.stderr)

    def test_strip_above_the_grid_does_not_warn(self):
        # The placement the live packet used as a workaround for this
        # bug: the strip sits between the heading and the grid. Both
        # orders are in the grid's eye-span; the check must accept both.
        result = verify(packet(grid_rows=40, strip_placement="before-grid"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(STRIP_WARN, result.stderr)

    def test_genuinely_missing_strip_still_warns(self):
        result = verify(packet(grid_rows=40, strip_placement="absent"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(STRIP_WARN, result.stderr)

    def test_missing_strip_in_short_packet_still_warns(self):
        result = verify(packet(grid_rows=2, strip_placement="absent"))
        self.assertIn(STRIP_WARN, result.stderr)


if __name__ == "__main__":
    unittest.main()
