# Brand Cohesion Rename (playbook → house-rules tooling)

**Date:** 2026-08-06
**Beads:** epic + 6 children (IDs recorded in the epic after `bd create --graph`)
**Status:** Approved
**Decision record:** [docs/decisions/0002-brand-cohesion-tooling-rename.md](../decisions/0002-brand-cohesion-tooling-rename.md)

## Architecture and component overview

One new component, three renamed ones, and a sweep:

- **`scripts/house-rules`** (new): thin bash dispatcher, the sole documented entry point. `init` → `scripts/init.sh`, `doctor` → `scripts/doctor.sh`, `sync` → `scripts/sync-rules.sh`; `help`/no-args prints usage. No logic of its own beyond dispatch — the implementation scripts remain independently runnable.
- **`scripts/init.sh`, `scripts/doctor.sh`** (renamed via `git mv` from `playbook-init.sh` / `playbook-doctor.sh`): content updated for the new dotfile names, `KIT_ROOT` internal variable (was `PLAYBOOK_ROOT`, never env-honored), lock dir `.house-rules-init.lock`, and self-referencing fix strings.
- **`scripts/install-aliases.sh`**: renders `hr` and `house-rules` aliases into `~/.house-rules-aliases.sh`; the rc block gains a content-aware update path (replace-when-stale on current markers — restores, in current-marker form, the capability retired with legacy migration in process-kit-26b).
- **Renderers**: init's AGENTS.md section and the `global-safety-net/*.md` block sources emit dispatcher-form commands only; heading becomes `## house-rules`. Known staleness fixed in passing: the nonexistent `--source-root` doctor flag claim in session-start, and sync-rules' two-generations-old `~/.cursor-sync-targets` migration hint.

## Data flow and key interfaces

- Invocation: `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" <init|doctor|sync> [args]`; interactive sugar `hr <subcommand>`.
- Machine state: `~/.house-rules-sync-targets` (read by sync/doctor, written by init registration), `~/.house-rules-aliases.sh` (written by install-aliases, sourced by the rc block), `~/.house-rules-ignore` (documented, read by the session-start protocol).
- Unchanged interfaces: doctor's exit codes and `SUMMARY:` keys, the `house-rules:` marker grammar, `PROCESS_KIT` env var, distributed-CLI manifest and drift keys, the conventions profile.
- Rendered artifacts (target AGENTS.md sections, `~/CLAUDE.md` blocks) regenerate from the updated sources during the field pass; content changes, block/section marker IDs do not.

## Trade-offs and decisions

Recorded with rationale in decision record 0002: single dispatcher over per-script or short-prefix names (A1); clean break over shims (A2); historical identity (`PROCESS_KIT`, clone path, bead prefix) untouched (A3); dated records and the generic `graybeard-playbook` name exempt from the sweep (A4); one coordinated v0.3.0 cut (A5).

## Non-goals

- No `HOUSE_RULES` env var, no clone-path change, no bead-prefix change (A3).
- No rewriting of dated records (A4).
- No legacy-name recognition (`playbook-*` filenames, old dotfiles) in code (A2).
- No change to doctor exit codes, SUMMARY keys, marker grammar, or the distribution manifest.

## Risks and open questions

- [x] Fixture suites hardcode `$INIT`/`$DOCTOR` script paths — updated in the same bead as the rename, CI proves it (the b3m/4ma gates now actually run on pushed commits).
- [x] Target AGENTS.md sections and `~/CLAUDE.md` blocks briefly reference old names between the kit cut and the field pass — mitigated by executing both in one session; the doctor stamp check flags any straggler.
- [ ] Machines other than the reference machine keep orphaned `~/.playbook-*` dotfiles until their installers re-run (accepted, decision 0002 consequences).
