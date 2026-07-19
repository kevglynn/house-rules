# Refinement Proposal: pragmatic-tdd capability topology

**Date:** 2026-07-19
**Initiator:** human (kit owner) + agent (authored) — **Reason initiated:** mechanism-side trigger — a mature, working capability suspected of being represented through a suboptimal combination of surfaces (single always-on rule carrying policy *and* procedure), surfaced during the retrospective that launched the refinement initiative. Plus opportunity: the operating-surface catalog opened placement options that did not exist when the rule was written.
**Mode:** retrospective · **Refinement object(s):** mechanisms
**Scope:** the pragmatic-tdd capability — `cursor/rules/pragmatic-tdd.mdc` and the surfaces it could span (skill, review lens, evidence tooling). Not in scope: the substance of the test discipline itself.
**Execution during refinement:** continues — no active work depends on the rule changing.
**Status:** Approved (2026-07-19, kit owner) — with one revision at the
approval gate: Option D's ledger pulled forward (see §8)
**Bead:** process-kit-vvx · **Spec:** [2026-07-19-refinement-initiative.md](../specs/2026-07-19-refinement-initiative.md)

## 1. Executive summary

The pragmatic-tdd discipline works and its content is validated — nothing in
this proposal changes what the discipline requires. What it changes is
*where the capability lives*. Today one always-on rule carries the policy,
the full operational playbook, and the quality taxonomy, while no surface
independently reviews test quality and no surface records test evidence.
The recommendation is a topology split (magnitude: local-to-cross-cutting;
transformation: split + relocate + add-enforcement): a thin always-on rule
keeping only obligations, exceptions, and evidence requirements; a
`pragmatic-tdd` skill carrying the per-bead-type playbooks and the
red-proof ceremony; and a fourth tier1-review lens giving the zero-signal
taxonomy a semantic detection surface. A stronger variant adding an
evidence-ledger CLI with CI verification was initially deferred, but the
deferral was reversed at the approval gate (§8): the ledger is a
distributable artifact whose gate host is target-repo CI, which typically
exists. It proceeds as a follow-up bead after the split lands.

## 2. Governing intent

Authoritative sources, in precedence order:

1. **The rule itself** (`cursor/rules/pragmatic-tdd.mdc`): "test-first
   discipline… stripped of dogma. The goal is **signal**, not coverage."
   Per-bead-type policies; a five-class zero-signal taxonomy with a
   one-sentence guardrail; "evidence, not penance."
2. **The initiative spec's intent frame**: evolution not remediation;
   outputs written for outside readers; fail-fast toward publication.
3. **PLAN.md skill-layer design rule**: rules state the law, skills encode
   the procedures; generic core / project overlay.
4. **The source research conversation**
   ([2026-07-19](../research/2026-07-19-chatgpt-prag-tdd-and-refinement-process.md)):
   both external models converged on policy-in-rule / procedure-in-skill /
   review-as-lens / no dedicated TDD subagent.

No conflicts among sources. The intent to preserve: *every obligation the
rule currently imposes survives the move; only its address changes.*

## 3. Evidence reviewed

- `cursor/rules/pragmatic-tdd.mdc` (66 lines, current text — the obligations
  inventory in §7 derives from it line by line)
- The kit's always-on rule load: 12 `alwaysApply` rules injected every
  session (context competition for every obligation in each)
- `skills/tier1-review/lenses.md`: three lens templates (correctness /
  structure / simplification); none reviews test quality; the simplify lens
  explicitly routes nothing to a test-signal reviewer because none exists
- [Operating-surface catalog memo](../research/2026-07-19-operating-surface-catalog.md),
  Parts 1–5: placement axes, CLI-first enforcement stack, the finding that
  no off-the-shelf durable red-then-green recorder exists, the
  profile-driven projection pattern
- [Trigger-layer spike](../research/2026-07-16-trigger-layer-spike.md) and
  its Part 4 correction (hooks are blocking-capable; bd lacks close events)
- External validation: TDD Guard / Probity exist and are adopted (~200k
  downloads) — independent confirmation that red-first skipping and
  zero-signal tests are real, common failure modes worth surfacing
- **Wanted but unavailable:** transcript-based adherence data (the
  scorecard has no TDD items yet — bead process-kit-9r8 creates them and
  the baseline); measured token cost per always-on rule (bead
  process-kit-l1h quantifies). Confidence ratings below reflect these gaps.

## 4. Assumption ledger

