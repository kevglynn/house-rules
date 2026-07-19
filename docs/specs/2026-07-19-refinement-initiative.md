# Refinement Initiative

**Date:** 2026-07-19
**Beads:** `process-kit-8va` (foundations + pragmatic-TDD pilot epic: ffa → vvx → {3ju, 4ek} → 2l2 → 9r8) and `process-kit-j2h` (refinement capability epic: tl1 → l1h → 7wz)
**Status:** Approved
**Source research:** [docs/research/2026-07-19-chatgpt-prag-tdd-and-refinement-process.md](../research/2026-07-19-chatgpt-prag-tdd-and-refinement-process.md)

## Architecture and component overview

Three linked outcomes, delivered as one sequenced initiative:

1. **Reshape pragmatic-tdd.** Split the single always-on rule into a topology of
   surfaces, each with a bounded responsibility:
   - **Thin policy rule** (`cursor/rules/pragmatic-tdd.mdc`, stays `alwaysApply`):
     when the discipline applies, what must be true when it does, legitimate
     exceptions, required completion evidence, and a pointer to the skill.
   - **Executable skill** (`skills/pragmatic-tdd/SKILL.md`): the per-bead-type
     playbooks (bug/feature/refactor/story/spike/…), the red-proof ceremony
     ("evidence, not penance"), the pattern-class scan, AC-to-test derivation.
   - **Test-signal review lens** (added to `skills/tier1-review/lenses.md`):
     independent semantic judgment — does the test fail for the intended reason,
     would it catch the original defect, is it implementation-coupled, is the
     claimed TDD evidence credible? The zero-signal taxonomy becomes shared
     vocabulary between the rule (prohibition), skill (avoidance), and lens
     (detection).
   - **No dedicated TDD subagent.** The lens rides the existing tier1 review.
   - **No hooks now.** Per the trigger-layer spike, hooks can only nudge/gate;
     red-state evidence capture and pre-commit test gates are deferred with an
     explicit upgrade trigger (see Non-goals).

2. **Refinement capability** (`skills/refinement/SKILL.md` + references). A
   reusable, human- or agent-initiated process that audits
   **intent → plan → execution → observed reality** — and the operating
   mechanisms themselves — and produces an evidence-grounded **refinement
   proposal**. A proposal becomes a **plan revision** only after approval; no
   silent plan mutation. Core components:
   - **Concept doc** (`docs/concepts` or alongside the skill): definition,
     control loop, trigger taxonomy, findings taxonomy, two-axis change
     classification (**magnitude** × **transformation**), operating-surface
     model (canonical spec / rule / skill / hook / reviewer / human gate).
   - **Refinement-proposal package template**: scope, initiator + reason,
     evidence reviewed, confirmed/invalidated assumptions, findings (each with
     evidence, affected dimension, magnitude, transformation, confidence,
     urgency), change options with costs/risks/reversibility, recommendation,
     affected artifacts, traceability record.
   - **Mechanism-placement audit reference**
     (`skills/refinement/references/mechanism-audit.md`): the audit questions
     for "is this capability in the right artifact, with the right activation,
     authority, and enforcement?", the surface-responsibility table, and the
     anti-pattern list (competing sources of truth, advisory-presented-as-
     enforcement, proxy metrics that incentivize performative compliance,
     always-on context bloat).
   - **Retrospective mode**: reviewing mature/completed work with no active
     plan — exactly the mode the kit audit needs.

3. **Kit-wide mechanism-placement audit.** The first real run of the skill:
   retrospective-mode review of the kit's own rules, skills, and hooks
   (context cost per always-on rule, overlap analysis such as
   session-lifecycle vs operating-model, enforceability gaps, split/merge/
   relocate/retire candidates). Output is a refinement proposal the user
   triages; accepted findings become beads.

**Sequencing insight (drives the whole structure):** the pragmatic-tdd reshape
*is* a refinement — a mechanism-placement refinement of a mature capability.
It runs as the pilot: foundations are written first, the pilot dogfoods the
proposal template, and the skill is authored from what the pilot actually
taught, not just the research doc's theory.

## Data flow and key interfaces

