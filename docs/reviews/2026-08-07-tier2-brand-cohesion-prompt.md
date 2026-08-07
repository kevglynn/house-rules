# Tier 2 cross-model review — brand-cohesion tooling wave (dispatcher + installers + marker scanners) (`process-kit-anq`)

Paste everything below this line into each external model (Grok, Gemini, GPT). Collect the responses and hand them back for triage.

---

Review this Bash installer/dispatcher tooling layer with a critical eye. Accept or reject each finding with a reason — don't rubber-stamp. Focus on: Hunt these failure classes, in priority order. (1) Marker-scanner escapes: an input file shape (rc file, ~/CLAUDE.md, or AGENTS.md content) that passes the refusal guards in rc_rewrite_block, rewrite_block, or refresh_agents_section yet reaches the mv with user bytes missing from the temp file — Tier 1 already caught nested-BEGIN-above-a-valid-block; look for what else slips: END-before-any-BEGIN, interleavings of well-formed and orphan blocks, markers at EOF without trailing newline, marker lines differing only in trailing whitespace, empty files, a block as the very first or last line. The three scanners are hand-copied variants — a divergence where one refuses and another rewrites the same shape is itself a finding. (2) Two-parser divergence: each installer has a separate currency/presence checker (awk extraction in rc_block_is_current, bash-loop extraction in current_block_content, version-stamp grep in init.sh) that decides WHETHER to rewrite, while the scanner decides HOW — find an input where the checker and the scanner disagree about what 'the block' is, e.g. a file whose first block is current but a later duplicate is stale (checker says current, stale copy persists forever), or where the checker routes a malformed file down a path the scanner cannot refuse. (3) Success-claim honesty: any path where stdout or the process exit code claims installed/refreshed/removed while the file state disagrees, including any state where install exits 0 but --check exits 1. (4) Clean-break completeness: any surviving code path that reads or writes an old ~/.playbook-* name, or any rendered/embedded documentation (doctor fix strings, the agent-protocol dispatch table, the AGENTS.md heredoc in init.sh) that teaches a command line that no longer works as written. (5) Dispatcher forwarding: argument mangling through the exec forwards (quoting, --, whitespace), exit-code passthrough, and wrong-directory assumptions when invoked via the hr alias from an arbitrary cwd. Style and performance polish is out of scope.

## Review discipline

- Verdicts require evidence. For every focus area and every finding — including a clean pass — quote the exact code that decides your conclusion. A verdict without quoted code is invalid.
- Scope objections are not rejections. A real defect that falls outside this change's scope is still a finding — report it tagged out-of-scope. Triage owns scope decisions, not you; never self-reject a finding you believe is real.
- The packet's claims — the context, the already-addressed list, the trusted-layer boundary — are assertions, not facts. Verify the ones your verdict depends on; disproving one counts as a finding.

## Context

This is the house-rules kit's tooling/distribution layer: a dispatcher (scripts/house-rules) fronting project bootstrap (init.sh), setup diagnosis (doctor.sh), and rule sync (sync-rules.sh), plus two machine-level installers that maintain marker-delimited blocks in user-owned files (install-aliases.sh writes a source block into ~/.bashrc or ~/.zshrc; install-global-safety-net.sh maintains three blocks in ~/CLAUDE.md; init.sh maintains a marker-delimited section in each target repo's AGENTS.md). The wave under review (v0.3.0, epic process-kit-jy9, commits 10ce28a..3eeacc8 on kevglynn/house-rules) retired the legacy 'playbook' tooling brand per decision record docs/decisions/0002-brand-cohesion-tooling-rename.md and spec docs/specs/2026-08-06-brand-cohesion-rename.md: the dispatcher is new; playbook-init.sh/playbook-doctor.sh were renamed to init.sh/doctor.sh with internal identifier renames; the machine dotfiles renamed (~/.house-rules-sync-targets, ~/.house-rules-aliases.sh) as a clean break with no legacy-name recognition in code; and because the rc block's sourced filename changed, install-aliases.sh gained a content-aware refresh path (rc_block_is_current + an emit argument on the strip scanner) — the only genuinely new state machine. A same-model Tier 1 review already ran; its Critical (nested-BEGIN data loss) and the accounting/consistency fixes landed as commit 3eeacc8. The fixture suite (scripts/tests/test_marker_migration.sh, 55 assertions) pins fresh-install idempotency, the malformed-marker refusals (orphan BEGIN, nested BEGIN, CRLF), refusal exit codes, the stale-block refresh, and rendered-section content.

The layers below are trusted, do not re-review: Do not re-review: the four distributed checker CLIs (scripts/tdd-ledger, defer-lint, close-reason-lint, banned-token-scan) and profiles/conventions.toml (unchanged this wave, reviewed under their own beads); the rule content under cursor/rules/ and claude/rules/ and the prose docs sweep (docs-only child, no-test exception claimed); git, gh, and GitHub Actions plumbing; the beads (bd) CLI.

## Rules this layer must uphold

