#!/usr/bin/env bash
set -euo pipefail

# One-command project setup for the playbook (house-rules).
# Replaces the 7+ manual steps in QUICKSTART.md with a single invocation.
#
# Usage:
#   ./scripts/playbook-init.sh                    # Interactive — asks for tool choice
#   ./scripts/playbook-init.sh --tool cursor      # Set up for Cursor
#   ./scripts/playbook-init.sh --tool claude       # Set up for Claude Code
#   ./scripts/playbook-init.sh --tool both         # Set up for both tools
#   ./scripts/playbook-init.sh --stealth           # Use bd init --stealth (personal repos)
#   ./scripts/playbook-init.sh --no-hooks          # Skip bd hooks install (default: install)
#   ./scripts/playbook-init.sh --skills            # Copy skills into .cursor/skills/
#   ./scripts/playbook-init.sh --help

PLAYBOOK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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
One-command project setup for the playbook (house-rules).

Usage: playbook-init.sh [options]

Options:
  --tool cursor|claude|both   Which tool to set up for (default: ask)
  --stealth                   Use bd init --stealth (for personal repos)
  --no-hooks                  Skip bd hooks install (default: install beads git hooks)
  --skills                    Copy skill directories from playbook into .cursor/skills/
  --help                      Show this help

Run from the root of the project you want to set up.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# ---------- Concurrency lock (mkdir is atomic on all filesystems) ----------

LOCKDIR="$PROJECT_ROOT/.playbook-init.lock"
# Clean stale locks older than 10 minutes
if [ -d "$LOCKDIR" ]; then
  lock_age=$(( $(date +%s) - $(stat -f %m "$LOCKDIR" 2>/dev/null || stat -c %Y "$LOCKDIR" 2>/dev/null || echo 0) ))
  if [ "$lock_age" -gt 600 ]; then
    rmdir "$LOCKDIR" 2>/dev/null || rm -rf "$LOCKDIR"
    echo "  Removed stale lock (age: ${lock_age}s)"
  fi
fi
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another playbook-init is running for this project. Exiting."
  exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

echo "=== Playbook Init: $(basename "$PROJECT_ROOT") ==="
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

if [ ! -d "$PLAYBOOK_ROOT/cursor/rules" ]; then
  echo "✗ Playbook repo not found at $PLAYBOOK_ROOT"
  echo "  Fix: git clone https://github.com/kevglynn/house-rules ~/process-kit"
  errors=$((errors + 1))
else
  echo "✓ Playbook repo at $PLAYBOOK_ROOT"
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
  if ! cp "$PLAYBOOK_ROOT/cursor/rules/"*.mdc "$dest/" 2>/tmp/playbook-init.cp.err; then
    echo "✗ Failed to copy Cursor rules → $dest"
    sed 's/^/    /' /tmp/playbook-init.cp.err 2>/dev/null
    rm -f /tmp/playbook-init.cp.err
    exit 1
  fi
  rm -f /tmp/playbook-init.cp.err
  count=$(ls -1 "$dest/"*.mdc 2>/dev/null | wc -l | tr -d ' ')
  echo "✓ Copied $count Cursor rules → .cursor/rules/"
fi

