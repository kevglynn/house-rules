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
#   ./scripts/init.sh --tier core        # Core-tier stamp only (no beads/scratchpad/sync)
#   ./scripts/init.sh --tier full        # Full bootstrap (default)
#   ./scripts/init.sh --stealth           # Use bd init --stealth (personal repos)
#   ./scripts/init.sh --no-hooks          # Skip bd hooks install (default: install)
#   ./scripts/init.sh --skills            # Copy skills into .cursor/skills/
#   ./scripts/init.sh --help

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/marker-rewrite.sh
. "$KIT_ROOT/scripts/lib/marker-rewrite.sh"
# shellcheck source=lib/backup-file.sh
. "$KIT_ROOT/scripts/lib/backup-file.sh"
TOOL=""
TIER="full"
STEALTH=false
NO_HOOKS=false
SKILLS=false
SAFE_MODE=true
PROJECT_ROOT="$(pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      # Guard before "$2": set -u otherwise aborts with raw "unbound variable".
      if [ $# -lt 2 ]; then
        echo "Error: --tool requires an argument (cursor|claude|both). See --help." >&2
        exit 1
      fi
      TOOL="$2"; shift 2 ;;
    --tier)
      if [ $# -lt 2 ]; then
        echo "Error: --tier requires an argument (core|full). See --help." >&2
        exit 1
      fi
      TIER="$2"; shift 2 ;;
    --stealth) STEALTH=true; shift ;;
    --no-hooks) NO_HOOKS=true; shift ;;
    --skills) SKILLS=true; shift ;;
    --unsafe) SAFE_MODE=false; shift ;;
    --help|-h)
      cat <<'EOF'
One-command project setup for house-rules.

Usage: init.sh [options]

Options:
  --tool <cursor|claude|both> Which tool to set up for (default: ask)
  --tier <core|full>          Install tier (default: full). core writes
                              .house-rules-tier only — no beads init,
                              scratchpad, or sync-target registration.
                              Pair with a plugin install for rules.
  --stealth                   Use bd init --stealth (for personal repos)
  --no-hooks                  Skip bd hooks install (default: install beads git hooks)
  --skills                    Copy skill directories from the kit into .cursor/skills/
  --unsafe                    Overwrite without writing .bak copies first
                              (default: back up any kit-owned file whose
                              bytes on disk differ from the kit's, same
                              convention as sync-rules.sh)
  --help                      Show this help

Re-running init is safe by default: a delivered file you have edited is
copied to <file>.<timestamp>.bak before it is replaced, as is AGENTS.md
before its house-rules section is refreshed. Files init creates but does not
own — the scratchpad, CODE_OF_CONDUCT.md, the PR template, the tdd-ledger
workflow — are never overwritten at all.

Run from the root of the project you want to set up.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

case "$TIER" in
  core|full) ;;
  *)
    echo "Invalid --tier: ${TIER} (use core or full)" >&2
    exit 1
    ;;
esac

# ---------- Concurrency lock (mkdir is atomic on all filesystems) ----------

LOCKDIR="$PROJECT_ROOT/.house-rules-init.lock"
# Acquire via mkdir. Stale locks (>10 min) are renamed aside atomically
# before mkdir — never rmdir-then-mkdir, which races when two concurrent
# inits both judge the lock stale and the second rmdir removes the first's
# fresh lock (process-kit-020).
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  if [ -d "$LOCKDIR" ]; then
    lock_age=$(( $(date +%s) - $(stat -f %m "$LOCKDIR" 2>/dev/null || stat -c %Y "$LOCKDIR" 2>/dev/null || echo 0) ))
    if [ "$lock_age" -gt 600 ]; then
      stale_victim="${LOCKDIR}.stale.$$"
      if mv "$LOCKDIR" "$stale_victim" 2>/dev/null; then
        rmdir "$stale_victim" 2>/dev/null || rm -rf "$stale_victim"
        echo "  Removed stale lock (age: ${lock_age}s)"
      fi
      if ! mkdir "$LOCKDIR" 2>/dev/null; then
        echo "Another house-rules init is running for this project. Exiting."
        exit 1
      fi
    else
      echo "Another house-rules init is running for this project. Exiting."
      exit 1
    fi
  else
    echo "Another house-rules init is running for this project. Exiting."
    exit 1
  fi