- Writer contract, uniform across the three marker rewriters: return 0 = written, 1 = I/O failure (callers fail loud), 2 = malformed markers (warn on stderr, target file left byte-identical).
- A guard refusal must never claim success: the process must exit nonzero and stdout must not report the item as installed/refreshed/removed.
- All writes to user-owned files are atomic: staged to a mktemp file in the same directory, then mv — no partial state on kill at any instruction boundary.
- doctor.sh's machine contract is frozen: exit 0/2/3/1 with SUMMARY keys ok | bootstrap_needed | rules_drift_cursor|claude|both | profile_drift | per-CLI drift keys | error; precedence rules documented in the file.
- Marker grammar is line-exact: '# BEGIN house-rules:aliases' / '# END house-rules:aliases' (rc), '<!-- BEGIN house-rules:<id> -->' (CLAUDE.md, AGENTS.md). Substring matches (grep -F presence checks) may be looser than the line-exact scanners, but a looser check must never route a file into a rewrite the scanner cannot safely refuse.
- Clean break: no code reads or writes the legacy ~/.playbook-* dotfile names or playbook-* script names. Deliberately retained history (not violations): the PROCESS_KIT env var, the ~/process-kit clone path, the process-kit-* bead prefix, historical comments, and the stale-body test fixture referencing .playbook-aliases.sh.
- Every command a rendered artifact or fix string teaches must work as written on a machine with only the kit clone present (dispatcher form: bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" <init|doctor|sync> ...).

## Already addressed (from prior review — don't re-report)

- Nested-BEGIN data loss (Tier 1 Critical): a BEGIN encountered while a block is open now breaks the scan and trips the refusal guard, in all three scanners; pinned by fixture cases 4b/5c/6b.
- Refusal accounting: malformed-marker refusals (return 2) now count as 'refused', print an explicit stderr summary, and exit 1 in install and uninstall modes of both installers; init.sh reports the failed section refresh and exits 1 after completing the rest of the bootstrap.
- install-global-safety-net.sh's duplicate replace_block/remove_block loops collapsed into one rewrite_block(id, emit) scanner; init.sh's refresh_agents_section aligned to the 0/1/2 writer contract. The remaining three-site cross-file duplication is an accepted ceiling with a defer: extraction trigger recorded at rewrite_block — do not re-report the duplication itself.
- doctor.sh fix strings swept to dispatcher form (8 sites); sync-rules.sh dead migration machinery removed (derive_repo_root, the removed ~/.cursor-sync-targets fallback's scaffolding, the v1.0-era claude/rules migration block); --show-version rebranded.
- Dispatcher: no-args is now a usage error (exit 64), same as unknown subcommands.
- Accepted ceilings / deferred minors (reject re-reports with a pointer, they are tracked in bead process-kit-020): raw 'unbound variable' aborts on dangling option values (--shell/--tool/--format/--version); init.sh stale-lock TOCTOU race between concurrent inits; init.sh fixed /tmp error-capture path; rc_file_for re-evaluating bashrc-vs-bash_profile per run (stranded inert block); fixture suite rename. Also accepted: ~/.playbook-aliases.sh orphaned on non-reference machines (decision 0002 consequences); the dispatcher has smoke + shellcheck coverage only (size-justified).

## Files

### scripts/house-rules

```
#!/usr/bin/env bash
# house-rules — single entry point for the kit's tooling (decision 0002 A1).
#
#   house-rules init [args]     project bootstrap        (scripts/init.sh)
#   house-rules doctor [args]   setup diagnosis          (scripts/doctor.sh)
#   house-rules sync [args]     rule sync to targets     (scripts/sync-rules.sh)
#
# The subcommand scripts remain independently runnable; this dispatcher is
# the documented form. Typical invocations:
#   bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" doctor --agent
#   hr doctor          # with the installed alias

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'USAGE'
Usage: house-rules <subcommand> [args...]

Subcommands:
  init      Bootstrap the current project (rules, checkers, profile, AGENTS.md)
  doctor    Diagnose project setup (--agent for machine-consumable output)
  sync      Sync rules from the kit to registered target repos

Each subcommand forwards its args unchanged; run one with --help for details.
USAGE
}

case "${1:-}" in
  init)   shift; exec bash "$SCRIPT_DIR/init.sh" "$@" ;;
  doctor) shift; exec bash "$SCRIPT_DIR/doctor.sh" "$@" ;;
  sync)   shift; exec bash "$SCRIPT_DIR/sync-rules.sh" "$@" ;;
  -h|--help|help)
    usage
    ;;
  "")
    # A missing subcommand is a usage error, same as an unknown one — an
    # accidentally empty variable must not print usage and "succeed".
    usage >&2
    exit 64
    ;;
  *)
    echo "house-rules: unknown subcommand '$1'" >&2
    usage >&2
    exit 64
    ;;
esac
```

### scripts/init.sh

```bash
#!/usr/bin/env bash
set -euo pipefail

# One-command project setup for house-rules.
# Replaces the 7+ manual steps in QUICKSTART.md with a single invocation.
#
# Usage:
#   ./scripts/init.sh                    # Interactive — asks for tool choice
#   ./scripts/init.sh --tool cursor      # Set up for Cursor
#   ./scripts/init.sh --tool claude       # Set up for Claude Code
#   ./scripts/init.sh --tool both         # Set up for both tools
#   ./scripts/init.sh --stealth           # Use bd init --stealth (personal repos)
#   ./scripts/init.sh --no-hooks          # Skip bd hooks install (default: install)
#   ./scripts/init.sh --skills            # Copy skills into .cursor/skills/
#   ./scripts/init.sh --help

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL=""
STEALTH=false
NO_HOOKS=false
SKILLS=false
PROJECT_ROOT="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)    TOOL="$2"; shift 2 ;;
    --stealth) STEALTH=true; shift ;;
    --no-hooks) NO_HOOKS=true; shift ;;
    --skills) SKILLS=true; shift ;;
    --help|-h)
      cat <<'EOF'
One-command project setup for house-rules.

Usage: init.sh [options]

Options:
  --tool cursor|claude|both   Which tool to set up for (default: ask)
  --stealth                   Use bd init --stealth (for personal repos)
  --no-hooks                  Skip bd hooks install (default: install beads git hooks)
  --skills                    Copy skill directories from the kit into .cursor/skills/
  --help                      Show this help

Run from the root of the project you want to set up.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# ---------- Concurrency lock (mkdir is atomic on all filesystems) ----------

LOCKDIR="$PROJECT_ROOT/.house-rules-init.lock"
# Clean stale locks older than 10 minutes
if [ -d "$LOCKDIR" ]; then
  lock_age=$(( $(date +%s) - $(stat -f %m "$LOCKDIR" 2>/dev/null || stat -c %Y "$LOCKDIR" 2>/dev/null || echo 0) ))
  if [ "$lock_age" -gt 600 ]; then
    rmdir "$LOCKDIR" 2>/dev/null || rm -rf "$LOCKDIR"
    echo "  Removed stale lock (age: ${lock_age}s)"
  fi
fi
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another house-rules init is running for this project. Exiting."
  exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

echo "=== house-rules init: $(basename "$PROJECT_ROOT") ==="
echo ""

# ---------- Prerequisites ----------

errors=0

if ! command -v git &>/dev/null; then
  echo "✗ git is not installed"
  errors=$((errors + 1))
else
  echo "✓ git $(git --version | awk '{print $3}')"
fi

if ! command -v bd &>/dev/null; then
  echo "✗ bd (beads) is not on PATH"
  if command -v brew &>/dev/null; then
    echo "  Fix: brew install beads"
  else
    echo "  Fix: See https://github.com/steveyegge/beads for install instructions"
  fi
  errors=$((errors + 1))
else
  echo "✓ bd $(bd --version 2>/dev/null || echo '(version unknown)')"
fi

if ! { [ -d "$PROJECT_ROOT/.git" ] || [ -f "$PROJECT_ROOT/.git" ]; }; then
  echo "✗ Not a git repository: $PROJECT_ROOT"
  echo "  Fix: Run from the root of a git repo, or run 'git init' first"
  errors=$((errors + 1))
else
  echo "✓ Git repository detected"
fi

if [ ! -d "$KIT_ROOT/cursor/rules" ]; then
  echo "✗ Kit repo not found at $KIT_ROOT"
  echo "  Fix: git clone https://github.com/kevglynn/house-rules ~/process-kit"
  errors=$((errors + 1))
else
  echo "✓ Kit repo at $KIT_ROOT"
fi

if [ $errors -gt 0 ]; then
  echo ""
  echo "Fix the $errors issue(s) above and re-run."
  exit 1
fi

# ---------- Tool choice ----------
#
# Security gate: refuse non-interactive invocation without an explicit
# --tool flag. Prevents prompt-injected agents from silently bootstrapping
# a repo behind the user's back — if there's no TTY, the flag must be
# passed explicitly (which means the agent had to declare the choice to
# the user before running).

if [ -z "$TOOL" ]; then
  if [ ! -t 0 ]; then
    echo "Error: --tool flag is required when stdin is not a terminal." >&2
    echo "" >&2
    echo "This script refuses non-interactive invocation without an" >&2
    echo "explicit tool choice to prevent silent bootstrapping." >&2
    echo "" >&2
    echo "Run with one of:" >&2
    echo "  --tool cursor   # Set up for Cursor" >&2
    echo "  --tool claude   # Set up for Claude Code" >&2
    echo "  --tool both     # Set up for both" >&2
    exit 1
  fi
  echo ""
  echo "Which tool are you setting up for?"
  echo "  1) Cursor"
  echo "  2) Claude Code"
  echo "  3) Both"
  read -rp "Choice [1/2/3]: " choice
  case "$choice" in
    1) TOOL="cursor" ;;
    2) TOOL="claude" ;;
    3) TOOL="both" ;;
    *) echo "Invalid choice. Use 1, 2, or 3."; exit 1 ;;
  esac
fi

echo ""

# ---------- Copy rules ----------

if [[ "$TOOL" == "cursor" || "$TOOL" == "both" ]]; then
  dest="$PROJECT_ROOT/.cursor/rules"
  mkdir -p "$dest"
  # Guard cp explicitly: set -e + an empty source glob or read-only
  # destination would otherwise abort the script mid-bootstrap with no
  # diagnostic and a misleading "0 rules" summary.
  if ! cp "$KIT_ROOT/cursor/rules/"*.mdc "$dest/" 2>/tmp/house-rules-init.cp.err; then
    echo "✗ Failed to copy Cursor rules → $dest"
    sed 's/^/    /' /tmp/house-rules-init.cp.err 2>/dev/null
    rm -f /tmp/house-rules-init.cp.err
    exit 1
  fi
  rm -f /tmp/house-rules-init.cp.err
  count=$(ls -1 "$dest/"*.mdc 2>/dev/null | wc -l | tr -d ' ')
  echo "✓ Copied $count Cursor rules → .cursor/rules/"
fi

if [[ "$TOOL" == "claude" || "$TOOL" == "both" ]]; then
  dest="$PROJECT_ROOT/.claude/rules"
  mkdir -p "$dest"
  if ! cp "$KIT_ROOT/claude/rules/"*.md "$dest/" 2>/tmp/house-rules-init.cp.err; then
    echo "✗ Failed to copy Claude rules → $dest"
    sed 's/^/    /' /tmp/house-rules-init.cp.err 2>/dev/null
    rm -f /tmp/house-rules-init.cp.err
    exit 1
  fi
  rm -f /tmp/house-rules-init.cp.err
  count=$(ls -1 "$dest/"*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "✓ Copied $count Claude Code rules → .claude/rules/"
fi

# ---------- Copy skills (opt-in) ----------

if $SKILLS; then
  skills_src="$KIT_ROOT/skills"
  # Tool-aware destinations: Claude Code reads .claude/skills/, Cursor reads
  # .cursor/skills/. A single hardcoded .cursor/skills/ dest previously left
  # --tool claude bootstraps with zero Claude-readable skills.
  skills_dests=""
  [[ "$TOOL" == "cursor" || "$TOOL" == "both" ]] && skills_dests=".cursor/skills"
  [[ "$TOOL" == "claude" || "$TOOL" == "both" ]] && skills_dests="$skills_dests .claude/skills"
  if [ -d "$skills_src" ]; then
    for skills_rel in $skills_dests; do
      skills_dest="$PROJECT_ROOT/$skills_rel"
      mkdir -p "$skills_dest"
      skills_count=0
      for skill_dir in "$skills_src"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        cp -rf "$skill_dir" "$skills_dest/"
        echo "  ↳ $skill_name"
        skills_count=$((skills_count + 1))
      done
      if [ "$skills_count" -gt 0 ]; then
        echo "✓ Copied $skills_count skill(s) → $skills_rel/"
      else
        echo "  (no skill directories found in $skills_src)"
      fi
    done
  else
    echo "  (no skills/ directory in the kit — skipping)"
  fi
fi

# ---------- Distributed CLIs (manifest-driven) ----------
#
# Every kit CLI that must live in the target repo is registered once in
# scripts/distributed-clis.list; this loop distributes each entry and
# doctor.sh drift-checks the same manifest. Per-script rationale
# and the field layout live in the manifest's header comments.

clis_manifest="$KIT_ROOT/scripts/distributed-clis.list"

if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r cli_name _cli_rest; do
    case "$cli_name" in ""|\#*) continue ;; esac
    cli_src="$KIT_ROOT/scripts/$cli_name"
    cli_dest="$PROJECT_ROOT/scripts/$cli_name"
    [ -f "$cli_src" ] || continue
    mkdir -p "$PROJECT_ROOT/scripts"
    if ! cp -f "$cli_src" "$cli_dest" 2>/tmp/house-rules-init.cp.err; then
      echo "✗ Failed to copy $cli_name → scripts/"
      sed 's/^/    /' /tmp/house-rules-init.cp.err 2>/dev/null
      rm -f /tmp/house-rules-init.cp.err
      exit 1
    fi
    rm -f /tmp/house-rules-init.cp.err
    chmod +x "$cli_dest"
    echo "✓ Copied $cli_name CLI → scripts/$cli_name"
  done < "$clis_manifest"
else
  echo "⚠ Distributed-CLI manifest missing at $clis_manifest — no kit CLIs distributed"
fi

# ---------- Conventions profile (data-shaped convention source) ----------
#
# The data file the distributed checkers read; ships verbatim (byte-drift-
# checked by house-rules doctor, SUMMARY key profile_drift). Ownership, skew,
# and inert-key rules: docs/operations.md.
# defer: hand-written parallel block instead of generalizing the manifest to
# data files. ceiling: duplicates the CLI-loop copy idiom per file. upgrade
# when: a second data-shaped file distributes.
profile_src="$KIT_ROOT/profiles/conventions.toml"
if [ -f "$profile_src" ]; then
  mkdir -p "$PROJECT_ROOT/profiles"
  if ! cp -f "$profile_src" "$PROJECT_ROOT/profiles/conventions.toml" 2>/tmp/house-rules-init.cp.err; then
    echo "✗ Failed to copy profiles/conventions.toml"
    sed 's/^/    /' /tmp/house-rules-init.cp.err 2>/dev/null
    rm -f /tmp/house-rules-init.cp.err
    exit 1
  fi
  rm -f /tmp/house-rules-init.cp.err
  echo "✓ Copied conventions profile → profiles/conventions.toml"
else
  echo "⚠ Conventions profile missing at $profile_src — distributed checkers will fall back to built-in grammars"
fi

# The CI gate that makes the ledger non-bypassable (not-overwriting, like
# the PR template — target repos may have customized it).
ledger_wf_src="$KIT_ROOT/templates/tdd-ledger-verify.yml"
ledger_wf_dest="$PROJECT_ROOT/.github/workflows/tdd-ledger-verify.yml"

if [ -f "$ledger_wf_src" ] && [ -f "$PROJECT_ROOT/scripts/tdd-ledger" ]; then
  if [ -f "$ledger_wf_dest" ]; then
    echo "✓ tdd-ledger CI workflow already exists (not overwriting)"
  else
    mkdir -p "$PROJECT_ROOT/.github/workflows"
    cp -f "$ledger_wf_src" "$ledger_wf_dest"
    echo "✓ Copied tdd-ledger CI workflow → .github/workflows/"
  fi
fi

# ---------- Beads init ----------

if [ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ]; then
  echo "✓ Beads already initialized (skipping bd init)"
else
  if $STEALTH; then
    BD_OUTPUT=$(echo N | bd init --stealth 2>&1) && echo "✓ Beads initialized (stealth mode)" || echo "  ✗ Beads init failed: $BD_OUTPUT"
  else
    BD_OUTPUT=$(echo N | bd init 2>&1) && echo "✓ Beads initialized" || echo "  ✗ Beads init failed: $BD_OUTPUT"
  fi
fi

# Bead-quality validation at creation time (the bead-authoring skill's
# validation phase prescribes this; without it the prescription is a silent
# no-op in fresh repos).
if command -v bd &>/dev/null && { [ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ]; }; then
  if bd config set validation.on-create warn >/dev/null 2>&1; then
    echo "✓ Set validation.on-create = warn"
  else
    echo "  (could not set validation.on-create — set manually: bd config set validation.on-create warn)"
  fi
fi

# ---------- Beads setup ----------

# Note: we skip 'bd setup cursor/claude' here because the kit's rules
# already provide beads workflow guidance with more depth than bd's built-in
# integration rule. Running bd setup would add a redundant beads.mdc.

# ---------- Beads git hooks (default-on) ----------
#
# Installs pre-commit / post-merge / pre-push (and related) shims so beads
# auto-exports and syncs across clones. See: bd hooks --help

HOOKS_INSTALLED=false
if $NO_HOOKS; then
  echo "✓ Skipping bd hooks install (--no-hooks)"
elif ! command -v bd &>/dev/null; then
  echo "  (bd not on PATH — skip bd hooks install)"
elif [ ! -d "$PROJECT_ROOT/.beads" ] && [ ! -d "$PROJECT_ROOT/.dolt" ]; then
  echo "  (no .beads — skip bd hooks install)"
else
  hooks_status=$(bd hooks list 2>/dev/null || true)
  if echo "$hooks_status" | grep -q '✓ pre-commit' \
    && echo "$hooks_status" | grep -q '✓ post-merge' \
    && echo "$hooks_status" | grep -q '✓ pre-push'; then
    echo "✓ Beads git hooks already installed (skipping bd hooks install)"
    HOOKS_INSTALLED=true
  elif BD_OUT=$(bd hooks install 2>&1); then
    echo "$BD_OUT"
    echo "✓ Installed beads git hooks"
    HOOKS_INSTALLED=true
  else
    echo "  ⚠ bd hooks install failed:"
    echo "$BD_OUT" | sed 's/^/    /'
    echo "    Fix manually from repo root: bd hooks install"
  fi
fi

# ---------- Scratchpad ----------

create_scratchpad() {
  local sp="$1"
  if [ ! -f "$sp" ]; then
    mkdir -p "$(dirname "$sp")"
    cat > "$sp" <<'SCRATCHPAD'
# Agent Scratchpad

## Background and Motivation

## Key Challenges and Analysis

## High-level Task Breakdown

## Current Status / Progress Tracking

## Executor's Feedback or Assistance Requests

## Lessons
SCRATCHPAD
    echo "✓ Created scratchpad at $(basename "$(dirname "$sp")")/$(basename "$sp")"
  else
    echo "✓ Scratchpad already exists at $(basename "$(dirname "$sp")")/$(basename "$sp") (not overwriting)"
  fi
}

if [[ "$TOOL" == "both" ]]; then
  create_scratchpad "$PROJECT_ROOT/.cursor/scratchpad.md"
  create_scratchpad "$PROJECT_ROOT/scratchpad.md"
elif [[ "$TOOL" == "cursor" ]]; then
  create_scratchpad "$PROJECT_ROOT/.cursor/scratchpad.md"
elif [[ "$TOOL" == "claude" ]]; then
  create_scratchpad "$PROJECT_ROOT/scratchpad.md"
fi

# ---------- Governance ----------

coc_src="$KIT_ROOT/CODE_OF_CONDUCT.md"
coc_dest="$PROJECT_ROOT/CODE_OF_CONDUCT.md"

if [ -f "$coc_src" ]; then
  if [ -f "$coc_dest" ]; then
    echo "✓ CODE_OF_CONDUCT.md already exists (not overwriting)"
  else
    cp -f "$coc_src" "$coc_dest"
    echo "✓ Copied CODE_OF_CONDUCT.md (Agentic Covenant)"
  fi
fi

# Canonical source is the kit's own .github/ copy (single source: GitHub
# reads it live on the kit repo, and init distributes the same file).
pr_template_src="$KIT_ROOT/.github/pull_request_template.md"
pr_template_dest="$PROJECT_ROOT/.github/pull_request_template.md"

if [ -f "$pr_template_src" ]; then
  if [ -f "$pr_template_dest" ]; then
    echo "✓ PR template already exists (not overwriting)"
  else
    mkdir -p "$PROJECT_ROOT/.github"
    cp -f "$pr_template_src" "$pr_template_dest"
    echo "✓ Copied PR template with Assisted-by disclosure"
  fi
fi

# ---------- AGENTS.md (per-repo agent discovery) ----------
#
# AGENTS.md is a de-facto 2026 convention read by Cursor, Claude Code,
# Codex, Copilot, and future agents. `bd init` also writes an AGENTS.md
# about beads, so we cannot assume the file is ours — we append a
# marker-delimited house-rules section, idempotent, respecting whatever
# content is already there.

agents_md="$PROJECT_ROOT/AGENTS.md"
# Marker prefix is "house-rules:" (final kit name, decision 0001 A1).
# Recognition of the predecessor playbook's legacy marker prefix was
# sunset 2026-08-06 (process-kit-26b) after a field sweep across every sync
# target and HOME artifact showed zero old-marker sections remaining.
agents_begin="<!-- BEGIN house-rules:agents-md -->"
agents_end="<!-- END house-rules:agents-md -->"

# Version stamp: sourced from the kit's VERSION file (single source of truth).
# Rendered as a machine-parseable marker line inside the section so
# doctor.sh can compare the target's stamp against the kit version.
kit_version="unknown"
kit_version_label="unknown"
if [ -f "$KIT_ROOT/VERSION" ]; then
  kit_version="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"
  kit_version_label="v$kit_version"
fi
generated_on="$(date -u +%Y-%m-%d)"

# Drift-key enumeration for the section text, generated from the manifest so
# the AGENTS.md contract can never lag a newly registered CLI. Manifest-
# external SUMMARY keys (profile_drift) are hand-listed in the heredoc —
# extend that line whenever such a key is added.
cli_drift_keys_md=""
if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r _cli_name cli_key _rest; do
    case "$_cli_name" in ""|\#*) continue ;; esac
    cli_drift_keys_md="${cli_drift_keys_md:+$cli_drift_keys_md | }\`$cli_key\`"
  done < "$clis_manifest"
fi

render_agents_section() {
  cat <<AGENTS_SECTION
$agents_begin
## house-rules

This project follows [house-rules](https://github.com/kevglynn/house-rules) — rules, skills, and scripts for working with coding agents.

**Rules location:** \`.cursor/rules/*.mdc\` (Cursor) and/or \`.claude/rules/*.md\` (Claude Code). Synced from \`\${PROCESS_KIT:-\$HOME/process-kit}\`. Do not edit in place.

**Ownership boundary:** \`.agents/overlay.md\` is project-editable (optional per-skill parameters; create it as needed). \`profiles/conventions.toml\`, when present, is kit-owned and drift-checked byte-for-byte — do not edit it here; change it in the kit and sync.

**Diagnose setup (human-readable):**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/house-rules" doctor
\`\`\`

**Diagnose (agent-consumable; structured exit codes + \`SUMMARY:\` line):**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/house-rules" doctor --agent
\`\`\`

Exit: \`0\`=ok, \`2\`=bootstrap_needed, \`3\`=drift, \`1\`=error. On exit 3 the SUMMARY key names what drifted: \`rules_drift_cursor\` | \`rules_drift_claude\` | \`rules_drift_both\` for stale rules, \`profile_drift\` for a stale \`profiles/conventions.toml\`, or ${cli_drift_keys_md:-a per-CLI drift key} for a stale distributed CLI (fix: re-copy the named file from the kit). See the \`agent-protocol\` block in \`~/CLAUDE.md\` for the full dispatch table.

**Sync rules with upstream:**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/house-rules" sync
\`\`\`

**Install the kit on a new machine:**
\`\`\`bash
git clone https://github.com/kevglynn/house-rules ~/process-kit
bash ~/process-kit/scripts/install-global-safety-net.sh   # per-machine, once
\`\`\`

Generated by \`house-rules init\` on ${generated_on} from house-rules ${kit_version_label}.
<!-- house-rules:version ${kit_version} -->
$agents_end
AGENTS_SECTION
}

# Replace the existing marker-delimited block in place (atomic tmp+mv), used
# when the section is present but its version stamp is stale or missing.
# Emits exactly one fresh section even if the file somehow carries several.
# Returns the shared writer contract (0 = written, 1 = I/O failure,
# 2 = malformed markers, warn-and-skip) — same codes as the block writers
# in install-aliases.sh and install-global-safety-net.sh, whose scan loop
# this mirrors (defer/extraction trigger noted at rewrite_block there).
refresh_agents_section() {
  local tmp in_block=0 emitted=0
  tmp="$(mktemp "${agents_md}.tmp.XXXXXX")" || return 1
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ] && [ "$line" = "$agents_begin" ]; then
      in_block=1
      if [ $emitted -eq 0 ]; then
        render_agents_section
        emitted=1
      fi
      continue
    fi
    if [ $in_block -eq 1 ]; then
      if [ "$line" = "$agents_end" ]; then
        in_block=0
      elif [ "$line" = "$agents_begin" ]; then
        # A BEGIN while a block is already open means the earlier BEGIN
        # lost its END and the scan is swallowing a real section plus any
        # user lines between them — stop here so the guard below refuses.
        break
      fi
      continue
    fi
    printf '%s\n' "$line"
  done < "$agents_md" > "$tmp"
  # Refuse the rewrite when the marker scan went wrong: an unpaired BEGIN
  # (in_block still open at EOF, or a nested BEGIN hit above) would have
  # swallowed user content into the tmp file — silently deleting it on
  # mv; a scan that consumed no BEGIN at all (emitted=0, e.g. CRLF or
  # indented marker lines that match the substring grep but not the
  # whole-line test) would claim success while rewriting nothing.
  if [ $in_block -eq 1 ] || [ $emitted -eq 0 ]; then
    rm -f "$tmp"
    echo "⚠ $agents_md: house-rules section markers are malformed (unpaired BEGIN or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
    return 2
  fi
  mv "$tmp" "$agents_md" || { rm -f "$tmp"; return 1; }
}

agents_refresh_failed=0
if [ -f "$agents_md" ] && grep -qF "$agents_begin" "$agents_md"; then
  if grep -qF "<!-- house-rules:version ${kit_version} -->" "$agents_md"; then
    echo "✓ AGENTS.md house-rules section current (${kit_version_label})"
  elif refresh_agents_section; then
    echo "✓ Refreshed AGENTS.md house-rules section → ${kit_version_label} (stamp was stale or missing)"
  else
    # Guard refusal (or write failure): warned on stderr above. The rest
    # of the bootstrap is still worth finishing, but the exit code must
    # not claim a clean setup while the section is stale.
    agents_refresh_failed=1
    echo "✗ AGENTS.md house-rules section is stale but was NOT refreshed — repair the marker lines and re-run init" >&2
  fi
elif [ -f "$agents_md" ]; then
  # Atomic write: stage to mktemp, then mv. A partial multi-line append
  # via { ... } >> would otherwise leave AGENTS.md with an orphan BEGIN
  # marker — and the next-run idempotency check (grep -qF "$agents_begin")
  # would falsely report "already present" without repairing the partial
  # block.
  agents_tmp="$(mktemp "${agents_md}.tmp.XXXXXX")"
  {
    cat "$agents_md"
    [ -n "$(tail -c1 "$agents_md" 2>/dev/null)" ] && printf '\n'
    printf '\n'
    render_agents_section
  } > "$agents_tmp"
  mv "$agents_tmp" "$agents_md"
  echo "✓ Appended house-rules section to existing AGENTS.md"
else
  agents_tmp="$(mktemp "${agents_md}.tmp.XXXXXX")"
  {
    printf '# AGENTS.md\n\n'
    printf 'Any agent landing in this repo: start here.\n\n'
    render_agents_section
  } > "$agents_tmp"
  mv "$agents_tmp" "$agents_md"
  echo "✓ Created AGENTS.md with house-rules section"
fi

# ---------- Sync targets ----------

# Throwaway bootstraps (test/verification runs under /tmp or $TMPDIR) must
# not register: dead entries surface as 'target does not exist' warnings on
# every later sync-rules.sh run until removed by hand.
TARGETS_FILE="$HOME/.house-rules-sync-targets"
tmp_root="${TMPDIR:-/tmp}"
case "$PROJECT_ROOT/" in
  "${tmp_root%/}/"* | /tmp/*)
    echo "– Skipped ~/.house-rules-sync-targets registration (throwaway path under ${tmp_root%/})"
    ;;
  *)
    if [ -f "$TARGETS_FILE" ] && grep -qF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
      echo "✓ Already in ~/.house-rules-sync-targets"
    else
      echo "$PROJECT_ROOT" >> "$TARGETS_FILE"
      echo "✓ Added to ~/.house-rules-sync-targets"
    fi
    ;;
esac

# ---------- Summary ----------

echo ""
echo "=== Setup complete ==="
echo ""
echo "What's ready:"
echo "  • $(ls -1 "$PROJECT_ROOT/.cursor/rules/"*.mdc 2>/dev/null | wc -l | tr -d ' ') Cursor rules" 2>/dev/null || true
echo "  • $(ls -1 "$PROJECT_ROOT/.claude/rules/"*.md 2>/dev/null | wc -l | tr -d ' ') Claude rules" 2>/dev/null || true
if $SKILLS; then
  for skills_rel in ${skills_dests:-}; do
    echo "  • $(ls -1d "$PROJECT_ROOT/$skills_rel/"*/ 2>/dev/null | wc -l | tr -d ' ') skills ($skills_rel/)" 2>/dev/null || true
  done
fi
echo "  • Beads task tracking (bd list, bd ready, bd create)"
if $HOOKS_INSTALLED; then
  echo "  • Beads git hooks (bd hooks install — auto-export / sync on commit & push)"
fi
if $NO_HOOKS; then
  echo "  • Beads git hooks skipped — run bd hooks install when ready"
fi
echo "  • Scratchpad for cross-session context"
[ -f "$coc_dest" ] && echo "  • Agentic Covenant (CODE_OF_CONDUCT.md)"
if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r cli_name _key _header _note cli_label cli_detail; do
    case "$cli_name" in ""|\#*) continue ;; esac
    [ -f "$PROJECT_ROOT/scripts/$cli_name" ] && \
      echo "  • $cli_label (scripts/$cli_name — $cli_detail)"
  done < "$clis_manifest"
fi
[ -f "$PROJECT_ROOT/profiles/conventions.toml" ] && \
  echo "  • Conventions profile (profiles/conventions.toml — data source the checkers read; kit-owned, drift-checked)"
[ -f "$ledger_wf_dest" ] && echo "  • TDD ledger CI gate (.github/workflows/tdd-ledger-verify.yml)"
[ -f "$pr_template_dest" ] && echo "  • PR template with Assisted-by disclosure (.github/pull_request_template.md)"
echo ""
echo "Next steps:"
echo "  1. Open this project in your editor"
echo '  2. Say "Planner mode" to break down a feature into tasks'
echo '  3. Say "Executor mode" to start implementing'
echo "  4. Run: bd prime (agent does this automatically at session start)"
echo "  5. ⚠ Rules take effect on next session start — restart your editor/CLI"
echo ""
echo "Verify setup: bash \"$KIT_ROOT/scripts/house-rules\" doctor"
if [ "$agents_refresh_failed" -eq 1 ]; then
  exit 1
fi
```

### scripts/doctor.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

# Validates the kit setup for the current project.
# Reports issues with fix commands. CI-friendly exit code.
#
# Usage:
#   ./scripts/doctor.sh                    # Check current directory
#   ./scripts/doctor.sh /path/to/project   # Check specific project
#   ./scripts/doctor.sh --agent            # Agent-consumable output
#   ./scripts/doctor.sh --help
#
# --agent mode emits a final "SUMMARY: <key>" line and uses structured exit
# codes for agent branching. See the agent-protocol global safety-net block
# for the full contract.
#
# Exit codes:
#   0 = ok (no action needed)
#   2 = bootstrap_needed (no rules in this repo)
#   3 = drift (kit-managed files present but stale vs kit source:
#       rules_drift_*, profile_drift, or a per-CLI key from
#       scripts/distributed-clis.list — dispatch on the SUMMARY key)
#   1 = generic error / other failure
#
# SUMMARY keys (--agent mode) for rules_drift carry the format that needs
# remediation: rules_drift_cursor, rules_drift_claude, rules_drift_both.
# profile_drift means profiles/conventions.toml is stale vs the kit copy.
# Each distributed CLI carries its own drift key, registered in
# scripts/distributed-clis.list (currently ledger_drift, defer_lint_drift,
# close_reason_lint_drift, banned_token_scan_drift — the manifest is the
# source of truth); the key means that scripts/<name> is stale vs the kit
# copy. Agents must dispatch on the specific key, not the generic exit
# code, to avoid running sync-rules.sh with the wrong --format.

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_MODE=false
PROJECT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)  AGENT_MODE=true; shift ;;
    -h|--help)
      cat <<'EOF'
