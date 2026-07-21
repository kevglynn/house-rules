# Bead Quality Standards

Every bead must be self-contained — a developer picking it up cold, without scratchpad or chat history, should have everything needed to understand, implement, and verify the work.

**Authoring procedure lives in the `skills/bead-authoring` skill** (worked `bd create` examples, dedupe search, validation mechanics, wisps). This rule states the standards; the skill is how you meet them.

## Required in every bead

### Description (`--description`)

- **What** the problem or feature is (not just the title restated)
- **Where** in the codebase it applies (files, modules, or components)
- **How** to approach the implementation (concrete steps, not vague direction)
- **Why** it matters (context on the motivation or user impact)

### Acceptance Criteria (`--acceptance`)

Required for **bug**, **feature**, **task**, **story**, and **spike** beads. Epics require **Success Criteria** instead. Use `bd create --acceptance "..."`.

| Type | Section name | What to specify |
|------|-------------|-----------------|
| bug | Acceptance Criteria | The fixed behavior |
| feature/task/story | Acceptance Criteria | Observable outcomes |
| spike | Acceptance Criteria | Questions to answer, timebox |
| epic | Success Criteria | Conditions for closing the epic |
| chore/decision/milestone | — | ACs optional |

Bullet points using behavioral language (should/shows/returns/renders), describing **observable outcomes**, not implementation steps. "Loading indicator appears" is an AC. "Add isLoading state variable" is not.

### Non-goals (recommended for feature beads)

Add a "Non-goals:" line in the description to prevent agent scope creep. State what this bead is explicitly NOT doing.

## Before creating a bead

Search first (`bd search "<topic>"`, `bd list --status=open`) and prefer extending, parenting, or depending on an existing bead over duplicating it. If the beads DB isn't running (cold start, broken redirect) or these are a new project's first beads, proceed without search and run `bd doctor` afterward (embedded-mode substitutes per `session-lifecycle.md` § Extended close). Validate with `bd lint` / `bd create --dry-run` (mechanics: the skill).

## Structure

Parent-child hierarchy and dependency-graph mechanics (`--parent`, `bd dep add`, `bd create --graph`) are owned by `skills/graph-planning` (Phase 2). Ephemeral wisps (`--ephemeral`, TTL compaction, `bd promote`): the bead-authoring skill.

## Anti-patterns

1. **Bead explosion.** 8+ beads for work that could be 3; a bead whose only AC is "file X exists" is too small — fold it into a sibling.
2. **Graph-free multi-bead planning.** 4+ beads with no dependency structure; more than 3 beads MUST be wired with `bd dep add` or `bd create --graph`.
3. **Stale accumulation.** A bead untouched for a week gets deferred, closed as won't-do, or reprioritized — `bd stale` catches these.
4. **Duplicate creation.** Creating a new bead without checking `bd search` first.
5. **Orphaned in-progress.** Claiming a bead and ending the session without closing it or leaving `bd note <id> "Progress: ..."`.
6. **Evidence-free closes.** `bd close --reason "Done"` with no AC mapping; "will be verified later" is an IOU, not evidence — see `bead-completion.md` § "Do not defer AC verification" for the four legitimate options.
7. **AC as implementation steps.** ACs describe observable outcomes ("Loading indicator appears when switching tabs"), not steps ("Add isLoading state variable").

## When closing beads

Close-side law — the evidence policy by bead type, the do-not-defer invariant, and the commit/branch/PR reference requirement — lives in `bead-completion.md`. Close-reason format and worked examples: the bead-authoring skill.
