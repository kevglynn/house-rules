# house-rules

A **versioned engineering playbook for AI coding agents** — rules and checkers that make process knowledge checkable, not something you hope the model remembers.

Works with Cursor and Claude Code today. Everything is plain markdown plus stdlib-only Python and bash, so nothing locks you to a tool.

## Try it now (no install)

Paste this into any terminal. No clone, no plugin, no account — just `curl` and `python3`:

```bash
curl -fsSL https://raw.githubusercontent.com/kevglynn/house-rules/main/scripts/banned-token-scan -o /tmp/banned-token-scan
printf '%s\n' 'This will take 2-3 weeks for one developer, but with an aggressive timeline we could ship by end of week.' | python3 /tmp/banned-token-scan
```

You should see labeled hits (`[time-units]`, `[team-size]`, `[schedule-framing]`, …) and exit code 1. That checker is one piece of the playbook: it flags human-baseline estimation so agents describe complexity, scope, sequencing, and risk instead.

## Install the core plugin

The fastest install path is the platform plugin — no clone, no HOME writes, no shell installer.

**Claude Code**

```text
/plugin marketplace add kevglynn/house-rules
/plugin install house-rules-core
```

**Cursor**

This repo ships `.cursor-plugin/plugin.json` for the `house-rules-core` plugin (rules + skills + checkers). Install from GitHub via Cursor's plugin flow (**Customize →** add / import the `kevglynn/house-rules` repo, then install `house-rules-core`), or clone and load the local plugin directory.

**Skills CLI**

```bash
npx skills add kevglynn/house-rules
```

That pulls the core skills (graybeard family, prose-voice) that the marketplace and skills layout declare. Pair with the Claude or Cursor plugin install above if you also want the rules and checkers loaded in-agent.

### What you get

- **Rules** — always-on law the agent reads every session (identity, deferrals, prose voice, subagent safety, the graybeard ladder).
- **Checkers** — single-file stdlib CLIs (`banned-token-scan`, `defer-lint`, …) with stable exit codes you can run locally or in CI. Checkable, not silently "enforced" by the model.

## Every repo on this machine (global safety net)

Optional. For agents that should carry a thin rule set even in repos you never bootstrapped — clone once, then run the installer:

```bash
git clone https://github.com/kevglynn/house-rules ~/house-rules
bash ~/house-rules/scripts/install-global-safety-net.sh
```

**Files it touches**

| Path | What happens |
|------|----------------|
| `~/CLAUDE.md` | Writes/updates three marker-delimited blocks: `agent-identity`, `session-start`, `agent-protocol` |
| `~/house-rules/global-safety-net/cursor-snippet.generated.md` | Regenerates a paste snippet for Cursor **Settings → Rules for AI → User Rules** (Cursor does not expose a safe cross-platform write to user-rules storage) |

Nothing else under `$HOME` is modified by this script. (Aliases are a separate optional step: `install-aliases.sh`.)

**Undo**

```bash
bash ~/house-rules/scripts/install-global-safety-net.sh --uninstall
```

That removes the managed blocks from `~/CLAUDE.md`. If you pasted the Cursor snippet manually, delete that paste from User Rules yourself (Cursor may also auto-import `~/CLAUDE.md` when that setting is on — editing the file is enough in that case).

## Full playbook upgrade

