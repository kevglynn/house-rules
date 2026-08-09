#!/usr/bin/env bash
# Fixture tests for init's overwrite safety (process-kit-jjj).
#
# process-kit-2d6 established that the kit must not destroy project-authored
# content without leaving a recoverable copy. That fix covered sync only.
# init writes to the same directories through a second door, and it is the
# command a user is most likely to re-run casually — so the same guarantee
# has to hold here, with the same convention, from one implementation.
#
# Harness style matches test_tier_mechanics.sh: mktemp repo + throwaway HOME;
# never touches the invoking user's HOME.
#   bash scripts/tests/test_init_backup.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INIT="$KIT_ROOT/scripts/init.sh"
SYNC="$KIT_ROOT/scripts/sync-rules.sh"

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

# bd shim: full-tier init runs a preflight that wants bd on PATH, and CI
# runners do not have it.
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

# A fresh repo with a completed install, ready to be re-initialized.
# Echoes "<home> <repo>".
seed_installed() {
  local h repo
  h="$(mktemp -d)"; CLEANUP+=("$h")
  repo="$h/project"
  mkdir -p "$repo"
  git -C "$repo" init -q
  ( cd "$repo" && HOME="$h" bash "$INIT" --tool cursor >/dev/null 2>&1 )
  printf '%s %s' "$h" "$repo"
}

reinit() { # reinit <home> <repo> [extra init args...]
  local h="$1" repo="$2"; shift 2
  ( cd "$repo" && HOME="$h" bash "$INIT" --tool cursor "$@" 2>&1 )
}

baks_in() { find "$1" -name '*.bak' 2>/dev/null; }
no_baks_in() { [ -z "$(baks_in "$1")" ]; }
some_baks_in() { [ -n "$(baks_in "$1")" ]; }

RULE_REL=".cursor/rules/operating-model.mdc"
EDIT_MARK="# LOCAL EDIT A PROJECT MADE"

# ---------------------------------------------------------------------------
# AC1: a locally-edited kit file survives a re-init as a timestamped .bak
# ---------------------------------------------------------------------------

echo "--- AC1: re-init preserves prior content as a .bak ---"
read -r H REPO <<< "$(seed_installed)"
RULE="$REPO/$RULE_REL"

check "precondition: the install delivered the rule" test -f "$RULE"

printf '%s\n' "$EDIT_MARK" >> "$RULE"
cp "$RULE" "$H/expected-prior-bytes"

OUT="$(reinit "$H" "$REPO")"

check "re-init writes a .bak beside the overwritten rule" \
  some_baks_in "$REPO/.cursor/rules"

BAK="$(baks_in "$REPO/.cursor/rules" | head -1)"
check "the .bak holds the pre-init bytes, not the kit's" \
  cmp -s "$H/expected-prior-bytes" "$BAK"

check "the rule itself is restored to the kit's bytes" \
  cmp -s "$KIT_ROOT/cursor/rules/operating-model.mdc" "$RULE"

check "the run says it backed the file up" \
  out_has "$OUT" "backed up operating-model.mdc"

# ---------------------------------------------------------------------------
# AC2: the convention is sync's convention, from one implementation
# ---------------------------------------------------------------------------

echo "--- AC2: backup convention matches sync ---"

# Name shape: <original>.<14-digit timestamp>[-n].bak — the same string sync
# produces, so an operator cleaning up .bak files has one pattern to learn.
check "the .bak name carries a 14-digit timestamp" \
  bash -c 'basename "$1" | grep -qE "^operating-model\.mdc\.[0-9]{14}(-[0-9]+)?\.bak$"' _ "$BAK"

# Same operator line, character for character, as the sync path prints.
read -r H2 REPO2 <<< "$(seed_installed)"
printf '%s\n' "$EDIT_MARK" >> "$REPO2/$RULE_REL"
# Registered by hand: init deliberately skips sync-target registration for
# paths under /tmp, which is where mktemp puts the fixture, so sync would
# otherwise find no targets and print nothing to compare against.
printf '%s\n' "$REPO2" > "$H2/.house-rules-sync-targets"
SYNC_OUT="$(cd "$REPO2" && HOME="$H2" bash "$SYNC" --format cursor 2>&1)"
check "sync prints the same backup line shape init does" \
  bash -c '
    i="$(grep -o "↳ backed up .* → .*\.bak" <<< "$1" | head -1 | sed -E "s/[0-9]{14}(-[0-9]+)?/TS/")"
    s="$(grep -o "↳ backed up .* → .*\.bak" <<< "$2" | head -1 | sed -E "s/[0-9]{14}(-[0-9]+)?/TS/")"
    [ -n "$i" ] && [ "$i" = "$s" ]' _ "$OUT" "$SYNC_OUT"

