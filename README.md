# house-rules

Versioned agent rules, skills, and checker CLIs that give AI coding agents a real engineering process: test discipline, evidence-based completion, review gates, and session hygiene, distributed to every repo you work in from one canonical source.

The name is literal: these are the house rules your agents work under. Works with Cursor and Claude Code today; everything is plain markdown plus stdlib-only Python and bash, so nothing locks you to a tool.

> **Returning to coding after time away?** Start with **[WELCOME.md](WELCOME.md)**, an agent-driven onboarding path for people who used to code and want to come back as agent-native builders.

## The problem it solves

Agents execute well inside a session and forget everything between sessions. Process knowledge (what to test, when to stop, how to close work, what evidence counts) lives in prompts that don't travel. This kit packages that knowledge as versioned artifacts on four surfaces:

- **Rules** are always-on law: thirteen canonical rule files covering TDD discipline, task-tracking hygiene, completion evidence, review triggers, prose voice, and session lifecycle.
- **Skills** are on-demand procedure: structured playbooks an agent loads at the moment they apply (reviews, debugging, planning breakdowns, refinement audits).
- **Checkers** are mechanical enforcement: single-file, stdlib-only CLIs that verify what the rules prescribe, with stable exit codes for CI.
- **Distribution** keeps all of it synchronized: one command bootstraps a repo, a doctor validates any setup, and a sync script pushes rule updates to every registered repo and its worktrees.

Conventions with both a prose home and a checker home are projected from a machine-readable profile (`profiles/conventions.toml`): the rule text agents read and the verdicts checkers enforce render from the same source, and a CI gate fails when they diverge. The [v0.2.0 release notes](docs/releases/v0.2.0.md) tell that story in full.

## Quickstart

One-time machine setup:

```bash
git clone https://github.com/kevglynn/house-rules ~/house-rules
bash ~/house-rules/scripts/install-global-safety-net.sh    # per-machine agent rule blocks
bash ~/house-rules/scripts/install-aliases.sh              # pbi, pbd aliases + PROCESS_KIT env var
```

Then point it at a project:

```bash
cd /path/to/your/project
bash ~/house-rules/scripts/playbook-init.sh
```

Both installers are non-interactive and safe for agents to run on your behalf. From there the kit is agent-operated:

- In any repo, tell your agent **"use the playbook."** It reads the agent-protocol block in your global rules, runs the doctor, and branches on the result, offering bootstrap, sync, or update with your consent.
- In any un-bootstrapped git repo, the agent prompts at session start: *"This project isn't bootstrapped with the playbook. Run init, skip, or add to ignore?"*
- Bootstrapped repos carry an `AGENTS.md` pointing any agent (Cursor, Claude Code, Codex, Copilot, future) at the setup, the rules, and the doctor. Discovery is automatic.

See **[QUICKSTART.md](QUICKSTART.md)** for all setup options and **[docs/concepts.md](docs/concepts.md)** for how the pieces fit together.

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

On-demand procedures for recurring tasks: planning breakdowns, bead authoring, TDD playbooks, two-tier reviews, systematic debugging, over-engineering audits (the graybeard family), refinement runs, prose voice discipline. The full catalog with maturity status is in **[skills/README.md](skills/README.md)**. This directory is also the incubation home for new process skills.

### Checker CLIs (`scripts/`)

Single-file, stdlib-only Python. Each documents its full contract in `--help`; all share the exit-code contract `0`=clean, `1`=violation, `2`=usage, `3`=I/O.

| CLI | Enforces |
|-----|----------|
| `conventions` | Commit types, branch grammar, and close-evidence shapes from `profiles/conventions.toml`; also renders the rule fragments CI byte-checks |
| `tdd-ledger` | Durable red-then-green TDD evidence, CI-verifiable |
| `defer-lint` | Every `defer:` comment carries its upgrade trigger |
| `close-reason-lint` | Bead close reasons carry commit refs and AC mapping |
| `banned-token-scan` | The agent-identity rule's no-human-estimation token classes |

