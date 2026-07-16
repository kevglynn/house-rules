# Shared Skills Library

Curated agent skills that work with any project bootstrapped by this kit. Each skill teaches an agent a structured approach to a recurring task. Rules state *what must happen*; skills encode *how to run it*.

## Available Skills

| Skill | Purpose | Triggers |
|-------|---------|----------|
| [brainstorming](brainstorming/SKILL.md) | Explore WHAT to build before HOW | "let's brainstorm", ambiguous feature requests, multiple valid approaches |
| [systematic-debugging](systematic-debugging/SKILL.md) | Hypothesis-driven bug investigation | "debug this", "why is this broken", unexpected failures, failed fix attempts |
| [council](council/SKILL.md) | Parallel multi-model analysis: diverse AI voices examine one task, synthesized into a briefing | "convene a council", "get perspectives", "diverse review" |
| [workspace-kickoff](workspace-kickoff/SKILL.md) | Orient in a new or resumed workspace: read orientation files, report, wait for direction | "start this workspace", "pick up where we left off", "begin session" |
| [ponytail-help](ponytail-help/SKILL.md) | Entry point for the ponytail family — pick the right lens | "use ponytail", unsure which ponytail skill applies |
| [ponytail-review](ponytail-review/SKILL.md) | Simplification review of a diff or file set | "ponytail review", over-engineering suspicion on a change |
| [ponytail-audit](ponytail-audit/SKILL.md) | Repo-wide over-engineering scan: dead code, stdlib replacements, YAGNI | "ponytail audit", periodic hygiene pass |
| [ponytail-gain](ponytail-gain/SKILL.md) | Find high-leverage simplification wins | "ponytail gain", "what can we delete" |
| [ponytail-debt](ponytail-debt/SKILL.md) | Harvest `defer:` comments and flag rotting deferrals | "ponytail debt", defer-ledger review |

Process skills for review/validation/packet workflows (tier1-review, tier2-handoff, packet, packet-deepdive) are incubating — see [PLAN.md](../PLAN.md).

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
