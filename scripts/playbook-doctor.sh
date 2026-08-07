#!/usr/bin/env bash
set -uo pipefail

# Validates the playbook setup for the current project.
# Reports issues with fix commands. CI-friendly exit code.
#
# Usage:
#   ./scripts/playbook-doctor.sh                    # Check current directory
#   ./scripts/playbook-doctor.sh /path/to/project   # Check specific project
#   ./scripts/playbook-doctor.sh --agent            # Agent-consumable output
#   ./scripts/playbook-doctor.sh --help
#
# --agent mode emits a final "SUMMARY: <key>" line and uses structured exit
# codes for agent branching. See the agent-protocol global safety-net block
# for the full contract.
#
# Exit codes:
#   0 = ok (no action needed)
#   2 = bootstrap_needed (no rules in this repo)
#   3 = drift (kit-managed files present but stale vs playbook source:
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

PLAYBOOK_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_MODE=false
PROJECT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)  AGENT_MODE=true; shift ;;
    -h|--help)
      cat <<'EOF'
Validates playbook setup for a project. Reports issues with fix commands.

Usage: playbook-doctor.sh [project-path] [--agent]

Checks:
  • bd (beads) is on PATH
  • Agent rules are present and match the canonical source
  • Each distributed CLI in scripts/distributed-clis.list (if present in
    the target) matches the kit copy
  • The conventions profile (profiles/conventions.toml, if present in the
    target) matches the kit copy byte-for-byte
  • Kit-resident references (skills/…, templates/…) cited by distributed
    rules resolve somewhere on this machine (warn-only)
  • AGENTS.md playbook section version stamp matches the kit VERSION (warn-only)
  • Beads is initialized (bd ping + bd list)
  • Beads git hooks recommended (pre-commit, post-merge, pre-push)
  • Scratchpad exists with correct sections
  • Project is in ~/.playbook-sync-targets
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

echo "=== Playbook Doctor: $(basename "$PROJECT_ROOT") ==="
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
  src_count=$(ls -1 "$PLAYBOOK_ROOT/cursor/rules/"*.mdc 2>/dev/null | wc -l | tr -d ' ')
  # Check that every canonical rule is present and current.
  # Extra rules from other tools (e.g. Jawnt) are fine — only flag missing or stale.
  stale=0
  missing=0
  for f in "$PLAYBOOK_ROOT/cursor/rules/"*.mdc; do
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
      check_pass "Cursor rules: $src_count playbook files up to date (+$extra from other tools)"
    else
      check_pass "Cursor rules: $mdc_count files, all up to date"
    fi
  else
    issues=""
    [ $missing -gt 0 ] && issues="$missing missing"
    [ $stale -gt 0 ] && { [ -n "$issues" ] && issues="$issues, "; issues="${issues}$stale stale"; }
    check_fail "Cursor rules: $issues (of $src_count expected)" "$PLAYBOOK_ROOT/scripts/sync-rules.sh --format cursor"
    cursor_stale=1
  fi
else
  check_warn "No Cursor rules (.cursor/rules/ not found)"
fi

