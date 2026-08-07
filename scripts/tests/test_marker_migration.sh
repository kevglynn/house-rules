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
check "agents-md fresh section: playbook-free" \
  bash -c "! grep -qi 'playbook' '$repo/AGENTS.md'"
check "agents-md fresh section: dispatcher-form commands only" \
  bash -c "grep -qF 'scripts/house-rules' '$repo/AGENTS.md' && ! grep -qE 'scripts/(init|doctor|sync-rules)\.sh' '$repo/AGENTS.md'"
sha1="$(sha256sum "$repo/AGENTS.md")"
out2="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md second run: byte-identical" test "$sha1" = "$sha2"
check "agents-md second run: says current" \
  out_has "$out2" "AGENTS.md house-rules section current"

# --- 3b. Stale version stamp: the section is present and well-formed but
#         stamped with an old kit version — init must refresh it in place
#         (one section, current stamp, user content intact). ---
sed -i 's/<!-- house-rules:version [^ ]* -->/<!-- house-rules:version 0.0.1 -->/' "$repo/AGENTS.md"
out3="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md stale stamp: reports the refresh" \
  out_has "$out3" "Refreshed AGENTS.md house-rules section"
check "agents-md stale stamp: still exactly one section" \
  count_is "$repo/AGENTS.md" "<!-- BEGIN house-rules:agents-md -->" 1
check "agents-md stale stamp: user section preserved" \
  file_has "$repo/AGENTS.md" "## User section stays"
check "agents-md stale stamp: stamp is current again" \
  bash -c "! grep -qF 'house-rules:version 0.0.1' '$repo/AGENTS.md'"

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
rc4=$?
check "claude-md orphan BEGIN: user content survives" \
  file_has "$h/CLAUDE.md" "## USER CONTENT SENTINEL"
check "claude-md orphan BEGIN: warns instead of rewriting" \
  out_has "$out" "malformed"
check "claude-md orphan BEGIN: does not claim Updated" \
  out_lacks "$out" "Updated block 'agent-identity'"
check "claude-md orphan BEGIN: exits nonzero (refusal is not success)" \
  test "$rc4" -ne 0

# --- 4b. Orphan BEGIN above a WELL-FORMED block in CLAUDE.md: a BEGIN seen
#         while a block is already open means the earlier BEGIN lost its
#         END — the rewrite must refuse, never swallow the user lines
#         between the orphan and the real block. ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN house-rules:agent-identity -->
orphan block, END marker lost
## CLAUDE NESTED SENTINEL
<!-- BEGIN house-rules:agent-identity -->
stale body forces the replace path
<!-- END house-rules:agent-identity -->
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
rc4b=$?
check "claude-md nested BEGIN: user content between markers survives" \
  file_has "$h/CLAUDE.md" "## CLAUDE NESTED SENTINEL"
check "claude-md nested BEGIN: warns malformed" \
  out_has "$out" "malformed"
check "claude-md nested BEGIN: does not claim Updated" \
  out_lacks "$out" "Updated block 'agent-identity'"
check "claude-md nested BEGIN: exits nonzero" \
  test "$rc4b" -ne 0

# --- 5. Orphan BEGIN in rc file at install: the block reads as present but
#        stale, so install takes the refresh path — whose rewrite loop must
#        refuse the malformed markers and leave the rc untouched (truncation
#        would eat everything below the orphan BEGIN). Same guard is
#        exercised on uninstall (case 8). ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
truncated, END lost
export USER_SENTINEL=1
EOF
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc5=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc orphan BEGIN at install: user content survives" \
  file_has "$h/.bashrc" "export USER_SENTINEL=1"
check "rc orphan BEGIN at install: rc left byte-identical" \
  test "$sha1" = "$sha2"
check "rc orphan BEGIN at install: warns malformed instead of rewriting" \
  out_has "$out" "malformed"
check "rc orphan BEGIN at install: exits nonzero (refusal is not success)" \
  test "$rc5" -ne 0

