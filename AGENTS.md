# AGENTS.md

Any agent landing in this repo: start here.

## About this repo

This is **process-kit** (working name) — the canonical source for AI coding agent rules, skills, hooks, and scripts. It distributes governance to project repos via sync scripts.

**This is the source repo, not a target repo.** Do not run `playbook-init.sh` here. To work on the kit itself:

- Rules are canonical in `cursor/rules/*.mdc` — edit there, then run `./scripts/sync-rules.sh --format claude --local` to regenerate `claude/rules/*.md`
- Skills live in `skills/<name>/SKILL.md` — see `skills/README.md` for the format and contribution checklist
- Hooks are in `.claude/hooks/` — these distribute to target repos via `playbook-init.sh`
- Scripts are in `scripts/` — see README.md for the full inventory
- Global safety-net block sources are in `global-safety-net/*.md` — installed per-machine by `install-global-safety-net.sh`
- This repo wires an IDE `postCreate` hook in `.cursor/worktrees.json` that runs its local `scripts/setup-worktree.sh` on worktree creation. That script is **not** distributed by `playbook-init.sh` — do not expect it in target repos (source-repo convention; relocated here from `worktree-awareness.mdc` to keep the distributed rule project-neutral)

## Identity conventions

- The kit name is a **working name**; the final name, license, and publication posture are open decisions tracked in [PLAN.md](PLAN.md).
- Skill and rule content must stay **project-neutral**: no project names, people, or project/user-specific parameters in the generic core. Project specifics belong in per-project overlay files in consuming repos; per-user parameters belong in the machine-global overlay (`~/.agents/overlay.md`) — both scopes documented in `skills/README.md`.
- Marker strings in installers use the `house-rules:` prefix (final name, 0001 A1). The installers still recognize the legacy `ai-dev-playbook:` markers written by the predecessor repo and rewrite those blocks in place under the new prefix on their next run — a one-shot migration, no duplicate blocks. Do not remove the legacy-recognition patterns while any machine or target repo still carries old-marker artifacts.

## For bootstrapping target repos

```bash
# One-command setup for a target project
bash ~/process-kit/scripts/playbook-init.sh --tool cursor|claude|both

# Verify setup
bash ~/process-kit/scripts/playbook-doctor.sh

# Sync rules after kit updates
bash ~/process-kit/scripts/sync-rules.sh --format all
```
