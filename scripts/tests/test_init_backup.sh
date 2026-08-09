#!/usr/bin/env bash
# Pins init's overwrite guarantee (process-kit-jjj): .bak contents, the
# shared implementation, the --unsafe waiver, and no litter when nothing
# changed. Rationale for the guarantee: scripts/lib/backup-file.sh.
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

skip() { echo "skip - $1"; }

out_has() { grep -qF -- "$2" <<< "$1"; }

# Sets H, REPO and INIT_ARGS in the CALLER. Deliberately not called through
# command substitution: a subshell's CLEANUP append is discarded, which
# leaked one full init tree per fixture.
seed_installed() { # seed_installed [init args...]
  INIT_ARGS=("$@")
  [ ${#INIT_ARGS[@]} -gt 0 ] || INIT_ARGS=(--tool cursor)
  H="$(mktemp -d)"; CLEANUP+=("$H")
  REPO="$H/project"
  mkdir -p "$REPO"
  git -C "$REPO" init -q
  ( cd "$REPO" && HOME="$H" bash "$INIT" "${INIT_ARGS[@]}" >/dev/null 2>&1 )
}

# Re-runs init against the current fixture with the same tool selection.
reinit() { # reinit [extra init args...]
  ( cd "$REPO" && HOME="$H" bash "$INIT" "${INIT_ARGS[@]}" "$@" 2>&1 )
}

baks_in()     { find "$1" -name '*.bak' 2>/dev/null; }
no_baks_in()  { [ -z "$(baks_in "$1")" ]; }
some_baks_in(){ [ -n "$(baks_in "$1")" ]; }
# The .bak beside a specific file, by that file's name.
bak_for()     { find "$(dirname "$1")" -name "$(basename "$1").*.bak" 2>/dev/null | head -1; }

RULE_REL=".cursor/rules/operating-model.mdc"
EDIT_MARK="# LOCAL EDIT A PROJECT MADE"

# ---------------------------------------------------------------------------
# AC1: a locally-edited kit file survives a re-init as a timestamped .bak
# ---------------------------------------------------------------------------

echo "--- AC1: re-init preserves prior content as a .bak ---"
seed_installed
RULE="$REPO/$RULE_REL"

check "precondition: the install delivered the rule" test -f "$RULE"

printf '%s\n' "$EDIT_MARK" >> "$RULE"
cp "$RULE" "$H/expected-prior-bytes"

OUT="$(reinit)"; RC=$?

# Captured at the call. A botched extraction that leaves the counter unset
# aborts init under `set -u` at the summary — after every file is copied, so
# every content assertion below still passes on a run that exited 1.
check "a safe-mode re-init exits 0" test "$RC" -eq 0

check "re-init writes a .bak beside the overwritten rule" \
  some_baks_in "$REPO/.cursor/rules"

BAK="$(bak_for "$RULE")"
check "the .bak holds the pre-init bytes, not the kit's" \
  cmp -s "$H/expected-prior-bytes" "$BAK"

check "the rule itself is restored to the kit's bytes" \
  cmp -s "$KIT_ROOT/cursor/rules/operating-model.mdc" "$RULE"

check "the run says it backed the file up" \
  out_has "$OUT" "backed up operating-model.mdc"

# The summary is the operator's only whole-run signal that a re-run replaced
# something. It reads a counter the lib owns, so deleting the increment would
# otherwise silently empty this line while every per-file assertion passed.
check "the run summarizes how many files it backed up" \
  out_has "$OUT" "1 file(s) backed up before overwrite"

# ---------------------------------------------------------------------------
# AC2: the convention is sync's convention, from one implementation
# ---------------------------------------------------------------------------

echo "--- AC2: backup convention matches sync ---"

BAK1="$(bak_for "$RULE")"
check "the .bak name carries a 14-digit timestamp" \
  bash -c 'basename "$1" | grep -qE "^operating-model\.mdc\.[0-9]{14}(-[0-9]+)?\.bak$"' _ "$BAK1"

# Same operator line, character for character, as the sync path prints.
seed_installed
H2="$H"; REPO2="$REPO"
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

# One implementation, not a third copy. Asserted behaviorally: sourcing each
# script's lib line must actually define the primitive. Grepping the scripts
# for the lib path matched the `# shellcheck source=` comment, so deleting
# the real source line left the check green.
lib_defines_via() { # lib_defines_via <script>
  local dir
  dir="$(grep -oE '^\. "\$KIT_ROOT/scripts/lib/backup-file\.sh"' "$1")" || return 1
  [ -n "$dir" ] || return 1
  ( KIT_ROOT="$KIT_ROOT"
    # shellcheck source=/dev/null
    . "$KIT_ROOT/scripts/lib/backup-file.sh"
    declare -F backup_file >/dev/null && declare -F backup_before_overwrite >/dev/null )
}
check "init sources a lib that defines the primitive" lib_defines_via "$INIT"
check "sync sources a lib that defines the primitive" lib_defines_via "$SYNC"

# A rename or a re-spelled duplicate is what AC2 forbids, and an anchored
# grep for one spelling cannot see either. Count definitions instead.
check "exactly one backup_file definition exists across scripts/" \
  bash -c '
    n="$(grep -rEc "^[[:space:]]*(function[[:space:]]+)?backup_file[[:space:]]*(\(\))?[[:space:]]*\{" \
          --include="*.sh" "$1/scripts" 2>/dev/null | awk -F: "{t+=\$2} END {print t+0}")"
    [ "$n" -eq 1 ]' _ "$KIT_ROOT"

# ---------------------------------------------------------------------------
# AC3: --unsafe waives backups, the same waiver sync offers
# ---------------------------------------------------------------------------

echo "--- AC3: --unsafe waives backups ---"
seed_installed
printf '%s\n' "$EDIT_MARK" >> "$REPO/$RULE_REL"
printf '\n# local tweak\n' >> "$REPO/profiles/conventions.toml"
printf '\n# local tweak\n' >> "$REPO/scripts/defer-lint"
reinit --unsafe >/dev/null; RC3=$?

check "--unsafe is an accepted flag, not a usage error" test "$RC3" -eq 0
# Whole repo, not just the rules dir: a regression where SAFE_MODE is honored
# at one site and ignored at another passes a rules-only assertion.
check "--unsafe writes no .bak anywhere in the repo" no_baks_in "$REPO"
check "--unsafe still installs the rule" \
  cmp -s "$KIT_ROOT/cursor/rules/operating-model.mdc" "$REPO/$RULE_REL"

# ---------------------------------------------------------------------------
# No gratuitous backups: the guarantee is about content, not about writes
# ---------------------------------------------------------------------------

echo "--- unchanged and first-time files are not backed up ---"
seed_installed
reinit >/dev/null
check "re-init over an untouched install writes no .bak" no_baks_in "$REPO"

h5="$(mktemp -d)"; CLEANUP+=("$h5")
repo5="$h5/fresh"; mkdir -p "$repo5"; git -C "$repo5" init -q
( cd "$repo5" && HOME="$h5" bash "$INIT" --tool cursor >/dev/null 2>&1 )
check "a first install writes no .bak" no_baks_in "$repo5"

# ---------------------------------------------------------------------------
# Pattern class: EVERY file init overwrites, not three hand-picked ones.
#
# The suite previously ran `--tool cursor` with no `--skills`, so the Claude
# rules loop and the skills walk were never executed — reverting either to a
# bare glob cp left every assertion green. This section installs the full
# surface, edits everything on it, and demands one .bak per edited file, so a
# new write site added later is covered without touching this test.
# ---------------------------------------------------------------------------

echo "--- every delivered file is covered, not just the ones named here ---"
seed_installed --tool both --skills

delivered_files() {
  {
    find "$REPO/.cursor/rules" "$REPO/.claude/rules" \
         "$REPO/.cursor/skills" "$REPO/.claude/skills" -type f 2>/dev/null
    [ -f "$REPO/profiles/conventions.toml" ] && echo "$REPO/profiles/conventions.toml"
    while IFS='|' read -r cli_name _rest; do
      case "$cli_name" in ""|\#*) continue ;; esac
      [ -f "$REPO/scripts/$cli_name" ] && echo "$REPO/scripts/$cli_name"
    done < "$KIT_ROOT/scripts/distributed-clis.list"
  } 2>/dev/null | sort -u
}

mapfile -t DELIVERED < <(delivered_files)
check "the full install delivered a substantial file set" \
  test "${#DELIVERED[@]}" -gt 20
covers_all_surfaces() {
  local listing pat
  listing="$(printf '%s\n' "${DELIVERED[@]}")"
  for pat in "/.cursor/rules/" "/.claude/rules/" "/skills/" "/profiles/conventions.toml"; do
    grep -qF -- "$pat" <<< "$listing" || return 1
  done
}
check "the full install covers all four surfaces" covers_all_surfaces

for f in "${DELIVERED[@]}"; do
  printf '\n%s\n' "$EDIT_MARK" >> "$f"
  cp "$f" "$f.expected"
done

reinit >/dev/null; RC6=$?
check "a full-surface re-init exits 0" test "$RC6" -eq 0

missing_bak=()
wrong_bytes=()
not_replaced=()
for f in "${DELIVERED[@]}"; do
  b="$(bak_for "$f")"
  if [ -z "$b" ]; then
    missing_bak+=("${f#"$REPO"/}")
    continue
  fi
  cmp -s "$f.expected" "$b" || wrong_bytes+=("${f#"$REPO"/}")
  # The write must still have happened: a "back up, then skip the write"
  # regression would leave the edit in place and look identical above.
  cmp -s "$f.expected" "$f" && not_replaced+=("${f#"$REPO"/}")
done

check "every edited file got a .bak (missing: ${missing_bak[*]:-none})" \
  test "${#missing_bak[@]}" -eq 0
check "every .bak holds that file's pre-init bytes (wrong: ${wrong_bytes[*]:-none})" \
  test "${#wrong_bytes[@]}" -eq 0
check "every edited file was actually replaced (stale: ${not_replaced[*]:-none})" \
  test "${#not_replaced[@]}" -eq 0

# ---------------------------------------------------------------------------
# AGENTS.md — the third posture: kit-owned bytes inside a project-owned file
# ---------------------------------------------------------------------------

echo "--- the AGENTS.md marker refresh is backed up too ---"
seed_installed
AGENTS="$REPO/AGENTS.md"
if [ -f "$AGENTS" ]; then
  # Stale the stamp so the refresh path fires, and plant project content
  # inside the managed block — the bytes the rewrite discards.
  sed -i 's/<!-- house-rules:version .* -->/<!-- house-rules:version 0.0.0 -->/' "$AGENTS"
  printf '%s\n' "$EDIT_MARK" >> "$AGENTS"
  cp "$AGENTS" "$H/expected-agents"

  AOUT="$(reinit)"
  check "the refresh actually fired" out_has "$AOUT" "Refreshed AGENTS.md"
  ABAK="$(bak_for "$AGENTS")"
  check "AGENTS.md is backed up before its section is rewritten" \
    test -n "$ABAK"
  check "the AGENTS.md .bak holds the pre-refresh bytes" \
    cmp -s "$H/expected-agents" "$ABAK"
else
  skip "AGENTS.md not delivered by this install"
fi

# ---------------------------------------------------------------------------
# A failed backup must abort, not overwrite. Mirrors scenario 10 of
# test_sync_cleanup.sh, which pins the same property on the sync side.
# ---------------------------------------------------------------------------

echo "--- an unbackupable file is never overwritten ---"
if [ "$(id -u)" -eq 0 ]; then
  skip "running as root, chmod cannot make the file unreadable"
else
  seed_installed
  VICTIM="$REPO/$RULE_REL"
  printf '%s\n' "$EDIT_MARK" >> "$VICTIM"
  cp "$VICTIM" "$H/expected-victim"
  chmod 000 "$VICTIM"

  FOUT="$(reinit)"; FRC=$?
  chmod 644 "$VICTIM"

  check "an unbackupable overwrite exits non-zero" test "$FRC" -ne 0
  check "the unbackupable file is left untouched" \
    cmp -s "$H/expected-victim" "$VICTIM"
  check "the run does not claim setup completed" \
    bash -c '! grep -qF "Setup complete" <<< "$1"' _ "$FOUT"
fi

echo ""
echo "Passed: $PASS  Failed: $FAIL"
[ "$FAIL" -eq 0 ]
