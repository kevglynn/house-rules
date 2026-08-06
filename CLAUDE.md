# CLAUDE.md

## Kit Rules

This repo's governance rules are in `.claude/rules/*.md` (auto-loaded by Claude Code; symlinked to the generated `claude/rules/`). They define:

- **beads-quality** — bead structure: What/Where/How/Why, acceptance criteria, non-goals
- **bead-completion** — evidence policy for closing beads (AC mapping, commit refs)
- **pragmatic-tdd** — test-first by bead type (bugs: reproduce first; features: ACs become tests)
- **operating-model** — Planner/Executor roles, scratchpad protocol
- **agent-identity** — no human-baseline estimation (no time units, team sizes, schedules)
- **multi-agent-review** — two-tier review protocol for structural changes
- **design-docs** — when and how to write design documents
- **worktree-awareness** — git worktree conventions
- **parallel-subagent-safety** — no foreground edits to files in a running subagent's blast radius
- **session-lifecycle** — mandatory session start/close protocol
- **defer-convention** — deliberate simplifications need a ceiling + upgrade trigger
- **graybeard-playbook** — minimal, correct code; stdlib/native/reuse before new

**These rules are not optional.** When creating beads, closing beads, writing tests, or planning work, follow the standards in `.claude/rules/`. If unsure, read the relevant rule file before proceeding.

## Working on the kit

This is the source repo, not a target repo — do not run `playbook-init.sh` here. Edit `cursor/rules/*.mdc` (canonical), then regenerate the Claude format with `./scripts/sync-rules.sh --format claude --local`. See AGENTS.md for the full source-repo conventions.
