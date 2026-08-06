#!/usr/bin/env bash
# Fixture tests for the legacy ai-dev-playbook -> house-rules marker
# migration (process-kit-0em) and the malformed-marker guards on the five
# marker-rewrite loops. Heredoc fixtures + throwaway HOME per case; never
# touches the invoking user's HOME. Run from anywhere:
#   bash scripts/tests/test_marker_migration.sh
set -u

KIT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SAFETY_NET="$KIT_ROOT/scripts/install-global-safety-net.sh"
ALIASES="$KIT_ROOT/scripts/install-aliases.sh"
INIT="$KIT_ROOT/scripts/playbook-init.sh"

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
file_lacks()    { ! grep -qF -- "$2" "$1"; }
out_has()       { grep -qF -- "$2" <<< "$1"; }
out_lacks()     { ! grep -qF -- "$2" <<< "$1"; }
count_is()      { [ "$(grep -cF -- "$2" "$1")" = "$3" ]; }

# --- 1. Legacy CLAUDE.md migrates in place: zero legacy markers, three
#        current blocks, second run byte-identical ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
# CLAUDE.md

user preamble stays

<!-- BEGIN ai-dev-playbook:agent-identity -->
old body one
<!-- END ai-dev-playbook:agent-identity -->

<!-- BEGIN ai-dev-playbook:session-start -->
old body two
<!-- END ai-dev-playbook:session-start -->

<!-- BEGIN ai-dev-playbook:agent-protocol -->
old body three
<!-- END ai-dev-playbook:agent-protocol -->

user epilogue stays
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "claude-md legacy migrates: no legacy markers left" \
  file_lacks "$h/CLAUDE.md" "ai-dev-playbook"
check "claude-md legacy migrates: three current blocks" \
  count_is "$h/CLAUDE.md" "<!-- BEGIN house-rules:" 3
check "claude-md legacy migrates: says Migrated" \
  out_has "$out" "Migrated block"
check "claude-md legacy migrates: user content preserved" \
  file_has "$h/CLAUDE.md" "user epilogue stays"
sha1="$(sha256sum "$h/CLAUDE.md")"
out2="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
sha2="$(sha256sum "$h/CLAUDE.md")"
check "claude-md second run: byte-identical" test "$sha1" = "$sha2"
check "claude-md second run: says already current" \
  out_has "$out2" "already current"

# --- 2. Legacy rc block migrates in place; user lines survive; idempotent ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
export USER_BEFORE=1
# BEGIN ai-dev-playbook:aliases
[ -f "$HOME/.playbook-aliases.sh" ] && . "$HOME/.playbook-aliases.sh"
# END ai-dev-playbook:aliases
export USER_AFTER=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
check "rc legacy migrates: no legacy markers left" \
  file_lacks "$h/.bashrc" "ai-dev-playbook"
check "rc legacy migrates: exactly one current block" \
  count_is "$h/.bashrc" "# BEGIN house-rules:aliases" 1
check "rc legacy migrates: user lines preserved" \
  file_has "$h/.bashrc" "export USER_AFTER=1"
sha1="$(sha256sum "$h/.bashrc")"
HOME="$h" bash "$ALIASES" --shell bash > /dev/null 2>&1
sha2="$(sha256sum "$h/.bashrc")"
check "rc second run: byte-identical" test "$sha1" = "$sha2"

# --- 3. Legacy AGENTS.md section migrates in place via playbook-init ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
# AGENTS.md

<!-- BEGIN ai-dev-playbook:agents-md -->
<!-- ai-dev-playbook:version 0.0.9 -->
old section body
<!-- END ai-dev-playbook:agents-md -->

## User section stays
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md legacy migrates: no legacy markers left" \
  file_lacks "$repo/AGENTS.md" "ai-dev-playbook"
check "agents-md legacy migrates: one current section" \
  count_is "$repo/AGENTS.md" "<!-- BEGIN house-rules:agents-md -->" 1
check "agents-md legacy migrates: says Migrated" \
  out_has "$out" "Migrated legacy-marked AGENTS.md"
check "agents-md legacy migrates: user section preserved" \
  file_has "$repo/AGENTS.md" "## User section stays"
