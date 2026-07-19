---
name: refinement
description: >-
  Run a deliberate, evidence-grounded audit of a project's intent, plan,
  execution, and operating mechanisms, producing a classified refinement
  proposal — a structured recommendation for change, or an explicit
  confirmation that no change is needed. Covers active-plan and retrospective
  modes, any scope from full project down to a single policy, and
  mechanism-placement audits ("is this capability on the right surface?").
  Use when the user says "run a refinement", "refine this epic", "refine this
  plan", "refine this rule", "is this still the right shape", "mechanism
  placement audit", or "retro on this capability".
---

# Refinement

Audit the control loop **intent → plan → execution → observed reality** and
produce a refinement proposal the deciding authority can approve, reject, or
challenge. The foundations — control loop, trigger taxonomy, findings
taxonomy, magnitude × transformation classification, operating-surface
model, placement principles — live in
[docs/refinement/concepts.md](../../docs/refinement/concepts.md). The output
format is
[docs/refinement/proposal-template.md](../../docs/refinement/proposal-template.md).
This skill is the procedure that connects them. Worked example: the
[pragmatic-tdd topology proposal](../../docs/refinements/2026-07-19-pragmatic-tdd-topology.md)
(the pilot run — a retrospective mechanism-placement refinement).

This skill depends on the kit's `docs/refinement/` tree (concepts doc and
proposal template). In a repo where the skill was copied without those docs,
read them from the kit checkout (`${PROCESS_KIT:-~/process-kit}/docs/refinement/`).

## When to Use This Skill

