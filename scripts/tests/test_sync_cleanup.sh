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
file_has()  { grep -qF -- "$2" "$1"; }

# The exact bytes seeded below, so "survived" can mean "is byte-identical"
# rather than "a file with this name exists" — a truncating bug leaves the
# name in place and would pass a bare -f check.
PROJ_MDC=$'---\ndescription: this project owns this rule\n---\n\n# Project rule\n'
PROJ_MD=$'# Project rule\n'
RETIRED_MDC=$'---\ndescription: legacy kit rule\n---\n\n# Ponytail\n'
RETIRED_MD=$'# Ponytail\n'

# Build a throwaway HOME + target repo seeded with one project-authored
# rule and one retired kit rule, in both formats. Sets HOME_DIR and TARGET
# directly: calling this in a command substitution would run the CLEANUP+=
# appends in a subshell, so the trap would never see the temp dirs and
# every run would leak two directories into /tmp.
setup_target() {
  HOME_DIR="$(mktemp -d)"; CLEANUP+=("$HOME_DIR")
  TARGET="$(mktemp -d)"; CLEANUP+=("$TARGET")

  mkdir -p "$TARGET/.cursor/rules" "$TARGET/.claude/rules"

  # Project-authored: this repo's own rule. The kit has never shipped it
  # and must not delete it.
  printf '%s' "$PROJ_MDC" > "$TARGET/.cursor/rules/my-project.mdc"
  printf '%s' "$PROJ_MD"  > "$TARGET/.claude/rules/my-project.md"

  # Retired kit rule: ponytail-playbook was renamed to graybeard-playbook
  # in kit history (the only such rename). Cleanup must still remove it.
  printf '%s' "$RETIRED_MDC" > "$TARGET/.cursor/rules/ponytail-playbook.mdc"
  printf '%s' "$RETIRED_MD"  > "$TARGET/.claude/rules/ponytail-playbook.md"

  printf '%s\n' "$TARGET" > "$HOME_DIR/.house-rules-sync-targets"
}

# cmp, not $(cat) — command substitution strips trailing newlines, so a
# string compare would call a file that lost its final newline identical.
content_is() { # content_is <path> <expected>
  [ -f "$1" ] && printf '%s' "$2" | cmp -s - "$1"
}

# A backup is only a backup if it holds the removed bytes and follows the
# convention the overwrite path uses (<name>.<14-digit stamp>.bak).
backup_matches() { # backup_matches <original-path> <expected-content>
  local orig="$1" expected="$2" bak found=0
  for bak in "$orig".*.bak; do
    [ -f "$bak" ] || continue
    [[ "$bak" =~ \.[0-9]{14}(-[0-9]+)?\.bak$ ]] || continue
    printf '%s' "$expected" | cmp -s - "$bak" || continue
    found=1
  done
  [ "$found" -eq 1 ]
}

# --- Scenario 1: default safe-mode sync against a target repo ---

setup_target
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all 2>&1)"; RC=$?

echo "--- project-authored rules must survive ---"
check "project .mdc survives the sync intact" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
check "project .md survives the sync intact" \
  content_is "$TARGET/.claude/rules/my-project.md" "$PROJ_MD"
# Assert the specific kept-wording, not just the filename: the pre-fix
# output also contained "my-project.mdc", inside "Removed stale:". A bare
# filename check would pass whether or not the file survived.
check "operator is warned the .mdc is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.mdc"
check "operator is warned the .md is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.md"
# Names the live removal message. "Removed stale:" was the pre-fix wording
# and no longer appears anywhere, so asserting its absence proved nothing.
check "project .mdc is never reported as removed" \
  out_lacks "$OUT" "Removed retired: my-project.mdc"
check "project .md is never reported as removed" \
  out_lacks "$OUT" "Removed retired: my-project.md"
check "unmanaged files are summarized for the operator" \
  out_has "$OUT" "2 unmanaged rule file(s) left in place"

echo "--- retired kit rules must still be removed ---"
check "retired .mdc is removed" \
  test ! -f "$TARGET/.cursor/rules/ponytail-playbook.mdc"
check "retired .md is removed" \
  test ! -f "$TARGET/.claude/rules/ponytail-playbook.md"

echo "--- deletion is recoverable, matching the overwrite path ---"
check "removed .mdc backup holds the removed bytes, stamped" \
  backup_matches "$TARGET/.cursor/rules/ponytail-playbook.mdc" "$RETIRED_MDC"
check "removed .md backup holds the removed bytes, stamped" \
  backup_matches "$TARGET/.claude/rules/ponytail-playbook.md" "$RETIRED_MD"

echo "--- the sync still did its real job ---"
check "kit rules were delivered (cursor)" \
  test -f "$TARGET/.cursor/rules/operating-model.mdc"
check "kit rules were delivered (claude)" \
  test -f "$TARGET/.claude/rules/operating-model.md"
check "a clean sync exits 0" \
  test "$RC" -eq 0

# --- Scenario 2: --dry-run must preview the destructive half ---
#
# docs/operations.md sells --dry-run as the safety valve for exactly this.
# Previewing only the writes tells an operator nothing will be removed.

setup_target
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all --dry-run 2>&1)"

echo "--- dry-run previews cleanup, changes nothing ---"
check "dry-run announces the pending retirement" \
  out_has "$OUT" "Would remove retired: ponytail-playbook.mdc"
