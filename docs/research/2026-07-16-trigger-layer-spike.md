# Trigger-layer spike — bd formulas, gate-close molecule, hook feasibility

**Date:** 2026-07-16 · **Type:** research memo (timeboxed spike; findings over polish)
**Environment:** bd 1.1.0 (dev build), Cursor hooks schema v1

The recurring failure mode of process is forgetting to start it. This spike
asked whether a **trigger layer** can make the kit's process skills fire at
lifecycle moments without being asked. Two questions: (1) can a bd formula
pour the standard review molecule when a gate epic closes, and is the feature
mature enough to adopt? (2) can hooks carry the session-close ceremony without
colliding with bd's installed hooks?

## Verdict

**Partially feasible now.** Auto-*scaffolding* the follow-up beads and
*nudging* the agent at the right moment both work today and are cheap.
Auto-*invoking* the skills from a gate-close event is not possible with any
mechanism bd or the agent tools expose — bd fires no event on close, and
skills are not programmatically invocable from bd. Adopt the scaffold + nudge
half; defer true auto-fire.

## Question 1 — bd formulas / the gate-close molecule: **ADOPT**

### What the feature actually is (verified by CLI)

The pipeline is `formula (.formula.json) → bd cook → proto → bd mol pour|wisp
→ real beads`. A formula **only batch-creates a structured bead graph** — it
cannot invoke commands or skills. So a "gate-close molecule" is a checklist +
dependency scaffold, not an executor. `bd mol distill` can reverse-engineer a
formula from an epic you already ran by hand.

Schema gotchas (cost several probes): the top-level name field is `"formula"`
(a string), not `"name"`; steps use `"id"`, not `"key"`; dependencies are
`"depends_on"`. `{{var}}` parameterization with `variables.<v>.required: true`
is enforced at cook/pour time.

### The working formula (validated end-to-end)

```json
{
  "formula": "mol-gate-close",
  "title": "Gate-close sequence for {{gate}}",
  "phase": "liquid",
  "variables": {
    "gate": { "description": "The gate epic id that just closed", "required": true }
  },
  "steps": [
    { "id": "packet",   "title": "Author packet for {{gate}}", "type": "task" },
    { "id": "tier1",    "title": "Tier-1 review the {{gate}} packet", "type": "task", "depends_on": ["packet"] },
    { "id": "deepdive", "title": "Packet-deepdive validation for {{gate}}", "type": "task", "depends_on": ["tier1"] },
    { "id": "deliver",  "title": "Deliver {{gate}} packet", "type": "task", "depends_on": ["deepdive"] }
  ]
}
```

**Live pour, observed:** installed to `.beads/formulas/`, then
`bd mol wisp mol-gate-close --var gate=<test-id>` created 5 issues (root +
four steps) with `{{gate}}` substituted into every title and the dependency
chain intact — the tier1 step showed `DEPENDS ON → packet` / `BLOCKS →
deepdive`, and only the unblocked first step was dispatchable. `bd mol burn`
discarded the test wisp cleanly. Use `wisp` (ephemeral) for tests, `pour`
(persistent, synced) for real gates.

### Maturity assessment

The core create-a-scaffold path (cook, pour, wisp, burn, variables,
dependencies) works and is adoptable now. The *fancier* chemistry — gate-type
steps (`gate: before/condition`), the `bd gate` waiter/patrol system,
`bd mol ready --gated` dispatch — is partially wired in this dev build
(`--gated` flag not recognized; gate-step schema could not be cooked cleanly).
**Adopt the plain dependency-chain formula; defer the native gate-step path.
Upgrade when:** bd's gate-resume dispatch (`bd mol ready --gated` / patrol)
lands in a tagged release.

## Question 2 — hooks for the session-close ceremony: **ADOPT (prototype proven)**

### The hook landscape (verified)

- **bd hooks are git hooks only** — five shims (`pre-commit`, `post-merge`,
  `pre-push`, `post-checkout`, `prepare-commit-msg`) under `.beads/hooks/`
  via `core.hooksPath`, managed by bd (rewritten on upgrade; don't edit in
  place). bd has **no on-close/on-create event hooks**; `bd close` exposes
  only workflow conveniences (`--continue`, `--suggest-next`, `--claim-next`).
- **Agent-tool hooks** (Cursor `hooks.json` / Claude Code hooks) fire on
  *agent* events — `sessionStart`, `sessionEnd`/`stop`, pre/post tool use —
  and can inject `additional_context` JSON. Neither consumer project had an
  agent-hooks file installed, so the surface is free: **no collision** with
  bd's git-hook chain (disjoint event spaces).

### The prototype (ran live)

A ~30-line `session-close-check.sh` designed as a `sessionEnd`/`stop` hook:
reads bd + git state, emits the ceremony as `additional_context` JSON. It
**nudges, never mutates**. Observed output on a real repo state — it correctly
listed the in-progress beads needing a note, the uncommitted files, and the
knowledge-capture prompt, as valid hook JSON:

1. in-progress beads → "add `bd note <id> 'Progress: …'` or close"
2. `git status --porcelain` dirt → "commit if needed"
3. HEAD trailer scan → strip command if an agent attribution trailer is present
4. knowledge-capture prompt (always shown; agent decides)

The same script body works for both Cursor and Claude Code hook shapes (both
consume command-hook stdout JSON); only the `hooks.json` wiring differs per
tool. This carries the ceremony **without duplicating bd's hooks** — bd's
shims handle sync/identity at git events; this handles the agent-session
ceremony at session events.

## The gap that stays a gap: detecting "gate closed"

bd emits nothing on close. "A gate epic just closed" is only observable by
**polling** (`bd query "type=epic AND status=closed AND updated<1d"` or an
epic/milestone with a `gate` label, diffed against a last-seen set). The
smallest viable detector: a `sessionStart` agent hook that runs the query and,
if a newly-closed gate has no poured molecule, injects "pour `mol-gate-close
--var gate=<id>` and run the sequence." A git `post-commit` hook (a new file —
bd doesn't install one, so no collision) can do the same detection outside
agent sessions. Both are **nudge/scaffold**, not auto-fire.

**Defer true auto-fire** (daemon polling bd + driving an agent headlessly via
an SDK): real scope, weekly-cadence payoff, not worth it. **Upgrade when:**
gate cadence rises well above weekly, or bd ships event hooks.

## Recommendations

| Mechanism | Call | Trigger to revisit |
|---|---|---|
| `mol-gate-close` formula (plain dependency chain) | **Adopt** — commit to `.beads/formulas/`, pour manually at gate close | — |
| Session-close ceremony agent hook | **Adopt** — wire the prototype into `hooks.json` per tool | — |
| `sessionStart` gate-close detector (poll + nudge/pour) | **Adopt next** — cheapest automation of the "when" | — |
| bd native gate-steps / patrol dispatch | **Defer** | `bd mol ready --gated` works in a tagged release |
| True auto-fire (daemon + headless agent) | **Defer** | gate cadence ≫ weekly, or bd ships event hooks |

Open design choices for adoption time: the canonical gate signal (dedicated
`gate` label vs milestone-type beads — labels are less brittle than title
matching); nudge-only vs auto-pour (auto-pour needs a dedup guard against
double-firing); whether tier1/tier2 belong inside the molecule or stay
pre-packet (formulas support `branch` steps, but complexity argues for a
fixed linear chain until proven otherwise).
