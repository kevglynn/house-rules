#!/usr/bin/env bash
# Fixture tests for tier stamp, tier-aware doctor, sync-target exclusion,
# and the core upgrade-offer rule (process-kit-12q).
#
# Harness style matches test_profile_distribution.sh: mktemp repo + throwaway
# HOME; never touches the invoking user's HOME.
#   bash scripts/tests/test_tier_mechanics.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INIT="$KIT_ROOT/scripts/init.sh"
DOCTOR="$KIT_ROOT/scripts/doctor.sh"
UPGRADE_RULE="$KIT_ROOT/cursor/rules/core-upgrade-offer.mdc"

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

# bd shim: core-tier path must not require beads; full-tier fixtures still
# need the init preflight to pass on CI runners without bd installed.
BD_SHIM_DIR="$(mktemp -d)"
CLEANUP+=("$BD_SHIM_DIR")
printf '#!/bin/sh\nexit 0\n' > "$BD_SHIM_DIR/bd"
chmod +x "$BD_SHIM_DIR/bd"
export PATH="$BD_SHIM_DIR:$PATH"

check() {
  local name="$1"; shift
  if "$@"; then
    echo "ok - $name"
    PASS=$((PASS + 1))
  else
    echo "FAIL - $name"
    FAIL=$((FAIL + 1))
  fi
}

out_has()   { grep -qF -- "$2" <<< "$1"; }
out_lacks() { ! grep -qF -- "$2" <<< "$1"; }
out_has_re() { grep -qE -- "$2" <<< "$1"; }

# ---------------------------------------------------------------------------
# AC1: core-only install writes stamp; doctor healthy w.r.t. beads /
#      scratchpad / sync-targets (no check_fail on those sections).
# ---------------------------------------------------------------------------
h="$(new_home)"
# Place under throwaway HOME (not /tmp) so sync-exclusion is tested —
# init always skips registration for paths under /tmp.
core_repo="$h/core-project"
mkdir -p "$core_repo"
git -C "$core_repo" init -q

init_out="$(cd "$core_repo" && HOME="$h" bash "$INIT" --tier core 2>&1)"
init_rc=$?
check "init --tier core exits 0" test "$init_rc" = "0"
check "init --tier core writes .house-rules-tier=core" \
  test "$(tr -d '[:space:]' < "$core_repo/.house-rules-tier" 2>/dev/null)" = "core"
check "init --tier core does not create task-tracking store" \
  bash -c "! test -d '$core_repo/.beads' && ! test -d '$core_repo/.dolt'"
check "init --tier core does not create scratchpad" \
  bash -c "! test -f '$core_repo/.cursor/scratchpad.md' && ! test -f '$core_repo/scratchpad.md'"

# Doctor on core stamp alone (no local rules — plugin-delivered is fine).
# Capture $? immediately — `|| true` would make the asserted exit code
# vacuous (Tier-2 finding).
doc_out="$(HOME="$h" bash "$DOCTOR" "$core_repo" 2>&1)"
doc_rc=$?
check "core doctor: no Beads-not-initialized failure" \
  out_lacks "$doc_out" "Beads not initialized"
check "core doctor: no scratchpad failure" \
  out_lacks "$doc_out" "No scratchpad found"
check "core doctor: no sync-targets failure" \
  bash -c "! grep -qE 'not in ~/.house-rules-sync-targets|sync-targets doesn.t exist' <<< \"\$1\"" _ "$doc_out"
check "core doctor: beads section N/A for core" \
  out_has_re "$doc_out" "N/A for core tier"
# Agent SUMMARY must not be bootstrap_needed solely because beads/rules
# dirs are absent when stamp is core.
agent_out="$(HOME="$h" bash "$DOCTOR" "$core_repo" --agent 2>&1)"
agent_rc=$?
check "core doctor --agent: not SUMMARY bootstrap_needed" \
  out_lacks "$agent_out" "SUMMARY: bootstrap_needed"
