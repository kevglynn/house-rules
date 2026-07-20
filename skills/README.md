# Shared Skills Library

Curated agent skills that work with any project bootstrapped by this kit. Each skill teaches an agent a structured approach to a recurring task. Rules state *what must happen*; skills encode *how to run it*.

## Available Skills

| Skill | Purpose | Triggers |
|-------|---------|----------|
| [brainstorming](brainstorming/SKILL.md) | Explore WHAT to build before HOW | "let's brainstorm", ambiguous feature requests, multiple valid approaches |
| [systematic-debugging](systematic-debugging/SKILL.md) | Hypothesis-driven bug investigation | "debug this", "why is this broken", unexpected failures, failed fix attempts |
| [council](council/SKILL.md) | Parallel multi-model analysis: diverse AI voices examine one task, synthesized into a briefing | "convene a council", "get perspectives", "diverse review" |
| [workspace-kickoff](workspace-kickoff/SKILL.md) | Orient in a new or resumed workspace: read orientation files, report, wait for direction | "start this workspace", "pick up where we left off", "begin session" |
| [ponytail-help](ponytail-help/SKILL.md) | Index for the ponytail family: which skill or rule fits the task | "use ponytail", "ponytail help", unsure which ponytail skill applies |
| [ponytail-review](ponytail-review/SKILL.md) | Simplification review of a diff or file set | "ponytail review", over-engineering suspicion on a change |
| [ponytail-audit](ponytail-audit/SKILL.md) | Repo-wide over-engineering scan: dead code, stdlib replacements, YAGNI | "ponytail audit", periodic hygiene pass |
| [ponytail-debt](ponytail-debt/SKILL.md) | Harvest `defer:` comments and flag rotting deferrals | "ponytail debt", defer-ledger review |
| [pragmatic-tdd](pragmatic-tdd/SKILL.md) | Per-bead-type TDD playbooks: bug/feature/story/refactor steps, red-proof ceremony, zero-signal taxonomy | "pragmatic tdd", starting a bug/feature/refactor bead, "write the failing test", "red-proof" |
| [tier1-review](tier1-review/SKILL.md) | Three-lens same-model review: parallel dispatch, triage table, fix commits, close evidence | "tier 1 review", "three-lens review", feature/refactor bead reaches self-review-done |
| [tier2-handoff](tier2-handoff/SKILL.md) | Cross-model review handoff: deterministic prompt assembler (`assemble.py`), response triage, close evidence | "tier 2 review", "cross-model review", "assemble the review prompt" |
| [packet](packet/SKILL.md) | Gate/sprint packet authoring: committed blueprint template + `render.py` (self-contained HTML share + headless blueprint/anchor verify) | "build the packet", "gate packet", "sprint packet" |
| [packet-deepdive](packet-deepdive/SKILL.md) | Four-lane packet validation (accuracy/cold-read/receipts/structure) + convergence, orchestrator-wrapped, with a resilience protocol and dispositions report | "deep-dive the packet", "validate the packet", "cold-read the gate packet" |
| [refinement](refinement/SKILL.md) | Evidence-grounded audit of intent/plan/execution/mechanisms producing a classified refinement proposal; includes retrospective mode and mechanism-placement audits | "run a refinement", "refine this epic/plan/rule", "is this still the right shape", "mechanism placement audit", "retro on this capability" |

## Project Overlay Convention

Skills that need project-specific parameters (model assignments, reader
rosters, paths, extra focus areas) read them from **one file in the
consuming repo: `.agents/overlay.md`**, with one `## <skill-name>` section
per skill. Skill cores never name a project, a person, or a project-specific
parameter; each skill documents the overlay keys it reads and behaves
sensibly when the file or its section is absent. Do not invent per-skill
overlay files — if the single-file convention stops fitting, change the
convention here, not in one skill.

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
- **Generic core / project overlay** — the SKILL.md never names a project, a person, or a project-specific parameter; project specifics (rosters, model assignments, paths) live in a per-project overlay file in the consuming repo, and the skill documents the overlay keys it reads
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
- [ ] Anti-patterns section exists
- [ ] No domain-specific assumptions (works for any project)
- [ ] No project names, people, or project-specific parameters in the core (overlay-ready)