if [ -d "$claude_rules" ]; then
  has_claude=true
  md_count=$(ls -1 "$claude_rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "$md_count" -eq 0 ]; then
    check_fail "Claude rules directory exists but is empty" "$PLAYBOOK_ROOT/scripts/sync-rules.sh --format claude"
    claude_stale=1
  else
    claude_src="$PLAYBOOK_ROOT/claude/rules"
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
        check_fail "Claude rules: $claude_stale of $md_count are stale" "$PLAYBOOK_ROOT/scripts/sync-rules.sh --format claude"
      fi
    else
      check_fail "Claude rules: $md_count files (expected $claude_src_count)" "$PLAYBOOK_ROOT/scripts/sync-rules.sh --format claude"
      claude_stale=1
    fi
  fi
fi

if ! $has_cursor && ! $has_claude; then
  check_fail "No rules found (neither .cursor/rules/ nor .claude/rules/)" "bash $PLAYBOOK_ROOT/scripts/playbook-init.sh --tool cursor|claude|both"
  bootstrap_missing=1
fi

# Warn if rules directories are gitignored (skip for the playbook repo itself,
# where .cursor/* is intentionally gitignored since cursor/rules/ is the source)
is_playbook_repo=false
[[ "$(cd "$PROJECT_ROOT" && pwd)" == "$(cd "$PLAYBOOK_ROOT" && pwd)" ]] && is_playbook_repo=true

if ! $is_playbook_repo; then
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
# playbook-init.sh copies it with cp -f (same semantics as rules), so each
# drift-checks against the kit copy the same way rules do. The tdd-ledger
# CI workflow (.github/workflows/tdd-ledger-verify.yml) is NOT drift-checked
# — init treats it as not-overwriting, so target repos may legitimately
# customize it; we only note its absence when that CLI is present.

clis_manifest="$PLAYBOOK_ROOT/scripts/distributed-clis.list"

if [ ! -f "$clis_manifest" ]; then
  echo "Distributed CLIs:"
  check_warn "Manifest missing at $clis_manifest — cannot drift-check kit CLIs"
  echo ""
else
  while IFS='|' read -r cli_name cli_key cli_header cli_note _label _detail; do
    case "$cli_name" in ""|\#*) continue ;; esac
    echo "$cli_header:"
    cli_src="$PLAYBOOK_ROOT/scripts/$cli_name"
    cli_dest="$PROJECT_ROOT/scripts/$cli_name"
    if [ ! -f "$cli_src" ]; then
      check_warn "Kit copy missing at $cli_src — cannot drift-check $cli_name"
    elif [ ! -f "$cli_dest" ]; then
      # Informational, not a failure: the repo may predate the CLI or not use it.
      echo "  – $cli_name not distributed here (optional — re-run playbook-init.sh to add it)"
    else
      if diff -q "$cli_src" "$cli_dest" > /dev/null 2>&1; then
        check_pass "$cli_name CLI matches the kit copy"
      else
        check_fail "$cli_name CLI is stale vs the kit copy — $cli_note" \
          "cp -f \"$cli_src\" \"$cli_dest\" && chmod +x \"$cli_dest\""
        cli_stale_keys="$cli_stale_keys $cli_key"
      fi
      if [ "$cli_name" = "tdd-ledger" ]; then
        if ! $is_playbook_repo && [ ! -f "$PROJECT_ROOT/.github/workflows/tdd-ledger-verify.yml" ]; then
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
    if [ -f "$PLAYBOOK_ROOT/global-safety-net/agent-protocol.md" ] && \
       ! grep -qF "\`$cli_key\`" "$PLAYBOOK_ROOT/global-safety-net/agent-protocol.md"; then
      check_warn "SUMMARY key $cli_key is not documented in global-safety-net/agent-protocol.md — add a dispatch-table row"
    fi
    echo ""
  done < "$clis_manifest"
fi

# ---------- Conventions profile (data-shaped convention source) ----------
#
# The data file the distributed checkers read; ships verbatim via
# playbook-init and byte-drift-checks here. Ownership and skew rules:
# docs/operations.md. Must run AFTER the CLI loop — the skew warn below
# reads cli_stale_keys.
# defer: hand-written parallel block instead of generalizing the manifest to
# data files. ceiling: re-implements the CLI loop's four states + the
# registration self-check per file. upgrade when: a second data-shaped file
# distributes.
echo "Conventions profile:"
profile_src="$PLAYBOOK_ROOT/profiles/conventions.toml"
profile_dest="$PROJECT_ROOT/profiles/conventions.toml"
profile_present=false
if [ ! -f "$profile_src" ]; then
  check_warn "Kit copy missing at $profile_src — cannot drift-check the profile"
elif [ ! -f "$profile_dest" ]; then
  # Informational, not a failure: the repo may predate the profile or not use it.
  echo "  – profiles/conventions.toml not distributed here (optional — re-run playbook-init.sh to add it)"
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
      check_warn "Conventions profile present but a profile-reading checker is stale — re-copy the stale checker(s) and the profile together (or re-run playbook-init.sh); a stale checker may mis-scan the current profile"
    fi ;;
esac
# Registration self-check: profile_drift is a manifest-external SUMMARY key,
# so nothing generates its documentation sites — the dispatch-table row in
# global-safety-net/agent-protocol.md (guarded here, same as the CLIs) and
# the hand-extended enumerations in this script's header/--help and init's
# rendered AGENTS.md section (not guarded; update by hand with any new key).
if [ -f "$PLAYBOOK_ROOT/global-safety-net/agent-protocol.md" ] && \
   ! grep -qF "\`profile_drift\`" "$PLAYBOOK_ROOT/global-safety-net/agent-protocol.md"; then
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
                  "$PLAYBOOK_ROOT/skills/$ref_name"; do
        [ -e "$cand" ] && resolved=true && break
      done
    else
      for cand in "$PROJECT_ROOT/templates/$ref_name" \
                  "$PLAYBOOK_ROOT/templates/$ref_name"; do
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

# ---------- AGENTS.md playbook section ----------
#
# playbook-init.sh stamps the AGENTS.md playbook section with a
# machine-parseable version marker (<!-- house-rules:version X.Y.Z -->)
# sourced from the kit's VERSION file. A stale stamp means the section's
# doctor/sync instructions and exit-code contract may describe an older kit.
# Sections written before the house-rules rename carry legacy
# "ai-dev-playbook:" markers — recognized here (presence + stamp) and flagged
# for migration; re-running playbook-init.sh rewrites them in place.
#
# Deliberately text-only (warn — no exit 3 / SUMMARY key): the section is
# discovery documentation, not executable machinery like rules or the
# tdd-ledger, so a stale stamp cannot break agent behavior mid-task. Keeping
# it out of the SUMMARY enum also keeps the agent-protocol dispatch table
# stable for existing agents.

echo "AGENTS.md:"

agents_md="$PROJECT_ROOT/AGENTS.md"
agents_marker="<!-- BEGIN house-rules:agents-md -->"
agents_marker_legacy="<!-- BEGIN ai-dev-playbook:agents-md -->"
kit_version=""
[ -f "$PLAYBOOK_ROOT/VERSION" ] && kit_version="$(tr -d '[:space:]' < "$PLAYBOOK_ROOT/VERSION")"

if $is_playbook_repo; then
  echo "  – kit repo itself: AGENTS.md is authored, not generated (stamp check skipped)"
elif [ ! -f "$agents_md" ] || ! grep -qF -e "$agents_marker" -e "$agents_marker_legacy" "$agents_md" 2>/dev/null; then
  # Informational, not a failure: pre-AGENTS.md bootstraps are legitimate.
  echo "  – No playbook section in AGENTS.md (re-run playbook-init.sh to add it)"
elif [ -z "$kit_version" ]; then
  check_warn "Kit VERSION file missing at $PLAYBOOK_ROOT/VERSION — cannot check the AGENTS.md section stamp"
else
  # One pass matches either marker generation; first-in-file wins (a file
  # carrying both stamps is a state the installers never produce).
  target_version="$(sed -nE 's/.*<!-- (house-rules|ai-dev-playbook):version ([^ ]*) -->.*/\2/p' "$agents_md" | head -n1)"
  if grep -qF "$agents_marker_legacy" "$agents_md"; then
    check_warn "AGENTS.md playbook section carries legacy ai-dev-playbook markers (stamped ${target_version:-<no stamp — pre-versioning init>}) — re-run: bash \"$PLAYBOOK_ROOT/scripts/playbook-init.sh\" --tool cursor|claude|both (migrates the section in place)"
  elif [ "$target_version" = "$kit_version" ]; then
    check_pass "AGENTS.md playbook section current (v$kit_version)"
  else
    check_warn "AGENTS.md playbook section is stamped ${target_version:-<no stamp — pre-versioning init>} but the kit is v$kit_version — re-run: bash \"$PLAYBOOK_ROOT/scripts/playbook-init.sh\" --tool cursor|claude|both (refreshes the section in place)"
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
        check_warn "Beads git hooks missing or incomplete (bd recommends pre-commit, post-merge, pre-push)" "bd hooks install"
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
  check_fail "No scratchpad found" "bash $PLAYBOOK_ROOT/scripts/playbook-init.sh --tool cursor|claude|both (creates it automatically)"
fi

echo ""

# ---------- Sync targets ----------

echo "Sync targets:"

TARGETS_FILE="$HOME/.playbook-sync-targets"
has_beads=false
[ -d "$PROJECT_ROOT/.beads" ] || [ -d "$PROJECT_ROOT/.dolt" ] && has_beads=true

if $is_playbook_repo; then
  # The kit is the sync SOURCE — registration as a target is inapplicable.
  echo "  – kit repo itself: sync source, not a target (registration check skipped)"
elif [ -f "$TARGETS_FILE" ]; then
  if grep -qF "$PROJECT_ROOT" "$TARGETS_FILE" 2>/dev/null; then
    check_pass "Project is in ~/.playbook-sync-targets"
  elif $has_beads; then
    check_fail "Beads project not in ~/.playbook-sync-targets — rules will drift silently" \
      "bash \"$PLAYBOOK_ROOT/scripts/playbook-init.sh\" --tool cursor|claude|both"
  else
    check_fail "Project not in ~/.playbook-sync-targets" "echo \"$PROJECT_ROOT\" >> ~/.playbook-sync-targets"
  fi
else
  check_fail "\$HOME/.playbook-sync-targets doesn't exist" "echo \"$PROJECT_ROOT\" >> \$HOME/.playbook-sync-targets"
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

installer="$PLAYBOOK_ROOT/scripts/install-global-safety-net.sh"
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
  echo "Run 'bash $PLAYBOOK_ROOT/scripts/playbook-init.sh' to fix most issues automatically."
  exit 1
else
  if [ $warn -gt 0 ]; then
    echo "All critical checks passed. Warnings are informational."
  else
    echo "Everything looks good!"
  fi
  exit 0
fi