Validates kit setup for a project. Reports issues with fix commands.

Usage: doctor.sh [project-path] [--agent]

Checks:
  • bd (beads) is on PATH
  • Agent rules are present and match the canonical source
  • Each distributed CLI in scripts/distributed-clis.list (if present in
    the target) matches the kit copy
  • The conventions profile (profiles/conventions.toml, if present in the
    target) matches the kit copy byte-for-byte
  • Kit-resident references (skills/…, templates/…) cited by distributed
    rules resolve somewhere on this machine (warn-only)
  • AGENTS.md house-rules section version stamp matches the kit VERSION (warn-only)
  • Beads is initialized (bd ping + bd list)
  • Beads git hooks recommended (pre-commit, post-merge, pre-push)
  • Scratchpad exists with correct sections
  • Project is in ~/.house-rules-sync-targets
  • Worktree hook present (if repo has worktrees)
  • Global safety net installed (per-machine agent rule blocks)

Flags:
  --agent   Emit a machine-consumable SUMMARY line and use structured
            exit codes (0=ok, 2=bootstrap_needed, 3=drift, 1=error).
            Exit 3 SUMMARY keys: rules_drift_cursor|rules_drift_claude|
            rules_drift_both (stale rules), profile_drift (stale
            profiles/conventions.toml), or the stale CLI's drift key
            from scripts/distributed-clis.list (rules drift wins when
            several drift, then profile_drift; CLI keys follow the
            manifest's line order).
  --help    Show this help.

Exit codes (human mode): 0 = all pass, 1 = issues found.
EOF
      exit 0
      ;;
    --*) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
    *)
      if [ -z "$PROJECT_ROOT" ]; then
        PROJECT_ROOT="$1"
      else
        echo "Too many arguments (use --help)" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

# --- Path validation (hardening for --agent mode, light checks otherwise) ---
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "ERROR: project path does not exist: $PROJECT_ROOT" >&2
  if $AGENT_MODE; then echo "SUMMARY: error"; fi
  exit 1
fi
# Resolve to absolute path (no symlink resolution assumptions)
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

echo "=== house-rules doctor: $(basename "$PROJECT_ROOT") ==="
echo ""

pass=0
fail=0
warn=0

# Agent-mode state: tracks the specific class of issue so SUMMARY can
# select the most accurate remediation category. The authoritative
# precedence chain is documented once, at the SUMMARY block below.
#
# rules_drift is split per-format so the SUMMARY can map directly to the
# correct sync-rules.sh --format flag. A flat rules_stale flag would
# default the agent's remediation to --format cursor (sync-rules' default)
# and create unwanted .cursor/rules/ files on Claude-only projects.
bootstrap_missing=0
cursor_stale=0
claude_stale=0
# Space-separated SUMMARY keys of stale distributed CLIs, appended in
# manifest order — so the first entry is the highest-precedence CLI drift.
cli_stale_keys=""
# Set to 1 when the distributed conventions profile drifts from the kit copy.
profile_stale=0

check_pass() { echo "  ✓ $1"; pass=$((pass + 1)); }
check_fail() { echo "  ✗ $1"; echo "    Fix: $2"; fail=$((fail + 1)); }
check_warn() { echo "  ⚠ $1"; warn=$((warn + 1)); }

# ---------- Prerequisites ----------

echo "Prerequisites:"

if command -v bd &>/dev/null; then
  check_pass "bd on PATH ($(bd --version 2>/dev/null || echo 'version unknown'))"
else
  check_fail "bd not on PATH" "brew install beads"
fi

if command -v git &>/dev/null; then
  check_pass "git on PATH"
else
  check_fail "git not on PATH" "Install git"
fi

echo ""

# ---------- Rules ----------

echo "Rules:"

cursor_rules="$PROJECT_ROOT/.cursor/rules"
claude_rules="$PROJECT_ROOT/.claude/rules"
has_cursor=false
has_claude=false

if [ -d "$cursor_rules" ]; then
  has_cursor=true
  mdc_count=$(ls -1 "$cursor_rules/"*.mdc 2>/dev/null | wc -l | tr -d ' ')
  src_count=$(ls -1 "$KIT_ROOT/cursor/rules/"*.mdc 2>/dev/null | wc -l | tr -d ' ')
  # Check that every canonical rule is present and current.
  # Extra rules from other tools (e.g. Jawnt) are fine — only flag missing or stale.
  stale=0
  missing=0
  for f in "$KIT_ROOT/cursor/rules/"*.mdc; do
    base="$(basename "$f")"
    if [ ! -f "$cursor_rules/$base" ]; then
      missing=$((missing + 1))
    elif ! diff -q "$f" "$cursor_rules/$base" > /dev/null 2>&1; then
      stale=$((stale + 1))
    fi
  done
  if [ $missing -eq 0 ] && [ $stale -eq 0 ]; then
    extra=$((mdc_count - src_count))
    if [ "$extra" -gt 0 ]; then
      check_pass "Cursor rules: $src_count kit files up to date (+$extra from other tools)"
    else
      check_pass "Cursor rules: $mdc_count files, all up to date"
    fi
  else
    issues=""
    [ $missing -gt 0 ] && issues="$missing missing"
    [ $stale -gt 0 ] && { [ -n "$issues" ] && issues="$issues, "; issues="${issues}$stale stale"; }
    check_fail "Cursor rules: $issues (of $src_count expected)" "bash \"$KIT_ROOT/scripts/house-rules\" sync --format cursor"
    cursor_stale=1
  fi
else
  check_warn "No Cursor rules (.cursor/rules/ not found)"
fi

if [ -d "$claude_rules" ]; then
  has_claude=true
  md_count=$(ls -1 "$claude_rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "$md_count" -eq 0 ]; then
    check_fail "Claude rules directory exists but is empty" "bash \"$KIT_ROOT/scripts/house-rules\" sync --format claude"
    claude_stale=1
  else
    claude_src="$KIT_ROOT/claude/rules"
    claude_src_count=$(ls -1 "$claude_src/"*.md 2>/dev/null | wc -l | tr -d ' ')
    if [ "$md_count" -eq "$claude_src_count" ]; then
      claude_stale=0
      for f in "$claude_src/"*.md; do
        base="$(basename "$f")"
        if [ -f "$claude_rules/$base" ]; then
          if ! diff -q "$f" "$claude_rules/$base" > /dev/null 2>&1; then
            claude_stale=$((claude_stale + 1))
          fi
        else
          claude_stale=$((claude_stale + 1))
        fi
      done
      if [ $claude_stale -eq 0 ]; then
        check_pass "Claude rules: $md_count files, all up to date"
      else
        check_fail "Claude rules: $claude_stale of $md_count are stale" "bash \"$KIT_ROOT/scripts/house-rules\" sync --format claude"
      fi
    else
      check_fail "Claude rules: $md_count files (expected $claude_src_count)" "bash \"$KIT_ROOT/scripts/house-rules\" sync --format claude"
      claude_stale=1
    fi
  fi
fi

if ! $has_cursor && ! $has_claude; then
  check_fail "No rules found (neither .cursor/rules/ nor .claude/rules/)" "bash \"$KIT_ROOT/scripts/house-rules\" init --tool cursor|claude|both"
  bootstrap_missing=1
fi

# Warn if rules directories are gitignored (skip for the kit repo itself,
# where .cursor/* is intentionally gitignored since cursor/rules/ is the source)
is_kit_repo=false
[[ "$(cd "$PROJECT_ROOT" && pwd)" == "$(cd "$KIT_ROOT" && pwd)" ]] && is_kit_repo=true

if ! $is_kit_repo; then
  if $has_claude && git -C "$PROJECT_ROOT" check-ignore -q ".claude/rules/test.md" 2>/dev/null; then
    check_warn ".claude/rules/ appears to be gitignored — rules won't be committed"
  fi
  if $has_cursor && git -C "$PROJECT_ROOT" check-ignore -q ".cursor/rules/test.mdc" 2>/dev/null; then
    check_warn ".cursor/rules/ appears to be gitignored — rules won't be committed"
  fi
  # Text-only advisory (never affects SUMMARY or exit codes): the overlay
  # is the project-editable surface; its absence just means skills run on
  # their documented defaults. Ownership boundary: skills/README.md
  # § Overlay Convention.
  if { $has_cursor || $has_claude; } && [ ! -f "$PROJECT_ROOT/.agents/overlay.md" ]; then
    check_warn "No .agents/overlay.md — skills run on documented defaults (optional per-project parameters; project-editable, unlike the kit-owned profiles/conventions.toml)"
  fi
fi

echo ""

# ---------- Distributed CLIs (manifest-driven) ----------
#
# Every kit CLI registered in scripts/distributed-clis.list is kit-managed:
# init.sh copies it with cp -f (same semantics as rules), so each
# drift-checks against the kit copy the same way rules do. The tdd-ledger
# CI workflow (.github/workflows/tdd-ledger-verify.yml) is NOT drift-checked
# — init treats it as not-overwriting, so target repos may legitimately
# customize it; we only note its absence when that CLI is present.

clis_manifest="$KIT_ROOT/scripts/distributed-clis.list"

if [ ! -f "$clis_manifest" ]; then
  echo "Distributed CLIs:"
  check_warn "Manifest missing at $clis_manifest — cannot drift-check kit CLIs"
  echo ""
else
  while IFS='|' read -r cli_name cli_key cli_header cli_note _label _detail; do
    case "$cli_name" in ""|\#*) continue ;; esac
    echo "$cli_header:"
    cli_src="$KIT_ROOT/scripts/$cli_name"
    cli_dest="$PROJECT_ROOT/scripts/$cli_name"
    if [ ! -f "$cli_src" ]; then
      check_warn "Kit copy missing at $cli_src — cannot drift-check $cli_name"
    elif [ ! -f "$cli_dest" ]; then
      # Informational, not a failure: the repo may predate the CLI or not use it.
      echo "  – $cli_name not distributed here (optional — re-run init.sh to add it)"
    else
      if diff -q "$cli_src" "$cli_dest" > /dev/null 2>&1; then
        check_pass "$cli_name CLI matches the kit copy"
      else
        check_fail "$cli_name CLI is stale vs the kit copy — $cli_note" \
          "cp -f \"$cli_src\" \"$cli_dest\" && chmod +x \"$cli_dest\""
        cli_stale_keys="$cli_stale_keys $cli_key"
      fi
      if [ "$cli_name" = "tdd-ledger" ]; then
        if ! $is_kit_repo && [ ! -f "$PROJECT_ROOT/.github/workflows/tdd-ledger-verify.yml" ]; then
          check_warn "tdd-ledger CLI present but no CI gate — copy templates/tdd-ledger-verify.yml → .github/workflows/"
        fi
        # Last-mile reminder: the workflow only actually gates merges if branch
        # protection marks it required — a state on the forge that no local tool
        # can inspect, so this is a reminder line rather than a check.
        if [ -f "$PROJECT_ROOT/.github/workflows/tdd-ledger-verify.yml" ]; then
          echo "  – Reminder: the CI workflow only blocks merges if 'tdd-ledger verify' is a required status check in branch protection (cannot be verified locally)"
        fi
      fi
    fi
    # Registration self-check: the human-facing dispatch table in
    # global-safety-net/agent-protocol.md is the one site the manifest
    # cannot generate — this warn is how a missing row gets caught
    # (the gap that shipped twice before the manifest existed).
    if [ -f "$KIT_ROOT/global-safety-net/agent-protocol.md" ] && \
       ! grep -qF "\`$cli_key\`" "$KIT_ROOT/global-safety-net/agent-protocol.md"; then
      check_warn "SUMMARY key $cli_key is not documented in global-safety-net/agent-protocol.md — add a dispatch-table row"
    fi
    echo ""
  done < "$clis_manifest"
fi

# ---------- Conventions profile (data-shaped convention source) ----------
#
# The data file the distributed checkers read; ships verbatim via
# house-rules init and byte-drift-checks here. Ownership and skew rules:
# docs/operations.md. Must run AFTER the CLI loop — the skew warn below
# reads cli_stale_keys.
# defer: hand-written parallel block instead of generalizing the manifest to
# data files. ceiling: re-implements the CLI loop's four states + the
# registration self-check per file. upgrade when: a second data-shaped file
# distributes.
echo "Conventions profile:"
profile_src="$KIT_ROOT/profiles/conventions.toml"
profile_dest="$PROJECT_ROOT/profiles/conventions.toml"
profile_present=false
if [ ! -f "$profile_src" ]; then
  check_warn "Kit copy missing at $profile_src — cannot drift-check the profile"
elif [ ! -f "$profile_dest" ]; then
  # Informational, not a failure: the repo may predate the profile or not use it.
  echo "  – profiles/conventions.toml not distributed here (optional — re-run init.sh to add it)"
else
  profile_present=true
  if diff -q "$profile_src" "$profile_dest" > /dev/null 2>&1; then
    check_pass "profiles/conventions.toml matches the kit copy"
  else
    check_fail "profiles/conventions.toml is stale vs the kit copy — checker verdicts and rule fragments may have diverged" \
      "cp -f \"$profile_src\" \"$profile_dest\""
    profile_stale=1
  fi
fi
# Version-skew guard: a stale PROFILE-READING checker can mis-scan the current
# profile (e.g. a pre-token-catalog scanner self-flags on a profile that now
# carries the token list). tdd-ledger never reads the profile, so ledger_drift
# alone must not fire this. Keys hardcoded: extend this list when a new
# profile-reading CLI joins the manifest.
case "$cli_stale_keys" in
  *defer_lint_drift*|*close_reason_lint_drift*|*banned_token_scan_drift*)
    if $profile_present; then
      check_warn "Conventions profile present but a profile-reading checker is stale — re-copy the stale checker(s) and the profile together (or re-run init.sh); a stale checker may mis-scan the current profile"
    fi ;;
