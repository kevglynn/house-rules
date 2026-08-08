#!/usr/bin/env bash
# shellcheck disable=SC2059
set -uo pipefail

# Multi-format rule sync from the kit repo (canonical source) to target
# repos AND their git worktrees.
#
# Usage:
#   ./scripts/sync-rules.sh                              # Sync cursor format (default)
#   ./scripts/sync-rules.sh --format claude               # Sync claude format
#   ./scripts/sync-rules.sh --format all                  # Sync both formats
#   ./scripts/sync-rules.sh --format cursor --check       # Check cursor drift
#   ./scripts/sync-rules.sh --format claude --local       # Generate claude/ in this repo only
#   ./scripts/sync-rules.sh --dry-run                     # Preview without writing
#   ./scripts/sync-rules.sh --version v1.0.0              # Sync rules from a specific release
#   ./scripts/sync-rules.sh --show-version                # Print current kit version
#   ./scripts/sync-rules.sh --help
#
# Config: ~/.house-rules-sync-targets (one repo root per line).
# Rules are auto-discovered from cursor/rules/*.mdc (no hardcoded file list).

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$KIT_ROOT/cursor/rules"
FORMAT="cursor"
CHECK_MODE=false
LOCAL_ONLY=false
DRY_RUN=false
# SAFE_MODE defaults to true: any locally modified target file is backed
# up as .bak before being overwritten. Pass --unsafe to allow silent
# overwrite (rarely correct; kept for parity with prior behavior).
SAFE_MODE=true
PIN_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --format)
      # Guard before "$2": set -u otherwise aborts with raw "unbound variable".
      if [ $# -lt 2 ]; then
        echo "Error: --format requires an argument (cursor|claude|all). See --help." >&2
        exit 1
      fi
      FORMAT="$2"; shift 2 ;;
    --check)   CHECK_MODE=true; shift ;;
    --local)   LOCAL_ONLY=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --unsafe)  SAFE_MODE=false; shift ;;
    --version)
      if [ $# -lt 2 ]; then
        echo "Error: --version requires an argument (git tag, e.g. v1.0.0). See --help." >&2
        exit 1
      fi
      PIN_VERSION="$2"; shift 2 ;;
    --show-version)
      if [ -f "$KIT_ROOT/VERSION" ]; then
        echo "house-rules v$(cat "$KIT_ROOT/VERSION" | tr -d '[:space:]')"
      else
        echo "house-rules (no VERSION file)"
      fi
      exit 0
      ;;
    -h|--help)
      cat <<'EOF'
Multi-format rule sync from the kit repo to target repos.

Usage: sync-rules.sh [options]

Options:
  --format cursor|claude|all   Output format (default: cursor; "both" is
                               accepted as an alias for "all" — init.sh
                               uses --tool both for the same concept)
  --check                      Report drift without syncing
  --local                      Generate in this repo only (claude/all)
  --dry-run                    Preview what would be written
  --unsafe                     Disable safe-mode backups (silent overwrite).
                               Default is ON: locally modified files are
                               backed up to .<ts>.bak before being
                               overwritten.
  --version TAG                Sync rules from a specific git tag (e.g. v1.0.0)
  --show-version               Print current kit version and exit
  --help                       Show this help

Config: ~/.house-rules-sync-targets (one repo root per line)

Versioning:
  Without --version, rules sync from the current working tree (latest edits).
  With --version, rules sync from the specified git tag. Teams can pin to a
  stable release and upgrade deliberately. See CHANGELOG.md for release notes.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# Accept "both" as an alias for "all" — init.sh uses --tool both
# for the same concept and cross-script muscle memory shouldn't silently
# fail. See agent-protocol.md for the contract.
if [[ "$FORMAT" == "both" ]]; then
  FORMAT="all"
fi

if [[ "$FORMAT" != "cursor" && "$FORMAT" != "claude" && "$FORMAT" != "all" ]]; then
  echo "Unknown format: $FORMAT (expected cursor, claude, all, or both)" >&2
  exit 1
fi

# --- Version pinning ---

