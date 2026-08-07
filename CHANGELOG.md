# Changelog

## 0.3.0 — 2026-08-07

Brand cohesion: the tooling layer stops speaking the retired "playbook" brand. One dispatcher, renamed machine state, re-rendered field — no artifact generation mixes the two brands. Decisions in [docs/decisions/0002](docs/decisions/0002-brand-cohesion-tooling-rename.md); full narrative: [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md).

### Added
- **`scripts/house-rules` dispatcher** — the sole documented entry point (`init | doctor | sync`), forwarding to the implementation scripts unchanged; `hr` and `house-rules` shell aliases replace `pbi`/`pbd`. A missing or unknown subcommand is a usage error (exit 64).
- **Content-aware rc-block refresh**: `install-aliases.sh` now detects a present-but-stale source block (the body changed at this cut — the sourced filename moved) and rewrites it in place, with the malformed-marker guards intact.
- Fixture coverage: the profile-distribution suite is a blocking CI gate (process-kit-b3m); both suites run on bd-less runners via a no-op shim (process-kit-4ma); new cases pin rendered-section content (playbook-free, dispatcher-form), CRLF rc blocks, stale-stamp refresh, and the nested-BEGIN guard below — 55 assertions total.

### Changed
- **Script renames**: `playbook-init.sh` → `init.sh`, `playbook-doctor.sh` → `doctor.sh` (independently runnable behind the dispatcher); internal `PLAYBOOK_ROOT` → `KIT_ROOT`; init lock → `.house-rules-init.lock`. Doctor exit codes, `SUMMARY:` keys, and the marker grammar are unchanged.
- **Machine-state renames, clean break**: `~/.playbook-sync-targets` → `~/.house-rules-sync-targets`, `~/.playbook-aliases.sh` → `~/.house-rules-aliases.sh`, the documented ignore file → `~/.house-rules-ignore`. No legacy-name recognition ships in code (decision 0002 A2).
- **Renderers and docs**: the AGENTS.md section and the global-safety-net blocks emit dispatcher-form commands only; active docs and rules swept of the tooling-brand "playbook" (dated records and the generic `graybeard-playbook` name exempt per 0002 A4). `PROCESS_KIT`, the `~/process-kit` clone path, and the `process-kit-*` bead prefix deliberately keep their names as documented history (A3).
- Legacy `ai-dev-playbook:` marker recognition sunset (process-kit-26b) after a field sweep showed zero old-marker artifacts; the 0.2.0 in-place migration machinery is removed.