esac
# Registration self-check: profile_drift is a manifest-external SUMMARY key,
# so nothing generates its documentation sites — the dispatch-table row in
# global-safety-net/agent-protocol.md (guarded here, same as the CLIs) and
# the hand-extended enumerations in this script's header/--help and init's
# rendered AGENTS.md section (not guarded; update by hand with any new key).
if [ -f "$KIT_ROOT/global-safety-net/agent-protocol.md" ] && \
   ! grep -qF "\`profile_drift\`" "$KIT_ROOT/global-safety-net/agent-protocol.md"; then
  check_warn "SUMMARY key profile_drift is not documented in global-safety-net/agent-protocol.md — add a dispatch-table row"
fi
echo ""

# ---------- Kit-resident references ----------
#
# Distributed rules cite skills/<name> and templates/<file> paths under the
# resolution law in operating-model.mdc: in-project copy → machine-global
# skills dir → kit clone. A pointer that resolves nowhere is a setup gap.
# Warn-only: the rules themselves instruct agents to note-don't-skip.

echo "Kit-resident references:"

ref_total=0
ref_unresolved=0
refs="$(grep -rhoE '(skills|templates)/[A-Za-z0-9._-]+' \
          "$PROJECT_ROOT/.cursor/rules" "$PROJECT_ROOT/.claude/rules" 2>/dev/null \
        | sed 's/\.$//' | sort -u)"
if [ -z "$refs" ]; then
  echo "  – No kit-resident references cited by distributed rules (or no rules present)"
else
  while IFS= read -r ref; do
    [ -n "$ref" ] || continue
    ref_total=$((ref_total + 1))
    ref_kind="${ref%%/*}"
    ref_name="${ref#*/}"
    resolved=false
    if [ "$ref_kind" = "skills" ]; then
      for cand in "$PROJECT_ROOT/.cursor/skills/$ref_name" \
                  "$PROJECT_ROOT/.claude/skills/$ref_name" \
                  "$PROJECT_ROOT/skills/$ref_name" \
                  "$HOME/.cursor/skills/$ref_name" \
                  "$HOME/.claude/skills/$ref_name" \
                  "$KIT_ROOT/skills/$ref_name"; do
        [ -e "$cand" ] && resolved=true && break
      done
    else
      for cand in "$PROJECT_ROOT/templates/$ref_name" \
                  "$KIT_ROOT/templates/$ref_name"; do
        [ -e "$cand" ] && resolved=true && break
      done
    fi
    if ! $resolved; then
      ref_unresolved=$((ref_unresolved + 1))
      check_warn "$ref cited by distributed rules resolves nowhere (project → global → kit clone)"
    fi
  done <<< "$refs"
  if [ $ref_unresolved -eq 0 ]; then
    check_pass "All $ref_total kit-resident references cited by rules resolve"
  fi
fi

echo ""

# ---------- AGENTS.md house-rules section ----------
#
# init.sh stamps the AGENTS.md house-rules section with a
# machine-parseable version marker (<!-- house-rules:version X.Y.Z -->)
# sourced from the kit's VERSION file. A stale stamp means the section's
# doctor/sync instructions and exit-code contract may describe an older kit.
# (Legacy predecessor-prefix marker recognition was sunset 2026-08-06,
# process-kit-26b, after a field sweep showed zero old-marker artifacts.)
#
# Deliberately text-only (warn — no exit 3 / SUMMARY key): the section is
# discovery documentation, not executable machinery like rules or the
# tdd-ledger, so a stale stamp cannot break agent behavior mid-task. Keeping
# it out of the SUMMARY enum also keeps the agent-protocol dispatch table
# stable for existing agents.

echo "AGENTS.md:"

agents_md="$PROJECT_ROOT/AGENTS.md"
agents_marker="<!-- BEGIN house-rules:agents-md -->"
kit_version=""
[ -f "$KIT_ROOT/VERSION" ] && kit_version="$(tr -d '[:space:]' < "$KIT_ROOT/VERSION")"

if $is_kit_repo; then
  echo "  – kit repo itself: AGENTS.md is authored, not generated (stamp check skipped)"
elif [ ! -f "$agents_md" ] || ! grep -qF "$agents_marker" "$agents_md" 2>/dev/null; then
  # Informational, not a failure: pre-AGENTS.md bootstraps are legitimate.
  echo "  – No house-rules section in AGENTS.md (re-run init.sh to add it)"
elif [ -z "$kit_version" ]; then
  check_warn "Kit VERSION file missing at $KIT_ROOT/VERSION — cannot check the AGENTS.md section stamp"
else
  target_version="$(sed -nE 's/.*<!-- house-rules:version ([^ ]*) -->.*/\1/p' "$agents_md" | head -n1)"
  if [ "$target_version" = "$kit_version" ]; then
    check_pass "AGENTS.md house-rules section current (v$kit_version)"
  else
    check_warn "AGENTS.md house-rules section is stamped ${target_version:-<no stamp — pre-versioning init>} but the kit is v$kit_version — re-run: bash \"$KIT_ROOT/scripts/house-rules\" init --tool cursor|claude|both (refreshes the section in place)"
  fi
fi

echo ""

# ---------- Beads ----------

echo "Beads:"

if [ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ]; then
  check_pass "Beads directory exists"
  if command -v bd &>/dev/null; then
    if bd ping > /dev/null 2>&1; then
      check_pass "bd ping ok (database reachable)"
      if bd list --status=open > /dev/null 2>&1; then
        check_pass "bd list works (database healthy)"
      else
        check_fail "bd list failed (database may be corrupted)" "bd doctor --agent"
      fi
      hooks_list_out=$(bd hooks list 2>/dev/null || true)
      if echo "$hooks_list_out" | grep -q '✓ pre-commit' \
        && echo "$hooks_list_out" | grep -q '✓ post-merge' \
        && echo "$hooks_list_out" | grep -q '✓ pre-push'; then
        check_pass "Beads git hooks: pre-commit, post-merge, pre-push installed"
      else
        check_warn "Beads git hooks missing or incomplete (bd recommends pre-commit, post-merge, pre-push) — fix: bd hooks install"
      fi
    else
      check_fail "bd ping failed (database unreachable)" "bd doctor --agent"
    fi
  fi
else
  check_fail "Beads not initialized" "bd init (or bd init --stealth for personal repos)"
fi

echo ""

# ---------- Scratchpad ----------

echo "Scratchpad:"

scratchpad=""
if [ -f "$PROJECT_ROOT/.cursor/scratchpad.md" ]; then
  scratchpad="$PROJECT_ROOT/.cursor/scratchpad.md"
elif [ -f "$PROJECT_ROOT/scratchpad.md" ]; then
  scratchpad="$PROJECT_ROOT/scratchpad.md"
fi

if [ -n "$scratchpad" ]; then
  check_pass "Scratchpad found at $(basename "$(dirname "$scratchpad")")/$(basename "$scratchpad")"
  missing_sections=0
  for section in "Background and Motivation" "Key Challenges and Analysis" "High-level Task Breakdown" "Current Status / Progress Tracking" "Executor's Feedback or Assistance Requests" "Lessons"; do
    if ! grep -qF "$section" "$scratchpad" 2>/dev/null; then
      missing_sections=$((missing_sections + 1))
    fi
  done
  if [ $missing_sections -eq 0 ]; then
    check_pass "All 6 required sections present"
  else
    check_warn "$missing_sections section(s) missing — see operating-model.mdc for the required titles"
  fi
else
  check_fail "No scratchpad found" "bash \"$KIT_ROOT/scripts/house-rules\" init --tool cursor|claude|both (creates it automatically)"
fi

echo ""

# ---------- Sync targets ----------

echo "Sync targets:"

TARGETS_FILE="$HOME/.house-rules-sync-targets"
has_beads=false
[ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ] && has_beads=true

if $is_kit_repo; then
  # The kit is the sync SOURCE — registration as a target is inapplicable.
  echo "  – kit repo itself: sync source, not a target (registration check skipped)"
elif [ -f "$TARGETS_FILE" ]; then
  if grep -qF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
    check_pass "Project is in ~/.house-rules-sync-targets"
  elif $has_beads; then
    check_fail "Beads project not in ~/.house-rules-sync-targets — rules will drift silently" \
      "bash \"$KIT_ROOT/scripts/house-rules\" init --tool cursor|claude|both"
  else
    check_fail "Project not in ~/.house-rules-sync-targets" "echo \"$PROJECT_ROOT\" >> ~/.house-rules-sync-targets"
  fi
else
  check_fail "\$HOME/.house-rules-sync-targets doesn't exist" "echo \"$PROJECT_ROOT\" >> \$HOME/.house-rules-sync-targets"
fi

echo ""

# ---------- Governance ----------

echo "Governance:"

if [ -f "$PROJECT_ROOT/CODE_OF_CONDUCT.md" ]; then
  if grep -qF "Agentic Covenant" "$PROJECT_ROOT/CODE_OF_CONDUCT.md" 2>/dev/null; then
    check_pass "CODE_OF_CONDUCT.md present (Agentic Covenant)"
  else
    check_warn "CODE_OF_CONDUCT.md exists but may not be the Agentic Covenant"
  fi
else
  check_warn "No CODE_OF_CONDUCT.md — consider adopting the Agentic Covenant"
fi

echo ""

# ---------- Global safety net (per-machine) ----------

echo "Global safety net:"

installer="$KIT_ROOT/scripts/install-global-safety-net.sh"
if [ -x "$installer" ]; then
  status_output="$(bash "$installer" --check 2>&1)"
  status_code=$?
  # The installer's --check always emits ✗/⚠ on nonzero exit, so the
  # branching collapses to: ok / out-of-date / not-installed.
  if [ $status_code -eq 0 ]; then
    check_pass "Global agent-identity block installed in ~/CLAUDE.md"
  elif printf '%s\n' "$status_output" | grep -qF "out of date"; then
    check_warn "Global safety net present in ~/CLAUDE.md but out of date — re-run: bash $installer"
  else
    check_warn "Global safety net not installed — optional but recommended for new repos: bash $installer"
  fi
else
  check_warn "Global safety net installer not found at $installer"
fi

# Explicitly unverifiable channel: Cursor either auto-imports ~/CLAUDE.md as
# an always-applied rule (settings toggle "Include Third-Party Plugins,
# Skills, and Other Configs" — undocumented behavior, toggle state not
# readable from disk) or needs the manual user-rules paste. Neither is
# verifiable by tooling. Reminder line only (never pass/fail).
echo "  – Cursor channel not verifiable by tooling — check Settings → Rules for the auto-imported CLAUDE rule (tracks ~/CLAUDE.md on restart); only if it's absent, paste manually: bash $installer --print-cursor-snippet"

echo ""

# ---------- Worktree hook ----------

echo "Worktree support:"

if [ -f "$PROJECT_ROOT/.cursor/worktrees.json" ]; then
  check_pass "Worktree hook present (.cursor/worktrees.json)"
else
  wt_count=$(git -C "$PROJECT_ROOT" worktree list --porcelain 2>/dev/null | grep -c '^worktree ')
  [ -z "$wt_count" ] && wt_count=0
  if [ "$wt_count" -gt 1 ]; then
    check_warn "Repo has $wt_count worktrees but no .cursor/worktrees.json hook"
  else
    check_pass "No worktrees (hook not needed yet)"
  fi
fi

echo ""

# ---------- Summary ----------

total=$((pass + fail + warn))
echo "=== Results: $pass passed, $fail failed, $warn warnings (of $total checks) ==="

# --- Agent-mode structured summary + exit ---
#
# Priority: bootstrap_needed > rules_drift > profile_drift > per-CLI drift
# keys in manifest line order (scripts/distributed-clis.list) > error > ok.
# The SUMMARY line is a stable contract; do not emit user-controlled paths
# or free-form strings — only the fixed rules keys and the manifest's
# registered per-CLI keys.
#
# rules_drift is split tri-state so the agent contract maps directly to a
# specific sync-rules.sh --format flag. Without this, an agent following
# the agent-protocol's "bash sync-rules.sh" recommendation on a Claude-only
# project would default to --format cursor (the script's default) and
# silently create unwanted .cursor/rules/ files in the target.
#
# Per-CLI drift keys reuse exit 3 (drift class) with their own SUMMARY
# keys rather than new exit codes, so the agent-protocol exit table stays
# stable. Rules drift wins the SUMMARY when several drift (existing agents
# already dispatch on rules_drift_*); among stale CLIs the first in
# manifest order wins; the losing findings are still in the text output.
cli_first_stale="${cli_stale_keys# }"
cli_first_stale="${cli_first_stale%% *}"
if $AGENT_MODE; then
  if [ $bootstrap_missing -eq 1 ]; then
    echo ""
    echo "SUMMARY: bootstrap_needed"
    exit 2
  # -ge, not -eq: claude_stale is a per-file counter (the Claude rules
  # check counts stale files), so two stale rules used to skip every
  # rules_drift_* branch and fall through to SUMMARY: error.
  elif [ $cursor_stale -ge 1 ] && [ $claude_stale -ge 1 ]; then
    echo ""
    echo "SUMMARY: rules_drift_both"
    exit 3
  elif [ $cursor_stale -ge 1 ]; then
    echo ""
    echo "SUMMARY: rules_drift_cursor"
    exit 3
  elif [ $claude_stale -ge 1 ]; then
    echo ""
    echo "SUMMARY: rules_drift_claude"
    exit 3
  elif [ $profile_stale -eq 1 ]; then
    echo ""
    echo "SUMMARY: profile_drift"
    exit 3
  elif [ -n "$cli_first_stale" ]; then
    echo ""
    echo "SUMMARY: $cli_first_stale"
    exit 3
  elif [ $fail -gt 0 ]; then
    echo ""
    echo "SUMMARY: error"
    exit 1
  else
    echo ""
    echo "SUMMARY: ok"
    exit 0
  fi
fi

if [ $fail -gt 0 ]; then
  echo ""
  echo "Run 'bash \"$KIT_ROOT/scripts/house-rules\" init' to fix most issues automatically."
  exit 1
