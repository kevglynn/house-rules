---
name: workspace-kickoff
description: >-
  Orients an agent in a new or resumed workspace by reading the canonical
  orientation files (CLAUDE.md, AGENTS.md, .cursor/scratchpad.md, and PLAN.md
  if present), summarizing what the workspace is for, current status, and the
  top blockers and next actions — then waiting for direction instead of
  executing. Use when the user says "start this workspace", "resume this
  workspace", "kick it off", "begin session", "pick up where we left off",
  "what is this workspace", or opens a scaffolded workspace for the first
  time in a session.
---

# Workspace Kickoff

## Purpose

Make the first turn of a session load-bearing. Read the orientation files,
produce a short situation report, and stop. Do not execute work until the
user confirms direction. This pattern relies on workspaces that follow the
scaffolding convention (CLAUDE.md, AGENTS.md, `.cursor/scratchpad.md`,
optional PLAN.md).

## The three-layer model

Scaffolded workspaces separate orientation across three files with
different update cadences. Respect the separation when summarizing —
don't blend them.

| Layer | File / System | Grain | Update cadence | What you pull from it |
|---|---|---|---|---|
| **Governing initiative** | `PLAN.md` | Goal, milestones, success criteria | Rarely — at milestone boundaries | "What is this workspace for; how far along are we at the milestone level" |
| **Tracked work** | beads (`bd ready`, `bd show <id>`) | Individual tasks with dependencies | Per task | "What's actually claimable right now" |
| **Working memory** | `.cursor/scratchpad.md` | In-flight item, blockers, decision log | Every session | "What's in progress this moment; what's gating us" |

`PLAN.md` may also be read by workspace tooling (e.g. an MCP plan
reader); treat it as structured metadata, not a to-do list. Beads are
the granular tasks that roll up to milestones. The scratchpad is a
session-level notebook — NEVER read it and think it's authoritative
for "what's next." Use `bd ready` for that.

## Steps

1. **Read the orientation files, in this priority order.** Some may be
   missing; that's fine, read what exists.

   | Priority | File / System | What it tells you |
   |---:|---|---|
   | 1 | `CLAUDE.md` or `AGENTS.md` | Working conventions, constraints, rules of the road |
   | 2 | `PLAN.md` | Goal, milestones, success criteria (coarse) |
   | 3 | `bd ready` (if `.beads/` exists) | Priority-sorted list of claimable tasks (fine-grained) |
   | 4 | `.cursor/scratchpad.md` | What's in flight, current blockers, decision log |
   | 5 | `README.md` | Human-facing summary (fallback only — the above are authoritative) |
   | 6 | `findings/` or equivalent | Latest artifacts from prior sessions |

2. **Produce a summary with this exact structure:**

   ```markdown
   ## Workspace: <name>
   **What it is:** <one sentence from PLAN.md goal or README>
   **Working mode / constraints:** <key rules from CLAUDE.md — e.g. learning-only, no PRs, beads-for-tracking>

   ## Where we are (per PLAN.md)
   <current milestone + one-line status>

   ## What's in flight (per scratchpad)
   <1–3 bullets: what's claimed/in-progress right now>

   ## Blockers
   <bullets — each with who/what unblocks it, and the beads ID if applicable. If none, say "none">

   ## Top 3 next actions (per `bd ready`, or scratchpad fallback)
   1. `<bead-id>` <title>
   2. `<bead-id>` <title>
   3. `<bead-id>` <title>

   ## Ready
   Waiting for your direction. Shall I proceed with #1, pick a different
   one, or do something else?
   ```

   If `.beads/` exists, run `bd ready` and use its output for the "Top 3."
   Do NOT invent a numbered list from scratchpad or PLAN — beads is the
   authoritative worklist. If `.beads/` doesn't exist, fall back to
   scratchpad's "Executor — next actions" section.

3. **Stop and wait.** Do not start executing any of the next actions, even
   if they look obviously correct. The human agrees or redirects before
   work begins.

## Fallback: workspace has no scaffolding

If none of CLAUDE.md, AGENTS.md, `.cursor/scratchpad.md`, or PLAN.md
exists, say so plainly and ask:

> This workspace doesn't have kickoff scaffolding yet (no CLAUDE.md,
> AGENTS.md, scratchpad, or PLAN.md). Want me to bootstrap them based
> on what's here, or would you rather tell me in chat what this
> workspace is?

Do not invent a summary from filesystem spelunking alone.

## Session etiquette the agent should honor

- **Start in planner mode.** The summary is the whole first turn. Don't
  drift into execution.
- **Update the scratchpad before ending.** Either the agent or the user
  rewrites `Executor — next actions` at session end so state carries
  forward. If the user says "done" or "stop" without updating, prompt
  them: *"Want me to update `.cursor/scratchpad.md` with today's progress
  before we stop?"*
- **Respect workspace-local rules over defaults.** If CLAUDE.md says
  learning-only, don't open PRs. If it says beads-for-tracking, don't
  use TodoWrite.

## Examples of correct kickoff output

### Example: a scaffolded investigation workspace

User prompt:
> Start this workspace.

Agent response (after reading PLAN.md + scratchpad + `bd ready`):

```markdown
## Workspace: ci-audit
**What it is:** Reduce wall-clock of the CI pipelines that gate customer releases.
**Working mode / constraints:** Learning-only — no PRs, no branches pushed to origin. Findings stay local.

## Where we are (per PLAN.md)
M1 (orientation) DONE. M2 (diagnose) IN PROGRESS. M3/M4 not started.

## What's in flight (per scratchpad)
- Nothing currently claimed. All M2 beads are ready.

## Blockers
- `ci-audit-r6d` — waiting on a conversation with the platform team about the LLM container deprecation. Gates the whole M2→M3 transition.

## Top 3 next actions (per `bd ready`)
1. `ci-audit-r6d` Message the platform team re: LLM container deprecation
2. `ci-audit-xpc` Inventory the main service's CI pipeline config end-to-end
3. `ci-audit-7ss` Attach real wall-clock timings from the CI provider's API

## Ready
Waiting for your direction. Shall I proceed with #1, pick a different one, or do something else?
```

### Example: a platform/tooling workspace

User prompt:
> Pick up where we left off.

Agent response:

```markdown
## Workspace: codebase-atlas
**What it is:** Progressive knowledge store and agent-ready CLI over the org's code-host workspace.
**Working mode / constraints:** Bash + jq + curl only. Scrapers idempotent. Views curated. `data/` gitignored.

## Where we are (per PLAN.md)
M1 (bootstrap) DONE. M2 (ship to the org remote) BLOCKED on token scopes. M3/M4 not started.

## What's in flight (per scratchpad)
- Nothing in-progress. First commit is local (0c50048), push gated on `atlas-le6`.

## Blockers
- `atlas-le6` — code-host API token lacks write scopes. Blocks `atlas-1dh` (create repo + push). Needs the token regenerated with repo-write scope and a keychain update.

## Top 3 next actions (per `bd ready`)
1. `atlas-le6` Regenerate the API token with write + pipeline scopes
2. `atlas-wf8` Author `skills/atlas-cli/SKILL.md` (ships with repo)
3. `atlas-v4g` `scrapers/sweep-pipeline-runs.sh` — unlocks real CI-audit timings

## Ready
Waiting for your direction.
```

## Anti-patterns

- **Don't execute on the first turn.** Even "obvious" next steps need
  human confirmation. The user might know something the scratchpad
  doesn't.
- **Don't rewrite the scratchpad, PLAN.md, or beads during summary.**
  Read them, report them. Updates happen at end-of-session or on
  explicit instruction.
- **Don't substitute filesystem exploration for reading orientation
  files.** If CLAUDE.md or PLAN.md exists, those are authoritative.
- **Don't invent a numbered to-do list from PLAN.md.** PLAN.md tracks
  milestones (M1, M2…), not next actions. If `.beads/` exists, use
  `bd ready` for the worklist.
- **Don't list more than 3–4 next actions.** Longer lists dilute focus.
- **Don't cite files verbatim.** Summarize. The user wrote them; they
  know what they say. Your value is compression and reprioritization.
