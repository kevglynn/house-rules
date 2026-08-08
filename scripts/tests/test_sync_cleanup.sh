#!/usr/bin/env bash
# Fixture tests for sync-rules.sh file ownership and cleanup (process-kit-2d6).
#
# The question this pass has to answer is "does the kit own this file?", and
# it has now been answered wrong twice. First it deleted anything it did not
# recognize, which destroyed project-authored rules (aurion.mdc in aurion,
# skills-contributing.md in agent-skills; recovered from git only because
# they happened to be committed). Then it deleted anything whose *name* the
# kit had ever used, which still deleted a project's own
# ponytail-playbook.mdc on a routine sync — a filename is not provenance.
#
# The contract these tests pin:
#   - ownership requires the bytes to match a version the kit shipped
#   - a default sync never deletes; --retire is the deliberate opt-in
#   - every destructive operation leaves a recoverable timestamped copy
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

# cmp, not $(cat) — command substitution strips trailing newlines, so a
# string compare would call a file that lost its final newline identical.
# That exact confusion is why sync_claude_to used to overwrite
# newline-only drift with no backup at all.
content_is() { # content_is <path> <expected>
  [ -f "$1" ] && printf '%s' "$2" | cmp -s - "$1"
}
files_match() { cmp -s "$1" "$2"; }

# A backup is only a backup if it holds the removed bytes and follows the
# convention the overwrite path uses (<name>.<14-digit stamp>.bak).
backup_of() { # backup_of <original-path> <expected-content-file>
  local orig="$1" expected="$2" bak found=0
  for bak in "$orig".*.bak; do
    [ -f "$bak" ] || continue
    [[ "$bak" =~ \.[0-9]{14}(-[0-9]+)?\.bak$ ]] || continue
    cmp -s "$expected" "$bak" || continue
    found=1
  done
  [ "$found" -eq 1 ]
}
no_backups_in() { ! compgen -G "$1/*.bak" > /dev/null; }

PROJ_MDC=$'---\ndescription: this project owns this rule\n---\n\n# Project rule\n'
PROJ_MD=$'# Project rule\n'

# Genuine kit bytes for a retired rule, straight out of kit history. The
# ownership test compares bytes, so a fixture that invents its own content
# for a retired name is testing the collision path, not the retire path.
RETIRED_STEM="ponytail-playbook"
KIT_BYTES="$(mktemp)"; CLEANUP+=("$KIT_BYTES")
for c in $(git -C "$KIT_ROOT" log --all --format=%H -- "cursor/rules/$RETIRED_STEM.mdc" 2>/dev/null); do
  if blob="$(git -C "$KIT_ROOT" rev-parse --verify --quiet "$c:cursor/rules/$RETIRED_STEM.mdc")"; then
    git -C "$KIT_ROOT" cat-file blob "$blob" > "$KIT_BYTES"
    break
  fi
done
if [ ! -s "$KIT_BYTES" ]; then
  echo "FAIL - cannot recover genuine kit bytes for $RETIRED_STEM from history" >&2
  echo "  (a shallow clone cannot run this suite; fetch full history)" >&2
  exit 1
fi
KIT_BYTES_MD="$(mktemp)"; CLEANUP+=("$KIT_BYTES_MD")
"$KIT_ROOT/scripts/sync-rules.sh" --help > /dev/null   # sanity: script runs

setup_target() {
  HOME_DIR="$(mktemp -d)"; CLEANUP+=("$HOME_DIR")
  TARGET="$(mktemp -d)"; CLEANUP+=("$TARGET")
  mkdir -p "$TARGET/.cursor/rules" "$TARGET/.claude/rules"
  printf '%s' "$PROJ_MDC" > "$TARGET/.cursor/rules/my-project.mdc"
  printf '%s' "$PROJ_MD"  > "$TARGET/.claude/rules/my-project.md"
  printf '%s\n' "$TARGET" > "$HOME_DIR/.house-rules-sync-targets"
}
seed_retired() { cp "$KIT_BYTES" "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"; }

# --- Scenario 1: a default sync reports, and deletes nothing ---

setup_target; seed_retired
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all 2>&1)"; RC=$?

