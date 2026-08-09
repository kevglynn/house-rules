# shellcheck shell=bash
# Shared timestamped-backup primitive for the kit's destructive writers.
# Sourced from KIT_ROOT (each caller remains a standalone bash script).
#
# Extracted from sync-rules.sh for process-kit-jjj. Both entry points write
# into the same directories in a target repo, so a project that edits a
# delivered file must get the same guarantee whichever one it re-runs, with
# the same .bak name shape and the same operator line. Two scripts that
# merely agree today drift the first time one is edited.
#
# Contract for backup_file: 0 = a recoverable copy exists, 1 = it does not.
# Every caller must treat 1 as "do not proceed with the destructive write" —
# that decision is the caller's, because what to do instead differs (sync
# skips the file and fails the run; init aborts the bootstrap).
#
# Callers own SAFE_MODE. This lib does not read it: a caller that forgets to
# check it should over-back-up, not silently skip the backup.

# Count of backups written this run. Read by callers for their summary line.
: "${SAFE_BACKUP_COUNT:=0}"

backup_file() {
  local path="$1" ts bak n=0
  ts="$(date +%Y%m%d%H%M%S)"
  bak="${path}.${ts}.bak"
  # One-second timestamp granularity, so two writers in the same second
  # collide. `set -C` makes the reservation atomic: a test-then-copy left a
  # window where both processes saw the name free, and the loser's cp then
  # overwrote the winner's backup with the already-written content — losing
  # the only copy of the original bytes.
  while ! ( set -C; : > "$bak" ) 2>/dev/null; do
    n=$((n + 1))
    if [ $n -gt 100 ]; then
      echo "✗ Could not reserve a backup name for $(basename "$path")" >&2
      return 1
    fi
    bak="${path}.${ts}-${n}.bak"
  done
  if ! cp "$path" "$bak"; then
    rm -f "$bak"
    return 1
  fi
  echo "    ↳ backed up $(basename "$path") → $(basename "$bak")"
  SAFE_BACKUP_COUNT=$((SAFE_BACKUP_COUNT + 1))
  return 0
}

# Back up DEST before overwriting it with SRC, then report whether the
# caller may proceed. Skips the backup when the bytes already match, so a
# re-run over an unchanged install leaves no .bak litter — the guarantee is
# about content that would be lost, not about writes that happen.
#
# 0 = safe to write, 1 = backup failed, caller must not overwrite.
backup_before_overwrite() { # <src> <dest>
  local src="$1" dest="$2"
  [ -f "$dest" ] || return 0
  cmp -s "$src" "$dest" && return 0
  backup_file "$dest"
}
