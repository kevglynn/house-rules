# Operating the Kit

Day-to-day mechanics for maintainers and adopters: distribution semantics, drift checking, worktree setup, and versioning. For first-time setup, start with [QUICKSTART.md](../QUICKSTART.md); for the conceptual model, read [concepts.md](concepts.md).

## Manual setup

The one-command path is `house-rules init` (see the README quickstart). The manual equivalent:

1. Clone the kit repo
2. Add your project repo roots to `~/.house-rules-sync-targets` (one path per line)
3. Run `./scripts/house-rules sync` to distribute Cursor rules
4. Run `./scripts/house-rules sync --format claude` to distribute Claude Code rules

To add a new project repo later, append its root path to `~/.house-rules-sync-targets`. The file is local and untracked, so there are no merge conflicts.

## Install tiers (core vs full)

The kit has two install tiers. A project-root stamp file `.house-rules-tier` records which one applies — a single line, `core` or `full`.

| Tier | How you get it | Stamp | Sync targets | Doctor |
|------|----------------|-------|--------------|--------|
| **full** | `house-rules init` (default `--tier full`) | writes `full` | registers in `~/.house-rules-sync-targets` | Full checks: rules drift, task tracking, scratchpad, sync registration |
| **core** | core plugin install, or `house-rules init --tier core` | writes `core` | **never** registered | Skips beads / scratchpad / sync-target failures (reports "N/A for core tier"); missing local rules dirs are fine (plugin-delivered) |

**Absent stamp = full** for backward compatibility — pre-tier repos keep today's doctor semantics.

`init --tier core` without `--tool` is stamp-only: no task-tracking init, no scratchpad, no sync-target append. Pair it with the `house-rules-core` plugin for rules. Re-run with `--tier core --tool cursor` (or `--tool claude` / `--tool both`) if you also want a local rules copy without upgrading to full.

Core installs are deliberately excluded from `~/.house-rules-sync-targets`. Kit sync would overwrite a core subset with the full rule set; keeping core off the list is the support guardrail.

The core plugin carries an in-agent upgrade offer (`core-upgrade-offer` rule): after core skills prove useful in a repo with no task tracking, the agent offers the full install once, with consent, and persists `.house-rules-upgrade-offered` so it does not re-nag.

## Checking for drift

```bash
./scripts/house-rules sync --check                    # Check cursor rules
./scripts/house-rules sync --format claude --check    # Check claude rules
```

Reports which targets have stale or missing rules without modifying anything.

## Regenerating Claude rules in the kit repo

```bash
./scripts/house-rules sync --format claude --local
```

## What syncs automatically vs. what you copy manually

**Rules** (`cursor/rules/*.mdc`) sync automatically via `house-rules sync`. Add a target repo to `~/.house-rules-sync-targets` and run the script: rules distribute to the repo and all its worktrees (Cursor) or to `.claude/rules/` (Claude Code).

**A routine sync never deletes anything.** It classifies every file in the rules directories it doesn't deliver, reports what it found, and leaves all of it in place. Deletion happens only when you pass `--retire`, which is the deliberate act of propagating a kit rename. The kit has renamed a rule once in its entire history, so making every sync destructive to cover that event bought nothing and cost real work — see [`profiles/retired-rules.list`](../profiles/retired-rules.list) for the list of names involved.

Ownership is decided by **bytes, not filenames**. A file is the kit's only if its content matches a version the kit actually shipped under that name. Three things follow:

| What's in the directory | What the sync does |
|---|---|
| A rule your project wrote | Kept, reported as **unmanaged** |
| A file reusing a kit rule's name, with different bytes | Kept, reported as a **name collision** |
| A rule the kit shipped and no longer delivers | Reported as **retirable**; removed only under `--retire` |

A locally-edited copy of a retired kit rule lands in the middle row and is kept — the kit would rather leave a stale rule than delete your edit. `--check` reports a retirable rule as drift so the condition is visible in CI, and never flags the first two rows.