The checker CLIs ship to target repos through one manifest (`scripts/distributed-clis.list`); the doctor drift-checks each against the kit copy. `profiles/conventions.toml` — the data those checkers read — ships in the same run as one atomic unit and is drift-checked byte-for-byte too (SUMMARY key `profile_drift`). In targets the checkers run **advisory** — they exit non-zero on findings like any linter, but nothing gates on that exit unless the target wires them into its own CI; blocking enforcement stays in the kit's CI. See [docs/operations.md](docs/operations.md) for the ownership and drift rules.

### Distribution scripts (`scripts/`)

| Script | What it does |
|--------|-------------|
| `playbook-init.sh` | One-command project setup: rules, beads, scratchpad, `AGENTS.md`, checker CLIs, sync registration |
| `playbook-doctor.sh` | Validates any setup; `--agent` mode emits a `SUMMARY:` key and structured exit codes agents branch on |
| `sync-rules.sh` | Multi-format rule sync with drift checking (`--check`), local regeneration (`--local`), and safe-by-default backups |
| `install-global-safety-net.sh` | Per-machine marker blocks in `~/CLAUDE.md` plus a Cursor user-rules snippet |
| `install-aliases.sh` | Per-machine `pbi`/`pbd` aliases and the `PROCESS_KIT` env var |
| `setup-worktree.sh` | Makes git worktrees share the main repo's beads database |

Distribution semantics, worktree setup, and drift-checking mechanics live in **[docs/operations.md](docs/operations.md)**.

## Governance and license

The kit ships **[The Agentic Covenant](CODE_OF_CONDUCT.md)** as its code of conduct: governance written for communities where humans and AI agents collaborate. AI-assisted contributions are explicitly welcome and disclosed with the `Assisted-by` convention. [docs/governance.md](docs/governance.md) covers how governance fits into the kit.

Licensed under **[Apache-2.0](LICENSE)**. Contribution process, CI gates, and release discipline are in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Status

v0.2.0 is the first public release. The rules, distribution scripts, and checker CLIs are exercised daily across a multi-repo setup and are the most battle-tested surfaces. Skills vary: each entry in [skills/README.md](skills/README.md) carries its maturity honestly, and several are incubating. Decision records in [docs/decisions/](docs/decisions/) document naming, licensing, and publication posture, amendments and all.

## Documentation

| Document | Audience |
|----------|---------|
| [WELCOME.md](WELCOME.md) | Returning coders / first-time agent-native builders |
| [QUICKSTART.md](QUICKSTART.md) | First-time setup in under 5 minutes |
| [docs/concepts.md](docs/concepts.md) | Why the kit exists and how the components work together |
| [sandbox/](sandbox/) | Hands-on 45-minute exercise teaching the full workflow by doing |
| [docs/operations.md](docs/operations.md) | Distribution semantics, worktrees, drift checking, versioning mechanics |
| [docs/glossary.md](docs/glossary.md) | Plain-English definitions of all terminology |
| [docs/README.md](docs/README.md) | Full reading order for guides and reference material |
| [docs/releases/](docs/releases/) | Release notes per version |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to propose and contribute changes |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | The Agentic Covenant |
| [CHANGELOG.md](CHANGELOG.md) | What changed and when |

## Versioning

Semantic versioning via the `VERSION` file and git tags. Teams pin to releases with `sync-rules.sh --version vX.Y.Z`; mechanics in [docs/operations.md](docs/operations.md), release process in [CONTRIBUTING.md](CONTRIBUTING.md).

## Origin and attribution

Extracted from a private predecessor playbook (organization-specific content removed) and restarted with fresh history at v0.1.0; incubated under the working name process-kit. Rules originally adapted from [obra/superpowers](https://github.com/obra/superpowers) and [ed3dai/ed3d-plugins](https://github.com/ed3dai/ed3d-plugins), cherry-picked for signal over dogma. The graybeard skill family adapts the "laziest senior dev" concept from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT), reimplemented and extended for this kit.
