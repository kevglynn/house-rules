---
name: bead-authoring
description: Single-bead lifecycle playbook — authoring worked examples (bd create with description/ACs/non-goals), dedupe search, validation mechanics (bd lint / --dry-run), wisps, JIT verification on pickup, progress notes, self-review before close, close-reason format with examples, and the bd remember when/when-not manual. Trigger phrases: "bead authoring", "write this bead", "draft the bd create", "picking up a bead", "close this bead", "close reason", "should I remember this".
---

# Bead Authoring

The procedure for the single-bead lifecycle: writing a bead worth picking up cold, verifying it on pickup, and closing it with evidence. The always-on rules state the law — `beads-quality.mdc` owns the authoring standards (self-containment, What/Where/How/Why, AC-by-type), `bead-completion.mdc` owns the close-side law (AC ownership, evidence policy, the do-not-defer invariant, the memory litmus test). This skill is how you meet them.

The B-IDs below are shared with the split's obligations checklist in the kit repo.

This skill reads no overlay keys — the procedure is identical in every project.

## When to Use This Skill

- Creating a bead and you want the worked example, validation mechanics, or wisp mechanics
- Picking up a bead (the JIT-verification question list)
- Closing a bead (the self-review pass, close-reason format and examples)
- Deciding whether to `bd remember` after a close

**Skip when:** the breakdown is 3+ beads needing a dependency graph — that is `skills/graph-planning`'s domain (this skill covers one bead at a time; graph-planning Phase 2 is the canonical home for parent-child and `--graph` mechanics). Test discipline by bead type is `pragmatic-tdd.mdc` + its skill. What counts as evidence and who owns ACs is rule law, not procedure — this skill never overrides `bead-completion.mdc`.

## Core Process

### Phase 1 — Before creating: dedupe search (B1)

Check that the work doesn't already have a bead (`beads-quality.mdc` anti-pattern 4 is the law here):

```bash
bd search "loading indicator"     # text search for related beads
bd list --status=open             # scan open beads for overlap
```

If a related bead exists, consider: should this be a child of that bead (`--parent`), a dependency (`bd dep add`), or an update to the existing bead's description?

**When to skip the search:** if the beads DB isn't running (cold start, broken redirect) or you're creating the first beads on a new project, proceed without search and run `bd doctor` afterward (embedded-mode substitutes per `session-lifecycle.mdc` § Extended close).

### Phase 2 — Author the bead (B2)

Apply `beads-quality.mdc`'s standards: What/Where/How/Why description, ACs as observable outcomes, a Non-goals line. Worked example:

```bash
# BAD — no ACs, no non-goals, description restates title
bd create "Fix loading state" -t bug -p 1

# GOOD — self-contained with ACs and non-goals
bd create "Add loading indicators to beads-ui tab switching" \
  --description="When switching tabs in beads-ui, the UI shows 'No issues' while data loads — indistinguishable from an empty workspace. Track subscription state in subscription-issue-store. Render spinner while loading. Files: src/client/subscription-issue-store.js, src/client/views/*.js. Non-goals: not changing the subscription protocol or server-side caching in this bead." \
  --acceptance="Switching to an unloaded tab shows a loading indicator, not 'No issues'. Tab with zero real issues still shows 'No issues' after load completes. Loading indicator disappears within 1s of data arriving." \
  -t feature -p 1
```

### Phase 3 — Validate (B3)

- `bd create --dry-run` to preview before creating
- `bd lint` to check open beads for missing required sections
- `bd config set validation.on-create warn` enables auto-validation at creation time

### Phase 4 — Structure: hierarchy and wisps (B4)

**Parent-child and dependency-graph mechanics** (`--parent`, hierarchical IDs, `bd dep add` vs containment, `bd create --graph`) are owned by `skills/graph-planning` Phase 2 — go there; they are not restated here.

**Ephemeral issues (wisps):** use `--ephemeral` for short-lived tracking that doesn't warrant permanent storage — agent heartbeats, exploratory investigation notes, temporary coordination signals. Wisps are subject to TTL compaction and excluded from exports. To promote a wisp to a permanent bead: `bd promote <wisp-id> --reason "..."`.

### Phase 5 — Pick up: JIT verification (B5)

Before writing any code, check what you're working on (`bd show --current`) and verify the bead's description against reality:

- Do the files and paths mentioned still exist?
- Do the APIs, interfaces, or patterns described still match the current codebase?
- Has anything changed since the bead was created that affects the approach?

