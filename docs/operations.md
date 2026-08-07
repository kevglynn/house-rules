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

Core installs are deliberately excluded from `~/.house-rules-sync-targets`. Kit sync would overwrite a core subset with the full rule set and delete unrecognized files; keeping core off the list is the support guardrail.

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

The sync's stale cleanup deletes any rule file it doesn't recognize, so on kit-synced repos the rules directories are **kit-exclusive**: a workspace-local rule placed in `.cursor/rules/` or `.claude/rules/` is removed on the next sync — no prompt, no backup. That includes rule files other tools put there: the doctor tolerates extras between syncs, but the sync removes them. Two safety valves exist. `--dry-run` previews every write and deletion, and local edits to *kit-recognized* files are backed up to a timestamped `.bak` before overwrite (safe mode, on by default; `--unsafe` disables it). Unrecognized files get neither. For repo-local always-on guidance in a synced repo, use the repo's own `AGENTS.md`/`CLAUDE.md` sections or a skill instead.

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
