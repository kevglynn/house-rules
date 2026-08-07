# AGENTS.md

Any agent landing in this repo: start here.

## About this repo

This is **house-rules** (incubated under the working name process-kit) — the canonical source for AI coding agent rules, skills, hooks, and scripts. It distributes governance to project repos via sync scripts. The `PROCESS_KIT` env var, the `process-kit-*` bead-ID prefix, and the default clone path `~/process-kit` keep their historical names — the env var and redirected GitHub URL make the directory name immaterial.

**This is the source repo, not a target repo.** Do not run `house-rules init` here. To work on the kit itself:

- Rules are canonical in `cursor/rules/*.mdc` — edit there, then run `./scripts/house-rules sync --format claude --local` to regenerate `claude/rules/*.md`
- Skills live in `skills/<name>/SKILL.md` — see `skills/README.md` for the format and contribution checklist
- Hooks are in `.claude/hooks/` — these distribute to target repos via `house-rules init`
- Scripts are in `scripts/` — see README.md for the full inventory
- Global safety-net block sources are in `global-safety-net/*.md` — installed per-machine by `install-global-safety-net.sh`
- This repo wires an IDE `postCreate` hook in `.cursor/worktrees.json` that runs its local `scripts/setup-worktree.sh` on worktree creation. That script is **not** distributed by `house-rules init` — do not expect it in target repos (source-repo convention; relocated here from `worktree-awareness.mdc` to keep the distributed rule project-neutral)

## Identity conventions

- The kit name (**house-rules**), license (Apache-2.0), and publication posture (public, history as-is) were decided 2026-08-05 — recorded with rationale in `docs/decisions/0001-naming-license-publication.md`.
- Skill and rule content must stay **project-neutral**: no project names, people, or project/user-specific parameters in the generic core. Project specifics belong in per-project overlay files in consuming repos; per-user parameters belong in the machine-global overlay (`~/.agents/overlay.md`) — both scopes documented in `skills/README.md`.
- Marker strings in installers use the `house-rules:` prefix (final name, 0001 A1). Recognition of the predecessor's legacy `ai-dev-playbook:` markers was sunset 2026-08-06 (process-kit-26b) after a field sweep across every sync target and HOME artifact showed zero old-marker artifacts remaining; the malformed-marker guards stayed — they protect current-marker files too.

## For bootstrapping target repos

```bash
# One-command setup for a target project
bash ~/process-kit/scripts/house-rules init --tool cursor|claude|both

# Verify setup
bash ~/process-kit/scripts/house-rules doctor

# Sync rules after kit updates
bash ~/process-kit/scripts/house-rules sync --format all
```