fi
# Per-run stderr capture for cp failures — never a fixed /tmp path (concurrent
# clobber + symlink-following write target; process-kit-020).
CP_ERR="$(mktemp "${TMPDIR:-/tmp}/house-rules-init.cp.XXXXXX")"
cleanup_init() {
  rm -f "$CP_ERR"
  rmdir "$LOCKDIR" 2>/dev/null || true
}
trap cleanup_init EXIT

# The one door for every kit-owned file init writes into the target repo.
# Rationale and the shared-convention contract: scripts/lib/backup-file.sh.
#
# A failed backup aborts instead of overwriting — proceeding would destroy
# the exact bytes the backup existed to preserve.
install_file() { # install_file <src> <dest> [label]
  local src="$1" dest="$2" label="${3:-$(basename "$2")}"
  # cp into a directory-shaped destination silently lands the file *inside*
  # it and returns 0, so the rule installs somewhere no agent reads and the
  # run still reports success.
  if [ -d "$dest" ]; then
    echo "✗ $label: destination is a directory ($dest) — refusing to install into it" >&2
    return 1
  fi
  if $SAFE_MODE && ! backup_before_overwrite "$src" "$dest"; then
    echo "✗ Failed to back up $label before overwrite — refusing to replace it" >&2
    return 1
  fi
  if ! cp -f "$src" "$dest" 2>"$CP_ERR"; then
    echo "✗ Failed to copy $label → $dest"
    sed 's/^/    /' "$CP_ERR" 2>/dev/null
    # The backup above may already have succeeded, in which case the
    # destination is now truncated or gone. Say so and point at the copy,
    # rather than leaving a message that reads as "nothing was written".
    if $SAFE_MODE; then
      echo "    destination may be partially written — restore from the .bak beside it" >&2
    fi
    return 1
  fi
}