else
  if [ $warn -gt 0 ]; then
    echo "All critical checks passed. Warnings are informational."
  else
    echo "Everything looks good!"
  fi
  exit 0
fi
```

### scripts/sync-rules.sh

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2059
set -uo pipefail

# Multi-format rule sync from the kit repo (canonical source) to target
# repos AND their git worktrees.
#
# Usage:
#   ./scripts/sync-rules.sh                              # Sync cursor format (default)
#   ./scripts/sync-rules.sh --format claude               # Sync claude format
#   ./scripts/sync-rules.sh --format all                  # Sync both formats
#   ./scripts/sync-rules.sh --format cursor --check       # Check cursor drift
#   ./scripts/sync-rules.sh --format claude --local       # Generate claude/ in this repo only
#   ./scripts/sync-rules.sh --dry-run                     # Preview without writing
#   ./scripts/sync-rules.sh --version v1.0.0              # Sync rules from a specific release
#   ./scripts/sync-rules.sh --show-version                # Print current kit version
#   ./scripts/sync-rules.sh --help
#
# Config: ~/.house-rules-sync-targets (one repo root per line).
# Rules are auto-discovered from cursor/rules/*.mdc (no hardcoded file list).

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$KIT_ROOT/cursor/rules"
FORMAT="cursor"
CHECK_MODE=false
LOCAL_ONLY=false
DRY_RUN=false
# SAFE_MODE defaults to true: any locally modified target file is backed
# up as .bak before being overwritten. Pass --unsafe to allow silent
# overwrite (rarely correct; kept for parity with prior behavior).
SAFE_MODE=true
PIN_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --format)  FORMAT="$2"; shift 2 ;;
    --check)   CHECK_MODE=true; shift ;;
    --local)   LOCAL_ONLY=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --unsafe)  SAFE_MODE=false; shift ;;
    --version) PIN_VERSION="$2"; shift 2 ;;
    --show-version)
      if [ -f "$KIT_ROOT/VERSION" ]; then
        echo "house-rules v$(cat "$KIT_ROOT/VERSION" | tr -d '[:space:]')"
      else
        echo "house-rules (no VERSION file)"
      fi
      exit 0
      ;;
    -h|--help)
      cat <<'EOF'
Multi-format rule sync from the kit repo to target repos.

Usage: sync-rules.sh [options]

Options:
  --format cursor|claude|all   Output format (default: cursor; "both" is
                               accepted as an alias for "all" — init.sh
                               uses --tool both for the same concept)
  --check                      Report drift without syncing
  --local                      Generate in this repo only (claude/all)
  --dry-run                    Preview what would be written
  --unsafe                     Disable safe-mode backups (silent overwrite).
                               Default is ON: locally modified files are
                               backed up to .<ts>.bak before being
                               overwritten.
  --version TAG                Sync rules from a specific git tag (e.g. v1.0.0)
  --show-version               Print current kit version and exit
  --help                       Show this help

Config: ~/.house-rules-sync-targets (one repo root per line)

Versioning:
  Without --version, rules sync from the current working tree (latest edits).
  With --version, rules sync from the specified git tag. Teams can pin to a
  stable release and upgrade deliberately. See CHANGELOG.md for release notes.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# Accept "both" as an alias for "all" — init.sh uses --tool both
# for the same concept and cross-script muscle memory shouldn't silently
# fail. See agent-protocol.md for the contract.
if [[ "$FORMAT" == "both" ]]; then
  FORMAT="all"
fi

if [[ "$FORMAT" != "cursor" && "$FORMAT" != "claude" && "$FORMAT" != "all" ]]; then
  echo "Unknown format: $FORMAT (expected cursor, claude, all, or both)" >&2
  exit 1
fi

# --- Version pinning ---

VERSIONED_TMPDIR=""
cleanup_versioned_tmp() {
  [ -n "$VERSIONED_TMPDIR" ] && rm -rf "$VERSIONED_TMPDIR"
}
trap cleanup_versioned_tmp EXIT

if [ -n "$PIN_VERSION" ]; then
  if ! git -C "$KIT_ROOT" rev-parse "$PIN_VERSION" &>/dev/null; then
    echo "Tag '$PIN_VERSION' not found in the kit repo."
    echo "Available tags: $(git -C "$KIT_ROOT" tag --list 'v*' | tr '\n' ' ')"
    echo ""
    echo "To create a release: git tag v1.0.0 && git push origin v1.0.0"
    exit 1
  fi

  VERSIONED_TMPDIR="$(mktemp -d)"
  mkdir -p "$VERSIONED_TMPDIR"

  while IFS= read -r filepath; do
    fname="$(basename "$filepath")"
    git -C "$KIT_ROOT" show "${PIN_VERSION}:${filepath}" > "$VERSIONED_TMPDIR/$fname" 2>/dev/null || true
  done < <(git -C "$KIT_ROOT" ls-tree --name-only "${PIN_VERSION}" cursor/rules/ 2>/dev/null | grep '\.mdc$')

  file_count=$(ls -1 "$VERSIONED_TMPDIR"/*.mdc 2>/dev/null | wc -l | tr -d ' ')
  if [ "$file_count" -eq 0 ]; then
    echo "No .mdc files found in tag '$PIN_VERSION' at cursor/rules/"
    exit 1
  fi

  SRC="$VERSIONED_TMPDIR"
  echo "Using rules from $PIN_VERSION ($file_count files)"
  echo ""
fi

# --- Auto-discover rule files ---

MDC_FILES=()
for f in "$SRC"/*.mdc; do
  [ -f "$f" ] && MDC_FILES+=("$(basename "$f")")
done

if [ ${#MDC_FILES[@]} -eq 0 ]; then
  echo "No .mdc files found in $SRC"
  exit 1
fi

# --- Frontmatter stripping (for claude format) ---

strip_frontmatter() {
  local file="$1"
  local in_frontmatter=false
  local frontmatter_ended=false
  local line_num=0

  while IFS= read -r line || [[ -n "$line" ]]; do
    line_num=$((line_num + 1))
    if [[ $line_num -eq 1 && "$line" == "---" ]]; then
      in_frontmatter=true
      continue
    fi
    if $in_frontmatter && [[ "$line" == "---" ]]; then
      in_frontmatter=false
      frontmatter_ended=true
      continue
    fi
    if $in_frontmatter; then
      continue
    fi
    if $frontmatter_ended && [[ -z "$line" ]]; then
      frontmatter_ended=false
      continue
    fi
    frontmatter_ended=false
    printf '%s\n' "$line"
  done < "$file"
}

# --- Stale file cleanup ---
#
# Deletes any rule file in a target's rules dir that isn't in the kit's
# MDC_FILES list. Deliberate consequence: kit-synced repos cannot carry
# workspace-local rules — a local .mdc/.md placed in .cursor/rules/ or
# .claude/rules/ is silently removed on the next sync. Repo-local always-on
# guidance in a synced repo belongs in that repo's own AGENTS.md/CLAUDE.md
# sections (or a skill), never in the synced rules directories.
# Verified 2026-08-04 (foreclosed a planned workspace rule in a consuming repo);
# also documented in README § "What syncs automatically".

cleanup_stale_cursor() {
  local dest="$1"
  [ -d "$dest" ] || return 0
  for existing in "$dest"/*.mdc; do
    [ -f "$existing" ] || continue
    local base
    base="$(basename "$existing")"
    local found=false
    for f in "${MDC_FILES[@]}"; do
      if [[ "$f" == "$base" ]]; then found=true; break; fi
    done
    if ! $found; then
      if $DRY_RUN; then
        echo "    [dry-run] Would remove stale: $base"
      else
        rm "$existing"
        echo "    Removed stale: $base"
      fi
    fi
  done
}

cleanup_stale_claude() {
  local dest="$1"
  [ -d "$dest" ] || return 0
  for existing in "$dest"/*.md; do
    [ -f "$existing" ] || continue
    local base
    base="$(basename "$existing")"
    local expected_mdc="${base%.md}.mdc"
    local found=false
    for f in "${MDC_FILES[@]}"; do
      if [[ "$f" == "$expected_mdc" ]]; then found=true; break; fi
    done
    if ! $found; then
      if $DRY_RUN; then
        echo "    [dry-run] Would remove stale: $base"
      else
        rm "$existing"
        echo "    Removed stale: $base"
      fi
    fi
  done
}

# --- Format-specific sync/check functions ---

safe_backup() {
  local src_file="$1" dest_file="$2"
  if $SAFE_MODE && [ -f "$dest_file" ]; then
    if ! diff -q "$src_file" "$dest_file" > /dev/null 2>&1; then
      # Timestamped .bak so two consecutive safe-mode syncs with local edits
      # between them don't silently destroy the user's first backup.
      local ts bak
      ts="$(date +%Y%m%d%H%M%S)"
      bak="${dest_file}.${ts}.bak"
      cp "$dest_file" "$bak"
      echo "    ↳ backed up $(basename "$dest_file") → $(basename "$bak")"
      safe_backup_count=$((safe_backup_count + 1))
    fi
  fi
}

sync_cursor_to() {
  local dest="$1"
  if $DRY_RUN; then
    echo "    [dry-run] Would copy ${#MDC_FILES[@]} .mdc files → $dest"
    return 0
  fi
  mkdir -p "$dest"
  for f in "${MDC_FILES[@]}"; do
    safe_backup "$SRC/$f" "$dest/$f"
    cp "$SRC/$f" "$dest/$f"
  done
  cleanup_stale_cursor "$dest"
}

sync_claude_to() {
  local dest="$1"
  if $DRY_RUN; then
    echo "    [dry-run] Would generate ${#MDC_FILES[@]} .md files → $dest"
    return 0
  fi
  mkdir -p "$dest"
  for f in "${MDC_FILES[@]}"; do
    local md_name="${f%.mdc}.md"
    if $SAFE_MODE && [ -f "$dest/$md_name" ]; then
      local expected
      expected="$(strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g')"
      local actual
      actual="$(cat "$dest/$md_name")"
      if [[ "$expected" != "$actual" ]]; then
        # Timestamped .bak (see safe_backup() rationale).
        local ts bak_name
        ts="$(date +%Y%m%d%H%M%S)"
        bak_name="${md_name}.${ts}.bak"
        cp "$dest/$md_name" "$dest/$bak_name"
        echo "    ↳ backed up $md_name → $bak_name"
        safe_backup_count=$((safe_backup_count + 1))
      fi
    fi
    strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g' > "$dest/$md_name"
  done
  cleanup_stale_claude "$dest"
}

check_cursor_in() {
  local dest="$1"
  local stale=0
  for f in "${MDC_FILES[@]}"; do
    if [ ! -f "$dest/$f" ]; then
      echo "  ✗ $f — missing"
      stale=1
    elif ! diff -q "$SRC/$f" "$dest/$f" > /dev/null 2>&1; then
      echo "  ✗ $f — differs"
      stale=1
    fi
  done
  if [ $stale -eq 0 ]; then
    echo "  ✓ all ${#MDC_FILES[@]} cursor rules up to date"
  fi
  return $stale
}

check_claude_in() {
  local dest="$1"
  local stale=0
  for f in "${MDC_FILES[@]}"; do
    local md_name="${f%.mdc}.md"
    if [ ! -f "$dest/$md_name" ]; then
      echo "  ✗ $md_name — missing"
      stale=1
    else
      local expected
      expected="$(strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g')"
      local actual
      actual="$(cat "$dest/$md_name")"
      if [[ "$expected" != "$actual" ]]; then
        echo "  ✗ $md_name — differs"
        stale=1
      fi
    fi
  done
  if [ $stale -eq 0 ]; then
    echo "  ✓ all ${#MDC_FILES[@]} claude rules up to date"
  fi
  return $stale
}

# --- Target validation ---

validate_target() {
  local target="$1"
  if [ ! -d "$target" ]; then
    echo "  ⚠ Target does not exist: $target (skipping)"
    return 1
  fi
  if ! { [ -d "$target/.git" ] || [ -f "$target/.git" ]; }; then
    echo "  ⚠ Target is not a git repo: $target (syncing anyway)"
  fi
  return 0
}

# --- Local-only mode (generate in this repo) ---

safe_backup_count=0

if $LOCAL_ONLY; then
  if [[ "$FORMAT" == "cursor" ]]; then
    echo "--local only applies to non-cursor formats (cursor rules are the source)."
    exit 1
  fi

  if [[ "$FORMAT" == "claude" || "$FORMAT" == "all" ]]; then
    dest="$KIT_ROOT/claude/rules"
    if $CHECK_MODE; then
      echo "Checking: $KIT_ROOT/claude/rules"
      check_claude_in "$dest" || { echo "Run without --check to regenerate."; exit 1; }
    else
      sync_claude_to "$dest"
      echo "Generated ${#MDC_FILES[@]} claude rules → $dest"
    fi
  fi
  exit 0
fi

# --- Load targets ---

CONFIG_FILE="$HOME/.house-rules-sync-targets"
TARGETS=()

if [ ! -f "$CONFIG_FILE" ]; then
  echo "No config file found."
  echo "Create ~/.house-rules-sync-targets with one repo root per line:"
  cat <<TMPL
# Repo roots to sync kit rules to (one per line).
# Lines starting with # are ignored. ~ is expanded to \$HOME.
#
# Example:
# ~/projects/my-repo
TMPL
  exit 1
fi

while IFS= read -r line; do
  line="${line/#\~/$HOME}"
  TARGETS+=("$line")
done < <(grep -v '^\s*#' "$CONFIG_FILE" | grep -v '^\s*$' | tr -d '\r')

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "No targets in $CONFIG_FILE. Add repo paths, one per line."
  exit 1
fi

# --- Format dispatch for a single repo ---

sync_repo() {
  local repo_root="$1" fmt="$2"
  local label="$fmt"

  if [[ "$fmt" == "cursor" ]]; then
    local cursor_dest="$repo_root/.cursor/rules"
    if $CHECK_MODE; then
      echo "Checking ($label): $repo_root"
      check_cursor_in "$cursor_dest" || return 1
    else
      sync_cursor_to "$cursor_dest"
      if ! $DRY_RUN; then echo "Synced ($label) → $repo_root"; fi
    fi
  elif [[ "$fmt" == "claude" ]]; then
    local claude_dest="$repo_root/.claude/rules"
    if $CHECK_MODE; then
      echo "Checking ($label): $repo_root"
      check_claude_in "$claude_dest" || return 1
    else
      sync_claude_to "$claude_dest"
      if ! $DRY_RUN; then echo "Synced ($label) → $repo_root"; fi

      # Warn if .claude/rules/ is gitignored
      if git -C "$repo_root" check-ignore -q ".claude/rules/test.md" 2>/dev/null; then
        echo "  ⚠ .claude/rules/ appears to be gitignored — rules won't be committed"
      fi
    fi
  fi
  return 0
}

sync_worktrees() {
  local repo_root="$1" fmt="$2"
  local local_wt=0
  if [[ "$fmt" != "cursor" ]]; then return 0; fi
  if ! { [ -d "$repo_root/.git" ] || [ -f "$repo_root/.git" ]; }; then return 0; fi

  while IFS= read -r line; do
    local wt_path="${line#worktree }"
    [ "$wt_path" = "$repo_root" ] && continue
    local wt_dest="$wt_path/.cursor/rules"
    if $CHECK_MODE; then
      echo "  ↳ worktree: $(basename "$wt_path")"
      check_cursor_in "$wt_dest" || stale_count=$((stale_count + 1))
    else
      sync_cursor_to "$wt_dest"
      if ! $DRY_RUN; then echo "  ↳ worktree: $(basename "$wt_path")"; fi
    fi
    local_wt=$((local_wt + 1))
  done < <(git -C "$repo_root" worktree list --porcelain 2>/dev/null | grep '^worktree ' || true)
  wt_count=$((wt_count + local_wt))
}

# --- Main sync loop ---

repo_count=0
wt_count=0
stale_count=0
error_count=0
safe_backup_count=0
errors_summary=()

FORMATS_TO_RUN=()
if [[ "$FORMAT" == "all" ]]; then
  FORMATS_TO_RUN=("cursor" "claude")
else
  FORMATS_TO_RUN=("$FORMAT")
fi

for target in "${TARGETS[@]}"; do
  repo_root="$target"

  if ! validate_target "$repo_root"; then
    error_count=$((error_count + 1))
    errors_summary+=("$repo_root: target does not exist")
    continue
  fi

  for fmt in "${FORMATS_TO_RUN[@]}"; do
    if ! sync_repo "$repo_root" "$fmt"; then
      stale_count=$((stale_count + 1))
    fi
    sync_worktrees "$repo_root" "$fmt"
  done
  repo_count=$((repo_count + 1))
done

# --- Summary ---

echo ""
fmt_label="$FORMAT"
ver_label=""
if [ -n "$PIN_VERSION" ]; then
  ver_label=" @ $PIN_VERSION"
elif [ -f "$KIT_ROOT/VERSION" ]; then
  ver_label=" @ v$(cat "$KIT_ROOT/VERSION" | tr -d '[:space:]')"
fi

if $DRY_RUN; then
  echo "[dry-run] Would sync ${#MDC_FILES[@]} rules ($fmt_label$ver_label) → $repo_count repos + $wt_count worktrees."
  echo "Re-run without --dry-run to apply."
elif $CHECK_MODE; then
  echo "Checked ${#MDC_FILES[@]} rules ($fmt_label$ver_label) across $repo_count repos + $wt_count worktrees."
  if [ $stale_count -gt 0 ]; then
    echo "$stale_count targets have stale or missing rules. Run without --check to sync."
  else
    echo "All targets up to date."
  fi
else
  echo "Done. ${#MDC_FILES[@]} rules ($fmt_label$ver_label) → $repo_count repos + $wt_count worktrees."
  if $SAFE_MODE && [ $safe_backup_count -gt 0 ]; then
    echo "$safe_backup_count file(s) had local changes — .bak copies preserved."
  fi
fi

if [ $error_count -gt 0 ]; then
  echo ""
  echo "⚠ $error_count target(s) skipped due to errors:"
  for msg in "${errors_summary[@]}"; do
    echo "  - $msg"
  done
fi

if $CHECK_MODE && [ $stale_count -gt 0 ]; then
  exit 1
fi
if [ $error_count -gt 0 ] && [ $repo_count -eq 0 ]; then
  exit 1
fi
exit 0
```