echo "--- a default sync never deletes ---"
check "project .mdc survives intact" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
check "project .md survives intact" \
  content_is "$TARGET/.claude/rules/my-project.md" "$PROJ_MD"
check "operator is warned the .mdc is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.mdc"
check "operator is warned the .md is unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.md"
check "a genuine retired kit rule is reported, not removed" \
  out_has "$OUT" "Retirable: $RETIRED_STEM.mdc"
check "the genuine retired kit rule is still on disk" \
  files_match "$KIT_BYTES" "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
check "nothing at all was removed" \
  out_lacks "$OUT" "Removed retired:"
check "the operator is told how to act on it" \
  out_has "$OUT" "Re-run with --retire"
check "kit rules were delivered (cursor)" \
  test -f "$TARGET/.cursor/rules/operating-model.mdc"
check "kit rules were delivered (claude)" \
  test -f "$TARGET/.claude/rules/operating-model.md"
check "a clean sync exits 0" \
  test "$RC" -eq 0

# --- Scenario 2: --retire is the opt-in that actually removes ---

echo "--- --retire removes, with a recoverable copy ---"
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --retire 2>&1)"
check "retired kit rule is removed under --retire" \
  test ! -f "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
check "removal left a stamped backup holding the removed bytes" \
  backup_of "$TARGET/.cursor/rules/$RETIRED_STEM.mdc" "$KIT_BYTES"
check "--retire still keeps the project rule" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"

# --- Scenario 3: a filename is not ownership ---
#
# The Tier 2 critical. A project independently authors a rule whose name
# the kit once used. Nothing about that file is the kit's, and no
# combination of flags may delete it.

setup_target
printf 'MY OWN CONTENT, nothing to do with the kit\n' > "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --retire --unsafe 2>&1)"

echo "--- a retired NAME with project bytes is not the kit's to delete ---"
check "project bytes under a retired name survive --retire --unsafe" \
  content_is "$TARGET/.cursor/rules/$RETIRED_STEM.mdc" $'MY OWN CONTENT, nothing to do with the kit\n'
check "it is reported as a name collision, not as retirable" \
  out_has "$OUT" "Name collision left in place: $RETIRED_STEM.mdc"
check "it is never announced as removed" \
  out_lacks "$OUT" "Removed retired: $RETIRED_STEM.mdc"

echo "--- a locally-edited kit rule is kept, not silently retired ---"
setup_target
cp "$KIT_BYTES" "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
printf '# one local edit\n' >> "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --retire 2>&1)"
check "edited retired rule is kept as a collision" \
  test -f "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
check "the edit itself is untouched" \
  bash -c 'grep -qF "# one local edit" "$1"' _ "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"

# --- Scenario 4: --dry-run previews and writes nothing, in both formats ---

setup_target; seed_retired
# Destination absent on purpose: with the dirs pre-created, a dry-run bug
# that creates directories is invisible.
rm -rf "$TARGET/.claude"
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format all --dry-run --retire 2>&1)"

echo "--- dry-run previews the destructive half, changes nothing ---"
check "dry-run announces the pending retirement" \
  out_has "$OUT" "Would remove retired: $RETIRED_STEM.mdc"
check "dry-run warns about the unmanaged file" \
  out_has "$OUT" "Unmanaged rule left in place: my-project.mdc"
check "dry-run leaves the retired file on disk" \
  files_match "$KIT_BYTES" "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
check "dry-run leaves the project file on disk" \
  content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"
check "dry-run writes no backups (cursor)" \
  no_backups_in "$TARGET/.cursor/rules"
check "dry-run does not create an absent destination" \
  test ! -d "$TARGET/.claude/rules"
check "dry-run delivers no rules" \
  test ! -f "$TARGET/.cursor/rules/operating-model.mdc.new"

# --- Scenario 5: --check reports retirable drift, not project files ---

setup_target; seed_retired
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor 2>&1)"   # deliver first
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --check 2>&1)"; RC=$?

echo "--- --check sees what a sync would act on ---"
check "check reports the retired kit rule as drift" \
  out_has "$OUT" "$RETIRED_STEM.mdc — retired kit rule still present"
