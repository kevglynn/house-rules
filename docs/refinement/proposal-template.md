# Refinement Proposal — Template

Copy this file to `docs/refinements/YYYY-MM-DD-<scope-name>.md` in the repo
under review and fill every section. If a section is genuinely inapplicable,
keep the heading and write why it doesn't apply — that feedback improves this
template. Concepts, taxonomies, and axis definitions live in
[concepts.md](concepts.md); don't restate them here.

A document from this template is a **proposal** until the Approval section is
filled by the deciding authority; only then do its accepted changes become
**plan revisions**.

---

# Refinement Proposal: [scope name]

**Date:** YYYY-MM-DD
**Initiator:** [human name / agent + session] — **Reason initiated:** [which trigger(s) from the trigger taxonomy, and what tripped them]
**Mode:** [active-plan | retrospective] · **Refinement object(s):** [work | mechanisms | both]
**Scope:** [full project | phase | epic | subsystem | capability | single policy — name it precisely]
**Execution during refinement:** [continues | paused for <scope> — why]
**Status:** Draft | Under review | Decided

## 1. Executive summary

[3-6 sentences: what was examined, the headline findings, the recommended
response, and the largest magnitude involved. Write it for someone who reads
nothing else.]

## 2. Governing intent

[The authoritative sources of intent for this scope and what they say:
problem, users, outcomes, constraints, non-goals, prior decisions with
rationale. Name the artifacts (spec, ADR, epic description) and flag any
conflicts between them — resolving which artifact is authoritative may itself
be a finding.]

## 3. Evidence reviewed

[What was actually examined, listed so the review is reproducible: code,
commits/PRs, test results, transcripts, bead history, measurements, user
feedback, artifact texts. Note evidence that was *wanted but unavailable* —
gaps lower confidence and belong in the record.]

## 4. Assumption ledger

| Assumption (from plan/intent) | Status | Evidence |
|---|---|---|
| … | confirmed / weakened / invalidated / untested | … |

## 5. Findings

One block per finding. Small refinements may have one; that's fine.

### F1 — [short name]

- **Type:** [from findings taxonomy]
- **Observation:** [what is true, stated neutrally]
- **Evidence:** [specific artifacts/measurements backing it]
- **Relates to:** [artifact, assumption, or AC affected]
- **Dimension(s):** [product intent / architecture / testing / conventions / …]
- **Magnitude:** [none … existential] · **Transformation:** [clarify / split / relocate / …]
- **Confidence:** [high/med/low] · **Urgency:** [blocks current work? safe to defer?]
- **Why it matters:** [consequence of leaving it alone]

## 6. Change options

For each finding (or coherent group of findings), the realistic responses —
always including "keep as is" so the do-nothing cost is explicit.

### Option set for F1

| Option | Benefits | Costs / risks | Work invalidated | Reversibility | Confidence |
|---|---|---|---|---|---|
| Keep as is | … | … | — | — | … |
| [minimal correction] | … | … | … | … | … |
| [broader change] | … | … | … | … | … |

[Note information still missing that would change the choice, and whether a
spike/experiment could obtain it.]

## 7. Recommendation

[The selected option per finding, with the reasoning for choosing it over the
alternatives. Where findings interact, state the combined sequence. Apply
smallest-sufficient-change; justify anything structural or larger.]

**Affected artifacts:** [each artifact that changes, with the nature of the change]
**Migration / transition steps:** [ordering, invalidated work handling, sync steps]
**For mechanism refinements — obligations checklist:** [every obligation in the
current artifact(s) mapped to its destination surface, proving nothing is
lost in the move. Required for any split/relocate/merge of rules, skills,
hooks, or lenses.]

## 8. Deferred and rejected

[Findings or options deliberately not acted on: the rejection reason, or the
defer trigger (what future condition reopens it). Nothing silently dropped.]

## 9. Open questions

- [ ] [Unresolved question, who/what can resolve it]

## 10. Approval

| Finding | Decision | Authority | Date | Rationale |
|---|---|---|---|---|
| F1 | accepted / rejected / deferred | [human name] | … | … |

**Resulting work items:** [bead IDs created from accepted findings]
**Traceability:** [where prior state is preserved — commit hash of the
pre-change artifacts, superseded doc links]