check "dry-run warns about the unmanaged file" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.mdc"
check "dry-run leaves the retired file on disk" \
  content_is "$TARGET/.cursor/rules/ponytail-playbook.mdc" "$RETIRED_MDC"
check "dry-run leaves the project file on disk" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
check "dry-run writes no backups" \
  bash -c '! compgen -G "$1/.cursor/rules/*.bak" > /dev/null' _ "$TARGET"

# --- Scenario 3: --unsafe still protects project rules ---
#
# --unsafe waives backups, not ownership. The keep-vs-delete decision is
# independent of safe mode, and this is the mode where a wrong deletion is
# unrecoverable.

setup_target
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all --unsafe 2>&1)"

echo "--- --unsafe waives backups, not project ownership ---"
check "unsafe mode still keeps the project rule" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
check "unsafe mode still removes the retired rule" \
  test ! -f "$TARGET/.cursor/rules/ponytail-playbook.mdc"
check "unsafe mode writes no backup for the deletion" \
  bash -c '! compgen -G "$1/.cursor/rules/ponytail-playbook.mdc.*.bak" > /dev/null' _ "$TARGET"

# --- Scenario 4: --version downgrade still removes newer kit rules ---
#
# A pinned sync delivers the tag's rule set. Rules added after the tag are
# kit artifacts, not project content, so keeping them would leave the pin
# describing a rule set the target does not have.

PIN_TAG="$(git -C "$KIT_ROOT" tag --list 'v0.2.0' 2>/dev/null || true)"
echo "--- --version downgrade removes post-tag kit rules ---"
if [ -z "$PIN_TAG" ]; then
  echo "skip - tag v0.2.0 not present in this clone"
else
  NEWER_RULE=""
  for f in "$KIT_ROOT/cursor/rules"/*.mdc; do
    b="$(basename "$f")"
    if ! git -C "$KIT_ROOT" cat-file -e "$PIN_TAG:cursor/rules/$b" 2>/dev/null; then
      NEWER_RULE="$b"; break
    fi
  done
  if [ -z "$NEWER_RULE" ]; then
    echo "skip - no rule postdates $PIN_TAG"
  else
    setup_target
    cp "$KIT_ROOT/cursor/rules/$NEWER_RULE" "$TARGET/.cursor/rules/$NEWER_RULE"
    OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --version "$PIN_TAG" 2>&1)"
    check "post-tag kit rule is removed on downgrade ($NEWER_RULE)" \
      test ! -f "$TARGET/.cursor/rules/$NEWER_RULE"
    check "downgrade still keeps the project rule" \
      content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
  fi
fi

# --- Scenario 5: --local prunes the kit's own generated projection ---
#
# claude/rules/ is 100% machine-generated. An orphan there is a build
# artifact, not someone's rule: left in place it stays loaded in the kit
# and ships to every new adopter through init's wholesale copy.

echo "--- --local prunes orphans in the generated projection ---"
FAKE_KIT="$(mktemp -d)"; CLEANUP+=("$FAKE_KIT")
mkdir -p "$FAKE_KIT/scripts" "$FAKE_KIT/profiles" "$FAKE_KIT/claude/rules"
cp -r "$KIT_ROOT/cursor" "$FAKE_KIT/cursor"
cp "$KIT_ROOT/scripts/sync-rules.sh" "$FAKE_KIT/scripts/"
cp "$KIT_ROOT/profiles/retired-rules.list" "$FAKE_KIT/profiles/"
printf '# orphaned build artifact\n' > "$FAKE_KIT/claude/rules/some-renamed-rule.md"

OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --local 2>&1)"
check "orphaned projection is pruned by --local" \
  test ! -f "$FAKE_KIT/claude/rules/some-renamed-rule.md"
check "--local still generates the real projection" \
  test -f "$FAKE_KIT/claude/rules/operating-model.md"

# The CI gate runs --check --local; it must fail on a committed orphan,
# not just fix it on the next regeneration.
printf '# orphaned build artifact\n' > "$FAKE_KIT/claude/rules/some-renamed-rule.md"
OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --check --local 2>&1)"; RC=$?
check "--check --local reports the orphan" \
  out_has "$OUT" "some-renamed-rule.md — orphaned projection"
check "--check --local exits non-zero on an orphan" \
  test "$RC" -ne 0

# --- Scenario 6: an unbackupable deletion must not report success ---
#
# The file-level outcome is already safe (keep it rather than delete it
# unbacked). The hazard is the exit code: automation running
# `sync-rules.sh && deploy` cannot tell that a retirement silently did not
# happen if the run still exits 0.

echo "--- a failed deletion backup surfaces as an error ---"
if [ "$(id -u)" -eq 0 ]; then
  echo "skip - running as root, chmod cannot make the file unreadable"
else
  setup_target
  chmod 000 "$TARGET/.cursor/rules/ponytail-playbook.mdc"
  OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor 2>&1)"; RC=$?
  chmod 644 "$TARGET/.cursor/rules/ponytail-playbook.mdc"
  check "unbackupable retired rule is left on disk" \
    test -f "$TARGET/.cursor/rules/ponytail-playbook.mdc"
  check "operator is told the backup failed" \
    out_has "$OUT" "Failed to back up ponytail-playbook.mdc before removal"
  check "the run does not claim the retirement succeeded" \
    out_lacks "$OUT" "Removed retired: ponytail-playbook.mdc"
  check "the run exits non-zero so automation can see it" \
    test "$RC" -ne 0
fi

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
