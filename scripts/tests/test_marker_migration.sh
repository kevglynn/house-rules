#!/usr/bin/env bash
# Fixture tests for the marker-rewrite loops in the three installers:
# fresh-install idempotency plus the malformed-marker guards (orphan BEGIN,
# CRLF markers) introduced by process-kit-0em. The legacy predecessor-prefix
# migration cases were retired with the migration machinery
# (process-kit-26b, sunset 2026-08-06); the guards outlive the migration —
# they protect current-marker files the same way. Heredoc fixtures +
# throwaway HOME per case; never touches the invoking user's HOME. Run from
# anywhere:
#   bash scripts/tests/test_marker_migration.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SAFETY_NET="$KIT_ROOT/scripts/install-global-safety-net.sh"
ALIASES="$KIT_ROOT/scripts/install-aliases.sh"
INIT="$KIT_ROOT/scripts/init.sh"

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

# bd shim: this suite exercises marker-rewrite logic, not beads.
# the init preflight hard-fails when bd is absent (CI runners don't
# have it), so a no-op stub keeps the preflight green and makes local and
# CI runs behaviorally identical (process-kit-4ma).
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

file_has()      { grep -qF -- "$2" "$1"; }
out_has()       { grep -qF -- "$2" <<< "$1"; }
out_lacks()     { ! grep -qF -- "$2" <<< "$1"; }
count_is()      { [ "$(grep -cF -- "$2" "$1")" = "$3" ]; }

# --- 1. Fresh CLAUDE.md install: three current blocks around user content;
#        second run byte-identical ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
# CLAUDE.md

user preamble stays
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "claude-md fresh install: three current blocks" \
  count_is "$h/CLAUDE.md" "<!-- BEGIN house-rules:" 3
check "claude-md fresh install: says Added" \
  out_has "$out" "Added block"
check "claude-md fresh install: user content preserved" \
  file_has "$h/CLAUDE.md" "user preamble stays"
sha1="$(sha256sum "$h/CLAUDE.md")"
out2="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
sha2="$(sha256sum "$h/CLAUDE.md")"
check "claude-md second run: byte-identical" test "$sha1" = "$sha2"
check "claude-md second run: says already current" \
  out_has "$out2" "already current"

# --- 2. Fresh rc install: one block; user lines survive; idempotent ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
export USER_BEFORE=1
EOF
HOME="$h" bash "$ALIASES" --shell bash > /dev/null 2>&1
check "rc fresh install: exactly one current block" \
  count_is "$h/.bashrc" "# BEGIN house-rules:aliases" 1
check "rc fresh install: user lines preserved" \
  file_has "$h/.bashrc" "export USER_BEFORE=1"
sha1="$(sha256sum "$h/.bashrc")"
HOME="$h" bash "$ALIASES" --shell bash > /dev/null 2>&1
sha2="$(sha256sum "$h/.bashrc")"
check "rc second run: byte-identical" test "$sha1" = "$sha2"

# --- 3. Fresh AGENTS.md section via init.sh; idempotent second run ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
# AGENTS.md

## User section stays
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md fresh section: one current section" \
  count_is "$repo/AGENTS.md" "<!-- BEGIN house-rules:agents-md -->" 1
check "agents-md fresh section: user section preserved" \
  file_has "$repo/AGENTS.md" "## User section stays"
sha1="$(sha256sum "$repo/AGENTS.md")"
out2="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md second run: byte-identical" test "$sha1" = "$sha2"
check "agents-md second run: says current" \
  out_has "$out2" "AGENTS.md house-rules section current"

# --- 4. Orphan BEGIN (no END) in CLAUDE.md: user content below the orphan
#        marker must survive; the rewrite must refuse, not truncate ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN house-rules:agent-identity -->
truncated block, END marker lost
## USER CONTENT SENTINEL
important user notes that must not be deleted
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "claude-md orphan BEGIN: user content survives" \
  file_has "$h/CLAUDE.md" "## USER CONTENT SENTINEL"
check "claude-md orphan BEGIN: warns instead of rewriting" \
  out_has "$out" "malformed"
check "claude-md orphan BEGIN: does not claim Updated" \
  out_lacks "$out" "Updated block 'agent-identity'"

# --- 5. Orphan BEGIN in rc file at install: the installer treats the block
#        as present (substring detection) and must leave the rc untouched —
#        no rewrite path exists on install, so no truncation is possible.
#        The rewrite-loop refusal guard is exercised on uninstall (case 8). ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
truncated, END lost
export USER_SENTINEL=1
EOF
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
sha2="$(sha256sum "$h/.bashrc")"
check "rc orphan BEGIN at install: user content survives" \
  file_has "$h/.bashrc" "export USER_SENTINEL=1"
check "rc orphan BEGIN at install: rc left byte-identical" \
  test "$sha1" = "$sha2"

# --- 6. Orphan BEGIN in AGENTS.md: same guard via init.sh ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
<!-- BEGIN house-rules:agents-md -->
truncated, END lost
## AGENTS USER SENTINEL
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md orphan BEGIN: user content survives" \
  file_has "$repo/AGENTS.md" "## AGENTS USER SENTINEL"
check "agents-md orphan BEGIN: warns instead of rewriting" \
  out_has "$out" "malformed"

# --- 7. CRLF-marked CLAUDE.md block: substring detection fires but the
#        line-exact rewrite cannot consume it — must refuse honestly, never
#        claim Updated while changing nothing ---
h="$(new_home)"
printf '%s\r\n' \
  "<!-- BEGIN house-rules:agent-identity -->" \
  "crlf body" \
  "<!-- END house-rules:agent-identity -->" > "$h/CLAUDE.md"
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "crlf block: does not claim Updated" \
  out_lacks "$out" "Updated block"
check "crlf block: warns about malformed markers" \
  out_has "$out" "malformed"
# The other (absent) blocks may legitimately be appended; the CRLF block
# itself must remain byte-for-byte (both marker lines + body).
check "crlf block: left as-is" \
  count_is "$h/CLAUDE.md" "house-rules:agent-identity" 2

# --- 8. Uninstall with an orphan BEGIN: remove loops share the guard —
#        user content below the orphan marker survives ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
truncated, END lost
export UNINSTALL_SENTINEL=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash --uninstall 2>&1)"
check "uninstall orphan BEGIN: user content survives" \
  file_has "$h/.bashrc" "export UNINSTALL_SENTINEL=1"
check "uninstall orphan BEGIN: warns instead of removing" \
  out_has "$out" "malformed"

echo ""
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]
