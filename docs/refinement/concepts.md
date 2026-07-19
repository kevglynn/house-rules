# Refinement in Agentic Development — Concepts

**Status:** Draft — taxonomies below are provisional until validated by two real
runs (the pragmatic-tdd pilot and the kit-wide audit). Revise freely with
evidence; record revisions in the changelog at the bottom.
**Spec:** [2026-07-19-refinement-initiative.md](../specs/2026-07-19-refinement-initiative.md)
**Source research:** [2026-07-19-chatgpt-prag-tdd-and-refinement-process.md](../research/2026-07-19-chatgpt-prag-tdd-and-refinement-process.md)

## Definition

A **refinement** is a deliberate, evidence-grounded audit of a project's
intent, plan, execution, and operating mechanisms that produces a classified
**refinement proposal** — a structured recommendation for change, or an
explicit confirmation that no change is needed.

A proposal becomes a **plan revision** only after approval. An audit never
automatically becomes an authoritative change ("no silent plan mutation").

Refinement is not a correction mechanism. Most refinements are caused by
**discovery, not failure** — implementation legitimately produces information
that could not have been known at planning time. Treating that information as
someone's fault suppresses it; treating it as normal input keeps plans honest.

## The control loop

Refinement operates as a recurring control loop across four things that change
at different rates:

> **Intent → Plan → Execution → Observed Reality**

Every refinement asks four questions:

1. Is the **intent** still correct?
2. Does the **plan** still express that intent?
3. Does **execution** still follow the plan?
4. Has **observed reality** revealed anything that should change the intent,
   the plan, the execution, or the governing conventions?

A valid answer to all four is "yes, nothing changes" — a **Level-0
confirmation** is a real outcome that locks in proven patterns and records
newly confirmed assumptions.

## Two objects of refinement

A refinement can target either (often both):

1. **The work** — product intent, plan, architecture, backlog, ACs.
2. **The operating system that governs execution** — rules, skills, hooks,
   review lenses, conventions, templates, approval gates. This is
   **mechanism-placement refinement**: the question is not "is the content
   right?" but "is this capability represented in the correct artifact,
   activated at the correct time, given the correct authority, and enforced
   through the correct mechanism?"

**Retrospective mode** applies the loop to mature or completed work with no
active plan. It may produce zero change to the underlying product while
substantially changing the mechanisms used to maintain it.

## Trigger taxonomy

What legitimately initiates a refinement. Grouped by where the signal
originates; a real trigger often spans groups.

| Family | Triggers |
|---|---|
| **Intent-side** | Changed priorities or stakeholder intent; scope imbalance (effort no longer matches value); quality-bar recalibration (prototype became foundational, or rigor is throttling exploration) |
| **Plan-side** | Plan staleness (completed work changed the decision landscape); sequence correction; specification ambiguity; missing requirements (failure cases, migrations, empty states, observability…); nonfunctional requirements becoming concrete |
| **Execution-side** | Execution drift from the plan; inconsistent agent decisions across sessions; accumulated implementation debt; local optimization at the expense of the whole; context loss (tickets without their why) |
| **Reality-side** | Discovery during implementation; invalidated assumptions; architecture under stress; interface mismatch between individually-correct components; dependency or environment change; new opportunity; risk concentration (progress everywhere except the hardest uncertainty); verification weakness (ACs pass, outcome unproven); product incoherence; complexity growth |
| **Mechanism-side** | A rule/skill/hook is skipped, misfires, duplicates another, can't enforce what it claims, or consumes disproportionate context; repeated failures indicating a missing rule, skill, hook, or review step |
| **Confirmation** | Periodic checkpoint (phase/epic close) with no adverse signal — run cheaply, confirm, lock in |

Not every trigger warrants the same depth. **Proportionality is a design
principle**: a convention question needs a conversation, not a full audit.

## Findings taxonomy

Each finding in a proposal is typed. The types matter because they route to
different responses (a planning weakness is not fixed by disciplining
execution, and vice versa).

- **Execution drift** — implementation diverged from an agreed plan
- **Planning weakness** — the plan was internally consistent but wrong or incomplete
- **Invalidated assumption** — a premise the plan rests on proved false
- **Newly discovered requirement** — omitted state, case, or constraint
- **Changed intent** — the goal itself moved
- **Architecture problem** — structure under stress or boundaries wrong
- **Missing convention** — recurring decisions with no governing rule
- **Accumulated debt** — normalized shortcuts, duplication, temporary adapters
- **Product incoherence** — parts work, whole confuses
- **Mechanism misplacement** — right capability, wrong artifact/activation/authority/enforcement
- **Opportunity** — a simpler approach, reusable primitive, or adjacent capability surfaced
- **Risk** — concentrated, untouched uncertainty
- **Harmless deviation** — divergence that needs recording, not fixing
- **Confirmed success** — evidence the plan or pattern is working; worth locking in

