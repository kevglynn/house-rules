#!/usr/bin/env bash
set -uo pipefail

# Installs the kit's "global safety net" — condensed, per-machine rule
# blocks that apply even in repos never bootstrapped with init.sh.
#
# Writes marker-delimited blocks into ~/CLAUDE.md (idempotent) and emits a
# combined paste snippet for Cursor's Global Preferences user rule
# (Cursor's user-rules storage lives in app settings and isn't safe to
# edit cross-platform from a script).
#
# Block sources live in global-safety-net/<id>.md (one file per concern).
# Adding a new concern = add a file + append its id to BLOCKS below.
#
# Usage:
#   ./scripts/install-global-safety-net.sh              # Install / update all blocks
#   ./scripts/install-global-safety-net.sh --check      # Report status, no writes
#   ./scripts/install-global-safety-net.sh --uninstall  # Remove managed blocks
#   ./scripts/install-global-safety-net.sh --print-cursor-snippet  # Re-print paste artifact
#   ./scripts/install-global-safety-net.sh --help

KIT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib/marker-rewrite.sh
. "$KIT_ROOT/scripts/lib/marker-rewrite.sh"
SAFETY_NET_DIR="$KIT_ROOT/global-safety-net"
CLAUDE_MD="$HOME/CLAUDE.md"
CURSOR_SNIPPET_FILE="$SAFETY_NET_DIR/cursor-snippet.generated.md"
MODE="install"

# Registry of block ids, in the order they should appear in ~/CLAUDE.md and
# in the Cursor paste snippet. Each id must have a matching source file at
# $SAFETY_NET_DIR/<id>.md. To add a concern, create the file and add the id.
BLOCKS=(
  "agent-identity"
  "session-start"
  "agent-protocol"
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)     MODE="check"; shift ;;
    --uninstall) MODE="uninstall"; shift ;;
    --print-cursor-snippet) MODE="print-snippet"; shift ;;
    -h|--help)
      cat <<'EOF'
Installs the kit's global safety net (per-machine agent rule blocks).

Usage: install-global-safety-net.sh [options]

Modes:
  (default)                 Install or update all registered blocks in
                            ~/CLAUDE.md and regenerate the Cursor paste
                            snippet at global-safety-net/cursor-snippet.generated.md.
  --check                   Report whether every block is present and current.
                            Exit 0 = all current, 1 = missing or stale.
  --uninstall               Remove all registered blocks from ~/CLAUDE.md.
  --print-cursor-snippet    Print the combined paste snippet for manual
                            Cursor user-rules paste (no writes).
  --help                    Show this help.

What this is for:
  Per-repo .cursor/rules/ only apply in bootstrapped projects. A fresh repo
  without the rules sees the agent revert to its base-model defaults —
  including human-baseline estimation and no discoverability of the
  kit itself. This script installs the condensed blocks at the
  per-machine level so they apply everywhere.

  Re-run any time to pick up content updates. Run --check in CI or the
  doctor script.
EOF
      exit 0
      ;;
    *) echo "Unknown option: $1 (use --help)" >&2; exit 1 ;;
  esac
done

# --- Block rendering ---

# Marker prefix is "house-rules:" (final kit name, decision 0001 A1).
# Recognition of the predecessor playbook's legacy marker prefix was
# sunset 2026-08-06 (process-kit-26b) after a field sweep showed zero
# old-marker blocks remaining on this machine's artifacts.
marker_begin() { printf '<!-- BEGIN house-rules:%s -->' "$1"; }
marker_end()   { printf '<!-- END house-rules:%s -->' "$1"; }

block_source_path() { printf '%s/%s.md' "$SAFETY_NET_DIR" "$1"; }

# Render a single block wrapped in markers.
render_block() {
  local id="$1"
  local src
  src="$(block_source_path "$id")"
  if [ ! -f "$src" ]; then
    echo "ERROR: missing block source: $src" >&2
    return 1
  fi
  marker_begin "$id"
  printf '\n'
  cat "$src"
  marker_end "$id"
  printf '\n'
}

# --- Per-block queries over ~/CLAUDE.md ---

has_block() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 1
  grep -qF "$(marker_begin "$id")" "$CLAUDE_MD"
}

current_block_content() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 1
  local begin end in_block=0
  begin="$(marker_begin "$id")"
  end="$(marker_end "$id")"
  while IFS= read -r line || [ -n "$line" ]; do
    if [ "$line" = "$begin" ]; then in_block=1; fi
    [ $in_block -eq 1 ] && printf '%s\n' "$line"
    if [ "$line" = "$end" ]; then in_block=0; fi
  done < "$CLAUDE_MD"
}

block_is_current() {
  local id="$1"
  local want have
  want="$(render_block "$id")" || return 1
  have="$(current_block_content "$id")"
  [ -n "$have" ] && [ "${have%$'\n'}" = "${want%$'\n'}" ]
}

