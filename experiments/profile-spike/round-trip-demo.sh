#!/usr/bin/env bash
# round-trip-demo.sh — SPIKE round-trip evidence (process-kit-vgz).
# One profile edit (add commit type `spike`) changes BOTH the checker
# verdict and the generated rule text, with no second edit anywhere.
# Usage: bash round-trip-demo.sh

set -eu
cd "$(dirname "$0")"
MSG="spike: profile-ize git grammar end-to-end (process-kit-vgz)"
EDITED=$(mktemp)
trap 'rm -f "$EDITED"' EXIT

echo "=== BEFORE (profile.yaml as committed) ==="
python3 ./conventions check-commit "$MSG" || true
python3 ./conventions render-rule | grep "Commit messages"

# The single edit: add `spike` to the commit type list.
sed 's/^  types: \[feat, fix, refactor, test, chore, docs\]$/  types: [feat, fix, refactor, test, chore, docs, spike]/' \
  profile.yaml > "$EDITED"
echo
echo "=== THE EDIT (one line) ==="
diff profile.yaml "$EDITED" || true

echo
echo "=== AFTER (same checker, same generator, edited profile) ==="
CONVENTIONS_PROFILE="$EDITED" python3 ./conventions check-commit "$MSG" || true
CONVENTIONS_PROFILE="$EDITED" python3 ./conventions render-rule | grep "Commit messages"
