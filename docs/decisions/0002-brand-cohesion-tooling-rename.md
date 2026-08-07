# 0002 — Brand cohesion: retire "playbook" tooling names

**Date:** 2026-08-06
**Status:** Decided
**Extends:** [0001 — naming, license, publication posture](0001-naming-license-publication.md)

## Context

0001 settled the kit's name (**house-rules**) and the `graybeard-*` skill-family rename, but the tooling layer still speaks a third brand: `playbook-init.sh`, `playbook-doctor.sh`, `pbi`/`pbd` aliases, `~/.playbook-sync-targets`, `~/.playbook-aliases.sh`, "the playbook" throughout active docs, and the rendered artifacts (target AGENTS.md sections, `~/CLAUDE.md` blocks) that teach agents all of it. Post-v0.2.0 the brand stack read: repo = house-rules, tools = playbook-\*, env = `PROCESS_KIT`, path = `~/process-kit` — sprawling and inconsistent, as the owner put it.

An inventory (2026-08-06) found "playbook" on 463 lines across 66 kit files, plus two machine dotfiles, 17 lines of `~/CLAUDE.md` block content, and ~4 references in each of the 15 sync targets' AGENTS.md sections.

## Decisions (A1–A5)

**A1 — Single dispatcher.** The kit's tooling gets one entry point: `scripts/house-rules` with subcommands `init | doctor | sync`, aliased `hr` (no collision on the reference machine). The implementation scripts become `scripts/init.sh` and `scripts/doctor.sh` (internal names behind the dispatcher; `sync-rules.sh` keeps its neutral name). Documented invocation form everywhere: `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" doctor --agent`.

*Rejected:* per-script rename (`house-rules-init.sh`, …) — still sprawls, N names instead of one; short prefix (`hr-init.sh`) — cryptic in docs, "hr" alone carries HR-department ambiguity in prose.

**A2 — Machine-state renames, clean break.** `~/.playbook-sync-targets` → `~/.house-rules-sync-targets`; `~/.playbook-aliases.sh` → `~/.house-rules-aliases.sh`; the documented ignore file `~/.playbook-ignore` → `~/.house-rules-ignore`; the init lock `.playbook-init.lock` → `.house-rules-init.lock`; internal shell variable `PLAYBOOK_ROOT` → `KIT_ROOT` (never env-honored, so no interface change). No legacy-name recognition ships in code — the audience is one maintainer plus agents, the field is re-rendered in the same cut, and 0em/26b just demonstrated what a lingering compatibility window costs. Old dotfiles are `mv`ed during the field pass.

*Rejected:* forwarding shims for one release — recreates the migration-machinery debt class retired hours earlier by process-kit-26b, for an audience that doesn't need it.

**A3 — Historical identity stays.** `PROCESS_KIT` env var, the `~/process-kit` clone path, and the `process-kit-*` bead-ID prefix keep their names, as decided at the v0.2.0 cut and documented in AGENTS.md/PLAN.md. The env var and redirected GitHub URL make the directory name immaterial; the bead prefix is an immutable historical record.

**A4 — Historical records are exempt.** CHANGELOG, `docs/decisions/`, `docs/refinements/`, `docs/research/`, `docs/releases/`, dated specs in `docs/specs/`, and `.beads/interactions.jsonl` keep "playbook" as historical fact — rewriting dated records falsifies history. `graybeard-playbook` also keeps its name: "playbook" there is the generic noun (it *is* a playbook), not the tooling brand.

**A5 — One coordinated cut, released as v0.3.0.** All renames, the renderer updates, the docs sweep, and the field re-render land in one wave and ship as v0.3.0, so no artifact generation exists that mixes the two tooling brands.

## Consequences

- Everything user- and agent-facing says **house-rules** (or the neutral `PROCESS_KIT`/`~/process-kit` documented as historical); "playbook" survives only in dated records and the graybeard rule's generic usage.
- Machines other than the reference machine that ran the old installers would keep orphaned `~/.playbook-*` dotfiles; re-running the installers creates the new-name artifacts and the old ones become inert (no reader remains). Accepted for an audience of one machine.
- The rc-block installer regains a content-aware update path (replace-when-stale keyed on current markers) — required to swap the sourced filename, and a durable improvement over the presence-only check.