check "check exits non-zero on that drift" \
  test "$RC" -ne 0
check "check does not claim everything is up to date" \
  out_lacks "$OUT" "all 14 cursor rules up to date"
check "check does not flag the project's own rule" \
  out_lacks "$OUT" "my-project.mdc —"
check "check wrote nothing" \
  no_backups_in "$TARGET/.cursor/rules"

# --- Scenario 6: whitespace in stems must not leak across names ---
#
# Stems were held in a space-delimited string, so "foo bar" made an
# unrelated "foo" look kit-owned, and a retired entry "old rule" parsed as
# "old". Both directions deleted the wrong file.

echo "--- whitespace in a stem does not confer ownership ---"
WKIT="$(mktemp -d)"; CLEANUP+=("$WKIT")
mkdir -p "$WKIT/scripts" "$WKIT/profiles" "$WKIT/cursor/rules"
cp "$KIT_ROOT/scripts/sync-rules.sh" "$WKIT/scripts/"
cp "$KIT_ROOT/cursor/rules/operating-model.mdc" "$WKIT/cursor/rules/"
printf 'alpha\nbeta\n' > "$WKIT/profiles/retired-rules.list"
setup_target
printf 'project bytes\n' > "$TARGET/.cursor/rules/alpha beta.mdc"
OUT="$(HOME="$HOME_DIR" bash "$WKIT/scripts/sync-rules.sh" --format cursor --retire 2>&1)"
check "'alpha beta' is not owned just because 'alpha' and 'beta' are" \
  content_is "$TARGET/.cursor/rules/alpha beta.mdc" $'project bytes\n'
check "it is reported as unmanaged" \
  out_has "$OUT" "Unmanaged rule left in place: alpha beta.mdc"

printf 'old rule\n' > "$WKIT/profiles/retired-rules.list"
setup_target
printf 'project bytes\n' > "$TARGET/.cursor/rules/old.mdc"
OUT="$(HOME="$HOME_DIR" bash "$WKIT/scripts/sync-rules.sh" --format cursor --retire 2>&1)"
check "a multi-word retired entry does not make 'old' deletable" \
  content_is "$TARGET/.cursor/rules/old.mdc" $'project bytes\n'

# --- Scenario 7: --version downgrade ---

PIN_TAG="$(git -C "$KIT_ROOT" tag --list 'v0.2.0' 2>/dev/null || true)"
echo "--- --version downgrade retires post-tag kit rules only ---"
if [ -z "$PIN_TAG" ]; then
  # A skip here is a silently green gate; CI checks out full history.
  echo "FAIL - tag v0.2.0 absent; cannot verify the downgrade guard"
  FAIL=$((FAIL + 1))