```
docs/research/…refinement-process.md      (source thinking)
        │
        ▼
concept doc + proposal template           (Epic 1, bead 1)
        │
        ▼
pragmatic-tdd refinement proposal         (pilot; dogfoods the template)
        │
        ├─► skills/pragmatic-tdd/SKILL.md     (procedure)
        ├─► cursor/rules/pragmatic-tdd.mdc    (thinned policy; sync-rules.sh → claude)
        ├─► skills/tier1-review/lenses.md     (test-signal lens)
        └─► docs/rule-effectiveness-scorecard.md  (TDD items + baseline)
        │
        ▼
skills/refinement/SKILL.md + references   (encodes pilot lessons)
        │
        ▼
kit-wide audit run → refinement proposal → user triage → reshape beads
```

Interfaces and conventions in play:
- Rule edits land in `cursor/rules/*.mdc` (canonical), then
  `./scripts/sync-rules.sh --format claude --local` regenerates the Claude
  projection. Consumers pick the change up on their next sync.
- Skills follow the generic-core / project-overlay convention
  (`skills/README.md`); new skills register in the README table with trigger
  phrases and skip conditions.
- The tier1-review lens roster lives in `skills/tier1-review/lenses.md`.
- Measurement rides `docs/rule-effectiveness-scorecard.md` and the
  `rule-efficacy-analyst` subagent (before/after transcript scoring).

## Trade-offs and decisions

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Separate canonical "doctrine" doc for pragmatic-tdd (GPT's four-projection model) | Single source of truth; projections can't drift silently | Fourth artifact to maintain; premature with only three cross-referencing artifacts | **Defer.** Rule/skill/lens cross-reference each other and share terminology. Upgrade when: actual drift between projections is observed. |
| Refinement capability as standalone project (per ChatGPT kickoff prompt) vs in-kit skill family | Standalone: room to grow into a product | In-kit matches how every kit capability matured (packet, tier1); standalone fragments incubation | **In-kit** (user-approved 2026-07-19). Extract later if it outgrows the kit. |
| Framework-first (all 20 kickoff-prompt deliverables) vs pilot-first | Framework-first: complete on paper | Process theater risk — the prompt's own principle 14; unvalidated taxonomy | **Minimal foundations → pilot → harden skill → first real run.** |
| Dedicated TDD subagent | Independent judgment | Disconnected from the implementer's loop; tier1 lens covers the review need | **No subagent.** Test-signal lens inside tier1-review. |
| TDD hooks (red-state capture, pre-commit gates) | Mechanical evidence, harder to skip | Spike showed hooks are nudge/gate only; noisy proxies incentivize performative tests | **Defer.** Upgrade when: transcript scoring shows agents skipping red-first despite the rule+skill split, or bd ships event hooks. |
| Agent-applied refinements (agent authority to mutate plans) | Full autonomy loop | Authority boundaries undesigned; violates "no silent plan mutation" until designed | **MVP is proposal-only.** Human approves all applications. Upgrade when: two+ refinement runs complete with clean traceability. |

## Non-goals

- **No TDD hooks in this initiative** (deferred with trigger above).
- **No bd-native automation** for triggering refinements (formulas/gates/
  patrol) — the trigger-layer spike's defer stands.
- **No full kickoff-prompt deliverable set**: state machine, versioning model,
  product-form exploration, phased product plan are out of scope until the
  pilot and kit audit prove the core loop.
- **No agent-applied plan mutations** — proposals only.
- **No changes to consuming projects** — this lands in the kit; consumers sync
  on their own cadence.

## Risks and open questions

- [ ] **Thinning the rule may regress behavior.** The always-on rule is the
      only surface guaranteed to be in context. Mitigation: obligations
      checklist diff (nothing lost, only relocated) + scorecard TDD items with
      before/after transcript scoring via rule-efficacy-analyst.
- [ ] **Skill invocation reliability.** A skill only fires if the rule pointer
      or the agent's judgment invokes it. The scorecard baseline should track
      invocation rate; if low, that is itself a mechanism-placement finding.
- [ ] **Taxonomy overfit.** The magnitude × transformation axes come from one
      conversation. The pilot and kit audit must be allowed to revise them —
      foundations doc is a draft until two runs validate it.
- [ ] **Kit audit scope creep.** Retrospective mode over every kit artifact
      could balloon. The audit produces a proposal for user triage; it does
      not execute reshapes.
- [ ] **Which findings taxonomy granularity is useful in practice?** (execution
      drift vs planning weakness vs invalidated assumption vs …) — validate
      during the pilot, prune what goes unused.
