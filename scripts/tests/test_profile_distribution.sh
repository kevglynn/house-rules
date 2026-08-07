#!/usr/bin/env bash
# Fixture tests for conventions-profile distribution and the profile_drift
# SUMMARY contract (process-kit-b3m). Guards the two regression classes the
# vr2 manual e2e could not durably pin:
#   (a) init's profile copy or the doctor's drift check silently breaking so
#       the doctor takes the "not distributed here (optional)" branch over a
#       genuinely drifted profile — the one mode where the doctor lies healthy;
#   (b) the SUMMARY elif chain reordering so profile_drift loses precedence
#       or emits a different key string than agents dispatch on.
# Harness style follows test_marker_migration.sh: mktemp repo + throwaway
# HOME; never touches the invoking user's HOME. Run from anywhere:
#   bash scripts/tests/test_profile_distribution.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INIT="$KIT_ROOT/scripts/playbook-init.sh"
DOCTOR="$KIT_ROOT/scripts/playbook-doctor.sh"

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

# bd shim: this suite exercises profile-distribution and doctor-SUMMARY
# logic, not beads. playbook-init's preflight hard-fails when bd is absent
# (CI runners don't have it), so a no-op stub keeps the preflight green and
# makes local and CI runs behaviorally identical (process-kit-4ma).
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

out_has()   { grep -qF -- "$2" <<< "$1"; }
out_lacks() { ! grep -qF -- "$2" <<< "$1"; }

# --- Shared fixture: one bootstrapped repo, mutated per scenario ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks > /dev/null 2>&1)

# --- 1. init distributes the profile byte-identical to the kit copy ---
check "init distributes profiles/conventions.toml" \
  test -f "$repo/profiles/conventions.toml"
check "distributed profile is byte-identical to the kit copy" \
  cmp -s "$KIT_ROOT/profiles/conventions.toml" "$repo/profiles/conventions.toml"

# --- 2. Mutated target profile: SUMMARY is exactly profile_drift, exit 3.
#        Rules are current (init just copied them), so nothing above
#        profile_drift in the precedence chain can mask it; unrelated
#        fixture failures (no beads, no scratchpad) rank below it. ---
echo "# fixture drift" >> "$repo/profiles/conventions.toml"
agent_out="$(HOME="$h" bash "$DOCTOR" "$repo" --agent 2>&1)"; rc=$?
check "mutated profile: doctor --agent exits 3" test "$rc" = "3"
check "mutated profile: SUMMARY line is exactly 'SUMMARY: profile_drift'" \
  test "$(printf '%s\n' "$agent_out" | tail -1)" = "SUMMARY: profile_drift"
human_out="$(HOME="$h" bash "$DOCTOR" "$repo" 2>&1)" || true
check "mutated profile: human mode names the stale profile" \
  out_has "$human_out" "profiles/conventions.toml is stale vs the kit copy"

# --- 3. Profile AND a distributed CLI both stale: profile_drift still wins
#        (precedence pin — agents dispatch on the specific key) ---
echo "# fixture stale" >> "$repo/scripts/defer-lint"
agent_out="$(HOME="$h" bash "$DOCTOR" "$repo" --agent 2>&1)"; rc=$?
check "profile + CLI both stale: exit 3" test "$rc" = "3"
check "profile + CLI both stale: profile_drift wins precedence" \
  test "$(printf '%s\n' "$agent_out" | tail -1)" = "SUMMARY: profile_drift"

# --- 4. Absent target profile: the doctor takes the optional branch and
#        emits no drift signal (guards the lies-healthy branch against
#        inversion: absence must read as "optional", never as drift; a bare
#        fixture repo has unrelated failures, so exit 0 is out of reach —
#        the pinned property is the branch plus the absent key). ---
cp -f "$KIT_ROOT/scripts/defer-lint" "$repo/scripts/defer-lint"
rm -f "$repo/profiles/conventions.toml"
human_out="$(HOME="$h" bash "$DOCTOR" "$repo" 2>&1)" || true
check "absent profile: optional/not-distributed branch taken" \
  out_has "$human_out" "not distributed here (optional"
agent_out="$(HOME="$h" bash "$DOCTOR" "$repo" --agent 2>&1)" || true
check "absent profile: no profile_drift SUMMARY emitted" \
  out_lacks "$agent_out" "SUMMARY: profile_drift"
check "absent profile: no stale-profile failure reported" \
  out_lacks "$agent_out" "profiles/conventions.toml is stale"

echo ""
echo "passed: $PASS  failed: $FAIL"
[ $FAIL -eq 0 ]