# --- 5b. Stale-but-well-formed rc block at install: the body changed across
#         kit versions (v0.3.0 dispatcher cut renamed the sourced file), so
#         a present block with an old body must be refreshed in place —
#         current body, still exactly one block, neighbors intact. ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
export USER_ABOVE=1
# BEGIN house-rules:aliases
[ -f "$HOME/.playbook-aliases.sh" ] && . "$HOME/.playbook-aliases.sh"
# END house-rules:aliases
export USER_BELOW=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
check "rc stale block: refreshed to current body" \
  file_has "$h/.bashrc" ".house-rules-aliases.sh"
check "rc stale block: old body gone" \
  bash -c "! grep -qF '.playbook-aliases.sh' '$h/.bashrc'"
check "rc stale block: still exactly one block" \
  count_is "$h/.bashrc" "# BEGIN house-rules:aliases" 1
check "rc stale block: neighbors intact" \
  bash -c "grep -qF 'export USER_ABOVE=1' '$h/.bashrc' && grep -qF 'export USER_BELOW=1' '$h/.bashrc'"
check "rc stale block: reports the refresh" \
  out_has "$out" "Refreshed the source block"

# --- 5c. Orphan BEGIN above a WELL-FORMED block at install: the currency
#         check reads the file as stale, so install takes the refresh path;
#         the scan opens at the orphan and would swallow the real block plus
#         every user line between — a BEGIN seen while a block is open must
#         make the rewrite refuse, never delete. ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN house-rules:aliases
export USER_BETWEEN=1
# BEGIN house-rules:aliases
[ -f "$HOME/.playbook-aliases.sh" ] && . "$HOME/.playbook-aliases.sh"
# END house-rules:aliases
export USER_BELOW_2=1
EOF
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc5c=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc nested BEGIN at install: user content between markers survives" \
  file_has "$h/.bashrc" "export USER_BETWEEN=1"
check "rc nested BEGIN at install: rc left byte-identical" \
  test "$sha1" = "$sha2"
check "rc nested BEGIN at install: warns malformed" \
  out_has "$out" "malformed"
check "rc nested BEGIN at install: exits nonzero" \
  test "$rc5c" -ne 0

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

# --- 6b. Orphan BEGIN above a WELL-FORMED section with a stale stamp: the
#         stamp check forces the refresh path; the scan must refuse at the
#         nested BEGIN instead of swallowing the user lines between. ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
<!-- BEGIN house-rules:agents-md -->
orphan, END lost
## AGENTS NESTED SENTINEL
<!-- BEGIN house-rules:agents-md -->
old body
<!-- house-rules:version 0.0.1 -->
<!-- END house-rules:agents-md -->
EOF
sha1="$(sha256sum "$repo/AGENTS.md")"
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
rc6b=$?
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md nested BEGIN: user content between markers survives" \
  file_has "$repo/AGENTS.md" "## AGENTS NESTED SENTINEL"
check "agents-md nested BEGIN: file left byte-identical" \
  test "$sha1" = "$sha2"
check "agents-md nested BEGIN: warns malformed" \
  out_has "$out" "malformed"
check "agents-md nested BEGIN: init exits nonzero" \
  test "$rc6b" -ne 0

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
rc8=$?
check "uninstall orphan BEGIN: user content survives" \
  file_has "$h/.bashrc" "export UNINSTALL_SENTINEL=1"
check "uninstall orphan BEGIN: warns instead of removing" \
  out_has "$out" "malformed"
check "uninstall orphan BEGIN: does not claim nothing-to-remove" \
  out_lacks "$out" "Nothing to remove"
check "uninstall orphan BEGIN: exits nonzero" \
  test "$rc8" -ne 0

# --- 9. CRLF rc block at install: the substring presence check fires but
#        the line-exact scan consumes nothing — must refuse, leave the file
#        byte-identical, and NOT exit 0 claiming the aliases are active. ---
h="$(new_home)"
printf '%s\r\n' \
  "# BEGIN house-rules:aliases" \
  "crlf body" \
  "# END house-rules:aliases" > "$h/.bashrc"
sha1="$(sha256sum "$h/.bashrc")"
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
rc9=$?
sha2="$(sha256sum "$h/.bashrc")"
check "rc crlf block: left byte-identical" \
  test "$sha1" = "$sha2"
check "rc crlf block: warns malformed" \
  out_has "$out" "malformed"
check "rc crlf block: exits nonzero" \
  test "$rc9" -ne 0

echo ""
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]