Run a refinement when a trigger from the
[trigger taxonomy](../../docs/refinement/concepts.md#trigger-taxonomy) fires.
The common shapes:

- **Drift detected** — execution has diverged from the plan, or agent
  decisions are inconsistent across sessions (execution-side triggers)
- **Assumption invalidated** — a premise the plan rests on proved false, or
  implementation discovered something planning couldn't know (reality-side)
- **Capability matured** — a mechanism works but its representation is
  suspect: skipped, duplicated, unenforceable, or context-hungry
  (mechanism-side; this was the pilot's trigger)
- **Opportunity opened** — a simpler approach, reusable primitive, or new
  placement option surfaced (reality-side)
- **Periodic hygiene** — a phase/epic close with no adverse signal: run
  cheaply, confirm, lock in (confirmation trigger)

**Skip it** (and say so) when:

- **Mid-execution firefighting** — something is broken *right now*. That is
  debugging (use systematic-debugging), not refinement. Refine afterward if
  the failure exposes a plan or mechanism question.
- **A single trivial change** — proportionality is a design principle. A
  wording fix or one obvious AC correction doesn't need a proposal; just do
  it through the normal bead flow.
- **Work already covered by an approved proposal** — execute the resulting
  beads; don't re-audit what was just decided.

## Operating Modes

**MVP is proposal-only.** Human or agent may *initiate* a refinement; only a
human *applies* one, at the Phase 9 approval gate. No silent plan mutation —
the proposal changes nothing until decided, and every accepted finding
becomes explicit work (beads), never an in-place quiet edit to ACs, plans,
or intent.

Two modes, chosen at scoping time:

- **Active-plan** — the scope has a live plan (epic, spec, backlog); the
  audit compares that plan against intent and reality.
- **Retrospective** — mature or completed work with no active plan. The
  governing intent is *reconstructed from artifacts* — rule text, specs,
  ADRs, research docs, the code itself — rather than read from a live plan.
  The pilot ran exactly this way (proposal §2 rebuilt intent from the rule,
  the spec, PLAN.md, and the source research, in precedence order). A
  retrospective may change nothing in the underlying work while
  substantially changing the mechanisms that maintain it.

## Scope

A refinement targets: **full project · phase · epic · subsystem · single
policy or capability**. Name the scope precisely, including what is *out* of
scope (the pilot excluded the test discipline's substance while auditing its
topology). **Scope determines evidence breadth, not process shape** — a
single-policy refinement runs the same phases as a project-wide one, just
over a smaller evidence base and at proportionate depth.

## Core Process

Fill the [proposal template](../../docs/refinement/proposal-template.md) as
you go — its sections map onto these phases.

### Phase 1 — Establish scope

Record: initiator, the trigger(s) that fired, mode (active-plan or
retrospective), object(s) (the work, the mechanisms, or both), the precise
scope boundary, and whether execution continues or pauses during the
refinement. (Template header — §1's executive summary comes last, in
Phase 8.)

### Phase 2 — Reconstruct governing intent

Identify the authoritative sources of intent for this scope and order them
by precedence — spec, ADRs, epic descriptions, rule text, research docs.
Flag conflicts between sources; resolving which artifact is authoritative
may itself be a finding. In retrospective mode this phase is
reconstruction, not lookup. (Template §2 lists what to capture.)

### Phase 3 — Gather evidence

List everything actually examined so the review is reproducible (template
§3 enumerates the categories). **Record evidence that was wanted but
unavailable**; gaps lower confidence and belong in the proposal (the pilot
recorded two such gaps and rated its confidence accordingly, proposal §3).

For large scopes, evidence gathering may be **parallelized across scoped
lanes** (subagents, each covering a disjoint slice of the scope with the
same method docs and vocabulary). Lane reports become citable evidence;
consolidation into findings stays with the coordinating agent (kit-wide
audit lesson — four lanes covered rules, skills, event/distribution, and
tracker/templates concurrently).

### Phase 4 — Compare against reality

Build the assumption ledger: each assumption the plan or capability design
rests on, marked confirmed / weakened / invalidated / untested, with
evidence. Then ask concepts.md's four control-loop questions. (Template §4.)

### Phase 5 — Produce findings

One block per finding, typed from the
[findings taxonomy](../../docs/refinement/concepts.md#findings-taxonomy) and
classified on the two axes (magnitude × transformation), with confidence,
urgency, and evidence. **Use concepts.md's magnitude scale by name** — if
delegating evidence work (parallel lanes), pass the scale into the lane
instructions; the kit-wide audit accidentally ran its lanes on an
improvised four-level scale and had to note the deviation. State
observations neutrally — what is true, not whose fault.

**Findings can be confirmations** (pilot lesson). A refinement that changes
nothing is a valid outcome: pilot finding F4 confirmed the discipline's
content and froze it (*magnitude: none — record and preserve*), which is
what made the rest of the reshape provably content-neutral. Record confirmed
successes with the same rigor as problems — they lock in proven patterns.
(Template §5.)

### Phase 6 — Generate change options

Build option sets per template §6 — **keep-as-is is mandatory** so the
do-nothing cost is explicit, and **a combined option set is permitted when
findings share one structural response** (pilot lesson: the pilot's five
findings — one a confirmation needing no options — resolved to one combined
set, proposal §6, and forcing per-finding tables would have meant
repetition). Note missing information that would change the choice and
whether a spike could obtain it.

### Phase 7 — Recommend

Select an option per finding with reasoning, applying
**smallest sufficient change** — but permit major change when justified;
sunk cost is not a preservation argument. List affected artifacts and
migration steps.

**For relocation-type changes (split / relocate / merge of rules, skills,
hooks, lenses), an obligations checklist is required** (pilot lesson): every
obligation in the current artifact(s) mapped to its destination surface,
proving nothing is lost in the move. The pilot's §7 checklist (O1–O17)
mapped every obligation of the monolithic rule to rule / skill / lens — that
table *is* the content-neutrality proof, and the shared obligation IDs keep
the destination artifacts agreeing by construction. (Template §7.)

### Phase 8 — Assemble the proposal package

Fill every remaining template section — executive summary, deferred and
rejected (nothing silently dropped; every deferral gets a reopen trigger),
open questions. Save as `docs/refinements/YYYY-MM-DD-<scope-name>.md` in the
repo under review.

**Template feedback loops back in the same cycle** (pilot lesson): if a
template or concepts-doc section doesn't fit your run, that friction is a
finding about the foundations — amend the foundations doc now, not "later."
The pilot found §6's per-finding option sets forced repetition; the template
was amended to permit combined sets *within the pilot's own cycle* (proposal
§8, "Template feedback"). The foundations docs are drafts until real runs
validate them; each run is obligated to push its corrections back.

### Phase 9 — Human approval gate

Present the proposal to the deciding authority for a per-finding decision
(accepted / rejected / deferred, with rationale), recorded in the template's
§10 table.

**The gate is a working step, not a rubber stamp** (pilot lesson) — design
your presentation to invite challenge. In the pilot, the human's challenge
at the gate *reversed a deferral*: the proposal had deferred the
evidence-ledger CLI because "the kit has no CI layer," and the challenge
exposed that rationale as conflating kit CI with target-repo CI — the ledger
is distributable and target repos have CI (proposal §8, F3 reversal).
Concretely: present the reasoning *behind* each deferral and rejection, not
just the disposition; name the weakest link in each rationale; expect the
authority to probe exactly there. A gate that only ever says yes is
enforcement theater.

### Phase 10 — Route to beads

Accepted findings become beads (per the project's bead-quality standards),
recorded in the proposal's "Resulting work items" line, with traceability:
prior state (commit hash of pre-change artifacts), the proposal's own
location, and superseded-doc links. If pre-existing beads already cover an
accepted finding, the proposal is the evidence they were correctly scoped —
say so rather than duplicating them (as the pilot did, §10).

## Mechanism-Placement Audits

When the refinement object includes mechanisms (rules, skills, hooks,
lenses, gates, trackers), use
[references/mechanism-audit.md](references/mechanism-audit.md): the audit
questions, the per-surface-class responsibility table, and the misplacement
anti-patterns. The taxonomies it operationalizes live in concepts.md's
operating-surface model.

## Project Overlay

Project-specific parameters live in `.agents/overlay.md` in the consuming
repo, under a `## refinement` section (shared overlay convention — one file,
one section per skill). The only key this skill reads:

| Key | Meaning | Default when absent |
|---|---|---|
| `intent_sources` | Precedence-ordered list of the project's authoritative-intent artifacts (specs dir, ADR dir, plan doc) for Phase 2 | Reconstruct from standard locations: `docs/specs/`, ADRs, PLAN.md, epic descriptions, rule text |

No other keys. The skill behaves sensibly with no overlay: intent is
reconstructed from artifacts, which retrospective mode requires anyway.

## Anti-Patterns

- **Remediation framing.** Treating a working system as broken because it
  could be improved. Refinement is evolution, not remediation — discovery is
  not failure, and findings phrased as blame suppress the information the
  loop exists to surface.
- **Evidence-free findings.** A finding grounded in vibes rather than
  observed fact, changed intent, or explicit reasoning. If the evidence was
  wanted but unavailable, say so and lower the confidence rating — don't
  assert anyway.
- **Option sets without keep-as-is.** Omitting the do-nothing option hides
  its cost and railroads the decision.
- **Silently modifying ACs or intent.** The proposal recommends; the §10
  authority decides; beads carry the change. An agent that "fixes" the plan
  in place has broken the no-silent-mutation invariant.
- **Scope creep.** Findings outside the established scope get *routed*
  (named and sent to the right owner or a future run), not absorbed. The
  pilot routed its profile-ization observation to the kit-wide audit rather
  than growing to include it (§5, "Routed elsewhere").
- **Deferrals without triggers.** "Deferred" with no reopen condition is a
  silent rejection. Every deferral names the future condition that reopens
  it.
- **Process theater.** Running the full ceremony on a question a
  conversation would settle. Depth must be proportionate to scope and risk —
  a cheap confirmation run is the correct response to a no-adverse-signal
  checkpoint.
