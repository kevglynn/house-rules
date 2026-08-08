#!/usr/bin/env bash
# Fixture tests for sync-rules.sh stale-rule cleanup (process-kit-2d6).
#
# The cleanup pass exists so a kit rule that gets renamed or retired stops
# haunting target repos. The hazard is that it cannot tell "a kit rule that
# went away" from "a rule this project wrote itself", and the destructive
# path is the one operation safe mode never covered: overwrites get a
# timestamped .bak, deletions got an unconditional rm.
#
# Two real rules were destroyed this way before the guard existed
# (aurion.mdc in aurion, skills-contributing.md in agent-skills; both
# recovered from git only because they happened to be committed).
#
# Harness style follows test_profile_distribution.sh: mktemp target +
# throwaway HOME, so the invoking user's real ~/.house-rules-sync-targets
# is never read or written. Run from anywhere:
#   bash scripts/tests/test_sync_cleanup.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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

# Build a throwaway HOME + target repo seeded with one project-authored
# rule and one retired kit rule, in both formats.
setup_target() {
  local home target
  home="$(mktemp -d)"; CLEANUP+=("$home")
  target="$(mktemp -d)"; CLEANUP+=("$target")

  mkdir -p "$target/.cursor/rules" "$target/.claude/rules"

  # Project-authored: this repo's own rule. The kit has never shipped it
  # and must not delete it.
  printf -- '---\ndescription: this project owns this rule\n---\n\n# Project rule\n' \
    > "$target/.cursor/rules/my-project.mdc"
  printf -- '# Project rule\n' > "$target/.claude/rules/my-project.md"

  # Retired kit rule: ponytail-playbook was renamed to graybeard-playbook
  # in kit history (the only such rename). Cleanup must still remove it.
  printf -- '---\ndescription: legacy kit rule\n---\n\n# Ponytail\n' \
    > "$target/.cursor/rules/ponytail-playbook.mdc"
  printf -- '# Ponytail\n' > "$target/.claude/rules/ponytail-playbook.md"

  printf '%s\n' "$target" > "$home/.house-rules-sync-targets"
  printf '%s %s' "$home" "$target"
}

read -r HOME_DIR TARGET <<< "$(setup_target)"

OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all 2>&1)"

echo "--- project-authored rules must survive ---"
check "project .mdc survives the sync" \
  test -f "$TARGET/.cursor/rules/my-project.mdc"
check "project .md survives the sync" \
  test -f "$TARGET/.claude/rules/my-project.md"
# Assert the specific kept-wording, not just the filename: the pre-fix
# output also contained "my-project.mdc", inside "Removed stale:". A bare
# filename check would pass whether or not the file survived.
check "operator is warned the .mdc is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.mdc"
check "operator is warned the .md is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.md"
check "project .mdc is never reported as stale" \
  out_lacks "$OUT" "Removed stale: my-project.mdc"
check "project .md is never reported as stale" \
  out_lacks "$OUT" "Removed stale: my-project.md"

echo "--- retired kit rules must still be removed ---"
check "retired .mdc is removed" \
  test ! -f "$TARGET/.cursor/rules/ponytail-playbook.mdc"
check "retired .md is removed" \
  test ! -f "$TARGET/.claude/rules/ponytail-playbook.md"

echo "--- deletion is recoverable, matching the overwrite path ---"
check "removed .mdc left a backup" \
  bash -c 'compgen -G "$1/.cursor/rules/ponytail-playbook.mdc.*.bak" > /dev/null' _ "$TARGET"
check "removed .md left a backup" \
  bash -c 'compgen -G "$1/.claude/rules/ponytail-playbook.md.*.bak" > /dev/null' _ "$TARGET"

echo "--- the sync still did its real job ---"
check "kit rules were delivered (cursor)" \
  test -f "$TARGET/.cursor/rules/operating-model.mdc"
check "kit rules were delivered (claude)" \
  test -f "$TARGET/.claude/rules/operating-model.md"

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
