# Shared Skills Library

Curated agent skills that work with any project bootstrapped by this kit. Each skill teaches an agent a structured approach to a recurring task. Rules state *what must happen*; skills encode *how to run it*.

## Available Skills

| Skill | Purpose | Triggers |
|-------|---------|----------|
| [brainstorming](brainstorming/SKILL.md) | Explore WHAT to build before HOW | "let's brainstorm", ambiguous feature requests, multiple valid approaches |
| [systematic-debugging](systematic-debugging/SKILL.md) | Hypothesis-driven bug investigation | "debug this", "why is this broken", unexpected failures, failed fix attempts |
| [council](council/SKILL.md) | Parallel multi-model analysis: diverse AI voices examine one task, synthesized into a briefing | "convene a council", "get perspectives", "diverse review" |
| [workspace-kickoff](workspace-kickoff/SKILL.md) | Orient in a new or resumed workspace: read orientation files, report, wait for direction | "start this workspace", "pick up where we left off", "begin session" |
| [graybeard-help](graybeard-help/SKILL.md) | Index for the graybeard family: which skill or rule fits the task | "use graybeard", "graybeard help", unsure which graybeard skill applies |
| [graybeard-review](graybeard-review/SKILL.md) | Simplification review of a diff or file set | "graybeard review", over-engineering suspicion on a change |
| [graybeard-audit](graybeard-audit/SKILL.md) | Repo-wide over-engineering scan: dead code, stdlib replacements, YAGNI | "graybeard audit", periodic hygiene pass |
| [graybeard-debt](graybeard-debt/SKILL.md) | Harvest `defer:` comments and flag rotting deferrals | "graybeard debt", defer-ledger review |
| [pragmatic-tdd](pragmatic-tdd/SKILL.md) | Per-bead-type TDD playbooks: bug/feature/story/refactor steps, red-proof ceremony, zero-signal taxonomy | "pragmatic tdd", starting a bug/feature/refactor bead, "write the failing test", "red-proof" |
| [tier1-review](tier1-review/SKILL.md) | Multi-lens same-model review (roster owned by the skill): parallel dispatch, triage table, fix commits, close evidence | "tier 1 review", "multi-lens review", feature/refactor bead reaches self-review-done |
| [tier2-handoff](tier2-handoff/SKILL.md) | Cross-model review handoff: deterministic prompt assembler (`assemble.py`), response triage, close evidence | "tier 2 review", "cross-model review", "assemble the review prompt" |
| [packet](packet/SKILL.md) | Gate/sprint packet authoring: committed blueprint template + `render.py` (self-contained HTML share + headless blueprint/anchor verify) | "build the packet", "gate packet", "sprint packet" |
| [packet-deepdive](packet-deepdive/SKILL.md) | Four-lane packet validation (accuracy/cold-read/receipts/structure) + convergence, orchestrator-wrapped, with a resilience protocol and dispositions report | "deep-dive the packet", "validate the packet", "cold-read the gate packet" |
| [refinement](refinement/SKILL.md) | Evidence-grounded audit of intent/plan/execution/mechanisms producing a classified refinement proposal; includes retrospective mode and mechanism-placement audits | "run a refinement", "refine this epic/plan/rule", "is this still the right shape", "mechanism placement audit", "retro on this capability" |
| [graph-planning](graph-planning/SKILL.md) | Planner playbook for multi-bead breakdowns: decomposition heuristics, `bd create --graph`, graph verification, mid-flight epic management | "plan this epic", "break down this initiative", "graph planning", a breakdown reaching 3+ beads |
| [bead-authoring](bead-authoring/SKILL.md) | Single-bead lifecycle playbook: authoring worked examples, dedupe search, validation mechanics, wisps, JIT verification, self-review, close-reason format, the `bd remember` when/when-not manual | "write this bead", "draft the bd create", "close this bead", "should I remember this" |

## Overlay Convention

Skills that need project-specific parameters (model assignments, reader
rosters, paths, extra focus areas) read them from **one file in the
consuming repo: `.agents/overlay.md`**, with one `## <skill-name>` section
per skill. Skill cores never name a project, a person, or a project-specific
parameter; each skill documents the overlay keys it reads and behaves
sensibly when the file or its section is absent. Do not invent per-skill
overlay files — if the single-file convention stops fitting, change the
convention here, not in one skill.

