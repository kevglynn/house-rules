#!/usr/bin/env bash
# demo-cases.sh — SPIKE demonstration cases (process-kit-vgz).
# Real commit messages from this repo's `git log` and real close reasons
# from `bd show`, plus synthetic negatives. Asserts expected exit codes.
# Usage: bash demo-cases.sh   (exit 0 = all cases behave as expected)

set -u
cd "$(dirname "$0")"
CHECK="python3 ./conventions"
pass=0; fail=0

case_expect() { # expect <exit-code> <label> <cmd...>
  local want="$1" label="$2"; shift 2
  "$@" >/dev/null 2>&1
  local got=$?
  if [ "$got" -eq "$want" ]; then
    echo "ok   [$label] exit $got"
    pass=$((pass+1))
  else
    echo "FAIL [$label] wanted exit $want, got $got"
    fail=$((fail+1))
  fi
}

echo "--- commit messages (real, from git log --oneline) ---"
case_expect 0 "real-commit-chore" $CHECK check-commit \
  "chore: enable validation.on-create warn in kit repo (process-kit-qxc)"
case_expect 0 "real-commit-feat" $CHECK check-commit \
  "feat: tdd-ledger CLI — durable red-then-green evidence + CI verify"
# SPIKE FINDING: this REAL commit (0fcdb1d) violates the repo's own prose
# rule — its summary is 87 chars against the "under 72" cap. Kept as an
# expected-fail case: it is live proof the prose convention is unenforced.
case_expect 1 "real-commit-fix-overlong" $CHECK check-commit \
  "fix: packet verifier strip check scans the grid structurally, not 1800 chars (segnolabs-cga)"
# Negatives
case_expect 1 "bad-type" $CHECK check-commit "wip: half-done stuff"
case_expect 1 "no-colon-format" $CHECK check-commit "added loading spinner"
case_expect 1 "summary-too-long" $CHECK check-commit \
  "docs: this summary deliberately rambles on far past the seventy-two character cap to trip the length check"

echo "--- branch names ---"
case_expect 0 "rule-example-branch" $CHECK check-branch "feat/gastown-abc-loading-ux"
# `spike` is not in the profile's type list — the prose never granted it.
case_expect 1 "spike-not-a-branch-type" $CHECK check-branch "spike/process-kit-vgz-profile-projection"
case_expect 1 "no-slash" $CHECK check-branch "main"
case_expect 1 "uppercase-slug" $CHECK check-branch "fix/Process-Kit-ABC-Thing"

echo "--- close reasons (real, from bd show) ---"
# Real task close (process-kit-815): commit ref + AC mapping — passes.
case_expect 0 "real-task-close" $CHECK check-close --type task \
  "Commit 52b45df, reviewed by coordinator. AC1: docs/README.md Directory index table covers specs/, research/, refinements/, decisions/. AC2: glossary gained 7 entries."
# Real feature close (process-kit-0ei): commits + AC mapping — passes.
case_expect 0 "real-feature-close" $CHECK check-close --type feature \
  "Commits 515bb21 (impl) + 92589d6 (tier1 fixes) on main. AC1: record-failing/record-passing append JSONL entries, verify exits 0 clean / 1 with named reasons."
# Real spike close (process-kit-2k9): won't-do with findings — passes.
case_expect 0 "real-spike-close" $CHECK check-close --type spike \
  "Closed as won't-do/obsolete (Planner decision): the spike's premise was eliminated by process-kit-amq (commit c816f2e)."
# Real epic close (process-kit-6hx): children closed + evidence — passes.
case_expect 0 "real-epic-close" $CHECK check-close --type epic \
  "All 5 children closed with commit-mapped evidence (815: 52b45df, opk: ed67eb9). Success criterion 1 met."
# Docs bead with the prescribed N/A marker — passes.
case_expect 0 "docs-na-close" $CHECK check-close --type docs \
  "N/A — documentation update, no verification needed. Commit 52b45df."
# Negatives
case_expect 1 "vague-done" $CHECK check-close --type feature "Done"
case_expect 1 "no-commit-ref" $CHECK check-close --type bug \
  "AC1: fixed the crash, test_login passes now."
case_expect 1 "iou-phrase" $CHECK check-close --type feature \
  "Commit a1b2c3f. AC1 will be verified later in the PR manual-check pass."
# Sanctioned deferral form is exempt from the IOU scan.
case_expect 0 "sanctioned-deferral" $CHECK check-close --type feature \
  "Commit a1b2c3f. AC1: spinner renders (verified). AC2 deferred to bead process-kit-xyz."
case_expect 1 "unknown-bead-type" $CHECK check-close --type gizmo "Commit a1b2c3f. AC1: done."

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