One case where the kit does overwrite: a project rule sharing a filename with a rule the kit is **currently delivering**. That's the ordinary sync path rather than cleanup, and it writes a `.bak` first. Name project rules distinctly.

Destructive operations are recoverable. An overwrite and a `--retire` deletion both write a timestamped `.bak` first (safe mode, on by default; `--unsafe` disables backups for both). The backup name is reserved atomically, so two syncs in the same second cannot overwrite each other's copy. If a backup can't be written the deletion is skipped and the run exits non-zero, so automation can tell it didn't happen.

The one exception is `--local`, the maintainer-only mode that regenerates the kit's own `claude/rules/`. That directory is generated in full and tracked in git, so git is the backup and no `.bak` is written on either the overwrite or the prune path — a backup there would break the byte-exactness the following `--check --local` enforces.

**`init` carries the same guarantee**, from the same implementation (`scripts/lib/backup-file.sh`). Re-running `house-rules init` over an existing install backs up any kit-owned file whose bytes on disk differ from the kit's — rules, skills, the conventions profile, and the distributed checker CLIs — under the same `<file>.<timestamp>.bak` name, and `--unsafe` waives it exactly as it does in sync. Unchanged files are not backed up, so a re-run over an untouched install leaves no `.bak` litter. A failed backup aborts rather than overwriting.

Three postures are in play, and the distinctions are deliberate. Files the kit **owns** (the four groups above) are overwritten, because delivering the current version is what init is for; the `.bak` is what makes that non-destructive. Files init **seeds but does not own** — the scratchpad, `CODE_OF_CONDUCT.md`, the PR template, the tdd-ledger workflow — are never overwritten at all, since the project is expected to edit them and the kit has no newer truth to deliver. `AGENTS.md` is the third case: a project-owned file containing a kit-owned block. Init rewrites only what sits between the `house-rules` markers, leaving the surrounding document untouched, but that rewrite discards anything a project wrote *inside* the block — and it fires on every kit version bump — so it takes a `.bak` of the whole file first, like any other owned overwrite. Init never deletes anything, so sync's keep-and-warn classification has no counterpart here.

`--dry-run` and `--check` never write to a target repo or to the kit checkout, and `--dry-run` previews the cleanup pass alongside the writes. Both do materialize a temporary directory when combined with `--version`, since the pinned rules are extracted from git before use.

**Worktree setup** (`.cursor/worktrees.json` + `scripts/setup-worktree.sh`) is a one-time manual copy per repo. These files may need repo-specific customization (additional dependencies, environment setup), so they're templates you adopt, not auto-synced artifacts.

**Skills** (`skills/`) are copied on demand: `house-rules init --skills` copies them into the tool-matching project dir (`.cursor/skills/` for Cursor, `.claude/skills/` for Claude Code, both for `--tool both`), or symlink individual skills for Claude Code (see [skills/README.md](../skills/README.md)).

**Templates** (`templates/`) carry two distribution semantics: `tdd-ledger-verify.yml` is distributed by `house-rules init` (as a not-overwriting copy into `.github/workflows/`), while `design-doc.md` is kit-resident: you copy it into `docs/specs/` when authoring a spec; init never ships it.

**The conventions profile** (`profiles/conventions.toml`) is the data-shaped source the checkers read — commit/branch grammar, close-evidence shape, defer grammar, the banned-token catalog, TDD obligations. `house-rules init` distributes it in the same run as the four checkers, and `house-rules doctor` drift-checks it byte-for-byte against the kit copy (SUMMARY key `profile_drift`, fix: `cp -f` the kit copy, same as the CLI rows).