| Assumption (from the capability's original design) | Status | Evidence |
|---|---|---|
| A1 — Always-on placement is the strongest available guarantee of TDD compliance | **Weakened** | A rule is advisory: privileged visibility, no enforcement. Catalog enforcement axis; documented harness-hook and agent-rationalization failure modes |
| A2 — Hooks can only nudge, so no mechanical layer is worth building | **Invalidated (corrected)** | Trigger-layer spike claim was bd-specific; harness hooks are blocking-capable; and the CLI+CI path (catalog Part 3) needs no hooks at all |
| A3 — The discipline's content (per-type policies, zero-signal taxonomy) is correct | **Confirmed** | In-use success; external tools independently encode the same failure modes; both external models endorsed content unchanged |
| A4 — A dedicated TDD subagent is the wrong primary owner of the loop | **Confirmed** | Grok and GPT converged; the tier1 lens pattern covers independent judgment without detaching from the implementer's loop |
| A5 — The full rule's always-on context cost is material | **Untested** | Plausible (12 always-on rules; this one ~66 lines) but unmeasured until l1h; confidence medium |

## 5. Findings

### F1 — Procedure living at the policy address

- **Type:** mechanism misplacement
- **Observation:** ~75% of the rule's text is step-by-step procedure (the
  numbered playbooks, the taxonomy's worked examples, the stash/revert
  ceremony) — operational content that pays always-on context cost yet is
  only needed when a qualifying bead is actually being implemented.
- **Evidence:** rule text vs the catalog's surface-class responsibilities;
  the "always-on rule carrying a full operational playbook" misplacement
  smell; PLAN.md's own law-vs-procedure design rule.
- **Relates to:** A1, A5 · **Dimension(s):** conventions, agent behavior
- **Magnitude:** local-to-cross-cutting · **Transformation:** split + relocate
- **Confidence:** high · **Urgency:** none blocking; sequenced now because
  downstream beads consume the result
- **Why it matters:** context competition dilutes every always-on rule, and
  procedure at the policy address is the pattern the whole kit is most
  likely to copy — fixing it here sets the template.

### F2 — No semantic surface for test quality

- **Type:** missing mechanism (verification weakness)
- **Observation:** the zero-signal taxonomy is prohibition-only. Nothing
  independently examines whether shipped tests would actually catch the
  defect, whether mocks swallowed the behavior, or whether claimed TDD
  evidence is credible. The tier1 roster reviews correctness, structure,
  and simplicity — not tests.
- **Evidence:** `skills/tier1-review/lenses.md` (three templates, none
  test-focused); catalog: review is the semantic control rules cannot
  provide themselves.
- **Relates to:** the taxonomy's enforcement path · **Dimension(s):** testing, quality standards
- **Magnitude:** local · **Transformation:** add-enforcement (semantic)
- **Confidence:** high · **Urgency:** low
- **Why it matters:** a prohibition nobody checks converges on ritual
  compliance — tests that exist but prove nothing.

### F3 — TDD evidence is asserted, never recorded

- **Type:** verification weakness + opportunity
- **Observation:** close reasons assert "test failed before fix, passes
  after," but nothing records the failing run or verifies the ordering. The
  evidence layer is prose at the advisory level.
- **Evidence:** catalog Part 3 comparative analysis; the finding that no
  off-the-shelf durable red-then-green recorder exists (TDD Guard/Probity
  hold session state only); the kit's own `bd close --reason` evidence
  policy.
- **Relates to:** A1 · **Dimension(s):** testing, observability
- **Magnitude:** local · **Transformation:** add-enforcement (mechanical)
- **Confidence:** high on the gap; medium on how much it matters here
  (no adherence baseline yet — see F5)
- **Why it matters:** observable evidence is what separates "the agent says
  it did TDD" from "the ledger shows it" — and it is the piece an outside
  adopter can verify without trusting anyone's narration.

### F4 — The discipline's content is confirmed (no change proposed)

- **Type:** confirmed success
- **Observation:** the per-bead-type policies map cleanly onto the bead
  types in real use; the five zero-signal classes match the failure modes
  external tooling independently targets; "evidence, not penance" has
  prevented the ritual-deletion anti-pattern it was written for.
- **Evidence:** §3 items; absence of any content-level complaint in the
  source research conversation despite two models pushing on it.
- **Magnitude:** none · **Transformation:** — (record and preserve)
- **Why it matters:** locks in what is working before anything moves —
  the split must be provably content-neutral (§7 obligations checklist).

### F5 — Post-split invocation reliability is unmeasured

- **Type:** risk
- **Observation:** after thinning, the playbooks live in a skill that must
  be invoked — by rule pointer or agent judgment. Invocation reliability is
  unknown because no TDD scorecard items exist yet.