sha1="$(sha256sum "$repo/AGENTS.md")"
out2="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
sha2="$(sha256sum "$repo/AGENTS.md")"
check "agents-md second run: byte-identical" test "$sha1" = "$sha2"
check "agents-md second run: says current" \
  out_has "$out2" "AGENTS.md playbook section current"

# --- 4. Mixed generations (legacy + current same id) collapse to one ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN ai-dev-playbook:agent-identity -->
legacy copy
<!-- END ai-dev-playbook:agent-identity -->
<!-- BEGIN house-rules:agent-identity -->
newer copy
<!-- END house-rules:agent-identity -->
EOF
HOME="$h" bash "$SAFETY_NET" > /dev/null 2>&1
check "mixed generations: single agent-identity block" \
  count_is "$h/CLAUDE.md" "<!-- BEGIN house-rules:agent-identity -->" 1
check "mixed generations: no legacy markers left" \
  file_lacks "$h/CLAUDE.md" "ai-dev-playbook"

# --- 5. Orphan legacy BEGIN (no END) in CLAUDE.md: user content below the
#        orphan marker must survive; the rewrite must refuse, not truncate ---
h="$(new_home)"
cat > "$h/CLAUDE.md" <<'EOF'
<!-- BEGIN ai-dev-playbook:agent-identity -->
truncated block, END marker lost
## USER CONTENT SENTINEL
important user notes that must not be deleted
EOF
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "claude-md orphan BEGIN: user content survives" \
  file_has "$h/CLAUDE.md" "## USER CONTENT SENTINEL"
check "claude-md orphan BEGIN: warns instead of migrating" \
  out_has "$out" "malformed"
check "claude-md orphan BEGIN: does not claim Migrated" \
  out_lacks "$out" "Migrated block 'agent-identity'"

# --- 6. Orphan legacy BEGIN in rc file: same guard ---
h="$(new_home)"
cat > "$h/.bashrc" <<'EOF'
# BEGIN ai-dev-playbook:aliases
truncated, END lost
export USER_SENTINEL=1
EOF
out="$(HOME="$h" bash "$ALIASES" --shell bash 2>&1)"
check "rc orphan BEGIN: user content survives" \
  file_has "$h/.bashrc" "export USER_SENTINEL=1"
check "rc orphan BEGIN: warns instead of migrating" \
  out_has "$out" "malformed"

# --- 7. Orphan legacy BEGIN in AGENTS.md: same guard via playbook-init ---
h="$(new_home)"
repo="$(mktemp -d)"
CLEANUP+=("$repo")
git -C "$repo" init -q
cat > "$repo/AGENTS.md" <<'EOF'
<!-- BEGIN ai-dev-playbook:agents-md -->
truncated, END lost
## AGENTS USER SENTINEL
EOF
out="$(cd "$repo" && HOME="$h" bash "$INIT" --tool cursor --no-hooks 2>&1)"
check "agents-md orphan BEGIN: user content survives" \
  file_has "$repo/AGENTS.md" "## AGENTS USER SENTINEL"
check "agents-md orphan BEGIN: warns instead of migrating" \
  out_has "$out" "malformed"

# --- 8. CRLF legacy CLAUDE.md: substring detection fires but the line-exact
#        rewrite cannot consume it — must refuse honestly, never claim
#        Migrated while changing nothing ---
h="$(new_home)"
printf '%s\r\n' \
  "<!-- BEGIN ai-dev-playbook:agent-identity -->" \
  "crlf body" \
  "<!-- END ai-dev-playbook:agent-identity -->" > "$h/CLAUDE.md"
out="$(HOME="$h" bash "$SAFETY_NET" 2>&1)"
check "crlf legacy: does not claim Migrated" \
  out_lacks "$out" "Migrated block"
check "crlf legacy: warns about malformed markers" \
  out_has "$out" "malformed"
# The other (absent) blocks may legitimately be appended; the CRLF legacy
# block itself must remain byte-for-byte (both marker lines + body).
check "crlf legacy: legacy block left as-is" \
  count_is "$h/CLAUDE.md" "ai-dev-playbook:agent-identity" 2

# --- 9. Uninstall with an orphan current BEGIN: remove loops share the
#        guard — user content below the orphan marker survives ---
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