When you want the whole loop — project bootstrap, task tracking with beads, sync across repos, the sandbox exercise — clone (if you haven't) and init:

```bash
git clone https://github.com/kevglynn/house-rules ~/house-rules   # skip if already cloned
bash ~/house-rules/scripts/install-aliases.sh                      # optional: hr / house-rules + PROCESS_KIT
cd /path/to/your/project
bash ~/house-rules/scripts/house-rules init
```

`~/house-rules` is the canonical clone path, but any path works: `install-aliases.sh` pins `PROCESS_KIT` to wherever you cloned, and agent-facing commands fall back to `~/process-kit` (the historical default) when it is unset.

From there the kit is agent-operated:

- Tell your agent **"use house-rules."** It runs the doctor and offers bootstrap, sync, or update with your consent.
- Un-bootstrapped git repos get a one-time session-start prompt.
- Bootstrapped repos carry an `AGENTS.md` so any agent finds the setup.

See **[QUICKSTART.md](QUICKSTART.md)** for all setup options, **[docs/concepts.md](docs/concepts.md)** for how the pieces fit, and **[docs/versioning.md](docs/versioning.md)** for how sync and releases pin. Support boundaries: **[SUPPORT.md](SUPPORT.md)**.

## What's inside

### Rules (`cursor/rules/`, canonical)

Canonical `.mdc` rule files, the single source of truth. The Claude Code format (`claude/rules/`) is generated from these, and CI fails on drift between the two.

| Rule | What it does |
|------|-------------|
| `operating-model.mdc` | Planner/Executor roles, scratchpad conventions, beads task tracking, workflow |
| `session-lifecycle.mdc` | Mandatory session start/close protocol: `bd prime`, in-progress check, knowledge capture |
| `beads-quality.mdc` | Bead creation standards: self-contained descriptions, acceptance criteria, non-goals |
| `bead-completion.mdc` | JIT verification, self-review against ACs, evidence-based closes, knowledge capture |
| `pragmatic-tdd.mdc` | Signal-first TDD by bead type, zero-signal test taxonomy |
| `multi-agent-review.mdc` | Two-tier review protocol: same-model multi-lens plus cross-model handoff |
| `design-docs.mdc` | When to create committed specs (3+ beads or high-risk areas) |
| `defer-convention.mdc` | Deliberate simplifications carry a ceiling and an upgrade trigger |
| `agent-identity.mdc` | No human-baseline estimation: describe complexity, scope, and risk instead of timelines |
| `prose-voice.mdc` | Human-facing prose follows the prose-voice skill: pattern budgets, punctuation fingerprint |
| `parallel-subagent-safety.mdc` | Blast-radius rules that prevent file conflicts between parent agents and subagents |
| `worktree-awareness.mdc` | Git worktree isolation: shared beads DB, commit-early discipline |
| `graybeard-playbook.mdc` | Lazy-senior-dev implementation ladder: minimal, correct code; stdlib before new |

### Skills (`skills/`)

On-demand procedures for recurring tasks: planning breakdowns, bead authoring, TDD playbooks, two-tier reviews, systematic debugging, over-engineering audits (the graybeard family), refinement runs, prose voice discipline. The full catalog is in **[skills/README.md](skills/README.md)**. This directory is also the incubation home for new process skills.

### Checker CLIs (`scripts/`)

Single-file, stdlib-only Python. Each documents its full contract in `--help`; all share the exit-code contract `0`=clean, `1`=violation, `2`=usage, `3`=I/O.

| CLI | Checks |
|-----|--------|
| `conventions` | Commit types, branch grammar, and close-evidence shapes from `profiles/conventions.toml`; also renders the rule fragments CI byte-checks |
| `tdd-ledger` | Durable red-then-green TDD evidence, CI-verifiable |
| `defer-lint` | Every `defer:` comment carries its upgrade trigger |
| `close-reason-lint` | Bead close reasons carry commit refs and AC mapping |
| `banned-token-scan` | The agent-identity rule's no-human-estimation token classes |
| `docs-path-lint` | Fenced doc commands reference script paths that exist (kit-repo-only, not distributed) |

The checker CLIs ship to target repos through one manifest (`scripts/distributed-clis.list`); the doctor drift-checks each against the kit copy. `profiles/conventions.toml` — the data those checkers read — ships in the same run as one atomic unit and is drift-checked byte-for-byte too (SUMMARY key `profile_drift`). In targets the checkers run **advisory** — they exit non-zero on findings like any linter, but nothing gates on that exit unless the target wires them into its own CI; blocking gates stay in the kit's CI. See [docs/operations.md](docs/operations.md) for the ownership and drift rules.

### Distribution scripts (`scripts/`)

| Script | What it does |
|--------|-------------|
| `house-rules init` | One-command project setup: rules, beads, scratchpad, `AGENTS.md`, checker CLIs, sync registration |
| `house-rules doctor` | Validates any setup; `--agent` mode emits a `SUMMARY:` key and structured exit codes agents branch on |
| `house-rules sync` | Multi-format rule sync with drift checking (`--check`), local regeneration (`--local`), and safe-by-default backups |
| `install-global-safety-net.sh` | Per-machine marker blocks in `~/CLAUDE.md` plus a Cursor user-rules snippet |
| `install-aliases.sh` | Per-machine `hr` / `house-rules` aliases and the `PROCESS_KIT` env var |
| `setup-worktree.sh` | Makes git worktrees share the main repo's beads database |

Shared shell code the installers source lives in `scripts/lib/` — `marker-rewrite.sh` (the managed-block rewrite the three installers share) and `backup-file.sh` (the timestamped-backup primitive `init` and `sync` share). A lib stays sourceable: no shebang, no top-level side effects, and a header comment stating its return-code contract. **`scripts/lib/` is not distributed** — it exists only in the kit clone, so nothing in `scripts/distributed-clis.list` may source it; a distributed CLI that grows a lib dependency breaks in every target.

Distribution semantics, worktree setup, and drift-checking mechanics live in **[docs/operations.md](docs/operations.md)**. Pinning and compatibility: **[docs/versioning.md](docs/versioning.md)**.

## Governance and license

The kit ships **[The Agentic Covenant](CODE_OF_CONDUCT.md)** as its code of conduct: governance written for communities where humans and AI agents collaborate. AI-assisted contributions are explicitly welcome and disclosed with the `Assisted-by` convention. [docs/governance.md](docs/governance.md) covers how governance fits into the kit.

Licensed under **[Apache-2.0](LICENSE)**. Contribution process, CI gates, and release discipline are in **[CONTRIBUTING.md](CONTRIBUTING.md)**. Questions and support boundaries: **[SUPPORT.md](SUPPORT.md)**.

## Status

v0.2.0 is the first public release. The rules, distribution scripts, and checker CLIs are exercised daily across a multi-repo setup and are the most battle-tested surfaces. Skills are newer and more uneven — the catalog in [skills/README.md](skills/README.md) lists what ships; several entries are still incubating. Decision records in [docs/decisions/](docs/decisions/) document naming, licensing, and publication posture, amendments and all.

## Documentation

| Document | Audience |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | First-time setup in under 5 minutes |
| [docs/concepts.md](docs/concepts.md) | Why the kit exists and how the components work together |
| [sandbox/](sandbox/) | Hands-on 45-minute exercise teaching the full workflow by doing |
| [docs/operations.md](docs/operations.md) | Distribution semantics, worktrees, drift checking, versioning mechanics |
| [docs/versioning.md](docs/versioning.md) | Compatibility contract: what sync pins, what a major bump means |
| [docs/glossary.md](docs/glossary.md) | Plain-English definitions of all terminology |
| [docs/README.md](docs/README.md) | Full reading order for guides and reference material |
| [docs/releases/](docs/releases/) | Release notes per version |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to propose and contribute changes |
| [SUPPORT.md](SUPPORT.md) | What is supported, what isn't, how to file issues |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | The Agentic Covenant |
| [CHANGELOG.md](CHANGELOG.md) | What changed and when |

### Returning coders (side door)

Used to ship code, been away, want an agent-driven onboarding path instead of the plugin/quickstart route above? Start with **[WELCOME.md](WELCOME.md)**.

## Versioning

Semantic versioning via the `VERSION` file and git tags. Teams pin to releases with `house-rules sync --version vX.Y.Z`; mechanics in [docs/operations.md](docs/operations.md) and the consumer contract in [docs/versioning.md](docs/versioning.md); release process in [CONTRIBUTING.md](CONTRIBUTING.md).

## Origin and attribution

Extracted from a private predecessor playbook (organization-specific content removed) and restarted with fresh history at v0.1.0; incubated under the working name process-kit. Rules originally adapted from [obra/superpowers](https://github.com/obra/superpowers) and [ed3dai/ed3d-plugins](https://github.com/ed3dai/ed3d-plugins), cherry-picked for signal over dogma. The graybeard skill family adapts the "laziest senior dev" concept from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT), reimplemented and extended for this kit.