### Fixed
- **Data-loss guard (Tier 1 review Critical)**: an orphan BEGIN above a well-formed marker block made all three installers' rewrite scanners silently delete the user content between them — newly reachable from install mode via the refresh path. A BEGIN seen while a block is open now refuses the rewrite; fixed test-first at every scanner (commit 3eeacc8, ledger red/green).
- **Honest refusal exits**: malformed-marker refusals in the installers exited 0 behind success banners ("Installed aliases", "Nothing to remove"); they now exit 1 with explicit warnings across install and uninstall in both installers and in init's section refresh.
- Doctor fix strings taught the retired direct-script invocation at 8 sites — swept to dispatcher form; `sync-rules.sh` shed dead migration machinery (`derive_repo_root`, the removed `~/.cursor-sync-targets` fallback's scaffolding, the v1.0-era `claude/rules` migration) and `--show-version` now says house-rules.

## 0.2.0 — 2026-08-06

First public release, under the final name **house-rules** (renamed from the working name `process-kit`; old GitHub URLs redirect). Full narrative: [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md).

### Added
- **Profile-driven conventions** (flagship): `profiles/conventions.toml` is the machine-readable source for the Tier 1 convention sets — commit types and branch grammar, close-evidence shape, defer-comment grammar, the banned-token catalog, and TDD obligations by bead type. `scripts/conventions` projects it into rule prose (`render-rule`) and answers verdicts (`check-commit`/`check-branch`/`check-close`); the affected rule sections are generated fragments byte-checked against the profile render by a CI regen gate with a seeded-drift self-test.
- **Checker CLI suite**: `tdd-ledger` (durable red-then-green evidence), `defer-lint`, `close-reason-lint`, `banned-token-scan` — stdlib-only single-file CLIs distributed to targets via one manifest (`scripts/distributed-clis.list`) and drift-checked by the doctor. The conventions profile ships alongside them and drift-checks byte-for-byte (SUMMARY key `profile_drift`). In targets everything runs advisory; blocking enforcement stays in the kit's CI.
- **Refinement framework**: the `refinement` skill, concepts doc, and proposal template — the rule-topology split below was its pilot.
- Apache-2.0 `LICENSE`; `CONTRIBUTING` refreshed to match; the Agentic Covenant ships as `CODE_OF_CONDUCT.md`.
- Kit CI self-enforcement: projection-drift gate (generated `claude/rules/` vs `cursor/rules/` canon), shellcheck at warning severity, fragment-regen gate, the three checker test suites, and the marker-migration fixture suite — each drift gate with a seeded self-test.

### Changed
- **Rule topology**: heavyweight rules split into thin always-on law plus on-demand skills (`operating-model` + `graph-planning`, `bead-completion`/`beads-quality` + `bead-authoring`, `pragmatic-tdd` rule + skill, `multi-agent-review` + `tier1-review`/`tier2-handoff`, `defer-convention` + the `defer-lint` checker).
- **Marker migration**: installer marker blocks renamed from the legacy `ai-dev-playbook:` prefix to `house-rules:`, with in-place migration of already-installed blocks and malformed-marker guards (orphaned or CRLF markers warn instead of truncating).
- **`graybeard-*` rename**: the lazy-senior-dev skill family (formerly `ponytail-*`) renamed with credit to [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT), which it was adapted from.
- **Neutrality**: per-user voice parameters moved out of the public core into overlay files (`.agents/overlay.md`, machine-global `~/.agents/overlay.md`); README rewritten as the public front door with deep operational content moved to `docs/operations.md`.
- Maintenance subagents in `.cursor/agents/` rewritten for the kit (no predecessor/org-specific references); org-neutral Agentic Covenant blog draft added at `docs/blog-agentic-covenant.md`.

### Fixed
- **packet skill:** `render.py --verify`'s divergence-strip check scanned a fixed 1800 characters past the grid heading, false-WARNing template-conformant packets whose grid rows carry rich linked evidence. The window is now structural and accepts the strip above or below the grid; behavioral tests added at `skills/packet/tests/test_render_verify.py`.

## 0.1.0 — 2026-07-15

Initial extraction. This repo starts with fresh git history; the content was carried from a private predecessor playbook at its v1.2.0, with all organization-specific material removed.

### Carried over
- 12 canonical Cursor rules (`cursor/rules/*.mdc`) and the generated Claude Code format (`claude/rules/*.md`, regenerated to full parity — `defer-convention` and `ponytail-playbook` were missing from the predecessor's generated set)
- Scripts: `playbook-init.sh`, `playbook-doctor.sh`, `sync-rules.sh`, `install-global-safety-net.sh`, `install-aliases.sh`, `setup-worktree.sh`
- Global safety net block sources (`global-safety-net/*.md`)
- Skills: brainstorming, systematic-debugging, ponytail family (audit/debt/gain/help/review)
- Onboarding: WELCOME.md, QUICKSTART.md, sandbox exercise, core docs (concepts, FAQ, glossary, governance, adoption guide, rule-effectiveness scorecard)
- Claude Code hooks (`.claude/hooks/`) and settings template
- Templates: PR template with Assisted-by disclosure

### New
- Migrated `council` and `workspace-kickoff` skills from user-level (`~/.cursor/skills/`) into the versioned `skills/` library
- Standalone identity: README, PLAN, AGENTS, CLAUDE rewritten for the kit under the working name `process-kit`
- `PROCESS_KIT` env var replaces `AI_DEV_PLAYBOOK` in fresh installs (installer marker strings keep the legacy prefix for in-place update compatibility; see `defer:` comments)

### Removed (relative to the predecessor)
- Organization-specific decks, examples, integration docs, and internal audit subagents
- The deprecated `sync-cursor-rules.sh` shim
