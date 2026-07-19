# Mechanism-Placement Audit Reference

Companion to [SKILL.md](../SKILL.md), used when a refinement's object
includes mechanisms — rules, skills, hooks, lenses, gates, trackers, CLIs.
The surface classes, six classification axes, and placement principles this
reference operationalizes are defined in the
[operating-surface model in concepts.md](../../../docs/refinement/concepts.md#the-operating-surface-model);
read that first. The worked example is the
[pragmatic-tdd topology proposal](../../../docs/refinements/2026-07-19-pragmatic-tdd-topology.md).

The core question is never "is the content right?" — it is: *is this
capability represented in the correct artifact, activated at the correct
time, given the correct authority, and enforced through the correct
mechanism?*

## The audit questions

Ask each question of every mechanism in scope. Each "no" or "unclear" is a
candidate finding (usually type *mechanism misplacement*).

1. **Right artifact class for the job?** Does the content match the bounded
   responsibility of the surface class it lives on (table below)? Obligations
   belong on normative surfaces, procedures on procedural ones, checkable
   facts on deterministic ones.
2. **Right activation?** Always-in-context, on-demand, event-driven,
   scheduled, or gate-at-boundary — does the mechanism fire when it's needed
   and *only* when it's needed? An always-on artifact that matters once per
   bead type is over-activated; a manually-invoked workflow that must never
   be skipped is under-activated.
3. **Right authority?** Advisory, judgment-at-deterministic-trigger,
   observable, or blocking — does the granted authority match the stakes?
   Not everything deserves blocking; almost nothing critical should be
   advisory-only.
4. **Enforceable where claimed?** Can this surface actually deliver the
   enforcement level it presents? A rule is an instruction with privileged
   visibility, not a guarantee; client-side git hooks are skippable; harness
   deny-hooks have documented ignore bugs. The only true trust boundary is a
   gate outside the agent harness.
5. **Duplicated across surfaces?** Does the same obligation, procedure, or
   data live in two places that can evolve independently? Cross-referencing
   with shared vocabulary is fine; parallel authoritative copies are not.
6. **Context cost proportionate to value?** What does this mechanism consume
   every session versus what it delivers? Always-on prose pays rent
   continuously; every obligation in every always-on rule competes with every
   other for attention.

## Surface-responsibility table

One row per surface class from the concepts.md catalog. The middle columns
are the placement test; the last column is what to look for when auditing.

| Class | Should own | Must not own | Misplacement smells |
|---|---|---|---|
| **Normative in-context** (rules, orientation docs, memories) | Obligations, prohibitions, applicability triggers, exceptions, evidence requirements — the law, stated tersely | Step-by-step procedure; enumerable data (paths, API lists, checklists); anything only needed occasionally | Rule length growing past a screen; worked examples in an always-on rule; agents quoting the rule but not following it |
| **Procedural on-demand** (skills, slash commands, templates) | Multi-step executable method — how to run the thing the law requires | The law itself (a skill nobody is obliged to invoke enforces nothing); state that must persist between runs | Procedure that must *always* apply but relies on invocation; skill restating its governing rule instead of pointing at it |
| **Deterministic executable** (CLIs, scripts, linters, tests-as-spec) | Deterministic computation, validation, evidence capture — checkable facts | Judgment calls; policy that changes faster than code | Prose checklists that could be a checker; a linter encoding a judgment nobody can evaluate; evidence asserted in prose that a script could record |
| **MCP tool-surface** | Schema-validated operations for shell-less clients, credential withholding, cross-project aggregation | Anything a CLI already covers where a shell exists (schema token cost; shell bypass is structural) | MCP as default rather than exception; duplicate MCP + CLI write paths |
| **Event & schedule** (hooks, automations, scheduled runs) | Detection and in-session feedback at the right moment | The trust boundary (deny decisions have been silently ignored); long procedures | Hook presented as the enforcement layer; scheduled job whose failure nobody notices |
| **Delegated judgment** (subagents, review lenses, cross-model review) | Independent semantic evaluation — is it substantively good | Deterministic checks (waste of a model); the implementer's own duties | Specialist agent disconnected from the implementer's loop; lens re-checking what a linter already enforces |
| **Platform & environment gates** (CI checks, branch protection, sandboxes) | Non-bypassable enforcement outside the agent harness — the only true trust boundary | Fast-feedback niceties better served in-session; judgment-shaped policy | A "required" check that can be skipped; the gate host misattributed (the pilot's F3 deferral conflated kit CI with target-repo CI — proposal §8) |
| **Human authority** (approval gates, flagged decisions) | Decisions explicitly reserved for people: intent, trade-offs, applying proposals | Volume triage a machine should pre-digest; decisions the human always rubber-stamps (that's a smell either way) | A gate that never says no (enforcement theater); humans flagged for decisions with an objectively correct answer |
| **Work-item system** (tracker: ACs, dependencies, lint) | Workflow substrate — the only surface that mechanically sequences daily work | Narrative context (that's docs/scratchpad); governing conventions | Plans tracked in ephemeral to-do tools; ACs duplicated into prose docs that drift |
| **Meta-surfaces** (distribution, measurement, overlays, persistence infra) | Governing the governing mechanisms: sync, scorecards, parameterization, memory | Direct project work; policy content of its own | Sync scripts whose output drifts from canon unnoticed; measurement that rewards the proxy, not the outcome |

Sidebar — **canonical specification**: introduce a prose spec only when
drift between projections is actually observed; use a machine-readable
profile when the convention is enumerable as data (see concepts.md for the
economics of each). Profiles carry data-shaped conventions; judgment-shaped
policy stays prose.

## Anti-patterns

- **Competing sources of truth.** Two artifacts each claiming to define the
  same convention, evolving independently. Fix by designating one canonical
  and demoting the rest to projections (generated, or cross-referencing with
  shared vocabulary — the pilot's O1–O17 obligation IDs appear identically
  in rule, skill, and lens so the layers agree by construction).
- **Advisory-presented-as-enforcement.** A convention that reads like a hard
  gate but is a rule the model can ignore, a client-side hook, or a
  devcontainer "boundary." State the real enforcement level, or move the
  claim to a surface that can deliver it.
- **Proxy metrics rewarding performative compliance.** A check that measures
  the ritual, not the outcome — tests that exist but prove nothing, a hook
  counting invocations. Prohibitions nobody semantically checks converge on
  ritual compliance; pair them with a delegated-judgment surface.
- **Always-on context bloat.** Enumerable facts or occasional-use content
  paying context cost every session while remaining unenforceable.
  Candidates for a skill (procedure), a profile + checker (data), or
  deletion.
- **Procedure at the policy address.** An always-on rule carrying the full
  operational playbook. The pilot's headline finding (F1): ~75% of the
  pragmatic-tdd rule was step-by-step procedure needed only when a
  qualifying bead was in flight — split into thin rule (law) + skill
  (procedure), with the obligations checklist proving content-neutrality.
- **Enforcement theater.** A gate that doesn't gate: an approval step that
  never says no, a required check that can be bypassed, a review lens whose
  findings are never triaged. Either give the gate real teeth and real
  challenges (the pilot's approval gate reversed a deferral — that is a gate
  working) or stop paying its ceremony cost.