# Whole-file preflight before multi-id walks (shared helper).
claude_md_markers_ok() {
  marker_html_stream_ok "$CLAUDE_MD"
}

claude_md_refuse_malformed() {
  echo "⚠ $CLAUDE_MD: house-rules markers are malformed (unpaired/nested/cross-ID BEGIN/END or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
}

# --- Single-block write operations (multi-pass: one file rewrite per block) ---

# Writer return codes (shared by the block writers): 0 = written,
# 1 = I/O failure (mktemp/write/mv — callers must fail loud, process-kit-e71),
# 2 = malformed markers (deliberate warn-and-skip, file untouched — the
# process-kit-0em guard contract).
append_block_new() {
  local id="$1"
  local tmp
  tmp="$(mktemp "${CLAUDE_MD}.tmp.XXXXXX")" || return 1
  {
    if [ ! -f "$CLAUDE_MD" ]; then
      printf '# CLAUDE.md\n\n'
      printf 'This file provides per-machine guidance to agents (read by Claude Code and surfaced to other agents via hooks).\n\n'
    else
      cat "$CLAUDE_MD"
      # Ensure trailing newline before appending
      [ -n "$(tail -c1 "$CLAUDE_MD" 2>/dev/null)" ] && printf '\n'
    fi
    render_block "$id"
    printf '\n'
  } > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$CLAUDE_MD" || { rm -f "$tmp"; return 1; }
}

# Strip every copy of the block; with `emit`, re-emit at the first BEGIN
# (position preserved). Shared scan/refusal: scripts/lib/marker-rewrite.sh.
rewrite_block() {
  local id="$1" emit="${2:-}"
  if [ -n "$emit" ]; then
    marker_rewrite_file "$CLAUDE_MD" "$(marker_begin "$id")" "$(marker_end "$id")" \
      html "block '$id' markers" render_block "$id"
  else
    marker_rewrite_file "$CLAUDE_MD" "$(marker_begin "$id")" "$(marker_end "$id")" \
      html "block '$id' markers"
  fi
}

remove_block() {
  local id="$1"
  [ -f "$CLAUDE_MD" ] || return 0
  has_block "$id" || return 0
  rewrite_block "$id"
}

# --- Cursor paste snippet ---

render_all_blocks() {
  local first=1
  for id in "${BLOCKS[@]}"; do
    if [ $first -eq 1 ]; then first=0; else printf '\n'; fi
    render_block "$id"
  done
}

write_cursor_snippet() {
  mkdir -p "$SAFETY_NET_DIR" || return 1
  render_all_blocks > "$CURSOR_SNIPPET_FILE"
}

print_cursor_instructions() {
  cat <<EOF

──────────────────────────────────────────────────────────────────────────
  CURSOR USER RULES — CHECK BEFORE PASTING (once per machine)
──────────────────────────────────────────────────────────────────────────

FIRST check whether Cursor is already importing ~/CLAUDE.md for you:
open Cursor → Settings → Rules and look for an auto-imported rule named
"CLAUDE" whose content matches ~/CLAUDE.md. It appears when the setting
"Include Third-Party Plugins, Skills, and Other Configs" is enabled.

If that rule is PRESENT, skip the paste entirely. The import already
carries these blocks into every Cursor conversation and re-reads
~/CLAUDE.md when Cursor restarts, so a manual paste would inject a
duplicate copy that goes stale after every kit update. Never edit and
save the imported rule in the settings UI (save semantics are
undocumented and may fork it from the file) — edit ~/CLAUDE.md via this
script and restart Cursor. Note the import is undocumented Cursor
behavior (observed 2026-08); if a future release drops it and the
CLAUDE rule disappears from settings, fall back to the paste below.

If that rule is ABSENT, paste the combined block below into:

  Cursor → Settings → Rules for AI → User Rules

(Add to existing content; don't replace it. Look for the BEGIN/END
markers to find and update it on future re-runs.)

The full snippet is also saved at:
  $CURSOR_SNIPPET_FILE

You can recall it any time with:
  cat "$CURSOR_SNIPPET_FILE"
  # or
  bash "$KIT_ROOT/scripts/install-global-safety-net.sh" --print-cursor-snippet

────────────────── PASTE BELOW THIS LINE ───────────────────────
EOF
  render_all_blocks
  cat <<'EOF'
────────────────── PASTE ABOVE THIS LINE ───────────────────────

The paste (when needed at all) is once per machine. The ~/CLAUDE.md
blocks above stay in sync via this script; the auto-imported CLAUDE
rule follows them on Cursor restart. Only a manual paste needs hand
maintenance: if you re-run the installer and block content has
drifted, re-run with --print-cursor-snippet to grab the fresh text.

EOF
}

# --- Dispatch ---

