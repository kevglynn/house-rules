# Multi-Agent Review

Structural code changes benefit from review by multiple independent perspectives. A single reviewer — human or AI — has blind spots. This rule defines a two-tier review protocol.

**Procedure lives in the skills.** Invoke `skills/tier1-review` for Tier 1 and `skills/tier2-handoff` for Tier 2. This rule states the obligations; the skills are how you meet them.

## When to trigger

Multi-agent review is required when:
- A component is decomposed (split into multiple production files)
- A shared component is created or significantly changed
- A structural refactor touches 3+ production files (excluding tests, docs, generated files, mechanical renames)
- The change affects accessibility, state management, or CSS architecture

NOT required for: bug fixes with clear, narrow scope; config/chore/docs beads; token substitutions or mechanical migrations with no structural change; test-only or docs-only changes.

## Lifecycle sequencing

Within the bead completion workflow (`bead-completion.md`): implement → **self-review against ACs** → **Tier 1** → fix findings, commit → **Tier 2** → fix findings, commit → `bd close` with evidence. Tier 1 supplements the self-review — it does not replace it. Review fixes land as a separate commit, never amended into the original.

## Tier 1: Same-model multi-lens review (autonomous)

The agent dispatches the full lens roster the skill defines — the rule states no count; the skill owns the roster and templates. Each pass runs with independent context; no pass sees another's findings until triage. Every finding is triaged and dispositioned per the skill; Critical and Important findings are fixed before close.

## Tier 2: Cross-model review (human-assisted)

Different models have different failure modes; same-model review misses model-specific blind spots.

- **Strongly recommended** for all structural changes. If deferred under time pressure, create a bead tracking the cross-model review before merge.
- **Required** (not deferrable) when the change touches: shared primitives (design system components, shared hooks); app shell or navigation infrastructure; authentication, authorization, or security boundaries; state management architecture.
- Prerequisite: the work is committed and pushed before handoff (reproducible snapshot, cross-worktree visibility).
- The agent assembles the review prompt and triages the returned findings per `skills/tier2-handoff/SKILL.md`; the human pastes the prompt to the external models the skill names and collects responses.

## When reviewers disagree

When two reviewers (lenses or models) flag opposite findings, treat the **more conservative** finding as the starting position and document the disagreement. Conflicting findings never cancel each other out.

## Evidence in bead close

The `bd close --reason` must note: whether Tier 1 ran and what finding categories were addressed; whether Tier 2 was completed, deferred (with tracking bead ID), or not required. This is in addition to the AC-mapped evidence required by `bead-completion.md`.

## Knowledge capture and tracking

Pattern-level insights from findings are captured per `bead-completion.md`'s `bd remember` protocol. All deferred findings — from both tiers — become beads with proper descriptions and acceptance criteria per `beads-quality.md`.