# Install every file matching <glob-ext> from a kit rules directory.
#
# Per-file rather than one glob cp, so an existing edited rule can be backed
# up before it is replaced. The empty-glob case is checked once after the
# loop: testing it per-iteration reports "no rules found" for a directory
# full of rules when a single entry happens not to be a regular file, and
# does so after the earlier entries are already installed.
install_rules_dir() { # install_rules_dir <src-dir> <ext> <dest> <label>
  local src_dir="$1" ext="$2" dest="$3" label="$4" found=0 rule_src
  for rule_src in "$src_dir"/*."$ext"; do
    [ -e "$rule_src" ] || continue
    if [ ! -f "$rule_src" ]; then
      echo "✗ $(basename "$rule_src") in $src_dir is not a regular file" >&2
      return 1
    fi
    install_file "$rule_src" "$dest/$(basename "$rule_src")" || return 1
    found=$((found + 1))
  done
  if [ "$found" -eq 0 ]; then
    echo "✗ Failed to copy $label → $dest"
    echo "    no .$ext rules found in $src_dir"
    return 1
  fi
  echo "✓ Copied $found $label → ${dest#"$PROJECT_ROOT"/}/"
}

echo "=== house-rules init: $(basename "$PROJECT_ROOT") ==="
echo "  tier: $TIER"
echo ""

# ---------- Prerequisites ----------

errors=0

if ! command -v git &>/dev/null; then
  echo "✗ git is not installed"
  errors=$((errors + 1))
else
  echo "✓ git $(git --version | awk '{print $3}')"
fi

# bd is required for the full playbook (task tracking). Core tier is the
# zero-dependency wedge — plugin-delivered rules, no task-tracking init.
if [[ "$TIER" == "full" ]]; then
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
else
  echo "– bd not required (core tier)"
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

# ---------- Core stamp-only path ----------
#
# Plugin installs deliver rules; this path only records the tier so doctor
# and sync-target logic know not to nag. Optional --tool still copies local
# rules below (same as full), but beads/scratchpad/sync stay skipped.
# Stamp is written here only after the path is known to be stamp-only —
# never before a --tool validation that may refuse.

if [[ "$TIER" == "core" && -z "$TOOL" ]]; then
  printf '%s\n' "$TIER" > "$PROJECT_ROOT/.house-rules-tier"
  echo "✓ Wrote .house-rules-tier ($TIER)"
  echo ""
  echo "=== Core tier stamped ==="
  echo ""
  echo "What's ready:"
  echo "  • .house-rules-tier = core"
  echo "  • Skipped task-tracking init, scratchpad, sync-target registration"
  echo ""
  echo "Next steps:"
  echo "  1. Install the house-rules-core plugin (marketplace / Cursor plugin)"
  echo "  2. Or re-run with --tier core --tool cursor (or --tool claude / --tool both) to copy local rules"
  echo "  3. Verify: bash \"$KIT_ROOT/scripts/house-rules\" doctor"
  echo ""
  exit 0
fi

# ---------- Tool choice ----------
#
# Security gate: refuse non-interactive invocation without an explicit
# --tool flag. Prevents prompt-injected agents from silently bootstrapping
# a repo behind the user's back — if there's no TTY, the flag must be
# passed explicitly (which means the agent had to declare the choice to
# the user before running).
# Validate --tool BEFORE writing .house-rules-tier so a refused/invalid
# invocation cannot leave a misleading authoritative stamp.

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
    echo "  --tier core     # Stamp core tier only (no --tool needed)" >&2
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

case "$TOOL" in
  cursor|claude|both) ;;
  *)
    echo "Invalid --tool: ${TOOL:-<empty>} (use cursor, claude, or both)" >&2
    exit 1
    ;;
esac

# ---------- Tier stamp (after tool validation) ----------
#
# Written once --tool is known-valid so doctor treats the stamp as
# authoritative. Mid-copy failures can still leave a stamp with a partial
# install — that is a known ceiling (doctor should still surface missing
# pieces); the refused-before-any-work case is the one we close here.

printf '%s\n' "$TIER" > "$PROJECT_ROOT/.house-rules-tier"
echo "✓ Wrote .house-rules-tier ($TIER)"

echo ""

# ---------- Copy rules ----------

if [[ "$TOOL" == "cursor" || "$TOOL" == "both" ]]; then
  dest="$PROJECT_ROOT/.cursor/rules"
  mkdir -p "$dest"
  install_rules_dir "$KIT_ROOT/cursor/rules" mdc "$dest" "Cursor rules" || exit 1
fi

if [[ "$TOOL" == "claude" || "$TOOL" == "both" ]]; then
  dest="$PROJECT_ROOT/.claude/rules"
  mkdir -p "$dest"
  install_rules_dir "$KIT_ROOT/claude/rules" md "$dest" "Claude Code rules" || exit 1
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
  # Core tier: only skills listed in profiles/core-manifest.list — never the
  # full skills/ tree (Tier-2 finding: --skills leaked full-tier skills).
  core_skill_allow=""
  if [[ "$TIER" == "core" ]]; then
    core_manifest="$KIT_ROOT/profiles/core-manifest.list"
    if [ -f "$core_manifest" ]; then
      while IFS='|' read -r kind path _rest; do
        case "$kind" in ""|\#*) continue ;; esac
        [[ "$kind" == "skill" ]] || continue
        core_skill_allow="$core_skill_allow $(basename "$path")"
      done < "$core_manifest"
    fi
  fi
  if [ -d "$skills_src" ]; then
    for skills_rel in $skills_dests; do
      skills_dest="$PROJECT_ROOT/$skills_rel"
      mkdir -p "$skills_dest"
      skills_count=0
      for skill_dir in "$skills_src"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        if [[ "$TIER" == "core" ]]; then
          case " $core_skill_allow " in
            *" $skill_name "*) ;;
            *) continue ;;
          esac
        fi
        # Walked per-file rather than cp -rf: a skill is a directory of
        # files a project may have edited, and a recursive copy overwrites
        # each of them with no chance to back one up. Like cp -rf, this adds
        # and replaces but never removes, so a file the kit no longer ships
        # stays put.
        #
        # Regular files only: unlike cp -rf, this does not carry symlinks or
        # recreate empty directories. No skill ships either today; a skill
        # that needs one must extend this walk.
        while IFS= read -r -d '' skill_file; do
          skill_rel="${skill_file#"$skill_dir"}"
          skill_file_dest="$skills_dest/$skill_name/$skill_rel"
          mkdir -p "$(dirname "$skill_file_dest")"
          install_file "$skill_file" "$skill_file_dest" \
            "$skill_name/$skill_rel" || exit 1
        done < <(find "$skill_dir" -type f -print0)
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
# Core tier: only CLIs listed in profiles/core-manifest.list.

clis_manifest="$KIT_ROOT/scripts/distributed-clis.list"
core_cli_allow=""
if [[ "$TIER" == "core" ]]; then
  core_manifest="$KIT_ROOT/profiles/core-manifest.list"
  if [ -f "$core_manifest" ]; then
    while IFS='|' read -r kind path _rest; do
      case "$kind" in ""|\#*) continue ;; esac
      [[ "$kind" == "cli" ]] || continue
      core_cli_allow="$core_cli_allow $(basename "$path")"
    done < "$core_manifest"
  fi
fi

if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r cli_name _cli_rest; do
    case "$cli_name" in ""|\#*) continue ;; esac
    if [[ "$TIER" == "core" ]]; then
      case " $core_cli_allow " in
        *" $cli_name "*) ;;
        *) continue ;;
      esac
    fi
    cli_src="$KIT_ROOT/scripts/$cli_name"
    cli_dest="$PROJECT_ROOT/scripts/$cli_name"
    [ -f "$cli_src" ] || continue
    mkdir -p "$PROJECT_ROOT/scripts"
    install_file "$cli_src" "$cli_dest" "$cli_name" || exit 1
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
  install_file "$profile_src" "$PROJECT_ROOT/profiles/conventions.toml" \
    "profiles/conventions.toml" || exit 1
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

if [[ "$TIER" == "core" ]]; then
  echo "– Skipped task-tracking init (core tier)"
elif [ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ]; then
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
if [[ "$TIER" == "full" ]] && command -v bd &>/dev/null && { [ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ]; }; then
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
if [[ "$TIER" == "core" ]]; then
  echo "– Skipped bd hooks install (core tier)"
elif $NO_HOOKS; then
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

if [[ "$TIER" == "core" ]]; then
  echo "– Skipped scratchpad (core tier)"
elif [[ "$TOOL" == "both" ]]; then
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
# 2 = malformed markers, warn-and-skip) via scripts/lib/marker-rewrite.sh.
refresh_agents_section() {
  # A third posture, distinct from the owned-overwrite and seeded-never-touch
  # groups: this rewrites kit-owned bytes *inside* a project-owned file.
  # Content outside the markers survives, but anything a project wrote
  # between them does not — and the refresh fires on every kit version bump,
  # in every target. Same guarantee as the delivered files, then: a
  # recoverable copy before the bytes go.
  if $SAFE_MODE && [ -f "$agents_md" ] && ! backup_file "$agents_md"; then
    echo "✗ Failed to back up AGENTS.md before refreshing its house-rules section" >&2
    return 1
  fi
  marker_rewrite_file "$agents_md" "$agents_begin" "$agents_end" \
    html "house-rules section markers" render_agents_section
}

# Structural currency: exactly one well-formed section containing the live
# version stamp. Stamp-anywhere grep was wrong — a later stale duplicate
# (or an orphan carrying the stamp text) could hide forever.
agents_section_is_current() {
  marker_html_section_contains "$agents_md" "$agents_begin" "$agents_end" \
    "<!-- house-rules:version ${kit_version} -->"
}

agents_refresh_failed=0
if [ -f "$agents_md" ] && grep -qF "$agents_begin" "$agents_md"; then
  if agents_section_is_current; then
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
# Core-tier installs must never register — they are not kit-sync consumers
# (rules arrive via plugin; registering would invite full-rule sync wipes).
# Reclassifying full→core must also *remove* any prior exact registration.
TARGETS_FILE="$HOME/.house-rules-sync-targets"
tmp_root="${TMPDIR:-/tmp}"
if [[ "$TIER" == "core" ]]; then
  echo "– Skipped ~/.house-rules-sync-targets registration (core tier)"
  if [ -f "$TARGETS_FILE" ] && grep -qxF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
    # grep exits 1 when every line matched (file becomes empty) — do not
    # treat that as failure or skip the mv.
    grep -vxF "$PROJECT_ROOT" "$TARGETS_FILE" > "$TARGETS_FILE.tmp" || true
    mv "$TARGETS_FILE.tmp" "$TARGETS_FILE"
    echo "✓ Removed prior sync-target registration (full→core)"
  fi
else
  case "$PROJECT_ROOT/" in
    "${tmp_root%/}/"* | /tmp/*)
      echo "– Skipped ~/.house-rules-sync-targets registration (throwaway path under ${tmp_root%/})"
      ;;
    *)
      if [ -f "$TARGETS_FILE" ] && grep -qxF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
        echo "✓ Already in ~/.house-rules-sync-targets"
      else
        echo "$PROJECT_ROOT" >> "$TARGETS_FILE"
        echo "✓ Added to ~/.house-rules-sync-targets"
      fi
      ;;
  esac
fi

# ---------- Summary ----------

echo ""
echo "=== Setup complete ==="
echo ""
# Same line sync prints, for the same reason: a re-run that quietly replaced
# a file someone had edited should say so in the summary, not only in the
# scrollback next to the file it touched.
if $SAFE_MODE && [ "$SAFE_BACKUP_COUNT" -gt 0 ]; then
  echo "$SAFE_BACKUP_COUNT file(s) backed up before overwrite — .bak copies preserved."
  echo ""
fi
echo "What's ready:"
echo "  • $(ls -1 "$PROJECT_ROOT/.cursor/rules/"*.mdc 2>/dev/null | wc -l | tr -d ' ') Cursor rules" 2>/dev/null || true
echo "  • $(ls -1 "$PROJECT_ROOT/.claude/rules/"*.md 2>/dev/null | wc -l | tr -d ' ') Claude rules" 2>/dev/null || true
if $SKILLS; then
  for skills_rel in ${skills_dests:-}; do
    echo "  • $(ls -1d "$PROJECT_ROOT/$skills_rel/"*/ 2>/dev/null | wc -l | tr -d ' ') skills ($skills_rel/)" 2>/dev/null || true
  done
fi
if [[ "$TIER" == "full" ]]; then
  echo "  • Beads task tracking (bd list, bd ready, bd create)"
  if $HOOKS_INSTALLED; then
    echo "  • Beads git hooks (bd hooks install — auto-export / sync on commit & push)"
  fi
  if $NO_HOOKS; then
    echo "  • Beads git hooks skipped — run bd hooks install when ready"
  fi
  echo "  • Scratchpad for cross-session context"
else
  echo "  • Task tracking / scratchpad skipped (core tier)"
fi
[ -f "$coc_dest" ] && echo "  • Agentic Covenant (CODE_OF_CONDUCT.md)"
if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r cli_name _key _header _note cli_label cli_detail; do
    case "$cli_name" in ""|\#*) continue ;; esac
    if [[ "$TIER" == "core" ]]; then
      case " $core_cli_allow " in
        *" $cli_name "*) ;;
        *) continue ;;
      esac
    fi
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