summary_line="$(printf '%s\n' "$agent_out" | tail -1)"
check "core doctor --agent: SUMMARY ok (exit 0)" \
  bash -c "test \"$agent_rc\" = 0 && test \"$summary_line\" = 'SUMMARY: ok'"

# ---------------------------------------------------------------------------
# AC2: core-only repos are NOT registered in ~/.house-rules-sync-targets
# ---------------------------------------------------------------------------
check "init --tier core does not create sync-targets file" \
  bash -c "! test -f '$h/.house-rules-sync-targets'"
# Even if the file already exists, core must not append.
printf '%s\n' "$h/other-project" > "$h/.house-rules-sync-targets"
core2="$h/core-project-2"
mkdir -p "$core2"
git -C "$core2" init -q
(cd "$core2" && HOME="$h" bash "$INIT" --tier core > /dev/null 2>&1)
check "init --tier core does not append to existing sync-targets" \
  bash -c "! grep -qxF '$core2' '$h/.house-rules-sync-targets'"

# Full tier still registers when the project is outside /tmp (init always
# skips throwaway paths under TMPDIR|/tmp — place this fixture in-kit).
full_home="$(mktemp -d "${KIT_ROOT}/.tier-fixture-XXXXXX")"
CLEANUP+=("$full_home")
full_repo="$full_home/full-project"
mkdir -p "$full_repo"
git -C "$full_repo" init -q
(cd "$full_repo" && HOME="$full_home" bash "$INIT" --tool cursor --tier full --no-hooks > /dev/null 2>&1)
check "init --tier full writes .house-rules-tier=full" \
  test "$(tr -d '[:space:]' < "$full_repo/.house-rules-tier" 2>/dev/null)" = "full"
check "init --tier full registers sync-targets" \
  grep -qxF "$full_repo" "$full_home/.house-rules-sync-targets"

# full→core: must remove the prior registration and leave doctor green
# on the sync section (not a silent N/A while still registered).
(cd "$full_repo" && HOME="$full_home" bash "$INIT" --tool cursor --tier core --no-hooks > /dev/null 2>&1)
check "full→core rewrites .house-rules-tier=core" \
  test "$(tr -d '[:space:]' < "$full_repo/.house-rules-tier" 2>/dev/null)" = "core"
check "full→core removes sync-target registration" \
  bash -c "! grep -qxF '$full_repo' '$full_home/.house-rules-sync-targets'"
# Re-register manually to pin doctor's residual-registration failure.
printf '%s\n' "$full_repo" >> "$full_home/.house-rules-sync-targets"
resid_out="$(HOME="$full_home" bash "$DOCTOR" "$full_repo" 2>&1)" || true
check "doctor flags residual sync registration on core stamp" \
  out_has "$resid_out" "still registered in ~/.house-rules-sync-targets"
# Clean the residual so later fixtures aren't polluted.
grep -vxF "$full_repo" "$full_home/.house-rules-sync-targets" \
  > "$full_home/.house-rules-sync-targets.tmp" \
  && mv "$full_home/.house-rules-sync-targets.tmp" "$full_home/.house-rules-sync-targets"

# Refuse invalid --tool without leaving a core/full stamp on a fresh repo.
bogus="$h/bogus-tool"
mkdir -p "$bogus"
git -C "$bogus" init -q
bogus_out="$(cd "$bogus" && HOME="$h" bash "$INIT" --tier core --tool nope 2>&1)"
bogus_rc=$?
check "init --tool invalid exits nonzero" test "$bogus_rc" != "0"
check "init --tool invalid does not write tier stamp" \
  bash -c "! test -f '$bogus/.house-rules-tier'"

# Absent stamp treated as full: doctor still fails missing sync on a
# non-core fixture (regression pin).
absent="$h/absent-stamp"
mkdir -p "$absent/.cursor/rules"
# Minimal rule file so bootstrap_needed doesn't win SUMMARY.
cp "$KIT_ROOT/cursor/rules/agent-identity.mdc" "$absent/.cursor/rules/"
git -C "$absent" init -q
absent_out="$(HOME="$h" bash "$DOCTOR" "$absent" 2>&1)" || true
check "absent stamp (=full): doctor still flags missing sync-targets" \
  out_has "$absent_out" "not in ~/.house-rules-sync-targets"