- **Evidence:** scorecard has zero TDD items; catalog lists "workflows
  depending on unreliable manual invocation" as a misplacement smell.
- **Relates to:** A1, A5 · **Dimension(s):** agent behavior, measurement
- **Magnitude:** minor · **Transformation:** standardize (measurement)
- **Confidence:** high that it needs measuring · **Urgency:** must land
  with the split, not after (bead 9r8 is already sequenced for this)
- **Why it matters:** this is the named regression risk of the whole
  reshape; the mitigation is data, not hope.

*Routed elsewhere:* the observation that the test-policy and
evidence-requirements tables are data-shaped (profile-pattern candidates)
is routed to the kit-wide audit (process-kit-l1h) per catalog Part 5 — out
of scope here.

## 6. Change options

The findings share one structural response, so options are evaluated as one
combined set (template note: §6 amended to permit this — see §8).

| Option | Benefits | Costs / risks | Work invalidated | Reversibility | Confidence |
|---|---|---|---|---|---|
| **A — Keep as is** | Zero effort; known-working | F1–F3 persist; the kit's flagship rule models procedure-at-policy-address for every future capability | — | — | high |
| **B — Thin rule only** (compress, no skill) | Cuts context cost | Destroys the playbooks instead of relocating them; agents lose the procedure entirely | The playbooks' value | easy | high |
| **C — Topology split** (thin rule + skill + tier1 test-signal lens + scorecard items) | Right content at right addresses; adds the missing semantic surface; measurable via 9r8 baseline; fully covered by existing beads 3ju→2l2, 4ek, 9r8 | Invocation-reliability risk (F5 — mitigated by measurement); four artifacts share vocabulary and could drift (mitigated: cross-references + shared terminology; a canonical doctrine doc stays deferred until drift is observed) | none | moderate (git revert restores the monolith) | high |
| **D — C + evidence-ledger CLI + CI verify** | Converts F3 from asserted to observable→blocking; publication-grade demonstrable enforcement | New tool to build and maintain; **the kit has no CI layer to host the verify gate**; adds scope before the baseline says it's needed | none | moderate | medium |

Missing information that would change the choice: the 9r8 baseline (does
red-first actually get skipped?) and the l1h audit's CI recommendation.
Both arrive without a spike.

## 7. Recommendation

**Adopt Option C now. Defer Option D's ledger with an explicit trigger.**

C is the smallest sufficient change that resolves F1 and F2 while F4 keeps
content frozen. D is specified and attractive — but it enforces at a layer
(CI) the kit doesn't have yet, and the smallest-sufficient-change principle
says let the baseline prove the need. The existing bead graph already
implements C exactly: `3ju` (skill) → `2l2` (thin rule + sync) with `4ek`
(lens) parallel, `9r8` (scorecard + baseline) after `2l2`.

**Affected artifacts:** `skills/pragmatic-tdd/SKILL.md` (new) ·
`cursor/rules/pragmatic-tdd.mdc` (thinned; claude projection regenerated) ·
`skills/README.md` (registration) · `skills/tier1-review/lenses.md` (fourth
template) · `docs/rule-effectiveness-scorecard.md` (TDD section).

**Migration / transition steps:** skill first (rule must point at something
that exists); rule thinned against the checklist below; sync to claude
format in the same commit; lens added; scorecard items + baseline recorded.
No consumer action required — consumers pick up the change on next sync.

### Obligations checklist (content-neutrality proof)

Every obligation in the current rule, mapped to its destination. **Rule**
= thin always-on rule; **Skill** = `skills/pragmatic-tdd`; **Lens** =
tier1 test-signal template. Nothing is dropped.