### scripts/install-aliases.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

# Installs the kit's minimal shell aliases (`hr`, `house-rules`) plus a
# PROCESS_KIT env var into the user's shell rc file. Uses the
# owned-file pattern: writes ~/.house-rules-aliases.sh (overwritten on every
# run, safe to regenerate) and adds a single marker-delimited source line
# to ~/.zshrc / ~/.bashrc. This avoids marker-block editing on the shell
# rc file for anything other than the one source line.
#
# Non-interactive by design — safe for agent-driven machine setup.
#
# Usage:
#   ./scripts/install-aliases.sh                # Install / update (auto-detect shell)
#   ./scripts/install-aliases.sh --shell zsh    # Force shell choice
#   ./scripts/install-aliases.sh --check        # Report status, no writes
#   ./scripts/install-aliases.sh --uninstall    # Remove aliases file + rc source line
#   ./scripts/install-aliases.sh --help

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ALIASES_FILE="$HOME/.house-rules-aliases.sh"
# Marker prefix is "house-rules:" (final kit name, decision 0001 A1).
# Recognition of the predecessor playbook's legacy marker prefix was
# sunset 2026-08-06 (process-kit-26b) after a field sweep showed zero
# old-marker rc blocks remaining.
SOURCE_BEGIN="# BEGIN house-rules:aliases"
SOURCE_END="# END house-rules:aliases"
MODE="install"
SHELL_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)     MODE="check"; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --shell)     SHELL_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      cat <<'EOF'
Installs minimal house-rules shell aliases.

Usage: install-aliases.sh [options]

Modes:
  (default)     Install or update aliases. Detects zsh/bash/fish via $SHELL.
  --check       Report whether aliases are installed and current (exit 1 if not).
  --uninstall   Remove the rc source line and delete ~/.house-rules-aliases.sh.
  --shell ARG   Override shell detection (zsh|bash|fish).
  --help        Show this help.

Installed aliases:
  hr                   The house-rules dispatcher (init | doctor | sync)
  house-rules          Same dispatcher, full name
  PROCESS_KIT          Exported env var pointing at the kit clone

The aliases source ~/.house-rules-aliases.sh, which is overwritten on each
install. Do not edit that file by hand. Re-run this installer to update.

Non-interactive by design — safe for agent-driven machine setup.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# --- Shell detection ---

detect_shell() {
  local name=""
  if [ -n "$SHELL_OVERRIDE" ]; then
    name="$SHELL_OVERRIDE"
  elif [ -n "${SHELL:-}" ]; then
    name="$(basename "$SHELL")"
  fi
  case "$name" in
    zsh)  echo "zsh" ;;
    bash) echo "bash" ;;
    fish) echo "fish" ;;
    *)    echo "unsupported" ;;
  esac
}

rc_file_for() {
  case "$1" in
    zsh)  echo "$HOME/.zshrc" ;;
    bash)
      if [ -f "$HOME/.bashrc" ]; then
        echo "$HOME/.bashrc"
      else
        echo "$HOME/.bash_profile"
      fi
      ;;
    fish) echo "$HOME/.config/fish/config.fish" ;;
    *) echo "" ;;
  esac
}

# --- Aliases file content ---

render_aliases_file() {
  cat <<ALIASES
# house-rules aliases (managed by install-aliases.sh)
#
# This file is regenerated by install-aliases.sh. Do not edit by hand —
# changes will be lost on the next install. To customize, edit your own
# shell rc and source this file earlier so your aliases take precedence.
#
# Re-run installer:
#   bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/install-aliases.sh"

export PROCESS_KIT="\${PROCESS_KIT:-$KIT_ROOT}"

# hr / house-rules: the kit dispatcher (init | doctor | sync)
alias hr='bash "\$PROCESS_KIT/scripts/house-rules"'
alias house-rules='bash "\$PROCESS_KIT/scripts/house-rules"'
ALIASES
}

# Writer return codes (shared by the writers below): 0 = written, 1 = I/O
# failure (mktemp/write/mv — callers must fail loud, process-kit-e71),
# 2 = malformed markers (deliberate warn-and-skip, file untouched — the
# process-kit-0em guard contract).
write_aliases_file() {
  local tmp
  tmp="$(mktemp "${ALIASES_FILE}.tmp.XXXXXX")" || return 1
  render_aliases_file > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$ALIASES_FILE" || { rm -f "$tmp"; return 1; }
}

aliases_file_is_current() {
  [ -f "$ALIASES_FILE" ] || return 1
  local want have
  want="$(render_aliases_file)"
  have="$(cat "$ALIASES_FILE")"
  [ "$want" = "$have" ]
}

# --- RC file block (single source line, marker-delimited so --uninstall works) ---

rc_block() {
  cat <<BLOCK
$SOURCE_BEGIN
[ -f "\$HOME/.house-rules-aliases.sh" ] && . "\$HOME/.house-rules-aliases.sh"
$SOURCE_END
BLOCK
}

rc_has_block() {
  local rc="$1"
  [ -f "$rc" ] || return 1
  grep -qF "$SOURCE_BEGIN" "$rc"
}

# Content check: the block's body can change across kit versions (it did at
# the v0.3.0 dispatcher cut, when the sourced filename changed), so presence
# alone is not "installed" — a present-but-stale block gets refreshed.
rc_block_is_current() {
  local rc="$1"
  rc_has_block "$rc" || return 1
  local want have
  want="$(rc_block)"
  have="$(awk -v b="$SOURCE_BEGIN" -v e="$SOURCE_END" \
    '$0==b{f=1} f{print} $0==e{f=0}' "$rc")"
  [ "$have" = "$want" ]
}

rc_append_block() {
  local rc="$1"
  mkdir -p "$(dirname "$rc")" || return 1
  # Atomic write: stage the new content (existing rc + spacer + block) to
  # a temp file in the same directory, then mv. A non-atomic group
  # append (`{ ... } >> "$rc"`) is exposed to OOM kills and SIGKILL
  # mid-write — the rc would be left with a syntactically broken shell
  # block (breaking every new terminal) and the orphan BEGIN marker
  # would make `rc_has_block` falsely report "already installed" on
  # re-run, bypassing repair.
  local tmp
  tmp="$(mktemp "${rc}.tmp.XXXXXX")" || return 1
  {
    if [ -f "$rc" ]; then
      cat "$rc"
      # Ensure trailing newline before appending
      [ -n "$(tail -c1 "$rc" 2>/dev/null)" ] && printf '\n'
      printf '\n'
    fi
    rc_block
    printf '\n'
  } > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$rc" || { rm -f "$tmp"; return 1; }
}

# One scanner for both rewrites: strips every managed block; with `emit`,
# re-emits the current block at the first BEGIN — in place, because block
# position in the rc is load-bearing (source-order precedence). Used by
# uninstall (strip) and by the content refresh (emit) when a present block
# body is stale.
rc_rewrite_block() {
  local rc="$1" emit="${2:-}"
  local tmp
  tmp="$(mktemp "${rc}.tmp.XXXXXX")" || return 1
  local in_block=0 consumed=0
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ] && [ "$line" = "$SOURCE_BEGIN" ]; then
      in_block=1
      if [ -n "$emit" ] && [ $consumed -eq 0 ]; then
        rc_block
      fi
      consumed=1
      continue
    fi
    if [ $in_block -eq 1 ]; then
      if [ "$line" = "$SOURCE_END" ]; then
        in_block=0
      elif [ "$line" = "$SOURCE_BEGIN" ]; then
        # A BEGIN while a block is already open means the earlier BEGIN
        # lost its END and the scan is swallowing a real block plus any
        # user lines between them — stop here so the guard below refuses.
        break
      fi
      continue
    fi
    printf '%s\n' "$line"
  done < "$rc" > "$tmp"
  # Refuse the rewrite when the marker scan went wrong: an unpaired BEGIN
  # (in_block still open at EOF, or a nested BEGIN hit above) would have
  # swallowed user content on mv; a scan that consumed no BEGIN (e.g.
  # CRLF or indented marker lines that match the substring grep but not
  # the whole-line test) would report a rewrite that never happened.
  if [ $in_block -eq 1 ] || [ $consumed -eq 0 ]; then
    rm -f "$tmp"
    echo "⚠ $rc: alias block markers are malformed (unpaired BEGIN or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
    return 2
  fi
  mv "$tmp" "$rc" || { rm -f "$tmp"; return 1; }
}

rc_remove_block() {
  local rc="$1"
  [ -f "$rc" ] || return 0
  rc_has_block "$rc" || return 0
  rc_rewrite_block "$rc"
}

# --- Dispatch ---

shell_kind="$(detect_shell)"
rc_file="$(rc_file_for "$shell_kind")"

if [ "$shell_kind" = "fish" ]; then
  cat >&2 <<'FISH'
Fish shell isn't supported yet by install-aliases.sh.

Workaround — paste the following into your ~/.config/fish/config.fish:

  set -x PROCESS_KIT "$HOME/process-kit"
  alias hr="bash \"$PROCESS_KIT/scripts/house-rules\""

Or use the scripts directly. File an issue if proper fish support would help.
FISH
  exit 1
fi

if [ "$shell_kind" = "unsupported" ]; then
  echo "ERROR: could not detect a supported shell (zsh or bash)." >&2
  echo "  Override with --shell zsh|bash|fish, or export SHELL before re-running." >&2
  exit 1
fi

case "$MODE" in
  check)
    missing=0
    if ! aliases_file_is_current; then
      echo "✗ $ALIASES_FILE missing or out of date"
      missing=1
    else
      echo "✓ $ALIASES_FILE installed and current"
    fi
    if ! rc_has_block "$rc_file"; then
      echo "✗ Source line not present in $rc_file"
      missing=1
    elif ! rc_block_is_current "$rc_file"; then
      echo "✗ Source block in $rc_file is out of date (re-run installer to refresh)"
      missing=1
    else
      echo "✓ Source line present in $rc_file"
    fi
    if [ $missing -eq 1 ]; then
      echo ""
      echo "  Fix: bash $(cd "$(dirname "$0")" && pwd)/install-aliases.sh"
      exit 1
    fi
    exit 0
    ;;

  uninstall)
    changed=0
    failed=0
    refused=0
    if [ -f "$ALIASES_FILE" ]; then
      if rm -f "$ALIASES_FILE"; then
        echo "✓ Removed $ALIASES_FILE"
        changed=1
      else
        echo "✗ Failed to remove $ALIASES_FILE (check permissions)" >&2
        failed=$((failed + 1))
      fi
    fi
    if rc_has_block "$rc_file"; then
      rc_remove_block "$rc_file"
      case $? in
        0)
          echo "✓ Removed source line from $rc_file"
          changed=1
          ;;
        2)
          # Malformed markers: warned on stderr, file untouched (0em
          # contract) — but the block is still there, so this uninstall
          # did not finish; report and exit nonzero, don't claim success.
          refused=$((refused + 1))
          ;;
        *)
          echo "✗ Failed to rewrite $rc_file removing the source line (write error — check permissions)" >&2
          failed=$((failed + 1))
          ;;
      esac
    fi
    if [ $changed -eq 0 ] && [ $failed -eq 0 ] && [ $refused -eq 0 ]; then
      echo "  Nothing to remove (not installed)."
    elif [ $changed -eq 1 ]; then
      echo ""
      echo "Restart your shell or run: source $rc_file"
    fi
    if [ $refused -gt 0 ]; then
      echo "⚠ The source block in $rc_file was NOT removed (malformed markers — see warning above; repair the marker lines and re-run)" >&2
    fi
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;

  install)
    echo "=== Installing house-rules aliases ($shell_kind) ==="
    echo ""

    failed=0
    refused=0
    if aliases_file_is_current; then
      echo "✓ $ALIASES_FILE is already current"
    elif write_aliases_file; then
      echo "✓ Wrote $ALIASES_FILE"
    else
      echo "✗ Failed to write $ALIASES_FILE (write error — check permissions)" >&2
      failed=$((failed + 1))
    fi

    if rc_block_is_current "$rc_file"; then
      echo "✓ Source line already present in $rc_file"
    elif rc_has_block "$rc_file"; then
      rc_rewrite_block "$rc_file" emit
      case $? in
        0) echo "✓ Refreshed the source block in $rc_file" ;;
        2)
          # Malformed markers: warned on stderr, file untouched (0em
          # contract) — but the rc still sources nothing current, so the
          # aliases are NOT active; report and exit nonzero, matching
          # what --check would say about this exact state.
          refused=$((refused + 1))
          ;;
        *)
          echo "✗ Failed to rewrite the source block in $rc_file (write error — check permissions)" >&2
          failed=$((failed + 1))
          ;;
      esac
    else
      if rc_append_block "$rc_file"; then
        echo "✓ Added source line to $rc_file"
      else
        echo "✗ Failed to append the source line to $rc_file (write error — check permissions)" >&2
        failed=$((failed + 1))
      fi
    fi

    echo ""
    echo "=== Done ==="
    echo ""
    echo "Activate now: source \"$rc_file\"   (or open a new terminal)"
    echo ""
    echo "Installed aliases:"
    echo "  hr             The house-rules dispatcher (init | doctor | sync)"
    echo "  house-rules    Same dispatcher, full name"
    echo "  PROCESS_KIT → $KIT_ROOT"
    echo ""
    echo "Verify: bash $(cd "$(dirname "$0")" && pwd)/install-aliases.sh --check"
    if [ $refused -gt 0 ]; then
      echo "⚠ The rc source block was NOT refreshed (malformed markers — see warning above); the aliases are not active until the marker lines in $rc_file are repaired and the installer re-run" >&2
    fi
    if [ $failed -gt 0 ]; then
      echo "✗ $failed write failure(s) above — the ✗-marked items were NOT installed" >&2
    fi
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;
esac
```

### scripts/install-global-safety-net.sh

```bash
#!/usr/bin/env bash
set -uo pipefail

# Installs the kit's "global safety net" — condensed, per-machine rule
# blocks that apply even in repos never bootstrapped with init.sh.
#
# Writes marker-delimited blocks into ~/CLAUDE.md (idempotent) and emits a
# combined paste snippet for Cursor's Global Preferences user rule
# (Cursor's user-rules storage lives in app settings and isn't safe to
# edit cross-platform from a script).
#
# Block sources live in global-safety-net/<id>.md (one file per concern).
# Adding a new concern = add a file + append its id to BLOCKS below.
#
# Usage:
#   ./scripts/install-global-safety-net.sh              # Install / update all blocks
#   ./scripts/install-global-safety-net.sh --check      # Report status, no writes
#   ./scripts/install-global-safety-net.sh --uninstall  # Remove managed blocks
#   ./scripts/install-global-safety-net.sh --print-cursor-snippet  # Re-print paste artifact
#   ./scripts/install-global-safety-net.sh --help

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SAFETY_NET_DIR="$KIT_ROOT/global-safety-net"
CLAUDE_MD="$HOME/CLAUDE.md"
CURSOR_SNIPPET_FILE="$SAFETY_NET_DIR/cursor-snippet.generated.md"
MODE="install"

