# Refinement Proposal: Kit-wide mechanism-placement audit

**Date:** 2026-07-19
**Initiator:** agent (refinement-initiative session) on behalf of kevglynn — **Reason initiated:** capability-matured + periodic-hygiene triggers (mechanism-side): the operating-surface catalog and the pragmatic-tdd pilot produced a placement doctrine the rest of the kit has never been audited against. Bead: process-kit-l1h.
**Mode:** retrospective · **Refinement object(s):** mechanisms
**Scope:** every operating surface the kit ships or prescribes — all always-on rules (`cursor/rules/*.mdc`), all registered skills (`skills/`), hooks (`.claude/hooks/`), distribution surfaces (init/sync/doctor scripts, safety net, templates), enforcement gaps (permissions, CI), memory/knowledge infra, tracker-usage prescriptions, and docs-governance surfaces. **Out of scope:** the *content* of any discipline (test policy substance, bead-quality standards substance) — this audits representation and placement only, per the pilot's precedent. No reshaping is executed under this proposal's bead; accepted findings become new beads.
**Execution during refinement:** continues — no live epic is paused; this is the first real run of the refinement capability itself.
**Status:** Draft

## 1. Executive summary

[Filled in Phase 8, after findings.]

## 2. Governing intent

Authoritative sources for what the kit's mechanisms are *for*, in precedence
order:

1. **PLAN.md** — the kit is a portable, project-neutral AI-native development
   kit (rules + skills + safety nets + distribution scripts), incubating
   toward open-source publication behind a readiness checklist (IP clear,
   skills stable, second-consumer proof, neutrality audit). Design rule:
   generic core / project overlay; skills never name projects or people.
2. **docs/specs/2026-07-19-refinement-initiative.md** — the governing intent
   frame for this cycle: *evolve, don't remediate*; climb toward the
   abstraction layer where agentic development works best; publish and learn
   fast. Mechanism placement is a first-class concern (CLI-first enforcement
   stack, profile-driven projection pattern).
3. **AGENTS.md / CLAUDE.md** — source-repo conventions: `cursor/rules/*.mdc`
   is canon, `claude/rules/` is a generated projection, skills follow
   `skills/README.md`, marker strings keep the legacy prefix until renaming
   lands as one migration.
4. **docs/refinement/concepts.md + docs/research/2026-07-19-operating-surface-catalog.md**
   — the placement doctrine itself: 10 surface classes, 6 axes, placement
   principles (law on normative surfaces, procedure on-demand, checkable
   facts deterministic, trust boundary outside the harness).
5. **The rule and skill texts themselves** — each artifact's self-declared
   purpose, used where higher sources are silent.

No conflicts detected between sources at this level; conflicts surfaced at
the per-artifact level are recorded as findings.

## 3. Evidence reviewed

- Full text of every `cursor/rules/*.mdc` (per-rule audit lane)
- Full text of every `skills/*/SKILL.md` + references + `skills/README.md`
  registry (skills audit lane)
- `.claude/hooks/*`, `scripts/playbook-init.sh`, `scripts/sync-rules.sh`,
  `scripts/playbook-doctor.sh`, `global-safety-net/`, `templates/`
  (event/distribution lane)
- Tracker prescriptions vs. observed practice in this repo's beads DB
  (`bd count`, `bd lint`, `bd stale`, close-reason sampling), templates and
  docs-governance surfaces, data-shaped-conventions inventory (tracker lane)
- The pilot proposal (`2026-07-19-pragmatic-tdd-topology.md`) as the worked
  precedent, and the trigger-layer spike
  (`docs/research/2026-07-16-trigger-layer-spike.md`) for hook capabilities
- **Wanted but unavailable:** cross-session transcript adherence data for
  most rules (the scorecard has a baseline only for pragmatic-tdd items);
  token-cost measurements per rule (estimated from size, not measured);
  target-repo usage data beyond the single private consumer. Confidence on
  context-cost and adherence findings is capped at *medium* accordingly.

## 4. Assumption ledger

| Assumption (kit design rests on) | Status | Evidence |
|---|---|---|
| A1 — Always-on rules are read and followed by agents in practice | untested (partially observable) | Scorecard exists but has recorded data only for the pragmatic-tdd baseline; no kit-wide adherence measurements |
| A2 — Law/procedure split (thin rule + skill) preserves adherence while cutting context cost | confirmed for pragmatic-tdd only | Pilot proposal + topology split executed this cycle; scorecard experiment open; untested for the other rules |
| A3 — `sync-rules.sh` keeps the claude projection drift-free | confirmed | Doctor drift check exercises it; ledger drift check added this cycle follows the same pattern |
| A4 — Skills get invoked when their trigger condition occurs | weakened | Mechanism-audit doctrine: voluntary invocation enforces nothing; refinement skill needed an explicit rule pointer added post-review; other skills' invocation paths unverified (skills lane auditing) |
| A5 — Target repos supply the CI trust boundary the kit's gates need | confirmed | F3 reversal in the pilot (kit-CI vs target-CI conflation); templates/tdd-ledger-verify.yml now ships |
| A6 — init distributes everything doctor re-checks (no unmonitored drift) | untested | Being audited in the event/distribution lane |
| A7 — The kit's conventions are mostly judgment-shaped (hence prose rules) | untested | Profile-projection research suggests a sizable data-shaped subset; tracker lane building the inventory |

## 5. Findings

[Pending: consolidated from the four audit lanes.]

## 6. Change options

[Pending.]

## 7. Recommendation

[Pending.]

## 8. Deferred and rejected

[Pending.]

## 9. Open questions

- [ ] [Pending.]

## 10. Approval

| Finding | Decision | Authority | Date | Rationale |
|---|---|---|---|---|
| — | — | kevglynn | — | — |

**Resulting work items:** [pending]
**Traceability:** [pending — pre-change commit hash recorded at decision time]