| # | Current obligation (rule text) | Destination |
|---|---|---|
| O1 | Bug: reproducing test written first, must fail on current code | **Rule** (obligation) + **Skill** (steps 1–2) |
| O2 | Bug: verify the test fails for the right reason | **Skill** (step 2) + **Lens** (fails-for-intended-reason check) |
| O3 | Bug: write the minimal fix | **Skill** (step 3) |
| O4 | Bug: verify the test passes; evidence = fails without fix, passes with | **Rule** (evidence requirement) + **Skill** (step 4) |
| O5 | Bug: pattern-class scan across codebase; fix all sites or file follow-up beads before close; test should fail on every unfixed site | **Rule** (one-line obligation) + **Skill** (rg procedure) + **Lens** (pattern-class-addressed check) |
| O6 | Feature: ACs become failing tests first (observable behavior, not internals) | **Rule** (obligation) + **Skill** (AC-derivation procedure) |
| O7 | Feature: verify fail → implement → verify pass | **Skill** (steps 3–5) |
| O8 | Story: identical to feature | **Rule** (applicability table) |
| O9 | Refactor: behavioral safety net before structural change; tests still pass after | **Rule** (obligation) + **Skill** (playbook) |
| O10 | Spike: tests optional; findings in close reason; promoted code inherits feature policy | **Rule** (exception + promotion clause) |
| O11 | Decision/milestone: no tests required | **Rule** (exception) |
| O12 | Epic: no direct tests; policy applies to children | **Rule** (exception) |
| O13 | Chore/config/docs: no tests; a test here is noise | **Rule** (exception) |
| O14 | Zero-signal taxonomy, 5 classes with examples (mocks; implementation details; type-system; tautological; helper-only-skipping-callsite) | **Skill** (full taxonomy, authoring-time avoidance) + **Lens** (detection criteria, same class names) |
| O15 | Guardrail: "if a test would pass whether or not the feature works, it's zero signal — don't write it" | **Rule** (verbatim) |
| O16 | Evidence-not-penance: stash/revert to prove red is legitimate; no ritual code deletion | **Skill** (red-proof ceremony) + **Rule** (evidence clause names the legitimate path in one line) |
| O17 | Framing: goal is signal, not coverage | **Rule** (one line) + **Skill** (intro) |

Shared vocabulary rule: the five zero-signal class names and the rule IDs of
obligations O1–O17 appear identically in all three artifacts, so the
advisory, procedural, and semantic layers agree by construction (borrowed
from the profile pattern's shared-namespace insight, applied to prose).

## 8. Deferred and rejected

- **Option B — rejected:** relocation without a destination is deletion.
- **Option D (evidence-ledger CLI + CI verify) — deferral REVERSED at the
  approval gate (2026-07-19).** The kit owner challenged the deferral
  rationale and the challenge held: the "no CI layer" objection
  misattributed the gate host — the ledger is a *distributable* artifact
  and target repos (the actual gate hosts) typically have CI. The baseline
  precondition was also weaker than framed, since external adoption of
  TDD Guard/Probity already evidences the failure mode; the 9r8 baseline
  remains valuable as before/after measurement, not as a gate. Revised
  disposition: **pulled forward as bead process-kit-0ei**, sequenced after
  the rule thinning (`2l2`) so the skill's red-proof ceremony can reference
  the ledger commands. Shape per catalog Part 3 (record-failing /
  record-passing / verify against a committed JSONL ledger); the kit adds a
  minimal CI workflow to dogfood the verify gate.
- **TDD hooks as enforcement — remains deferred** per the spec non-goal;
  Probity-style `requireCommand` gating noted as optional in-session UX
  only, subordinate to the same trigger as Option D.
- **Profile-ization of the data-shaped tables — routed** to the kit audit
  (l1h), not deferred: it is a kit-wide question, not a pragmatic-tdd one.
- **Template feedback (AC obligation of this pilot):** one defect found and
  fixed — §6 mandated per-finding option sets, which forces repetition when
  findings share one structural response; the template now permits a
  combined option set with a note. Everything else fit without modification.

## 9. Open questions

- [ ] Does the thinned rule reliably trigger skill invocation? (Answered by
      9r8's invocation-rate item after the split lands.)
- [ ] What is the actual token cost of each always-on rule? (Answered by
      l1h; updates A5 and the D trigger's urgency.)

## 10. Approval

| Finding | Decision | Authority | Date | Rationale |
|---|---|---|---|---|
| F1 (split + relocate) | approved | kit owner | 2026-07-19 | Option C as recommended |
| F2 (test-signal lens) | approved | kit owner | 2026-07-19 | Option C as recommended |
| F3 (ledger) | approved — **pulled forward**, not deferred | kit owner | 2026-07-19 | Deferral rationale conflated kit CI with target-repo CI; see §8. Bead process-kit-0ei |
| F4 (content frozen) | approved | kit owner | 2026-07-19 | Obligations checklist is the neutrality proof |
| F5 (measure via 9r8) | approved | kit owner | 2026-07-19 | Baseline reframed as before/after measurement (F3 revision), still required |

**Resulting work items:** process-kit-3ju, -2l2, -4ek, -9r8 (pre-existing;
this proposal is the evidence they were correctly scoped) + process-kit-0ei
(evidence-ledger CLI, created at the approval gate, depends on 2l2).
**Traceability:** prior state = `cursor/rules/pragmatic-tdd.mdc` at commit
`a288891` (pre-split); this proposal at `e28bf2e`; the approval-gate
challenge and F3 reversal recorded in §8. Post-split diffs will reference
this document.
