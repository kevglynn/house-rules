# AGENTS.md

Any agent landing in this repo: start here.

## About this repo

This is **house-rules** (incubated under the working name process-kit) — the canonical source for AI coding agent rules, skills, checker CLIs, and distribution scripts. It distributes governance to project repos via sync scripts. The canonical clone path is `~/house-rules`; any path works, because `install-aliases.sh` pins the `PROCESS_KIT` env var to the actual clone root and the scripts resolve their own location. The env var, the `process-kit-*` bead-ID prefix, and the unset-var fallback path in agent-facing commands (`${PROCESS_KIT:-$HOME/process-kit}`) keep their historical names.

**This is the source repo, not a target repo.** Do not run `house-rules init` here. To work on the kit itself:

- Rules are canonical in `cursor/rules/*.mdc` — edit there, then run `./scripts/house-rules sync --format claude --local` to regenerate `claude/rules/*.md`
- Skills live in `skills/<name>/SKILL.md` — see `skills/README.md` for the format and contribution checklist
- Core-tier membership is declared in `profiles/core-manifest.list` — a listed rule or skill must stay free of bd/beads references (enforced in kit CI by `scripts/tests/test_core_manifest.py`)
- The kit ships no hook files of its own — the old `.claude/hooks/` layer was retired (process-kit-amq). `house-rules init` installs **beads** git hooks in target repos via `bd hooks install`
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
bash ~/house-rules/scripts/house-rules init --tool cursor
# (or --tool claude / --tool both)

# Verify setup
bash ~/house-rules/scripts/house-rules doctor

# Sync rules after kit updates
bash ~/house-rules/scripts/house-rules sync --format all
```