if [[ "$TOOL" == "claude" || "$TOOL" == "both" ]]; then
  dest="$PROJECT_ROOT/.claude/rules"
  mkdir -p "$dest"
  if ! cp "$PLAYBOOK_ROOT/claude/rules/"*.md "$dest/" 2>/tmp/playbook-init.cp.err; then
    echo "✗ Failed to copy Claude rules → $dest"
    sed 's/^/    /' /tmp/playbook-init.cp.err 2>/dev/null
    rm -f /tmp/playbook-init.cp.err
    exit 1
  fi
  rm -f /tmp/playbook-init.cp.err
  count=$(ls -1 "$dest/"*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "✓ Copied $count Claude Code rules → .claude/rules/"
fi

# ---------- Copy skills (opt-in) ----------

if $SKILLS; then
  skills_src="$PLAYBOOK_ROOT/skills"
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
    echo "  (no skills/ directory in playbook — skipping)"
  fi
fi

# ---------- Distributed CLIs (manifest-driven) ----------
#
# Every kit CLI that must live in the target repo is registered once in
# scripts/distributed-clis.list; this loop distributes each entry and
# playbook-doctor.sh drift-checks the same manifest. Per-script rationale
# and the field layout live in the manifest's header comments.

clis_manifest="$PLAYBOOK_ROOT/scripts/distributed-clis.list"

if [ -f "$clis_manifest" ]; then
  while IFS='|' read -r cli_name _cli_rest; do
    case "$cli_name" in ""|\#*) continue ;; esac
    cli_src="$PLAYBOOK_ROOT/scripts/$cli_name"
    cli_dest="$PROJECT_ROOT/scripts/$cli_name"
    [ -f "$cli_src" ] || continue
    mkdir -p "$PROJECT_ROOT/scripts"
    if ! cp -f "$cli_src" "$cli_dest" 2>/tmp/playbook-init.cp.err; then
      echo "✗ Failed to copy $cli_name → scripts/"
      sed 's/^/    /' /tmp/playbook-init.cp.err 2>/dev/null
      rm -f /tmp/playbook-init.cp.err
      exit 1
    fi
    rm -f /tmp/playbook-init.cp.err
    chmod +x "$cli_dest"
    echo "✓ Copied $cli_name CLI → scripts/$cli_name"
  done < "$clis_manifest"
else
  echo "⚠ Distributed-CLI manifest missing at $clis_manifest — no kit CLIs distributed"
fi

# ---------- Conventions profile (data-shaped convention source) ----------
#
# The data file the distributed checkers read; ships verbatim (byte-drift-
# checked by playbook-doctor, SUMMARY key profile_drift). Ownership, skew,
# and inert-key rules: docs/operations.md.
# defer: hand-written parallel block instead of generalizing the manifest to
# data files. ceiling: duplicates the CLI-loop copy idiom per file. upgrade
# when: a second data-shaped file distributes.
profile_src="$PLAYBOOK_ROOT/profiles/conventions.toml"
if [ -f "$profile_src" ]; then
  mkdir -p "$PROJECT_ROOT/profiles"
  if ! cp -f "$profile_src" "$PROJECT_ROOT/profiles/conventions.toml" 2>/tmp/playbook-init.cp.err; then
    echo "✗ Failed to copy profiles/conventions.toml"
    sed 's/^/    /' /tmp/playbook-init.cp.err 2>/dev/null
    rm -f /tmp/playbook-init.cp.err
    exit 1
  fi
  rm -f /tmp/playbook-init.cp.err
  echo "✓ Copied conventions profile → profiles/conventions.toml"
else
  echo "⚠ Conventions profile missing at $profile_src — distributed checkers will fall back to built-in grammars"
fi

# The CI gate that makes the ledger non-bypassable (not-overwriting, like
# the PR template — target repos may have customized it).
ledger_wf_src="$PLAYBOOK_ROOT/templates/tdd-ledger-verify.yml"
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

# Note: we skip 'bd setup cursor/claude' here because the playbook's 8 rules
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

coc_src="$PLAYBOOK_ROOT/CODE_OF_CONDUCT.md"
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
pr_template_src="$PLAYBOOK_ROOT/.github/pull_request_template.md"
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
# marker-delimited playbook section, idempotent, respecting whatever
# content is already there.

agents_md="$PROJECT_ROOT/AGENTS.md"
# Marker prefix is "house-rules:" (final kit name, decision 0001 A1). Target
# repos bootstrapped by the predecessor playbook carry the legacy
# "ai-dev-playbook:" prefix in AGENTS.md, so the section scan below recognizes
# BOTH prefixes: a legacy-marked section is rewritten in place under the new
# markers, never duplicated. Keep the legacy recognition until no target repo
# still carries an old-marker section.
agents_begin="<!-- BEGIN house-rules:agents-md -->"
agents_end="<!-- END house-rules:agents-md -->"
agents_begin_legacy="<!-- BEGIN ai-dev-playbook:agents-md -->"
agents_end_legacy="<!-- END ai-dev-playbook:agents-md -->"

# Version stamp: sourced from the kit's VERSION file (single source of truth).
# Rendered as a machine-parseable marker line inside the section so
# playbook-doctor.sh can compare the target's stamp against the kit version.
playbook_version="unknown"
playbook_version_label="unknown"
if [ -f "$PLAYBOOK_ROOT/VERSION" ]; then
  playbook_version="$(tr -d '[:space:]' < "$PLAYBOOK_ROOT/VERSION")"
  playbook_version_label="v$playbook_version"
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

render_playbook_agents_section() {
  cat <<AGENTS_SECTION
$agents_begin
## house-rules (agent playbook)

This project follows [house-rules](https://github.com/kevglynn/house-rules) — rules, skills, and scripts for working with coding agents.

**Rules location:** \`.cursor/rules/*.mdc\` (Cursor) and/or \`.claude/rules/*.md\` (Claude Code). Synced from \`\${PROCESS_KIT:-\$HOME/process-kit}\`. Do not edit in place.

**Ownership boundary:** \`.agents/overlay.md\` is project-editable (optional per-skill parameters; create it as needed). \`profiles/conventions.toml\`, when present, is kit-owned and drift-checked byte-for-byte — do not edit it here; change it in the kit and sync.

**Diagnose setup (human-readable):**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/playbook-doctor.sh"
\`\`\`

**Diagnose (agent-consumable; structured exit codes + \`SUMMARY:\` line):**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/playbook-doctor.sh" --agent
\`\`\`

Exit: \`0\`=ok, \`2\`=bootstrap_needed, \`3\`=drift, \`1\`=error. On exit 3 the SUMMARY key names what drifted: \`rules_drift_cursor\` | \`rules_drift_claude\` | \`rules_drift_both\` for stale rules, \`profile_drift\` for a stale \`profiles/conventions.toml\`, or ${cli_drift_keys_md:-a per-CLI drift key} for a stale distributed CLI (fix: re-copy the named file from the kit). See the \`agent-protocol\` block in \`~/CLAUDE.md\` for the full dispatch table.

**Sync rules with upstream:**
\`\`\`bash
bash "\${PROCESS_KIT:-\$HOME/process-kit}/scripts/sync-rules.sh"
\`\`\`

**Install the kit on a new machine:**
\`\`\`bash
git clone https://github.com/kevglynn/house-rules ~/process-kit
bash ~/process-kit/scripts/install-global-safety-net.sh   # per-machine, once
\`\`\`

Generated by \`playbook-init.sh\` on ${generated_on} from house-rules ${playbook_version_label}.
<!-- house-rules:version ${playbook_version} -->
$agents_end
AGENTS_SECTION
}

# Replace the existing marker-delimited block in place (atomic tmp+mv), used
# when the section is present but its version stamp is stale or missing, or
# when it carries legacy markers. Recognizes both marker prefixes and emits
# exactly one fresh section even if the file somehow carries several.
refresh_playbook_agents_section() {
  local tmp in_block=0 emitted=0
  tmp="$(mktemp "${agents_md}.tmp.XXXXXX")"
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ] && { [ "$line" = "$agents_begin" ] || [ "$line" = "$agents_begin_legacy" ]; }; then
      in_block=1
      if [ $emitted -eq 0 ]; then
        render_playbook_agents_section
        emitted=1
      fi
      continue
    fi
    if [ $in_block -eq 1 ]; then
      if [ "$line" = "$agents_end" ] || [ "$line" = "$agents_end_legacy" ]; then
        in_block=0
      fi
      continue
    fi
    printf '%s\n' "$line"
  done < "$agents_md" > "$tmp"
  # Refuse the rewrite when the marker scan went wrong: an unpaired BEGIN
  # (in_block still open at EOF) would have swallowed everything below it
  # into the tmp file — silently deleting user content on mv; a scan that
  # consumed no BEGIN at all (emitted=0, e.g. CRLF or indented marker
  # lines that match the substring grep but not the whole-line test)
  # would claim success while rewriting nothing.
  if [ $in_block -eq 1 ] || [ $emitted -eq 0 ]; then
    rm -f "$tmp"
    echo "⚠ $agents_md: playbook section markers are malformed (unpaired BEGIN or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
    return 1
  fi
  mv "$tmp" "$agents_md"
}

# Legacy check comes first: a legacy (or mixed) file is always rewritten in
# place, migrating the section to the current markers.
if [ -f "$agents_md" ] && grep -qF "$agents_begin_legacy" "$agents_md"; then
  if refresh_playbook_agents_section; then
    echo "✓ Migrated legacy-marked AGENTS.md playbook section to house-rules markers (${playbook_version_label})"
  fi
elif [ -f "$agents_md" ] && grep -qF "$agents_begin" "$agents_md"; then
  if grep -qF "<!-- house-rules:version ${playbook_version} -->" "$agents_md"; then
    echo "✓ AGENTS.md playbook section current (${playbook_version_label})"
  elif refresh_playbook_agents_section; then
    echo "✓ Refreshed AGENTS.md playbook section → ${playbook_version_label} (stamp was stale or missing)"
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
    render_playbook_agents_section
  } > "$agents_tmp"
  mv "$agents_tmp" "$agents_md"
  echo "✓ Appended playbook section to existing AGENTS.md"
else
  agents_tmp="$(mktemp "${agents_md}.tmp.XXXXXX")"
  {
    printf '# AGENTS.md\n\n'
    printf 'Any agent landing in this repo: start here.\n\n'
    render_playbook_agents_section
  } > "$agents_tmp"
  mv "$agents_tmp" "$agents_md"
  echo "✓ Created AGENTS.md with playbook section"
fi

# ---------- Sync targets ----------

# Throwaway bootstraps (test/verification runs under /tmp or $TMPDIR) must
# not register: dead entries surface as 'target does not exist' warnings on
# every later sync-rules.sh run until removed by hand.
TARGETS_FILE="$HOME/.playbook-sync-targets"
tmp_root="${TMPDIR:-/tmp}"
case "$PROJECT_ROOT/" in
  "${tmp_root%/}/"* | /tmp/*)
    echo "– Skipped ~/.playbook-sync-targets registration (throwaway path under ${tmp_root%/})"
    ;;
  *)
    if [ -f "$TARGETS_FILE" ] && grep -qF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
      echo "✓ Already in ~/.playbook-sync-targets"
    else
      echo "$PROJECT_ROOT" >> "$TARGETS_FILE"
      echo "✓ Added to ~/.playbook-sync-targets"
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
echo "Verify setup: bash $PLAYBOOK_ROOT/scripts/playbook-doctor.sh"