else
  NEWER_RULE=""
  for f in "$KIT_ROOT/cursor/rules"/*.mdc; do
    b="$(basename "$f")"
    if ! git -C "$KIT_ROOT" cat-file -e "$PIN_TAG:cursor/rules/$b" 2>/dev/null; then
      NEWER_RULE="$b"; break
    fi
  done
  if [ -z "$NEWER_RULE" ]; then
    echo "FAIL - no rule postdates $PIN_TAG; the downgrade guard is untested"
    FAIL=$((FAIL + 1))
  else
    setup_target
    cp "$KIT_ROOT/cursor/rules/$NEWER_RULE" "$TARGET/.cursor/rules/$NEWER_RULE"
    OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --version "$PIN_TAG" --retire 2>&1)"
    check "genuine post-tag kit rule is retired on downgrade ($NEWER_RULE)" \
      test ! -f "$TARGET/.cursor/rules/$NEWER_RULE"
    check "downgrade keeps the project rule" \
      content_is "$TARGET/.cursor/rules/my-project.mdc" "$PROJ_MDC"

    # Same name, project bytes: the case the old fixture could not catch,
    # because it seeded genuine kit content under that name.
    setup_target
    printf 'I wrote this before the kit ever had one\n' > "$TARGET/.cursor/rules/$NEWER_RULE"
    OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --version "$PIN_TAG" --retire --unsafe 2>&1)"
    check "project bytes under a post-tag kit name survive the downgrade" \
      content_is "$TARGET/.cursor/rules/$NEWER_RULE" $'I wrote this before the kit ever had one\n'
    check "and are reported as a collision" \
      out_has "$OUT" "Name collision left in place: $NEWER_RULE"
  fi
fi

# --- Scenario 8: trailing-newline-only drift is still drift ---

echo "--- byte-level comparison on the claude overwrite path ---"
setup_target
HOME="$HOME_DIR" bash "$SYNC" --format claude > /dev/null 2>&1
printf '\n' >> "$TARGET/.claude/rules/operating-model.md"
cp "$TARGET/.claude/rules/operating-model.md" "$KIT_BYTES_MD"
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format claude --check 2>&1)"; RC=$?
check "check flags a newline-only difference" \
  out_has "$OUT" "operating-model.md — differs"
check "check exits non-zero on it" \
  test "$RC" -ne 0
OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format claude 2>&1)"
check "the newline-only edit is backed up before overwrite" \
  backup_of "$TARGET/.claude/rules/operating-model.md" "$KIT_BYTES_MD"

# --- Scenario 9: the generated projection holds exactly the projection ---

echo "--- --local keeps the kit's generated directory exact ---"
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
# git is the backup for a tracked generated directory; a .bak in there
# breaks the exactness guarantee the CI gate is supposed to enforce.
check "pruning leaves no .bak inside the generated directory" \
  no_backups_in "$FAKE_KIT/claude/rules"

# The overwrite path, not the deletion path: the routine kit loop is "edit a
# cursor rule, re-sync", which lands on an existing .md whose bytes differ
# from the new render. Backing that up drops a .bak into the same tracked
# directory the next --check --local is required to find empty, so the
# documented loop leaves the tree in a state the kit's own gate rejects.
printf '# stale hand-edit\n' >> "$FAKE_KIT/claude/rules/operating-model.md"
OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --local 2>&1)"
check "regenerating over a changed projection leaves no .bak" \
  no_backups_in "$FAKE_KIT/claude/rules"
check "regenerating over a changed projection restores the real render" \
  bash -c '! grep -qF "# stale hand-edit" "$1"' _ "$FAKE_KIT/claude/rules/operating-model.md"
OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --check --local 2>&1)"; RC=$?
check "the check immediately after a local sync passes" \
  test "$RC" -eq 0

printf '# orphaned build artifact\n' > "$FAKE_KIT/claude/rules/some-renamed-rule.md"
OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --check --local 2>&1)"; RC=$?
check "--check --local reports the orphan" \
  out_has "$OUT" "some-renamed-rule.md — orphaned projection"
check "--check --local exits non-zero on an orphan" \
  test "$RC" -ne 0
rm -f "$FAKE_KIT/claude/rules/some-renamed-rule.md"

printf 'stray\n' > "$FAKE_KIT/claude/rules/notes.txt"
OUT="$(bash "$FAKE_KIT/scripts/sync-rules.sh" --format claude --check --local 2>&1)"; RC=$?
check "--check --local reports a non-projection file" \
  out_has "$OUT" "notes.txt — not part of the projection"
check "--check --local exits non-zero on it" \
  test "$RC" -ne 0
rm -f "$FAKE_KIT/claude/rules/notes.txt"

# --- Scenario 10: an unbackupable deletion must not report success ---

echo "--- a failed deletion backup surfaces as an error ---"
if [ "$(id -u)" -eq 0 ]; then
  echo "skip - running as root, chmod cannot make the file unreadable"
else
  setup_target; seed_retired
  chmod 000 "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
  OUT="$(HOME="$HOME_DIR" bash "$SYNC" --format cursor --retire 2>&1)"; RC=$?
  chmod 644 "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
  check "unbackupable retired rule is left on disk" \
    test -f "$TARGET/.cursor/rules/$RETIRED_STEM.mdc"
  check "the run does not claim the retirement succeeded" \
    out_lacks "$OUT" "Removed retired: $RETIRED_STEM.mdc"
  check "the run exits non-zero so automation can see it" \
    test "$RC" -ne 0
fi

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