- **Kit-owned, not project-editable.** The profile drift-checks byte-for-byte, so it must stay identical to the kit copy. Change conventions in the kit and re-sync; do not edit the distributed copy. (Contrast `.agents/overlay.md`, which *is* project-editable — the ownership boundary is stated in [skills/README.md](../skills/README.md#overlay-convention).)
- **Ships verbatim, including inert keys.** The `[fragments]` paths and `rule_*` keys are render-only — their only consumer is the kit-only `conventions` CLI (not distributed), so they are harmless dead data in a target. They ship unchanged because byte-drift-checking rules out per-target rewrites.
- **One sync unit.** The profile and the profile-reading checkers (`defer-lint`, `close-reason-lint`, `banned-token-scan`; `tdd-ledger` does not read it) version together. A target holding a stale checker against a fresh profile is a skew hazard (an old scanner can mis-read a profile that gained a section), so the doctor warns when the profile is present but a profile-reading checker is stale — re-copy both, or re-run `house-rules init`.
- **Advisory in targets, blocking in the kit.** The distributed checkers resolve the profile at the target repo root and run advisory: they exit non-zero on findings like any linter, but nothing gates on that exit unless the target wires them into its own CI. The kit's own CI is where profile↔fragment drift and the checker suites block. One consequence worth stating plainly: a target has no fragment-regen gate, so any target-side edit to the profile's rule/catalog sections silently moves the rule↔checker contract onto that repo's own responsibility — another reason to treat the file as kit-owned.

## The maintainer workflow

1. Edit rules in `cursor/rules/` (the kit repo is the canonical source)
2. Run `./scripts/house-rules sync --format claude --local` to regenerate `claude/rules/`
3. Run `./scripts/house-rules sync` to distribute Cursor rules to project repos
4. Run `./scripts/house-rules sync --format claude` to distribute Claude rules to project repos
5. (Optional) If you use the Settings UI rule for personal conventions, keep `cursor/settings-ui/instructions-rule.md` in sync and paste into Cursor Settings

Rules are auto-discovered: adding a new `.mdc` file to `cursor/rules/` automatically includes it in the next sync. No script edits needed.

## Worktree setup for beads

When Cursor creates a worktree, it bypasses `bd worktree create`, so beads can't find the database. The setup script fixes this by writing a `.beads/redirect` file that points the worktree to the main repo's database. All worktrees share one beads instance.

### How it works

1. `.cursor/worktrees.json` tells Cursor to run `scripts/setup-worktree.sh` on every new worktree (`postCreate` hook)
2. The script detects the main repo via `git rev-parse --git-common-dir` and writes an absolute-path redirect
3. `bd list` (and all other `bd` commands) work from the worktree immediately

### Adopting in your repo

1. Copy `scripts/setup-worktree.sh` into your repo (keep it executable: `chmod +x`)
2. Copy `.cursor/worktrees.json` into your repo's `.cursor/` directory
3. Commit both files
4. Optionally pin `dolt.port` in `.beads/config.yaml` to a repo-specific port. This prevents random-port warnings when multiple shells or worktrees connect to Dolt; choose a port that won't collide with other beads-enabled repos on the same machine.

### For existing worktrees

Run the script manually from the worktree root:

```bash
bash scripts/setup-worktree.sh
```

If the worktree already has a local beads database from a previous `bd init`, the script will detect it and warn rather than overwrite.

### Portability

The setup script is pure shell (no `python3` or `bd` binary required). Validated on bd 0.61.0 (Homebrew) and macOS/Linux. On Windows, use WSL or Git Bash.

## Versioning mechanics

The kit uses semantic versioning via the `VERSION` file and git tags. The compatibility contract — what MAJOR/MINOR mean for synced repos, rename stubs, the Breaking-for-synced-repos changelog convention — is in [versioning.md](versioning.md).

Two ways to pin, with different coverage:

```bash
git -C ~/house-rules checkout v0.3.0           # full pin: rules, doctor, checkers, profile
./scripts/house-rules sync --version v0.3.0    # rules-only pin; the clone stays where it is
./scripts/house-rules sync --show-version      # print current version
```

`sync --version` reads rules out of the git tag, but the doctor drift-checks targets against the clone's *current checkout* — a clone sitting at `main` will report tag-pinned rules as stale. Pinning the clone itself keeps every tool on one version and is the right default for anyone not developing the kit; syncing from `main` is maintainer / advanced mode.

Release process details live in [CONTRIBUTING.md](../CONTRIBUTING.md); release notes live in [releases/](releases/).