If reality doesn't match: update the implementation approach, note the discrepancy, and proceed. **Never modify the acceptance criteria** — AC ownership is `bead-completion.mdc` law; a wrong or impossible AC means blocking the bead and escalating to the Planner.

### Phase 6 — During work: progress tracking (B6)

Use `bd note <id> "progress update"` to append implementation notes to the bead's notes field (persistent, visible in `bd show`). Use `bd comment <id> "observation"` for timestamped discussion entries. Notes record decisions; comments record conversation. This keeps context attached to the work item rather than only in the scratchpad.

### Phase 7 — Close: self-review, then evidence (B7, B8)

**Self-review pass (B7)** — the same agent that did the work, not a separate reviewer; a deliberate pause to check the work against the spec:

1. Re-read each acceptance criterion from the bead (`bd show <id>`)
2. For each AC, verify it is satisfied by the code as written
3. If any AC is not met, fix it or escalate — do not declare done

**Close reason (B8)** — evidence mapped to ACs, with a commit hash, branch name, or PR URL (the policy, per-type table, and do-not-defer invariant are `bead-completion.mdc` law):

```bash
# BAD — vague
bd close gastown-abc --reason "Done"

# GOOD — evidence mapped to ACs
bd close gastown-abc --reason "Commit a1b2c3f on feature/loading-ux. AC1: spinner renders on tab switch (verified manually). AC2: empty state shows after load (test_empty_tab passes). AC3: spinner gone <1s (verified manually)."
```

Continuation flags: `bd close ... --suggest-next` (show newly unblocked issues) or `--claim-next` (auto-claim the next highest-priority ready issue).

### Phase 8 — After close: knowledge capture (B9)

`bead-completion.mdc` owns the litmus test (would a fresh agent waste significant time or make a wrong assumption without this?). This phase is the manual for applying it. Most bead closures produce **no memory** — this step is for the exceptions.

```bash
bd remember "AccountService.sync silently skips soft-deleted records — \
  the WHERE clause in account_repo.rb:47 filters them with no error" \
  --key account-sync-soft-deletes
```

**When to remember:**

- A fix that required non-obvious investigation (the root cause wasn't where you first looked)
- A codebase pattern not apparent from reading the code ("module X is called by a background job, not the controller")
- A corrected assumption — something you got wrong that cost investigation time
- A library/config quirk or environment-specific behavior not in docs
- A misleading error message where the real cause was different from what the error suggested

**When NOT to remember:**

- Task-specific progress notes (that's the scratchpad)
- Anything already codified in the project's agent rules
- Obvious facts derivable from the code or docs
- Temporary workarounds (create a follow-up bead instead)
- Performance numbers or benchmarks (too volatile)
- Speculative improvements ("this could be refactored to use X")

**Key discipline:**

- Always use `--key` with a descriptive kebab-case identifier (`<area>-<topic>`) — enables deduplication and future pruning; never rely on auto-generated keys from content
- Check before creating: `bd memories <keyword>` to search for existing memories on the topic; update with `bd remember --key <existing-key> "corrected info"` rather than creating a parallel entry
- One memory per bead, max — capturing more than two means the bead was too large or you're recording progress notes

Staleness handling (a memory contradicts the codebase) is `bead-completion.mdc` law: update or remove immediately, never work around silently.

## Anti-Patterns

The seven bead anti-patterns are `beads-quality.mdc` law (cited by number below); these are the procedural failure modes this skill prevents:

| Anti-Pattern | Why It Fails | Better Approach |
|--------------|-------------|-----------------|
| Skipping the dedupe search | Two beads tracking the same work confuse agents and users (`beads-quality.mdc` anti-pattern 4) | Phase 1 before every create |
| Title-restating description | The bead is not self-contained; the next agent re-derives everything | Phase 2's worked example — What/Where/How/Why |
| Coding before JIT verification | The bead's described approach may no longer match the codebase; work lands in the wrong place | Phase 5's question list before the first edit |
| "Done" close reasons | Evidence-free closes (`beads-quality.mdc` anti-pattern 6) are indistinguishable from unverified work | Phase 7's format: commit ref + per-AC evidence |
| Remembering progress notes | Memory pollution — task-specific context outlives its usefulness (`bd note` is the right home) | Phase 8's when-NOT list; apply the litmus test |
| Keyless memories | Auto-generated keys defeat deduplication and pruning | Always `--key <area>-<topic>` |