# Registry of block ids, in the order they should appear in ~/CLAUDE.md and
# in the Cursor paste snippet. Each id must have a matching source file at
# $SAFETY_NET_DIR/<id>.md. To add a concern, create the file and add the id.
BLOCKS=(
  "agent-identity"
  "session-start"
  "agent-protocol"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)     MODE="check"; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --print-cursor-snippet) MODE="print-snippet"; shift ;;
    -h|--help)
      cat <<'EOF'
Installs the kit's global safety net (per-machine agent rule blocks).

Usage: install-global-safety-net.sh [options]

Modes:
  (default)                 Install or update all registered blocks in
                            ~/CLAUDE.md and regenerate the Cursor paste
                            snippet at global-safety-net/cursor-snippet.generated.md.
  --check                   Report whether every block is present and current.
                            Exit 0 = all current, 1 = missing or stale.
  --uninstall               Remove all registered blocks from ~/CLAUDE.md.
  --print-cursor-snippet    Print the combined paste snippet for manual
                            Cursor user-rules paste (no writes).
  --help                    Show this help.

What this is for:
  Per-repo .cursor/rules/ only apply in bootstrapped projects. A fresh repo
  without the rules sees the agent revert to its base-model defaults —
  including human-baseline estimation and no discoverability of the
  kit itself. This script installs the condensed blocks at the
  per-machine level so they apply everywhere.

  Re-run any time to pick up content updates. Run --check in CI or the
  doctor script.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# --- Block rendering ---

# Marker prefix is "house-rules:" (final kit name, decision 0001 A1).
# Recognition of the predecessor playbook's legacy marker prefix was
# sunset 2026-08-06 (process-kit-26b) after a field sweep showed zero
# old-marker blocks remaining on this machine's artifacts.
marker_begin() { printf '<!-- BEGIN house-rules:%s -->' "$1"; }
marker_end()   { printf '<!-- END house-rules:%s -->' "$1"; }

block_source_path() { printf '%s/%s.md' "$SAFETY_NET_DIR" "$1"; }

# Render a single block wrapped in markers.
render_block() {
  local id="$1"
  local src
  src="$(block_source_path "$id")"
  if [ ! -f "$src" ]; then
    echo "ERROR: missing block source: $src" >&2
    return 1
  fi
  marker_begin "$id"
  printf '\n'
  cat "$src"
  marker_end "$id"
  printf '\n'
}

# --- Per-block queries over ~/CLAUDE.md ---

has_block() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 1
  grep -qF "$(marker_begin "$id")" "$CLAUDE_MD"
}

current_block_content() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 1
  local begin end in_block=0
  begin="$(marker_begin "$id")"
  end="$(marker_end "$id")"
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$line" = "$begin" ]; then in_block=1; fi
    [ $in_block -eq 1 ] && printf '%s\n' "$line"
    if [ "$line" = "$end" ]; then in_block=0; fi
  done < "$CLAUDE_MD"
}

block_is_current() {
  local id="$1"
  local want have
  want="$(render_block "$id")" || return 1
  have="$(current_block_content "$id")"
  [ -n "$have" ] && [ "${have%$'\n'}" = "${want%$'\n'}" ]
}

# --- Single-block write operations (multi-pass: one file rewrite per block) ---

# Writer return codes (shared by the block writers): 0 = written,
# 1 = I/O failure (mktemp/write/mv — callers must fail loud, process-kit-e71),
# 2 = malformed markers (deliberate warn-and-skip, file untouched — the
# process-kit-0em guard contract).
append_block_new() {
  local id="$1"
  local tmp
  tmp="$(mktemp "${CLAUDE_MD}.tmp.XXXXXX")" || return 1
  {
    if [ ! -f "$CLAUDE_MD" ]; then
      printf '# CLAUDE.md\n\n'
      printf 'This file provides per-machine guidance to agents (read by Claude Code and surfaced to other agents via hooks).\n\n'
    else
      cat "$CLAUDE_MD"
      # Ensure trailing newline before appending
      [ -n "$(tail -c1 "$CLAUDE_MD" 2>/dev/null)" ] && printf '\n'
    fi
    render_block "$id"
    printf '\n'
  } > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$CLAUDE_MD" || { rm -f "$tmp"; return 1; }
}

# One scanner for both rewrites: strips every copy of the block; with
# `emit`, re-emits the current render at the first BEGIN (position in the
# file is preserved). Used by install (emit) and uninstall (strip).
#
# defer: this marker-scan loop is hand-copied across the three installers
# (rc_rewrite_block in install-aliases.sh, refresh_agents_section in
# init.sh, here) because each installer must stay a standalone single
# file. ceiling: a scan or guard fix must be hand-propagated to all three
# copies. upgrade when: a fourth copy appears, or a scan-behavior fix has
# to land in every copy — extract a sourced scripts/lib helper then.
rewrite_block() {
  local id="$1" emit="${2:-}"
  local tmp
  tmp="$(mktemp "${CLAUDE_MD}.tmp.XXXXXX")" || return 1
  local begin end in_block=0 consumed=0
  begin="$(marker_begin "$id")"
  end="$(marker_end "$id")"
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ] && [ "$line" = "$begin" ]; then
      in_block=1
      if [ -n "$emit" ] && [ $consumed -eq 0 ]; then
        render_block "$id"
      fi
      consumed=1
      continue
    fi
    if [ $in_block -eq 1 ]; then
      if [ "$line" = "$end" ]; then
        in_block=0
      elif [ "$line" = "$begin" ]; then
        # A BEGIN while a block is already open means the earlier BEGIN
        # lost its END and the scan is swallowing a real block plus any
        # user lines between them — stop here so the guard below refuses.
        break
      fi
      continue
    fi
    printf '%s\n' "$line"
  done < "$CLAUDE_MD" > "$tmp"
  # Refuse the rewrite when the marker scan went wrong: an unpaired BEGIN
  # (in_block still open at EOF, or a nested BEGIN hit above) would have
  # swallowed user content on mv; a scan that consumed no BEGIN (e.g.
  # CRLF or indented marker lines that match the substring grep but not
  # the whole-line test) would claim success while rewriting nothing.
  if [ $in_block -eq 1 ] || [ $consumed -eq 0 ]; then
    rm -f "$tmp"
    echo "⚠ $CLAUDE_MD: block '$id' markers are malformed (unpaired BEGIN or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
    return 2
  fi
  mv "$tmp" "$CLAUDE_MD" || { rm -f "$tmp"; return 1; }
}

remove_block() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 0
  has_block "$id" || return 0
  rewrite_block "$id"
}

# --- Cursor paste snippet ---

render_all_blocks() {
  local first=1
  for id in "${BLOCKS[@]}"; do
    if [ $first -eq 1 ]; then first=0; else printf '\n'; fi
    render_block "$id"
  done
}

write_cursor_snippet() {
  mkdir -p "$SAFETY_NET_DIR" || return 1
  render_all_blocks > "$CURSOR_SNIPPET_FILE"
}

print_cursor_instructions() {
  cat <<EOF

──────────────────────────────────────────────────────────────────────────
  CURSOR USER RULES — CHECK BEFORE PASTING (once per machine)
──────────────────────────────────────────────────────────────────────────

FIRST check whether Cursor is already importing ~/CLAUDE.md for you:
open Cursor → Settings → Rules and look for an auto-imported rule named
"CLAUDE" whose content matches ~/CLAUDE.md. It appears when the setting
"Include Third-Party Plugins, Skills, and Other Configs" is enabled.

If that rule is PRESENT, skip the paste entirely. The import already
carries these blocks into every Cursor conversation and re-reads
~/CLAUDE.md when Cursor restarts, so a manual paste would inject a
duplicate copy that goes stale after every kit update. Never edit and
save the imported rule in the settings UI (save semantics are
undocumented and may fork it from the file) — edit ~/CLAUDE.md via this
script and restart Cursor. Note the import is undocumented Cursor
behavior (observed 2026-08); if a future release drops it and the
CLAUDE rule disappears from settings, fall back to the paste below.

If that rule is ABSENT, paste the combined block below into:

  Cursor → Settings → Rules for AI → User Rules

(Add to existing content; don't replace it. Look for the BEGIN/END
markers to find and update it on future re-runs.)

The full snippet is also saved at:
  $CURSOR_SNIPPET_FILE

You can recall it any time with:
  cat "$CURSOR_SNIPPET_FILE"
  # or
  bash "$KIT_ROOT/scripts/install-global-safety-net.sh" --print-cursor-snippet

────────────────── PASTE BELOW THIS LINE ───────────────────────
EOF
  render_all_blocks
  cat <<'EOF'
────────────────── PASTE ABOVE THIS LINE ───────────────────────

The paste (when needed at all) is once per machine. The ~/CLAUDE.md
blocks above stay in sync via this script; the auto-imported CLAUDE
rule follows them on Cursor restart. Only a manual paste needs hand
maintenance: if you re-run the installer and block content has
drifted, re-run with --print-cursor-snippet to grab the fresh text.

EOF
}

# --- Dispatch ---

# Verify all source files exist before any mode runs.
# Use exit 1 (generic error). Exit 2 is reserved for doctor.sh's
# "bootstrap_needed" contract — agents dispatching on exit codes from
# this script must not be misled into running init.sh.
for id in "${BLOCKS[@]}"; do
  src="$(block_source_path "$id")"
  if [ ! -f "$src" ]; then
    echo "ERROR: block source missing for '$id' at $src" >&2
    echo "  Registry in this script lists '$id' but the file is absent." >&2
    exit 1
  fi
done

case "$MODE" in
  check)
    missing=0
    stale=0
    for id in "${BLOCKS[@]}"; do
      if ! has_block "$id"; then
        echo "✗ Block '$id' not installed in $CLAUDE_MD"
        missing=$((missing + 1))
      elif ! block_is_current "$id"; then
        echo "⚠ Block '$id' present but out of date in $CLAUDE_MD"
        stale=$((stale + 1))
      else
        echo "✓ Block '$id' installed and current"
      fi
    done
    if [ $missing -gt 0 ] || [ $stale -gt 0 ]; then
      echo ""
      echo "  Fix: bash $(cd "$(dirname "$0")" && pwd)/install-global-safety-net.sh"
      exit 1
    fi
    exit 0
    ;;

  uninstall)
    removed=0
    failed=0
    refused=0
    for id in "${BLOCKS[@]}"; do
      if has_block "$id"; then
        remove_block "$id"
        case $? in
          0)
            echo "✓ Removed block '$id' from $CLAUDE_MD"
            removed=$((removed + 1))
            ;;
          2)
            # Malformed markers: warned on stderr, file untouched (0em
            # contract) — the block is still there; count it so the exit
            # code says the uninstall did not finish.
            refused=$((refused + 1))
            ;;
          *)
            echo "✗ Failed to rewrite $CLAUDE_MD removing block '$id' (write error — check permissions)" >&2
            failed=$((failed + 1))
            ;;
        esac
      fi
    done
    if [ $removed -eq 0 ] && [ $failed -eq 0 ] && [ $refused -eq 0 ]; then
      echo "  No managed blocks found in $CLAUDE_MD (nothing to do)"
    fi
    if [ $refused -gt 0 ]; then
      echo "⚠ $refused block(s) were NOT removed (malformed markers — see warnings above; repair the marker lines and re-run)" >&2
    fi
    echo ""
    echo "Note: if you previously pasted the snippet into Cursor's user"
    echo "rules, remove it manually via Cursor → Settings → Rules for AI."
    echo "(An auto-imported CLAUDE rule needs no action — it follows the"
    echo "file ~/CLAUDE.md on the next Cursor restart.)"
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;

  print-snippet)
    render_all_blocks
    exit 0
    ;;

  install)
    echo "=== Installing global safety net ==="
    echo ""

    failed=0
    refused=0
    for id in "${BLOCKS[@]}"; do
      if ! has_block "$id"; then
        if append_block_new "$id"; then
          echo "✓ Added block '$id' to $CLAUDE_MD"
        else
          echo "✗ Failed to write block '$id' to $CLAUDE_MD (write error — check permissions)" >&2
          failed=$((failed + 1))
        fi
      elif block_is_current "$id"; then
        echo "✓ Block '$id' is already current (no changes)"
      else
        rewrite_block "$id" emit
        case $? in
          0) echo "✓ Updated block '$id' in $CLAUDE_MD" ;;
          2)
            # Malformed markers: warned on stderr, file untouched (0em
            # contract) — the block stays stale; count it so the exit
            # code says the install did not finish.
            refused=$((refused + 1))
            ;;
          *)
            echo "✗ Failed to rewrite block '$id' in $CLAUDE_MD (write error — check permissions)" >&2
            failed=$((failed + 1))
            ;;
        esac
      fi
    done

    if write_cursor_snippet; then
      echo "✓ Wrote combined Cursor paste snippet to $CURSOR_SNIPPET_FILE"
    else
      echo "✗ Failed to write Cursor paste snippet to $CURSOR_SNIPPET_FILE" >&2
      failed=$((failed + 1))
    fi

    print_cursor_instructions

    echo "=== Done ==="
    echo ""
    echo "Verify anytime: bash $(cd "$(dirname "$0")" && pwd)/install-global-safety-net.sh --check"
    if [ $refused -gt 0 ]; then
      echo "⚠ $refused block(s) were NOT updated (malformed markers — see warnings above); repair the marker lines in $CLAUDE_MD and re-run" >&2
    fi
    if [ $failed -gt 0 ]; then
      echo "✗ $failed write failure(s) above — the ✗-marked items were NOT installed" >&2
    fi
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;
esac
```

### global-safety-net/agent-protocol.md

```markdown
## house-rules — agent protocol

If the user invokes the kit ("use house-rules", "bootstrap this repo",
"sync the rules", "run the doctor", "check house-rules"):

1. Run `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" doctor --agent` to get structured status. The `--agent` mode emits a `SUMMARY: <key>` line and a stable exit code.

2. Branch on the **SUMMARY key**, not the bare exit code, when the exit code is `3` (drift). The SUMMARY carries what drifted so the recommended remediation matches. Do not execute until the user consents.

   | Exit | SUMMARY key | Meaning | Proposed action |
   |------|-------------|---------|-----------------|
   | `0` | `ok` | Healthy | Report status; no action |
   | `2` | `bootstrap_needed` | No rules in this repo | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" init --tool cursor\|claude\|both` |
   | `3` | `rules_drift_cursor` | Cursor rules stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" sync --format cursor` |
   | `3` | `rules_drift_claude` | Claude rules stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" sync --format claude` |
   | `3` | `rules_drift_both` | Both stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" sync --format all` |
   | `3` | `profile_drift` | `profiles/conventions.toml` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/profiles/conventions.toml" profiles/conventions.toml` |
   | `3` | `ledger_drift` | `scripts/tdd-ledger` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/tdd-ledger" scripts/tdd-ledger && chmod +x scripts/tdd-ledger` |
   | `3` | `defer_lint_drift` | `scripts/defer-lint` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/defer-lint" scripts/defer-lint && chmod +x scripts/defer-lint` |
   | `3` | `close_reason_lint_drift` | `scripts/close-reason-lint` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/close-reason-lint" scripts/close-reason-lint && chmod +x scripts/close-reason-lint` |
   | `3` | `banned_token_scan_drift` | `scripts/banned-token-scan` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/banned-token-scan" scripts/banned-token-scan && chmod +x scripts/banned-token-scan` |
   | `1` | `error` | Generic error | Show the doctor's full text output to the user |

   Drift precedence when several drift at once: rules drift wins the SUMMARY, then `profile_drift`, then `ledger_drift`, then `defer_lint_drift`, then `close_reason_lint_drift`, then `banned_token_scan_drift`; the lower-precedence findings still appear in the doctor's text output, so check them after fixing the reported one. The profile and the profile-reading checkers version together: when the doctor's text output shows both a stale checker and the profile advisory, re-copy both (or re-run `house-rules init`). Some findings are text-only and never affect the SUMMARY or exit code (e.g. a stale AGENTS.md section version stamp, or the unverifiable Cursor user-rules paste) — scan the doctor's warning lines for these, don't rely on the exit code alone.

3. Do not invoke `house-rules sync` without `--format` on a Claude-only project. The sync defaults to `--format cursor` and will create unwanted `.cursor/rules/` files in the target.

4. Never run bootstrap, sync, or update silently. Always ask before making changes that modify the project or `~/.house-rules-sync-targets`.

