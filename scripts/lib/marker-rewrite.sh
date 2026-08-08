# Shared house-rules marker scan + refusal for the three installers.
# Sourced from KIT_ROOT (each installer remains a standalone bash script).
#
# Contract for marker_rewrite_file: 0 = written, 1 = I/O failure,
# 2 = malformed markers (warn-and-skip, file untouched).

# Return 0 if LINE is any HTML house-rules BEGIN/END marker line (prefix
# match — includes near-miss trailing junk that still starts with the
# marker prefix).
_marker_is_html_hr_line() {
  case "$1" in
    '<!-- BEGIN house-rules:'*|'<!-- END house-rules:'*) return 0 ;;
    *) return 1 ;;
  esac
}

# Same for rc-style `# BEGIN/END house-rules:` markers.
_marker_is_rc_hr_line() {
  case "$1" in
    '# BEGIN house-rules:'*|'# END house-rules:'*) return 0 ;;
    *) return 1 ;;
  esac
}

# Rewrite PATH: strip every exact BEGIN/END pair; if EMIT_FN is non-empty,
# re-emit its output at the first BEGIN (position preserved).
#
# Usage:
#   marker_rewrite_file <path> <begin> <end> <html|rc> <warn_what> [emit_fn [emit_arg]]
#
# warn_what is the phrase after "path: " in the refusal warning
# (e.g. "block 'foo' markers", "alias block markers").
marker_rewrite_file() {
  local path="$1" begin="$2" end="$3" style="$4" warn_what="$5"
  local emit_fn="${6:-}" emit_arg="${7:-}"
  local tmp in_block=0 consumed=0 malformed=0 line

  tmp="$(mktemp "${path}.tmp.XXXXXX")" || return 1

  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ]; then
      if [ "$line" = "$begin" ]; then
        in_block=1
        if [ -n "$emit_fn" ] && [ $consumed -eq 0 ]; then
          if [ -n "$emit_arg" ]; then
            "$emit_fn" "$emit_arg"
          else
            "$emit_fn"
          fi
        fi
        consumed=1
        continue
      fi
      # Orphan END for this pair is malformed grammar — refuse rather
      # than copy it through and claim a clean rewrite.
      if [ "$line" = "$end" ]; then
        malformed=1
        break
      fi
      printf '%s\n' "$line"
      continue
    fi
    # in_block=1: only the exact END closes cleanly. Any other managed
    # marker (nested/cross-ID BEGIN/END, near-miss END with trailing
    # whitespace) means the scan would discard user bytes — refuse.
    if [ "$line" = "$end" ]; then
      in_block=0
      continue
    fi
    if [ "$style" = "rc" ]; then
      if _marker_is_rc_hr_line "$line"; then
        malformed=1
        break
      fi
    else
      if _marker_is_html_hr_line "$line"; then
        malformed=1
        break
      fi
    fi
    continue
  done < "$path" > "$tmp"

  # Refuse when unpaired BEGIN (still open at EOF), nested/cross-ID/
  # near-miss, orphan END, or no BEGIN consumed (e.g. CRLF markers).
  if [ $in_block -eq 1 ] || [ $consumed -eq 0 ] || [ $malformed -eq 1 ]; then
    rm -f "$tmp"
    echo "⚠ $path: $warn_what are malformed (unpaired/nested/cross-ID BEGIN/END or not line-exact, e.g. CRLF); file left untouched — repair the marker lines manually" >&2
    return 2
  fi
  mv "$tmp" "$path" || { rm -f "$tmp"; return 1; }
}

# Whole-file HTML house-rules marker grammar check: flat sequence of
# well-formed, non-overlapping pairs. Used before multi-id walks so a
# later id's rewrite cannot destroy bytes nested under an earlier
# malformed block.
#
# Usage: marker_html_stream_ok <path>
# Returns 0 if ok (or path missing), 1 if malformed.
marker_html_stream_ok() {
  local path="$1"
  [ -f "$path" ] || return 0
  local in_block_id="" line id expected
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      '<!-- BEGIN house-rules:'*)
        id="${line#<!-- BEGIN house-rules:}"
        id="${id%% -->*}"
        if [ -n "$in_block_id" ]; then
          return 1
        fi
        expected="<!-- BEGIN house-rules:${id} -->"
        if [ "$line" != "$expected" ]; then
          return 1
        fi
        in_block_id="$id"
        ;;
      '<!-- END house-rules:'*)
        id="${line#<!-- END house-rules:}"
        id="${id%% -->*}"
        if [ -z "$in_block_id" ] || [ "$id" != "$in_block_id" ]; then
          return 1
        fi
        expected="<!-- END house-rules:${id} -->"
        if [ "$line" != "$expected" ]; then
          return 1
        fi
        in_block_id=""
        ;;
    esac
  done < "$path"
  [ -z "$in_block_id" ]
}

# Exactly one well-formed HTML section between BEGIN/END, containing
# NEEDLE as an exact line. Used for AGENTS.md stamp currency.
#
# Usage: marker_html_section_contains <path> <begin> <end> <needle>
# Returns 0 if current, 1 otherwise.
marker_html_section_contains() {
  local path="$1" begin="$2" end="$3" needle="$4"
  local in_block=0 count=0 found=0 line
  while IFS= read -r line || [ -n "$line" ]; do
    if [ $in_block -eq 0 ]; then
      if [ "$line" = "$begin" ]; then
        in_block=1
        count=$((count + 1))
        if [ "$count" -gt 1 ]; then
          return 1
        fi
        continue
      fi
      if [ "$line" = "$end" ]; then
        return 1
      fi
      continue
    fi
    if [ "$line" = "$end" ]; then
      in_block=0
      continue
    fi
    if _marker_is_html_hr_line "$line"; then
      return 1
    fi
    if [ "$line" = "$needle" ]; then
      found=1
    fi
  done < "$path"
  [ $in_block -eq 0 ] && [ "$count" -eq 1 ] && [ "$found" -eq 1 ]
}