Per-user parameters (voice fingerprints, personal reader personas —
anything that follows the user across projects rather than belonging to one
repo) live in a **machine-global overlay: `~/.agents/overlay.md`**, same
format, one `## <skill-name>` section per skill. A skill that reads
per-user keys checks both files; the per-project file wins for any key both
define, and both files are optional. Conflict resolution is replace, not
merge, unless a skill's key table documents additive behavior for a
roster-shaped key.

### Overlay vs. profile — the two-surface placement law

A bootstrapped repo can carry two config-like surfaces with opposite
ownership rules, and a cold agent must be able to tell them apart. The
**overlay** (`.agents/overlay.md`, plus the machine-global
`~/.agents/overlay.md`) is project/user-owned, agent-read, markdown:
judgment-shaped parameters that skills consume, meant to be edited in the
consuming repo. The **profile** (`profiles/conventions.toml`) is kit-owned,
tool-read, TOML: data-shaped conventions consumed by deterministic checkers
and renderers, drift-checked byte-for-byte by `playbook-doctor.sh` — never
edited in a consuming repo (change it in the kit, then sync).

Promotion trigger: the first deterministic tool that needs an overlay key
graduates that key to a fenced TOML block inside `.agents/overlay.md` — the
single-file convention is preserved and the block is parsed with stdlib
`tomllib`. Until that trigger fires, overlay content stays prose.

Rejected alternative (decision, 2026-08-05): a `[project]` section inside
the distributed profile. Three reasons: no deterministic overlay consumer
exists today (the skill-embedded CLIs do not parse overlay content); the
byte-for-byte drift check collides structurally with target-owned edits
(either every project edit flags as drift, or the gate learns region
exclusions and recreates the two-ownership boundary inside one file); and
judgment-shaped overlay prose (reviewer-lane guidance, voice notes) cannot
live in TOML, so the file could never actually be single.

## How to Use

### Cursor

Copy skills into a project during bootstrap:

```bash
bash ~/process-kit/scripts/playbook-init.sh --tool cursor --skills
```

Or reference one directly in a conversation:

```
Read ~/process-kit/skills/brainstorming/SKILL.md
```

### Claude Code

Skills in `~/.claude/skills/` are auto-discovered. To use a kit skill, symlink it:

```bash
ln -s ~/process-kit/skills/brainstorming ~/.claude/skills/brainstorming
```

Or reference it directly in a conversation by asking the agent to read the SKILL.md file.

## Contributing a Skill

### What makes a good shared skill

- **Universally applicable** — useful across most projects, not domain-specific
- **Generic core / overlay** — the SKILL.md never names a project, a person, or a project- or user-specific parameter; project specifics (rosters, model assignments, paths) live in the per-project overlay, user specifics (voice, personal reader personas) in the machine-global overlay (see the Overlay Convention above), and the skill documents the overlay keys it reads
- **Structured process** — teaches a repeatable method, not just tips
- **Beads-integrated** — works with the kit's beads workflow where relevant
- **Proven** — based on patterns that have demonstrably improved outcomes

### Skill format

Each skill lives in `skills/<skill-name>/SKILL.md` with this structure:

```markdown
---
name: skill-name
description: One-paragraph description including trigger phrases.
---

# Skill Name

[What this skill does — 1-2 sentences]

## When to Use This Skill
[Conditions that trigger this skill]

## Core Process
[The structured method, with clear phases/steps]

## Anti-Patterns
[Common mistakes this skill prevents]
```

Reference files (if needed) go in `skills/<skill-name>/` alongside the SKILL.md (see council's `voices.md`) or in `skills/<skill-name>/references/`.

### Submission checklist

- [ ] SKILL.md follows the format above
- [ ] Description includes trigger phrases
- [ ] "When to Use" includes skip conditions (when NOT to use)
- [ ] Process is structured with clear phases
- [ ] Anti-patterns section exists — only when it names failure modes the core process doesn't already state; omit it rather than restate phases or cited rules
- [ ] No domain-specific assumptions (works for any project)
- [ ] No project names, people, or project/user-specific parameters in the core (overlay-ready, both scopes)