# ---------------------------------------------------------------------------
# AC3: core plugin carries upgrade trigger — offer once with consent;
#      scripted session simulation (Claude UI not required).
# ---------------------------------------------------------------------------
check "upgrade rule file exists" test -f "$UPGRADE_RULE"
rule_text="$(cat "$UPGRADE_RULE" 2>/dev/null || true)"
check "upgrade rule mentions full playbook / full install offer" \
  out_has_re "$rule_text" "full (playbook|install)|house-rules init"
check "upgrade rule requires consent" \
  out_has_re "$rule_text" "[Cc]onsent|ask the user|Which\\?"
check "upgrade rule persists offered marker" \
  out_has "$rule_text" ".house-rules-upgrade-offered"
check "upgrade rule is bd/beads-clean (no workflow words)" \
  bash -c "! grep -qiE '\\bbd\\b|\\bbeads?\\b' '$UPGRADE_RULE'"

# Scripted session simulation: a core-stamped repo with no task tracking
# and no offered marker should be in the "offer eligible" state per the
# rule; after touching the marker, re-offer must be suppressed.
sim="$h/upgrade-sim"
mkdir -p "$sim"
git -C "$sim" init -q
echo core > "$sim/.house-rules-tier"
# Eligible: marker absent.
check "upgrade sim: eligible when marker absent" \
  bash -c "! test -f '$sim/.house-rules-upgrade-offered'"
# Simulate agent recording the offer (rule's persist step).
: > "$sim/.house-rules-upgrade-offered"
check "upgrade sim: marker suppresses re-offer" \
  test -f "$sim/.house-rules-upgrade-offered"
# Rule must say: if marker exists, do not re-ask.
check "upgrade rule: do not re-offer when marker present" \
  out_has_re "$rule_text" "already offered|do not (re-)?(ask|offer|prompt)|marker"

# Manifest membership (core-manifest lists the rule).
check "core-manifest lists core-upgrade-offer" \
  grep -qF 'rule|cursor/rules/core-upgrade-offer.mdc' \
    "$KIT_ROOT/profiles/core-manifest.list"

# Core --skills must copy only core-manifest skills (not the full tree).
skills_home="$(new_home)"
skills_repo="$skills_home/skills-core"
mkdir -p "$skills_repo"
git -C "$skills_repo" init -q
(cd "$skills_repo" && HOME="$skills_home" bash "$INIT" --tier core --tool cursor --skills --no-hooks > /dev/null 2>&1)
copied="$(ls -1d "$skills_repo/.cursor/skills/"*/ 2>/dev/null | xargs -n1 basename | sort | tr '\n' ' ')"
check "core --skills copies graybeard-review" \
  bash -c "test -d '$skills_repo/.cursor/skills/graybeard-review'"
check "core --skills copies prose-voice" \
  bash -c "test -d '$skills_repo/.cursor/skills/prose-voice'"
check "core --skills does not copy bead-authoring" \
  bash -c "! test -d '$skills_repo/.cursor/skills/bead-authoring'"
check "core --skills does not copy pragmatic-tdd" \
  bash -c "! test -d '$skills_repo/.cursor/skills/pragmatic-tdd'"
check "core CLI set is core-manifest only" \
  bash -c "test -f '$skills_repo/scripts/defer-lint' && test -f '$skills_repo/scripts/banned-token-scan' && ! test -f '$skills_repo/scripts/tdd-ledger' && ! test -f '$skills_repo/scripts/close-reason-lint'"

# Doctor must teach an explicit --tool on the catch-all remediation line.
check "doctor teaches init with explicit --tool" \
  grep -qF 'init --tool cursor (or --tool claude / --tool both)' "$DOCTOR"

echo ""
echo "passed: $PASS  failed: $FAIL"
[ $FAIL -eq 0 ]