5. If `"${PROCESS_KIT:-$HOME/process-kit}"` does not exist on this machine, instruct the user to clone the kit: `git clone https://github.com/kevglynn/house-rules ~/process-kit`. Do not attempt to clone on behalf of the user without explicit consent.

The canonical kit location is `${PROCESS_KIT:-$HOME/process-kit}`.
```

### global-safety-net/session-start.md

```markdown
## house-rules — project bootstrap check

At session start, if the workspace root is a git repository AND **neither**
`.cursor/rules/` **nor** `.claude/rules/` is present AND the absolute
workspace path is not listed in `~/.house-rules-ignore` (if that file exists):
ask the user **once per session**:

> This project isn't bootstrapped with house-rules. Options:
>
> 1. Run `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" init --tool cursor|claude|both` to bootstrap
> 2. Skip for this session
> 3. Add this repo to `~/.house-rules-ignore` to silence this prompt permanently
>
> Which?

Act on the user's answer. If either rules directory is present, this block
is satisfied by the project's own rules — do not prompt.

If the user picks (1), confirm the tool choice before invoking, then pass
the chosen tool explicitly as `--tool cursor`, `--tool claude`, or
`--tool both`. Do not invoke `house-rules init` without a `--tool` flag or
an interactive terminal — the init refuses non-TTY invocation when the
tool isn't specified.

If `"${PROCESS_KIT:-$HOME/process-kit}"` does not exist, tell the
user to clone the kit first:

> house-rules is not installed at `~/process-kit`. Clone it
> with: `git clone https://github.com/kevglynn/house-rules ~/process-kit`

Do not re-ask in the same session after the user answers.
```

### global-safety-net/agent-identity.md

```markdown
## Agent identity — no human-baseline estimation

Never estimate effort, timelines, or team size using human development
baselines. Avoid **time units** (hours/days/weeks/months/quarters/sprints),
**team-size claims** ("two engineers", "small team", "team of N"),
**schedule framing** (timeline, schedule, ambitious, aggressive, ETA, "by
EOD"), and **estimation verbs** ("I estimate", "ballpark", "roughly N
hours") when framing work-to-be-done.

Not regressions (these are fine): historical facts ("the bug was open for 3
weeks"), product or API behavior ("a 30-second timeout"), quoted
references, and agent-process units ("one invocation", "N tool calls").

Instead describe: **complexity** (dependencies, unknowns), **scope**
(files/components affected), **sequencing** (what blocks what), and
**technical risk**. The question is "what are the dependencies and risks?"
— not "how long will this take?"

If you catch drift mid-response, correct inline and continue. See
`.cursor/rules/agent-identity.mdc` (Cursor) or
`.claude/rules/agent-identity.md` (Claude Code) in any
house-rules-bootstrapped project for the full rule (banned-token
scan, review protocol, and edge cases). The canonical source is
`cursor/rules/agent-identity.mdc` in the kit repo itself.
```

### scripts/tests/test_marker_migration.sh

```bash
#!/usr/bin/env bash
# Fixture tests for the marker-rewrite loops in the three installers:
# fresh-install idempotency plus the malformed-marker guards (orphan BEGIN,
# CRLF markers) introduced by process-kit-0em. The legacy predecessor-prefix
# migration cases were retired with the migration machinery
# (process-kit-26b, sunset 2026-08-06); the guards outlive the migration —
# they protect current-marker files the same way. Heredoc fixtures +
# throwaway HOME per case; never touches the invoking user's HOME. Run from
# anywhere:
#   bash scripts/tests/test_marker_migration.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SAFETY_NET="$KIT_ROOT/scripts/install-global-safety-net.sh"
ALIASES="$KIT_ROOT/scripts/install-aliases.sh"
INIT="$KIT_ROOT/scripts/init.sh"

PASS=0
FAIL=0
CLEANUP=()
cleanup() {
  local d
  for d in "${CLEANUP[@]:-}"; do
    [ -n "$d" ] && rm -rf "$d"
  done
}
trap cleanup EXIT

new_home() {
  local h
  h="$(mktemp -d)"
  CLEANUP+=("$h")
  printf '%s' "$h"
}

# bd shim: this suite exercises marker-rewrite logic, not beads.
# the init preflight hard-fails when bd is absent (CI runners don't
# have it), so a no-op stub keeps the preflight green and makes local and
# CI runs behaviorally identical (process-kit-4ma).
BD_SHIM_DIR="$(mktemp -d)"
CLEANUP+=("$BD_SHIM_DIR")
printf '#!/bin/sh\nexit 0\n' > "$BD_SHIM_DIR/bd"
chmod +x "$BD_SHIM_DIR/bd"
export PATH="$BD_SHIM_DIR:$PATH"

check() { # check <name> <condition...>
  local name="$1"; shift
  if "$@"; then
    echo "ok - $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL - $name"
    FAIL=$((FAIL + 1))
  fi
}

file_has()      { grep -qF -- "$2" "$1"; }
out_has()       { grep -qF -- "$2" <<< "$1"; }
out_lacks()     { ! grep -qF -- "$2" <<< "$1"; }
count_is()      { [ "$(grep -cF -- "$2" "$1")" = "$3" ]; }

# --- 1. Fresh CLAUDE.md install: three current blocks around user content;
#        second run byte-identical ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
# CLAUDE.md

user preamble stays
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "claude-md fresh install: three current blocks" \
  count_is "$h/CLAUDE.md" "<!-- BEGIN house-rules:" 3
check "claude-md fresh install: says Added" \
  out_has "$out" "Added block"
check "claude-md fresh install: user content preserved" \
  file_has "$h/CLAUDE.md" "user preamble stays"
sha1="$(sha256sum "$h/CLAUDE.md")"
out2="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
sha2="$(sha256sum "$h/CLAUDE.md")"
check "claude-md second run: byte-identical" test "$sha1" = "$sha2"
check "claude-md second run: says already current" \
  out_has "$out2" "already current"

# --- 2. Fresh rc install: one block; user lines survive; idempotent ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
export USER_BEFORE=1
EOF
HOME="$h" bash "$ALIASES" --shell bash > /dev/null 2>&1
check "rc fresh install: exactly one current block" \
  count_is "$h/.bashrc" "# BEGIN house-rules:aliases" 1
check "rc fresh install: user lines preserved" \
  file_has "$h/.bashrc" "export USER_BEFORE=1"
sha1="$(sha256sum "$h/.bashrc")"
HOME="$h" bash "$ALIASES" --shell bash > /dev/null 2>&1
sha2="$(sha256sum "$h/.bashrc")"
check "rc second run: byte-identical" test "$sha1" = "$sha2"

# --- 3. Fresh AGENTS.md section via init.sh; idempotent second run ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
# AGENTS.md

## User section stays
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md fresh section: one current section" \
  count_is "$repo/AGENTS.md" "<!-- BEGIN house-rules:agents-md -->" 1
check "agents-md fresh section: user section preserved" \
  file_has "$repo/AGENTS.md" "## User section stays"
check "agents-md fresh section: playbook-free" \
  bash -c "! grep -qi 'playbook' '$repo/AGENTS.md'"
check "agents-md fresh section: dispatcher-form commands only" \
  bash -c "grep -qF 'scripts/house-rules' '$repo/AGENTS.md' && ! grep -qE 'scripts/(init|doctor|sync-rules)\.sh' '$repo/AGENTS.md'"
sha1="$(sha256sum "$repo/AGENTS.md")"
out2="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md second run: byte-identical" test "$sha1" = "$sha2"
check "agents-md second run: says current" \
  out_has "$out2" "AGENTS.md house-rules section current"

# --- 3b. Stale version stamp: the section is present and well-formed but
#         stamped with an old kit version — init must refresh it in place
#         (one section, current stamp, user content intact). ---
sed -i 's/<!-- house-rules:version [^ ]* -->/<!-- house-rules:version 0.0.1 -->/' "$repo/AGENTS.md"
out3="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md stale stamp: reports the refresh" \
  out_has "$out3" "Refreshed AGENTS.md house-rules section"
check "agents-md stale stamp: still exactly one section" \
  count_is "$repo/AGENTS.md" "<!-- BEGIN house-rules:agents-md -->" 1
check "agents-md stale stamp: user section preserved" \
  file_has "$repo/AGENTS.md" "## User section stays"
check "agents-md stale stamp: stamp is current again" \
  bash -c "! grep -qF 'house-rules:version 0.0.1' '$repo/AGENTS.md'"

# --- 4. Orphan BEGIN (no END) in CLAUDE.md: user content below the orphan
#        marker must survive; the rewrite must refuse, not truncate ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN house-rules:agent-identity -->
truncated block, END marker lost
## USER CONTENT SENTINEL
important user notes that must not be deleted
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
rc4=$?
check "claude-md orphan BEGIN: user content survives" \
  file_has "$h/CLAUDE.md" "## USER CONTENT SENTINEL"
check "claude-md orphan BEGIN: warns instead of rewriting" \
  out_has "$out" "malformed"
check "claude-md orphan BEGIN: does not claim Updated" \
  out_lacks "$out" "Updated block 'agent-identity'"
check "claude-md orphan BEGIN: exits nonzero (refusal is not success)" \
  test "$rc4" -ne 0

# --- 4b. Orphan BEGIN above a WELL-FORMED block in CLAUDE.md: a BEGIN seen
#         while a block is already open means the earlier BEGIN lost its
#         END — the rewrite must refuse, never swallow the user lines
#         between the orphan and the real block. ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN house-rules:agent-identity -->
orphan block, END marker lost
## CLAUDE NESTED SENTINEL
<!-- BEGIN house-rules:agent-identity -->
stale body forces the replace path
<!-- END house-rules:agent-identity -->
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
rc4b=$?
check "claude-md nested BEGIN: user content between markers survives" \
  file_has "$h/CLAUDE.md" "## CLAUDE NESTED SENTINEL"
check "claude-md nested BEGIN: warns malformed" \
  out_has "$out" "malformed"
check "claude-md nested BEGIN: does not claim Updated" \
  out_lacks "$out" "Updated block 'agent-identity'"
check "claude-md nested BEGIN: exits nonzero" \
  test "$rc4b" -ne 0

# --- 5. Orphan BEGIN in rc file at install: the block reads as present but
#        stale, so install takes the refresh path — whose rewrite loop must
#        refuse the malformed markers and leave the rc untouched (truncation
#        would eat everything below the orphan BEGIN). Same guard is
#        exercised on uninstall (case 8). ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
truncated, END lost
export USER_SENTINEL=1
EOF
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc5=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc orphan BEGIN at install: user content survives" \
  file_has "$h/.bashrc" "export USER_SENTINEL=1"
check "rc orphan BEGIN at install: rc left byte-identical" \
  test "$sha1" = "$sha2"
check "rc orphan BEGIN at install: warns malformed instead of rewriting" \
  out_has "$out" "malformed"
check "rc orphan BEGIN at install: exits nonzero (refusal is not success)" \
  test "$rc5" -ne 0

# --- 5b. Stale-but-well-formed rc block at install: the body changed across
#         kit versions (v0.3.0 dispatcher cut renamed the sourced file), so
#         a present block with an old body must be refreshed in place —
#         current body, still exactly one block, neighbors intact. ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
export USER_ABOVE=1
# BEGIN house-rules:aliases
[ -f "$HOME/.playbook-aliases.sh" ] && . "$HOME/.playbook-aliases.sh"
# END house-rules:aliases
export USER_BELOW=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
check "rc stale block: refreshed to current body" \
  file_has "$h/.bashrc" ".house-rules-aliases.sh"
check "rc stale block: old body gone" \
  bash -c "! grep -qF '.playbook-aliases.sh' '$h/.bashrc'"
check "rc stale block: still exactly one block" \
  count_is "$h/.bashrc" "# BEGIN house-rules:aliases" 1
check "rc stale block: neighbors intact" \
  bash -c "grep -qF 'export USER_ABOVE=1' '$h/.bashrc' && grep -qF 'export USER_BELOW=1' '$h/.bashrc'"
check "rc stale block: reports the refresh" \
  out_has "$out" "Refreshed the source block"

# --- 5c. Orphan BEGIN above a WELL-FORMED block at install: the currency
#         check reads the file as stale, so install takes the refresh path;
#         the scan opens at the orphan and would swallow the real block plus
#         every user line between — a BEGIN seen while a block is open must
#         make the rewrite refuse, never delete. ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
export USER_BETWEEN=1
# BEGIN house-rules:aliases
[ -f "$HOME/.playbook-aliases.sh" ] && . "$HOME/.playbook-aliases.sh"
# END house-rules:aliases
export USER_BELOW_2=1
EOF
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc5c=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc nested BEGIN at install: user content between markers survives" \
  file_has "$h/.bashrc" "export USER_BETWEEN=1"
check "rc nested BEGIN at install: rc left byte-identical" \
  test "$sha1" = "$sha2"
check "rc nested BEGIN at install: warns malformed" \
  out_has "$out" "malformed"
check "rc nested BEGIN at install: exits nonzero" \
  test "$rc5c" -ne 0

# --- 6. Orphan BEGIN in AGENTS.md: same guard via init.sh ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
<!-- BEGIN house-rules:agents-md -->
truncated, END lost
## AGENTS USER SENTINEL
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md orphan BEGIN: user content survives" \
  file_has "$repo/AGENTS.md" "## AGENTS USER SENTINEL"
check "agents-md orphan BEGIN: warns instead of rewriting" \
  out_has "$out" "malformed"

# --- 6b. Orphan BEGIN above a WELL-FORMED section with a stale stamp: the
#         stamp check forces the refresh path; the scan must refuse at the
#         nested BEGIN instead of swallowing the user lines between. ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
<!-- BEGIN house-rules:agents-md -->
orphan, END lost
## AGENTS NESTED SENTINEL
<!-- BEGIN house-rules:agents-md -->
old body
<!-- house-rules:version 0.0.1 -->
<!-- END house-rules:agents-md -->
EOF
sha1="$(sha256sum "$repo/AGENTS.md")"
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
rc6b=$?
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md nested BEGIN: user content between markers survives" \
  file_has "$repo/AGENTS.md" "## AGENTS NESTED SENTINEL"
check "agents-md nested BEGIN: file left byte-identical" \
  test "$sha1" = "$sha2"
check "agents-md nested BEGIN: warns malformed" \
  out_has "$out" "malformed"
check "agents-md nested BEGIN: init exits nonzero" \
  test "$rc6b" -ne 0

# --- 7. CRLF-marked CLAUDE.md block: substring detection fires but the
#        line-exact rewrite cannot consume it — must refuse honestly, never
#        claim Updated while changing nothing ---
h="$(new_home)"
printf '%s\r\n' \
  "<!-- BEGIN house-rules:agent-identity -->" \
  "crlf body" \
  "<!-- END house-rules:agent-identity -->" > "$h/CLAUDE.md"
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "crlf block: does not claim Updated" \
  out_lacks "$out" "Updated block"
check "crlf block: warns about malformed markers" \
  out_has "$out" "malformed"
# The other (absent) blocks may legitimately be appended; the CRLF block
# itself must remain byte-for-byte (both marker lines + body).
check "crlf block: left as-is" \
  count_is "$h/CLAUDE.md" "house-rules:agent-identity" 2

# --- 8. Uninstall with an orphan BEGIN: remove loops share the guard —
#        user content below the orphan marker survives ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
truncated, END lost
export UNINSTALL_SENTINEL=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash --uninstall 2>&1)"
rc8=$?
check "uninstall orphan BEGIN: user content survives" \
  file_has "$h/.bashrc" "export UNINSTALL_SENTINEL=1"
check "uninstall orphan BEGIN: warns instead of removing" \
  out_has "$out" "malformed"
check "uninstall orphan BEGIN: does not claim nothing-to-remove" \
  out_lacks "$out" "Nothing to remove"
check "uninstall orphan BEGIN: exits nonzero" \
  test "$rc8" -ne 0

# --- 9. CRLF rc block at install: the substring presence check fires but
#        the line-exact scan consumes nothing — must refuse, leave the file
#        byte-identical, and NOT exit 0 claiming the aliases are active. ---
h="$(new_home)"
printf '%s\r\n' \
  "# BEGIN house-rules:aliases" \
  "crlf body" \
  "# END house-rules:aliases" > "$h/.bashrc"
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc9=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc crlf block: left byte-identical" \
  test "$sha1" = "$sha2"
check "rc crlf block: warns malformed" \
  out_has "$out" "malformed"
check "rc crlf block: exits nonzero" \
  test "$rc9" -ne 0

echo ""
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]
```

## Report format

For each finding: severity (Critical / Important / Minor), file + location, what, why it matters, suggested fix. List rejected candidate findings with the reason for rejection. End with an overall verdict.
