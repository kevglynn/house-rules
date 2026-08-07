# Quick Start

Setup takes under 5 minutes. Choose your path below.

## Prerequisites

1. **Clone the kit** (skip if already cloned):
   ```bash
   git clone https://github.com/kevglynn/house-rules ~/house-rules
   ```

   `~/house-rules` is the canonical path these docs use throughout. Cloned somewhere else? That works too: the scripts resolve their own location, and `install-aliases.sh` (below) pins the `PROCESS_KIT` env var to your actual clone root so the `hr` alias and the machine-global agent blocks find the kit. When `PROCESS_KIT` is unset, agent-facing commands fall back to `~/process-kit` — the kit's historical default path.

2. **Install beads** (skip if `bd` is already on PATH):
   ```bash
   brew install beads
   ```

   **Supported shells:** bash and zsh. Fish users: aliases from `install-aliases.sh` are not supported; use the full script paths instead.

   **Non-Homebrew install:** See the [beads repository](https://github.com/steveyegge/beads) for alternative install methods.

## One-time machine setup (recommended first step)

**Why this matters:** Per-repo rules only apply in bootstrapped projects. Without the safety net, an agent opening a fresh repo has zero knowledge the kit exists — it can't bootstrap what it doesn't know about. The safety net solves this by injecting a minimal bootstrap prompt into your machine-wide `~/CLAUDE.md` (and Cursor user rules). It's a one-time install that ensures every repo gets at least a "would you like to bootstrap?" prompt.

Two installers, run once per machine. Both are non-interactive and safe for agents to run on your behalf after asking — so you can literally tell Cursor or Claude Code to "install the kit" and it will invoke these for you.

```bash
# Per-machine agent rule blocks (agent-identity, session-start, agent-protocol)
# Writes marker-delimited blocks to ~/CLAUDE.md and generates a Cursor paste snippet.
bash ~/house-rules/scripts/install-global-safety-net.sh

# hr / house-rules shell aliases + PROCESS_KIT env var
# Writes ~/.house-rules-aliases.sh and adds one guarded source line to your rc file.
bash ~/house-rules/scripts/install-aliases.sh
```

After `install-global-safety-net.sh`, paste the generated snippet into **Cursor → Settings → Rules for AI → User Rules**. Recall the snippet any time with:

```bash
cat ~/house-rules/global-safety-net/cursor-snippet.generated.md
# or
bash ~/house-rules/scripts/install-global-safety-net.sh --print-cursor-snippet
```

Verify either installer anytime:

```bash
bash ~/house-rules/scripts/install-global-safety-net.sh --check
bash ~/house-rules/scripts/install-aliases.sh --check
```

Once both are installed, you can say **"use house-rules"** to any agent in any repo — it will read the agent-protocol block, run the doctor, and offer bootstrap/sync/update with your consent.

## One-command project setup (recommended)

From your project root, after shell aliases are installed:

```bash
hr init                                        # interactive tool choice
# or
hr init --tool cursor                          # skip interactive prompt
# or without aliases:
bash ~/house-rules/scripts/house-rules init
```

The script will:
- Ask which tool you use (Cursor, Claude Code, or both)
- Copy the appropriate rules into your project
- Initialize beads task tracking
- Install **beads git hooks** (`bd hooks install`) so pre-commit / post-merge / pre-push keep `issues.jsonl` and the Dolt DB in sync across clones (see `bd hooks --help`)
- Create a scratchpad for cross-session context
- Register your project for rule sync updates

**Opt out of hooks:** pass `--no-hooks` if you manage git hooks yourself or use a repo where hook installation is not allowed. You can run `bd hooks install` later from the project root.

Verify everything is configured:

```bash
hr doctor                                          # human-readable
bash ~/house-rules/scripts/house-rules doctor      # same thing without aliases
```

For agent-consumable status (structured exit codes + `SUMMARY:` footer):

```bash
bash ~/house-rules/scripts/house-rules doctor --agent
# Exit: 0=ok, 2=bootstrap_needed, 3=rules_drift, 1=error
# On rules_drift, SUMMARY carries the format: rules_drift_cursor|rules_drift_claude|rules_drift_both
```

Options:
```bash
# Explicit tool choice (required if stdin is not a terminal)
bash ~/house-rules/scripts/house-rules init --tool cursor
bash ~/house-rules/scripts/house-rules init --tool claude
bash ~/house-rules/scripts/house-rules init --tool both

# Personal repos (hides .beads from git)
bash ~/house-rules/scripts/house-rules init --stealth

# Skip beads git hooks (default is to install them)
bash ~/house-rules/scripts/house-rules init --tool cursor --no-hooks
```

`house-rules init` refuses non-interactive invocation without `--tool` — this is a security gate against prompt-injected agents silently bootstrapping a repo.

## Manual setup

<details>
<summary>Cursor (manual steps)</summary>

```bash
cd /path/to/your/project

# Copy rules
mkdir -p .cursor/rules
cp ~/house-rules/cursor/rules/*.mdc .cursor/rules/

# Initialize beads
bd init
bd setup cursor

# Create scratchpad
cat > .cursor/scratchpad.md <<'EOF'
# Agent Scratchpad

## Background and Motivation

## Key Challenges and Analysis

## High-level Task Breakdown

## Current Status / Progress Tracking

## Executor's Feedback or Assistance Requests

## Lessons
EOF

# Register for sync updates
echo "$(pwd)" >> ~/.house-rules-sync-targets
```

</details>

<details>
<summary>Claude Code (manual steps)</summary>

```bash
cd /path/to/your/project

# Copy rules
mkdir -p .claude/rules
cp ~/house-rules/claude/rules/*.md .claude/rules/

# Initialize beads
bd init
bd setup claude

# Register for sync updates
echo "$(pwd)" >> ~/.house-rules-sync-targets
```

Then reference the rules in your project's `CLAUDE.md`:

```markdown
# Project Rules

See `.claude/rules/` for the full operating model, including:
- `operating-model.md` — Planner/Executor roles, session protocol, error recovery
- `beads-quality.md` — How to create well-formed beads with ACs
- `bead-completion.md` — How to pick up, verify, and close beads
- `pragmatic-tdd.md` — Test discipline by bead type
- `design-docs.md` — When and how to write design specs
```

</details>

## What you just installed

| Component | What it does |
|-----------|-------------|
| **Beads (`bd`)** | Task tracking for AI agents. Tasks have acceptance criteria, dependencies, and status. `bd ready` → `bd close`. |
| **Planner/Executor model** | Two modes for your agent. Planner breaks down work. Executor picks up one task at a time. |
| **12 agent rules** | Standards for quality, testing, completion, review, design docs, worktrees, and identity. |
| **Scratchpad** | Shared markdown file for cross-session context — decisions, progress, and lessons persist. |

New to these concepts? Read **[Core Concepts](docs/concepts.md)** for the full picture.

## Day-to-day usage

- Say **"Planner mode"** to break down a new feature into tasks
- Say **"Executor mode"** to start implementing
- The agent uses `bd ready` to find the next unblocked task, claims it, implements it, and closes it with evidence
- At session start, the agent runs `bd prime` to reload context

## Keeping rules updated

The kit repo is the source of truth. To sync updates to all registered projects:

```bash
cd ~/house-rules && git pull

# Sync to all projects in ~/.house-rules-sync-targets
./scripts/house-rules sync --format cursor   # Cursor users
./scripts/house-rules sync --format claude    # Claude Code users
```

## What the global safety net covers

The machine setup at the top of this doc installs three marker-delimited blocks into `~/CLAUDE.md` (and a matching Cursor user-rules paste snippet). Each block addresses a different un-bootstrapped-repo failure mode:

- **`agent-identity`** — condensed version of the rule that keeps agents from reverting to human-baseline estimation ("this will take 2-3 weeks with one developer") in repos where the full rule isn't loaded.
- **`session-start`** — the bootstrap-check prompt. When the agent opens a repo with no `.cursor/rules/` and no `.claude/rules/`, it asks once: *run init, skip, or add to `~/.house-rules-ignore`?*
- **`agent-protocol`** — the contract for how agents respond to "use house-rules." Tells them to run `house-rules doctor --agent`, branch on the exit code, and propose the right remediation with your consent.

Block sources are individual files at `global-safety-net/*.md`. Add a file + registry entry in `install-global-safety-net.sh` to add a new concern.

`house-rules doctor` also reports the status of each block as part of its normal output, so you'll see a warning if anything goes missing or stale.

## Verify your setup anytime

```bash
bash ~/house-rules/scripts/house-rules doctor
```

Reports pass/fail/warn for every check and prints fix commands for anything that's off.

## What's next

- **[FAQ](docs/faq.md)** — Common questions from real adopters (Cursor vs Claude, multiple agents, migration)
- **[Onboarding Sandbox](sandbox/)** — 45-minute hands-on exercise teaching the full workflow by doing
- **[Core Concepts](docs/concepts.md)** — Why the kit exists and how the pieces fit together
- **[Glossary](docs/glossary.md)** — Definitions for all terminology
- **[Full docs](docs/README.md)** — Reading order for decks, guides, and reference material
- **[Contributing](CONTRIBUTING.md)** — How to propose and contribute changes
