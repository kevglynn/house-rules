# Multi-Agent Review

Structural code changes benefit from review by multiple independent perspectives. This rule defines when to trigger review; the skills define how to run it.

## When to trigger

Multi-agent review is required when:
- A component is decomposed (split into multiple production files)
- A shared component is created or significantly changed
- A structural refactor touches 3+ production files (excluding tests, docs, generated files, mechanical renames)
- The change affects accessibility, state management, or CSS architecture

NOT required for: bug fixes with clear, narrow scope; config/chore/docs beads; token substitutions or mechanical migrations with no structural change; test-only or docs-only changes.

Tier 2 (cross-model) is additionally **required** — not deferrable — when the change touches shared primitives (design-system components, shared hooks), app shell or navigation, auth/authorization/security boundaries, or state-management architecture. For other structural changes it is strongly recommended; if deferred under time pressure, create a bead tracking the cross-model review before merge.

## Lifecycle position

Within bead completion: implement → self-review against ACs → **Tier 1** (invoke `skills/tier1-review`) → fix and commit → **Tier 2** (invoke `skills/tier2-handoff`) → fix and commit → `bd close`. Review fixes land as separate commits.

Whatever the disposition, the bead's close reason records review status: Tier 1/Tier 2 run (with findings summary), deferred (with the tracking bead ID), or not required (with the reason). "Review not required" is a recorded judgment, not a silent default.

## When reviewers disagree

Treat the more conservative finding as the starting position. Conflicting findings never cancel each other out.