# Verify all source files exist before any mode runs.
# Use exit 1 (generic error). Exit 2 is reserved for doctor.sh's
# "bootstrap_needed" contract — agents dispatching on exit codes from
# this script must not be misled into running init.sh.
for id in "${BLOCKS[@]}"; do
  src="$(block_source_path "$id")"
  if [ ! -f "$src" ]; then
    echo "ERROR: block source missing for '$id' at $src" >&2
    echo "  Registry in this script lists '$id' but the file is absent." >&2
    exit 1
  fi
done

case "$MODE" in
  check)
    if ! claude_md_markers_ok; then
      claude_md_refuse_malformed
      exit 1
    fi
    missing=0
    stale=0
    for id in "${BLOCKS[@]}"; do
      if ! has_block "$id"; then
        echo "✗ Block '$id' not installed in $CLAUDE_MD"
        missing=$((missing + 1))
      elif ! block_is_current "$id"; then
        echo "⚠ Block '$id' present but out of date in $CLAUDE_MD"
        stale=$((stale + 1))
      else
        echo "✓ Block '$id' installed and current"
      fi
    done
    if [ $missing -gt 0 ] || [ $stale -gt 0 ]; then
      echo ""
      echo "  Fix: bash $(cd "$(dirname "$0")" && pwd)/install-global-safety-net.sh"
      exit 1
    fi
    exit 0
    ;;

  uninstall)
    if ! claude_md_markers_ok; then
      claude_md_refuse_malformed
      exit 1
    fi
    removed=0
    failed=0
    refused=0
    for id in "${BLOCKS[@]}"; do
      if has_block "$id"; then
        remove_block "$id"
        case $? in
          0)
            echo "✓ Removed block '$id' from $CLAUDE_MD"
            removed=$((removed + 1))
            ;;
          2)
            # Malformed markers: warned on stderr, file untouched (0em
            # contract) — the block is still there; count it so the exit
            # code says the uninstall did not finish.
            refused=$((refused + 1))
            ;;
          *)
            echo "✗ Failed to rewrite $CLAUDE_MD removing block '$id' (write error — check permissions)" >&2
            failed=$((failed + 1))
            ;;
        esac
      fi
    done
    if [ $removed -eq 0 ] && [ $failed -eq 0 ] && [ $refused -eq 0 ]; then
      echo "  No managed blocks found in $CLAUDE_MD (nothing to do)"
    fi
    if [ $refused -gt 0 ]; then
      echo "⚠ $refused block(s) were NOT removed (malformed markers — see warnings above; repair the marker lines and re-run)" >&2
    fi
    echo ""
    echo "Note: if you previously pasted the snippet into Cursor's user"
    echo "rules, remove it manually via Cursor → Settings → Rules for AI."
    echo "(An auto-imported CLAUDE rule needs no action — it follows the"
    echo "file ~/CLAUDE.md on the next Cursor restart.)"
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;

  print-snippet)
    render_all_blocks
    exit 0
    ;;

  install)
    echo "=== Installing global safety net ==="
    echo ""

    if ! claude_md_markers_ok; then
      claude_md_refuse_malformed
      exit 1
    fi

    failed=0
    refused=0
    for id in "${BLOCKS[@]}"; do
      if ! has_block "$id"; then
        if append_block_new "$id"; then
          echo "✓ Added block '$id' to $CLAUDE_MD"
        else
          echo "✗ Failed to write block '$id' to $CLAUDE_MD (write error — check permissions)" >&2
          failed=$((failed + 1))
        fi
      elif block_is_current "$id"; then
        echo "✓ Block '$id' is already current (no changes)"
      else
        rewrite_block "$id" emit
        case $? in
          0) echo "✓ Updated block '$id' in $CLAUDE_MD" ;;
          2)
            # Malformed markers: warned on stderr, file untouched (0em
            # contract) — the block stays stale; count it so the exit
            # code says the install did not finish.
            refused=$((refused + 1))
            ;;
          *)
            echo "✗ Failed to rewrite block '$id' in $CLAUDE_MD (write error — check permissions)" >&2
            failed=$((failed + 1))
            ;;
        esac
      fi
    done

    if write_cursor_snippet; then
      echo "✓ Wrote combined Cursor paste snippet to $CURSOR_SNIPPET_FILE"
    else
      echo "✗ Failed to write Cursor paste snippet to $CURSOR_SNIPPET_FILE" >&2
      failed=$((failed + 1))
    fi

    print_cursor_instructions

    echo "=== Done ==="
    echo ""
    echo "Verify anytime: bash $(cd "$(dirname "$0")" && pwd)/install-global-safety-net.sh --check"
    if [ $refused -gt 0 ]; then
      echo "⚠ $refused block(s) were NOT updated (malformed markers — see warnings above); repair the marker lines in $CLAUDE_MD and re-run" >&2
    fi
    if [ $failed -gt 0 ]; then
      echo "✗ $failed write failure(s) above — the ✗-marked items were NOT installed" >&2
    fi
    [ $((failed + refused)) -gt 0 ] && exit 1
    exit 0
    ;;
esac