# One implementation, not a third copy. The bead is explicit that the
# convention must have a single owner; two scripts that merely agree today
# drift the first time one is edited.
LIB="$KIT_ROOT/scripts/lib/backup-file.sh"
check "the backup primitive lives in a shared lib" test -f "$LIB"
check "the lib defines backup_file" \
  grep -q '^backup_file()' "$LIB"
check "init sources the shared lib" \
  grep -q 'lib/backup-file.sh' "$INIT"
check "sync sources the shared lib" \
  grep -q 'lib/backup-file.sh' "$SYNC"
check "init does not define its own backup_file" \
  bash -c '! grep -q "^backup_file()" "$1"' _ "$INIT"
check "sync does not define its own backup_file" \
  bash -c '! grep -q "^backup_file()" "$1"' _ "$SYNC"

# ---------------------------------------------------------------------------
# AC3: --unsafe waives backups, the same waiver sync offers
# ---------------------------------------------------------------------------

echo "--- AC3: --unsafe waives backups ---"
read -r H3 REPO3 <<< "$(seed_installed)"
printf '%s\n' "$EDIT_MARK" >> "$REPO3/$RULE_REL"
reinit "$H3" "$REPO3" --unsafe >/dev/null; RC3=$?

# Captured at the call, not read from $? after an intervening check — which
# would report the check's own status and pass no matter what init did.
check "--unsafe is an accepted flag, not a usage error" test "$RC3" -eq 0
check "--unsafe writes no .bak" no_baks_in "$REPO3/.cursor/rules"
check "--unsafe still installs the rule" \
  cmp -s "$KIT_ROOT/cursor/rules/operating-model.mdc" "$REPO3/$RULE_REL"

# ---------------------------------------------------------------------------
# No gratuitous backups: the guarantee is about content, not about writes
# ---------------------------------------------------------------------------

echo "--- unchanged and first-time files are not backed up ---"
read -r H4 REPO4 <<< "$(seed_installed)"
# Nothing edited: every delivered file already matches the kit's bytes.
reinit "$H4" "$REPO4" >/dev/null
check "re-init over an untouched install writes no .bak" \
  no_baks_in "$REPO4/.cursor/rules"

h5="$(mktemp -d)"; CLEANUP+=("$h5")
repo5="$h5/fresh"; mkdir -p "$repo5"; git -C "$repo5" init -q
( cd "$repo5" && HOME="$h5" bash "$INIT" --tool cursor >/dev/null 2>&1 )
check "a first install writes no .bak" no_baks_in "$repo5/.cursor/rules"

# ---------------------------------------------------------------------------
# The other destructive doors: the guarantee must not be rules-only
# ---------------------------------------------------------------------------

echo "--- the same guarantee covers every file init overwrites ---"
read -r H6 REPO6 <<< "$(seed_installed)"

printf '\n%s\n' "# local tweak" >> "$REPO6/profiles/conventions.toml"
cp "$REPO6/profiles/conventions.toml" "$H6/expected-profile"
printf '\n%s\n' "# local tweak" >> "$REPO6/scripts/defer-lint"
cp "$REPO6/scripts/defer-lint" "$H6/expected-cli"

reinit "$H6" "$REPO6" >/dev/null

check "an edited conventions.toml is backed up" \
  some_baks_in "$REPO6/profiles"
check "the profile .bak holds the edited bytes" \
  bash -c 'cmp -s "$1" "$(find "$2" -name "conventions.toml.*.bak" | head -1)"' \
  _ "$H6/expected-profile" "$REPO6/profiles"
check "an edited distributed CLI is backed up" \
  bash -c '[ -n "$(find "$1" -name "defer-lint.*.bak" 2>/dev/null)" ]' _ "$REPO6/scripts"
check "the CLI .bak holds the edited bytes" \
  bash -c 'cmp -s "$1" "$(find "$2" -name "defer-lint.*.bak" | head -1)"' \
  _ "$H6/expected-cli" "$REPO6/scripts"

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