## Two-axis change classification

Proposed changes are classified on **two independent axes**, per affected
dimension — never collapsed into one project-wide "level."

### Axis 1 — Magnitude

| Magnitude | Meaning |
|---|---|
| **None** | Confirmation; record and continue |
| **Minor** | Wording, clarification, single AC |
| **Local** | One component, story, or policy |
| **Cross-cutting** | Multiple related parts of the remaining plan; core intent and architecture intact |
| **Structural** | The plan's structure no longer represents how the project should proceed (phases, boundaries, sequencing) |
| **Strategic** | Intent, target user, value proposition, or central solution changes |
| **Existential** | Stop, suspend, or split the project |

### Axis 2 — Transformation

What operation is performed: **clarify · correct · extend · restrict ·
reorder · split · merge · relocate · promote · demote · replace ·
standardize · automate · add-enforcement · remove · suspend**.

Example: the pragmatic-tdd reshape is *magnitude: local-to-cross-cutting*,
*transformation: split + relocate* — far more descriptive than "a Level 2."

### Secondary attributes

Each finding/change also carries: **confidence** (how sure are we),
**urgency** (does this block current work), **reversibility** (can it be
undone), **affected scope** (which artifacts), and **evidence source**
(observation, transcript, measurement, stakeholder statement).

## Refinement dimensions

Findings are compartmentalized by the part of the project they affect —
product intent, scope, requirements, architecture, data model, interfaces,
sequencing, testing, quality standards, conventions, agent behavior,
documentation, operations. A single refinement legitimately produces
different magnitudes in different dimensions (e.g. *none* for product intent,
*cross-cutting* for test conventions). Preserve that granularity.

## The operating-surface model

For mechanism-placement refinement, capabilities are mapped onto surfaces,
each with a **bounded responsibility**. A capability may span several
surfaces, but each surface answers for one kind of control:

| Surface | Responsibility | Kind of control |
|---|---|---|
| **Canonical specification** | Authoritative definition of the capability (only introduce when drift between projections is actually observed; otherwise cross-referencing surfaces suffice) | Source of truth |
| **Rule / policy** | Applicability triggers, obligations, prohibitions, exceptions, required evidence — always in context | Normative (soft — an agent can still miss or rationalize it) |
| **Skill / procedure** | Multi-step, stateful executable method, invoked on demand | Procedural |
| **Hook / automation** | Event-driven detection, evidence capture, mechanical gates — observable facts, never semantic judgment | Mechanical |
| **Reviewer / lens** | Independent semantic judgment on the result (is it substantively good, not just formally compliant) | Semantic |
| **Human decision point** | Authority explicitly reserved for human approval | Authority |

A rule is **not a guarantee** — it is an instruction with privileged
visibility. When a behavior matters, expect to need normative + mechanical
+ semantic control together, each on its own surface.

Common misplacement smells: an always-on rule carrying a full operational
playbook (context bloat); competing sources of truth evolving independently;
an advisory convention presented as hard enforcement; a hook measuring a
proxy that rewards performative compliance; a workflow that depends on
unreliable manual invocation; a specialist agent disconnected from the
implementer's loop.

## Design principles

1. **No silent plan mutation** — every change produces an explicit record.
2. **Evidence before intervention** — findings ground in observed fact,
   changed intent, or explicit reasoning.
3. **Discovery is not failure.**
4. **Preserve rationale** — the reasoning behind decisions stays accessible.
5. **Smallest sufficient change** — don't refactor the plan when a convention
   fixes it; **but permit major change when justified** — sunk cost is not a
   preservation argument.
6. **Separate findings from decisions** — establish what is true before
   deciding what to change.
7. **Scoped refinement** — a phase, an epic, one policy; not always the world.
8. **Outcomes are executable** — a proposal ends in actionable changes, not a
   retrospective essay.
9. **Proportionality (no process theater)** — depth and cost of the
   refinement match the scope and risk under review.
10. **Human and agent initiation; MVP is proposal-only application** — either
    can start a refinement; only a human approves applying one (authority
    boundaries for autonomous application are future work, gated on clean
    traceability across multiple runs).

## Traceability

Every applied revision retains: prior state, new state, reason, supporting
evidence, deciding authority, date/project state, and affected artifacts —
sufficient to answer *what changed, why, on whose authority, and which
version of the plan governed a given implementation decision*.

## Changelog

- 2026-07-19 — Initial draft, distilled from the source research conversation.
