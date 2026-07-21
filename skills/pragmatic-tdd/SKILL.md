---
name: pragmatic-tdd
description: Per-bead-type TDD playbooks — the operational procedure behind the pragmatic-tdd rule. Use when starting a bug/feature/refactor bead, when you need to write the failing test, or when proving red-then-green after the fact. Triggers on "pragmatic tdd", "starting a bug/feature/refactor bead", "write the failing test", "red-proof", "prove the test fails".
---

# Pragmatic TDD

The step-by-step playbooks for test-first work, by bead type. The goal is **signal**, not coverage (O17) — every test must be able to catch a real defect, or it should not exist. The always-on `pragmatic-tdd` rule states the obligations and exceptions; this skill is how you execute them.

This skill reads no overlay keys — the procedure is identical in every project.

## When to Use This Skill

Use this skill when:
- Implementing a **bug**, **feature**, **story**, or **refactor** bead
- You need to derive failing tests from acceptance criteria
- You wrote implementation before the test and need to prove the test would have failed (red-proof)
- A spike's prototype code is being promoted to a feature (the promoted work inherits the feature playbook)

Skip this skill when:
- Working a **spike** bead that stays investigative (deliverable is knowledge; tests optional)
- Working **decision**, **milestone**, **epic**, **chore**, **config**, or **docs** beads — no tests required; a test there is noise

The applicability policy (which bead types require tests, and the exceptions above) is owned by the always-on `pragmatic-tdd` rule. This skill carries the procedure for the types that qualify.

## Core Process

Where the evidence ledger is distributed (`scripts/tdd-ledger` in
kit-bootstrapped repos), record every observed red and green as you go —
`record-failing` the moment a required test fails, `record-passing` when it
passes — not only in the recovery ceremony below. The happy path produces
ledger evidence too.

### Bug beads — test first, always (O1–O5)

1. Write a test that reproduces the bug (the test MUST fail on the current code) (O1)
2. Verify the test fails for the right reason (feature missing, not typo/import error) (O2)
3. Write the minimal fix (O3)
4. Verify the test passes (O4)
5. **Scan for the bug pattern class across the codebase** (`rg`/`grep` for the anti-pattern, not the specific line). The bug often lives in more than one site — inlined at callsites, duplicated in sibling helpers, or copy-pasted into similar code. Fix every matching site in the same bead, or file follow-up beads before closing. Your reproducing test should fail on every unfixed site; if it doesn't, the test is scoped too narrowly. (O5)

A test that reproduces the bug proves the fix addresses the actual failure mode — but only for the site the test exercises. Step 5 is what prevents the "fixed one of three, shipped two" failure mode.

### Feature beads — ACs become tests (O6–O7)

1. Read the `--acceptance` criteria from the bead
2. Write failing tests that assert each AC (observable behavior, not internals) (O6)
3. Verify tests fail
4. Implement to make them pass
5. Verify all tests pass

### Story beads — same as feature beads (O8)

ACs become tests. Treat stories identically to feature beads.

### Refactor beads — safety net first (O9)

1. Check if behavioral tests already exist for the code being refactored
2. If not, write them BEFORE changing structure (test current behavior)
3. Refactor
4. Verify all behavioral tests still pass

The behavior shouldn't change — only the structure. Tests prove that.

## The red-proof ceremony (O16)

Evidence, not penance. The goal is proving the test catches the problem — not ritually deleting code. If you wrote implementation before the test:

1. Stash or revert the implementation change
2. Run the test
3. Confirm it fails — and fails for the right reason
4. Re-apply the change and confirm the test passes

The evidence that matters: the test fails without the fix and passes with it. How you obtain that evidence is flexible; that you obtain it is not.

**Durable form — the evidence ledger.** Record the red and green runs with `scripts/tdd-ledger` (distributed to `scripts/` in kit-bootstrapped repos): `tdd-ledger record-failing --test-id <id> --bead <bead-id> --output <test output>` at step 3, and `tdd-ledger record-passing` with the same ids at step 4. This appends to a committed `.tdd-ledger.jsonl`; `tdd-ledger verify` (run by CI where present) checks that every green has a prior red — converting the ceremony's evidence from close-reason prose into checkable data. Note: the CI workflow only actually blocks merges if the repo marks it as a required status check via branch protection — otherwise a red `verify` is advisory.

## Zero-signal test taxonomy — DO NOT WRITE THESE (O14)

Check every test you author against these five classes before it ships. (The tier1 test-signal review lens detects the same five classes by the same names — shared vocabulary is deliberate.)

1. **Testing mocks, not behavior.** `verify(mockService).fetchData(argX)` — proves the plumbing is connected, not that the feature works. If the mock changes, the test breaks. If the feature breaks, the test passes.

2. **Testing implementation details.** `expect(internalCache.size).toBe(3)` — breaks on any refactor, catches no real bugs. Tests should assert what the user/caller observes, not how the internals work.

3. **Testing what the type system enforces.** `expect(typeof getName()).toBe('string')` — TypeScript already does this. The test adds maintenance cost with zero signal.

4. **Tautological tests.** Agent writes `add(a, b) { return a + b }`, then writes `expect(add(2,3)).toBe(5)`. The test is a restatement of the implementation. It will never catch a real bug.

5. **Helper-only tests that skip the original callsite.** Fixing a bug by extracting or editing a pure helper and then testing the helper in isolation does not prove the bug is fixed at the callsite that triggered it. If the bug was reproduced via `foo()`, the regression test must drive `foo()` — or exercise the helper in the exact shape `foo()` uses it. Testing the helper alone leaves the original failure mode unprotected, and the fix may not even reach the callsite (e.g., if the callsite inlines the bug pattern rather than calling the helper). Pair this with step 5 of the bug-bead playbook to catch duplicated pattern sites.

**The guardrail (O15):** If a test would pass whether or not the feature actually works correctly, it's zero signal. Don't write it. (The rule states this verbatim too — advisory and procedural layers agree by construction.)

## Anti-Patterns

| Anti-Pattern | Why It Fails | Better Approach |
|--------------|-------------|-----------------|
| Skipping red | A test that never failed proves nothing — it may not exercise the bug at all | Write the test first; if you didn't, run the red-proof ceremony |
| Ritual code deletion | Deleting working code to "do TDD properly" wastes the work for zero extra evidence | Stash/revert, prove red, re-apply (O16) |
| Fixed one of three, shipped two | The reproducing test covers one site; sibling sites keep the bug | Pattern-class scan (bug step 5) before close |
| Testing the mock | Test passes when the feature is broken | Assert observable behavior, not plumbing (taxonomy class 1) |
| Helper-only regression test | Original callsite stays unprotected | Drive the test through the callsite that triggered the bug (taxonomy class 5) |
| Coverage as the goal | Tests written to hit a number, not to catch defects | Signal, not coverage — apply the guardrail to every test |