VERSIONED_TMPDIR=""
cleanup_versioned_tmp() {
  [ -n "$VERSIONED_TMPDIR" ] && rm -rf "$VERSIONED_TMPDIR"
}
trap cleanup_versioned_tmp EXIT

if [ -n "$PIN_VERSION" ]; then
  if ! git -C "$KIT_ROOT" rev-parse "$PIN_VERSION" &>/dev/null; then
    echo "Tag '$PIN_VERSION' not found in the kit repo."
    echo "Available tags: $(git -C "$KIT_ROOT" tag --list 'v*' | tr '\n' ' ')"
    echo ""
    echo "To create a release: git tag v1.0.0 && git push origin v1.0.0"
    exit 1
  fi

  VERSIONED_TMPDIR="$(mktemp -d)"
  mkdir -p "$VERSIONED_TMPDIR"

  while IFS= read -r filepath; do
    fname="$(basename "$filepath")"
    git -C "$KIT_ROOT" show "${PIN_VERSION}:${filepath}" > "$VERSIONED_TMPDIR/$fname" 2>/dev/null || true
  done < <(git -C "$KIT_ROOT" ls-tree --name-only "${PIN_VERSION}" cursor/rules/ 2>/dev/null | grep '\.mdc$')

  file_count=$(ls -1 "$VERSIONED_TMPDIR"/*.mdc 2>/dev/null | wc -l | tr -d ' ')
  if [ "$file_count" -eq 0 ]; then
    echo "No .mdc files found in tag '$PIN_VERSION' at cursor/rules/"
    exit 1
  fi

  SRC="$VERSIONED_TMPDIR"
  echo "Using rules from $PIN_VERSION ($file_count files)"
  echo ""
fi

# --- Auto-discover rule files ---

MDC_FILES=()
for f in "$SRC"/*.mdc; do
  [ -f "$f" ] && MDC_FILES+=("$(basename "$f")")
done

if [ ${#MDC_FILES[@]} -eq 0 ]; then
  echo "No .mdc files found in $SRC"
  exit 1
fi

# Rule stems the kit used to ship and no longer does — the only files the
# cleanup pass may delete from a target. A missing or empty list is
# deliberately fail-safe: nothing gets removed, everything unrecognized is
# reported as unmanaged.
RETIRED_STEMS=""
RETIRED_LIST="$KIT_ROOT/profiles/retired-rules.list"
if [ -f "$RETIRED_LIST" ]; then
  # `read -r stem _` (default IFS) trims surrounding whitespace and takes
  # the first field; `|| [ -n "$stem" ]` keeps a final line that has no
  # trailing newline, which would otherwise be dropped silently — and with
  # a one-entry list, dropping it no-ops the whole feature.
  while read -r stem _ || [ -n "$stem" ]; do
    case "$stem" in ""|\#*) continue ;; esac
    RETIRED_STEMS="$RETIRED_STEMS $stem"
  done < "$RETIRED_LIST"
fi

# Stems the kit is delivering on THIS run (honors --version pinning).
DELIVERED_STEMS=""
for f in "${MDC_FILES[@]}"; do
  DELIVERED_STEMS="$DELIVERED_STEMS ${f%.mdc}"
done

# Every stem the kit has ever owned: what the working tree ships today,
# plus what it has retired. Read from the working tree even under
# --version, so a downgrade still recognizes newer rules as kit artifacts
# and removes them rather than mistaking them for project content.
KIT_KNOWN_STEMS="$RETIRED_STEMS"
for f in "$KIT_ROOT/cursor/rules"/*.mdc; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  KIT_KNOWN_STEMS="$KIT_KNOWN_STEMS ${b%.mdc}"
done

# Counted here rather than in the sync loop: --local runs the cleanup pass
# without entering that loop, and `set -u` would abort on an unset counter.
unmanaged_count=0

# --- Frontmatter stripping (for claude format) ---

strip_frontmatter() {
  local file="$1"
  local in_frontmatter=false
  local frontmatter_ended=false
  local line_num=0

  while IFS= read -r line || [[ -n "$line" ]]; do
    line_num=$((line_num + 1))
    if [[ $line_num -eq 1 && "$line" == "---" ]]; then
      in_frontmatter=true
      continue
    fi
    if $in_frontmatter && [[ "$line" == "---" ]]; then
      in_frontmatter=false
      frontmatter_ended=true
      continue
    fi
    if $in_frontmatter; then
      continue
    fi
    if $frontmatter_ended && [[ -z "$line" ]]; then
      frontmatter_ended=false
      continue
    fi
    frontmatter_ended=false
    printf '%s\n' "$line"
  done < "$file"
}

# --- Stale file cleanup ---
#
# Three outcomes per unrecognized file in a rules directory:
#   kit rule we are delivering  → overwritten by the sync loop, .bak first
#   kit rule we are not         → removed, .bak first ("retired")
#   anything else               → LEFT IN PLACE and reported ("unmanaged")
#
# The third case is the point. This pass used to delete whatever it did not
# recognize, which destroyed project-authored rules that were never
# committed and therefore unrecoverable (process-kit-2d6). A project may
# keep its own rules in .cursor/rules/ or .claude/rules/; the kit will not
# update or remove them. Operator-facing contract: docs/operations.md
# § "What syncs automatically vs. what you copy manually".
#
# "Kit rule we are not delivering" covers two cases, both genuine kit
# artifacts rather than project content: a stem on the retired list (a rule
# the kit renamed or dropped), and — under --version — a rule newer than
# the pinned tag, which must go for the downgrade to produce the rule set
# the tag describes.

in_stem_set() { # in_stem_set <stem> <space-delimited set>
  [[ " $2 " == *" $1 "* ]]
}

# Timestamped backup, shared by every destructive path so the convention
# (name shape, operator message, counter) has one owner. Returns 1 if the
# copy fails; each caller decides what that means for its own flow.
backup_file() {
  local path="$1" ts bak n=0
  ts="$(date +%Y%m%d%H%M%S)"
  bak="${path}.${ts}.bak"
  # One-second timestamp granularity: two syncs in the same second would
  # otherwise clobber the first backup, and on the deletion path that
  # backup is the only remaining copy.
  while [ -e "$bak" ]; do
    n=$((n + 1))
    bak="${path}.${ts}-${n}.bak"
  done
  if ! cp "$path" "$bak"; then
    return 1
  fi
  echo "    ↳ backed up $(basename "$path") → $(basename "$bak")"
  safe_backup_count=$((safe_backup_count + 1))
  return 0
}

retire_or_keep() {
  local existing="$1" base="$2" stem="$3"

  # A generated projection directory (--local writes the kit's own
  # claude/rules/) has no project-authored content by construction, so an
  # unrecognized file there is an orphaned build artifact, not someone's
  # rule. Keeping it would leave a retired rule loaded in the kit and ship
  # it to every new adopter via init's wholesale copy.
  if ! $LOCAL_ONLY && ! in_stem_set "$stem" "$KIT_KNOWN_STEMS"; then
    echo "  ⚠ Unmanaged rule left in place: $base (not a kit rule — the kit will not update or remove it)"
    unmanaged_count=$((unmanaged_count + 1))
    return 0
  fi

  if $DRY_RUN; then
    echo "    [dry-run] Would remove retired: $base"
    return 0
  fi

  if $SAFE_MODE && ! backup_file "$existing"; then
    echo "✗ Failed to back up $base before removal — leaving it in place" >&2
    return 1
  fi
  if ! rm "$existing"; then
    echo "✗ Failed to remove retired rule $base" >&2
    return 1
  fi
  echo "    Removed retired: $base"
}

# One pass over both formats: a file is kit-managed iff its stem is in the
# set being delivered, whichever extension it wears.
cleanup_stale() { # cleanup_stale <dest> <ext>
  local dest="$1" ext="$2" rc=0
  [ -d "$dest" ] || return 0
  for existing in "$dest"/*."$ext"; do
    [ -f "$existing" ] || continue
    local base stem
    base="$(basename "$existing")"
    stem="${base%.$ext}"
    in_stem_set "$stem" "$DELIVERED_STEMS" && continue
    retire_or_keep "$existing" "$base" "$stem" || rc=1
  done
  return $rc
}

# --- Format-specific sync/check functions ---

safe_backup() {
  local src_file="$1" dest_file="$2"
  if $SAFE_MODE && [ -f "$dest_file" ]; then
    if ! diff -q "$src_file" "$dest_file" > /dev/null 2>&1; then
      if ! backup_file "$dest_file"; then
        echo "✗ Failed to back up $(basename "$dest_file") before overwrite — refusing to sync this file" >&2
        return 1
      fi
    fi
  fi
  return 0
}

sync_cursor_to() {
  local dest="$1"
  if $DRY_RUN; then
    echo "    [dry-run] Would copy ${#MDC_FILES[@]} .mdc files → $dest"
    # Report-only: the cleanup pass is the destructive half, so a preview
    # that omits it hides exactly what an operator runs --dry-run to see.
    cleanup_stale "$dest" mdc
    return 0
  fi
  mkdir -p "$dest" || return 1
  for f in "${MDC_FILES[@]}"; do
    safe_backup "$SRC/$f" "$dest/$f" || return 1
    cp "$SRC/$f" "$dest/$f" || return 1
  done
  cleanup_stale "$dest" mdc
}

sync_claude_to() {
  local dest="$1"
  if $DRY_RUN; then
    echo "    [dry-run] Would generate ${#MDC_FILES[@]} .md files → $dest"
    cleanup_stale "$dest" md
    return 0
  fi
  mkdir -p "$dest" || return 1
  for f in "${MDC_FILES[@]}"; do
    local md_name="${f%.mdc}.md"
    if $SAFE_MODE && [ -f "$dest/$md_name" ]; then
      local expected
      expected="$(strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g')"
      local actual
      actual="$(cat "$dest/$md_name")"
      if [[ "$expected" != "$actual" ]]; then
        if ! backup_file "$dest/$md_name"; then
          echo "✗ Failed to back up $md_name before overwrite — refusing to sync this file" >&2
          return 1
        fi
      fi
    fi
    strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g' > "$dest/$md_name" || return 1
  done
  cleanup_stale "$dest" md
}

# A generated projection directory should contain nothing but the
# projection. In a target repo an extra file is a project's own rule and
# none of our business, so this only fires under --local — otherwise CI's
# `--check --local` stays green while an orphaned rule sits committed in
# claude/rules/, gets loaded alongside its replacement, and ships to every
# new adopter through init's wholesale copy.
check_no_orphans() { # check_no_orphans <dest> <ext>
  local dest="$1" ext="$2" orphan=0
  $LOCAL_ONLY || return 0
  [ -d "$dest" ] || return 0
  for existing in "$dest"/*."$ext"; do
    [ -f "$existing" ] || continue
    local base stem
    base="$(basename "$existing")"
    stem="${base%.$ext}"
    in_stem_set "$stem" "$DELIVERED_STEMS" && continue
    echo "  ✗ $base — orphaned projection (no matching cursor/rules/$stem.mdc)"
    orphan=1
  done
  return $orphan
}

check_cursor_in() {
  local dest="$1"
  local stale=0
  for f in "${MDC_FILES[@]}"; do
    if [ ! -f "$dest/$f" ]; then
      echo "  ✗ $f — missing"
      stale=1
    elif ! diff -q "$SRC/$f" "$dest/$f" > /dev/null 2>&1; then
      echo "  ✗ $f — differs"
      stale=1
    fi
  done
  if [ $stale -eq 0 ]; then
    echo "  ✓ all ${#MDC_FILES[@]} cursor rules up to date"
  fi
  return $stale
}

check_claude_in() {
  local dest="$1"
  local stale=0
  for f in "${MDC_FILES[@]}"; do
    local md_name="${f%.mdc}.md"
    if [ ! -f "$dest/$md_name" ]; then
      echo "  ✗ $md_name — missing"
      stale=1
    else
      local expected
      expected="$(strip_frontmatter "$SRC/$f" | sed 's/\.mdc/\.md/g')"
      local actual
      actual="$(cat "$dest/$md_name")"
      if [[ "$expected" != "$actual" ]]; then
        echo "  ✗ $md_name — differs"
        stale=1
      fi
    fi
  done
  check_no_orphans "$dest" md || stale=1
  if [ $stale -eq 0 ]; then
    echo "  ✓ all ${#MDC_FILES[@]} claude rules up to date"
  fi
  return $stale
}

# --- Target validation ---

validate_target() {
  local target="$1"
  if [ ! -d "$target" ]; then
    echo "  ⚠ Target does not exist: $target (skipping)"
    return 1
  fi
  if ! { [ -d "$target/.git" ] || [ -f "$target/.git" ]; }; then
    echo "  ⚠ Target is not a git repo: $target (syncing anyway)"
  fi
  return 0
}

# --- Local-only mode (generate in this repo) ---

safe_backup_count=0

if $LOCAL_ONLY; then
  if [[ "$FORMAT" == "cursor" ]]; then
    echo "--local only applies to non-cursor formats (cursor rules are the source)."
    exit 1
  fi

  if [[ "$FORMAT" == "claude" || "$FORMAT" == "all" ]]; then
    dest="$KIT_ROOT/claude/rules"
    if $CHECK_MODE; then
      echo "Checking: $KIT_ROOT/claude/rules"
      check_claude_in "$dest" || { echo "Run without --check to regenerate."; exit 1; }
    else
      sync_claude_to "$dest"
      echo "Generated ${#MDC_FILES[@]} claude rules → $dest"
    fi
  fi
  exit 0
fi

# --- Load targets ---

CONFIG_FILE="$HOME/.house-rules-sync-targets"
TARGETS=()

if [ ! -f "$CONFIG_FILE" ]; then
  echo "No config file found."
  echo "Create ~/.house-rules-sync-targets with one repo root per line:"
  cat <<TMPL
# Repo roots to sync kit rules to (one per line).
# Lines starting with # are ignored. ~ is expanded to \$HOME.
#
# Example:
# ~/projects/my-repo
TMPL
  exit 1
fi

while IFS= read -r line; do
  line="${line/#\~/$HOME}"
  TARGETS+=("$line")
done < <(grep -v '^\s*#' "$CONFIG_FILE" | grep -v '^\s*$' | tr -d '\r')

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "No targets in $CONFIG_FILE. Add repo paths, one per line."
  exit 1
fi

# --- Format dispatch for a single repo ---

sync_repo() {
  local repo_root="$1" fmt="$2"
  local label="$fmt"

  if [[ "$fmt" == "cursor" ]]; then
    local cursor_dest="$repo_root/.cursor/rules"
    if $CHECK_MODE; then
      echo "Checking ($label): $repo_root"
      check_cursor_in "$cursor_dest" || return 1
    else
      sync_cursor_to "$cursor_dest" || return 1
      if ! $DRY_RUN; then echo "Synced ($label) → $repo_root"; fi
    fi
  elif [[ "$fmt" == "claude" ]]; then
    local claude_dest="$repo_root/.claude/rules"
    if $CHECK_MODE; then
      echo "Checking ($label): $repo_root"
      check_claude_in "$claude_dest" || return 1
    else
      sync_claude_to "$claude_dest" || return 1
      if ! $DRY_RUN; then echo "Synced ($label) → $repo_root"; fi

      # Warn if .claude/rules/ is gitignored
      if git -C "$repo_root" check-ignore -q ".claude/rules/test.md" 2>/dev/null; then
        echo "  ⚠ .claude/rules/ appears to be gitignored — rules won't be committed"
      fi
    fi
  fi
  return 0
}

sync_worktrees() {
  local repo_root="$1" fmt="$2"
  local local_wt=0
  if [[ "$fmt" != "cursor" ]]; then return 0; fi
  if ! { [ -d "$repo_root/.git" ] || [ -f "$repo_root/.git" ]; }; then return 0; fi

  while IFS= read -r line; do
    local wt_path="${line#worktree }"
    [ "$wt_path" = "$repo_root" ] && continue
    local wt_dest="$wt_path/.cursor/rules"
    if $CHECK_MODE; then
      echo "  ↳ worktree: $(basename "$wt_path")"
      check_cursor_in "$wt_dest" || stale_count=$((stale_count + 1))
    else
      sync_cursor_to "$wt_dest"
      if ! $DRY_RUN; then echo "  ↳ worktree: $(basename "$wt_path")"; fi
    fi
    local_wt=$((local_wt + 1))
  done < <(git -C "$repo_root" worktree list --porcelain 2>/dev/null | grep '^worktree ' || true)
  wt_count=$((wt_count + local_wt))
}

# --- Main sync loop ---

repo_count=0
wt_count=0
stale_count=0
error_count=0
safe_backup_count=0
errors_summary=()

FORMATS_TO_RUN=()
if [[ "$FORMAT" == "all" ]]; then
  FORMATS_TO_RUN=("cursor" "claude")
else
  FORMATS_TO_RUN=("$FORMAT")
fi

for target in "${TARGETS[@]}"; do
  repo_root="$target"

  if ! validate_target "$repo_root"; then
    error_count=$((error_count + 1))
    errors_summary+=("$repo_root: target does not exist")
    continue
  fi

  # Core-tier stamps are not sync consumers — rules arrive via plugin.
  # Skipping here is the last-line defense when a residual registration
  # survives (full→core without re-init) or doctor has not yet flagged it.
  if [ -f "$repo_root/.house-rules-tier" ]; then
    target_tier="$(tr -d '[:space:]' < "$repo_root/.house-rules-tier")"
    if [[ "$target_tier" == "core" ]]; then
      echo "  – Skipping $repo_root (core tier stamp — not a sync consumer)"
      continue
    fi
  fi

  for fmt in "${FORMATS_TO_RUN[@]}"; do
    if ! sync_repo "$repo_root" "$fmt"; then
      if $CHECK_MODE; then
        stale_count=$((stale_count + 1))
      else
        error_count=$((error_count + 1))
        errors_summary+=("$repo_root ($fmt): sync failed")
      fi
    fi
    sync_worktrees "$repo_root" "$fmt"
  done
  repo_count=$((repo_count + 1))
done

# --- Summary ---

echo ""
fmt_label="$FORMAT"
ver_label=""
if [ -n "$PIN_VERSION" ]; then
  ver_label=" @ $PIN_VERSION"
elif [ -f "$KIT_ROOT/VERSION" ]; then
  ver_label=" @ v$(cat "$KIT_ROOT/VERSION" | tr -d '[:space:]')"
fi

if $DRY_RUN; then
  echo "[dry-run] Would sync ${#MDC_FILES[@]} rules ($fmt_label$ver_label) → $repo_count repos + $wt_count worktrees."
  echo "Re-run without --dry-run to apply."
elif $CHECK_MODE; then
  echo "Checked ${#MDC_FILES[@]} rules ($fmt_label$ver_label) across $repo_count repos + $wt_count worktrees."
  if [ $stale_count -gt 0 ]; then
    echo "$stale_count targets have stale or missing rules. Run without --check to sync."
  else
    echo "All targets up to date."
  fi
else
  echo "Done. ${#MDC_FILES[@]} rules ($fmt_label$ver_label) → $repo_count repos + $wt_count worktrees."
  if $SAFE_MODE && [ $safe_backup_count -gt 0 ]; then
    echo "$safe_backup_count file(s) backed up before overwrite or removal — .bak copies preserved."
  fi
fi

if [ $unmanaged_count -gt 0 ]; then
  echo ""
  echo "⚠ $unmanaged_count unmanaged rule file(s) left in place across all targets."
  echo "  These are not kit rules. The kit will not update or remove them."
fi

if [ $error_count -gt 0 ]; then
  echo ""
  echo "⚠ $error_count target(s) skipped due to errors:"
  for msg in "${errors_summary[@]}"; do
    echo "  - $msg"
  done
fi

if $CHECK_MODE && [ $stale_count -gt 0 ]; then
  exit 1
fi
if [ $error_count -gt 0 ]; then
  exit 1
fi
exit 0
