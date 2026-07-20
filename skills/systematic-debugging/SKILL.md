---
name: systematic-debugging
description: Structured approach to diagnosing and fixing bugs. Use when a bug is reported, a test fails unexpectedly, behavior doesn't match expectations, or when "something is wrong" but the cause isn't clear. Triggers on "debug this", "why is this broken", "this doesn't work", "investigate this failure", unexpected test failures, or when multiple fix attempts have failed.
---

# Systematic Debugging

A disciplined approach to finding and fixing bugs. Prevents the "change random things and hope" anti-pattern by enforcing hypothesis-driven investigation.

## When to Use This Skill

Use this skill when:
- A bug is reported (user report, failing test, error log)
- Behavior doesn't match expectations
- A fix attempt didn't work and you're not sure why
- The failure is intermittent or hard to reproduce
- Multiple possible causes exist and you need to narrow down

Skip this skill when:
- The bug is obvious (typo, missing import, wrong variable name)
- The error message directly points to the fix
- You've seen this exact bug before and know the fix

## Core Process

### Step 1: Reproduce

Before investigating, confirm you can trigger the bug.

```bash
# Run the failing test, hit the endpoint, trigger the action
# Record the exact error output
```

**If you can't reproduce:** That IS the finding. Document what you tried and the conditions under which it supposedly occurs. Don't guess at fixes for bugs you can't trigger.

**If a bead exists:** The pragmatic-tdd rule requires bug beads to have a reproducing test FIRST. Write a test that fails for the right reason before proceeding.

### Step 2: Characterize

Understand the shape of the failure before guessing at causes.

**Answer these questions:**
1. **What is the actual behavior?** (exact error, wrong output, missing data)
2. **What is the expected behavior?** (from the bug report, test, or spec)
3. **When did it start?** (recent change, always broken, intermittent)
4. **What's the scope?** (one input, all inputs, specific conditions)

**Useful commands:**
```bash
# When did this code last change?
git log --oneline -10 -- path/to/suspicious/file

# What changed recently in this area?
git diff HEAD~5 -- path/to/directory/

# Is this a known pattern?
bd memories "error keyword"
```

### Step 3: Hypothesize

Form 2-3 specific hypotheses about the cause. Rank by likelihood.

**Format:**

| # | Hypothesis | How to Confirm/Reject | Likelihood |
|---|-----------|----------------------|------------|
| 1 | [Specific claim about what's wrong] | [Exact test or check] | High/Med/Low |
| 2 | [Alternative cause] | [Different test] | High/Med/Low |
| 3 | [Less likely but possible] | [How to rule out] | High/Med/Low |

**Common hypothesis categories:**
- **Data:** Wrong input, missing field, unexpected null, encoding issue
- **State:** Race condition, stale cache, initialization order
- **Logic:** Wrong conditional, off-by-one, missing case
- **Environment:** Config mismatch, version difference, missing dependency
- **Integration:** API contract changed, schema drift, timeout

### Step 4: Test Hypotheses

Work through hypotheses **in order of likelihood**. For each:

1. Design a specific test that distinguishes this hypothesis from others
2. Run the test
3. Record the result
4. Move to the next hypothesis if rejected

**Do NOT fix anything yet.** The goal is to identify the root cause with confidence, not to make changes that might accidentally work.

**Log findings as you go:**
```bash
bd note {BEAD_ID} "Hypothesis 1 (wrong input): REJECTED — input validated correctly at entry point. Hypothesis 2 (stale cache): CONFIRMED — cache returns stale value when key contains special characters."
```

### Step 5: Fix

Once the root cause is confirmed:

1. Write a test that reproduces the exact failure (if not done in Step 1)
2. Write the minimal fix
3. Verify the test passes
4. **Scan for the pattern class** — the bug often lives in more than one site

```bash
# Search for the same anti-pattern elsewhere
rg "pattern-that-caused-the-bug" --type py
```

Fix every matching site or file follow-up beads for each.

### Step 6: Verify and Close

1. Run the full test suite (not just the new test)
2. Confirm no regressions
3. Close the bead with evidence mapping to the acceptance criteria

## Escalation Rules

**Stop and escalate when:**
- 3+ hypotheses have been rejected with no new leads
- The fix requires changes outside your bead's scope
- The bug appears to be in a dependency or external system
- You're not confident in your diagnosis

**How to escalate:**
```bash
bd note {BEAD_ID} "Tried: [hypothesis 1 — rejected because X], [hypothesis 2 — rejected because Y], [hypothesis 3 — rejected because Z]. No remaining leads. Possible: [speculative cause that needs different expertise]."
bd update {BEAD_ID} --status=blocked
```

## Anti-Patterns

| Anti-Pattern | Why It Fails | Better Approach |
|--------------|-------------|-----------------|
| Change and pray | No understanding of root cause; may mask the bug | Hypothesize first, then fix |
| Fix without reproducing | Can't verify the fix works | Always reproduce first |
| Blame the framework | Wastes time on unlikely causes | Start with your code |
| Fix the symptom | Root cause produces new symptoms later | Find the actual cause |
| Shotgun debugging (change 5 things) | Can't tell which change helped | One change at a time |
| Skip the pattern scan | Same bug lives in 3 other files | Always search for siblings |

## Integration with Beads Workflow

For bug beads, this skill's diagnosis feeds directly into the bug playbook —
reproducing test first, red-proof, minimal fix, pattern-class scan, ledger.
Follow [skills/pragmatic-tdd/SKILL.md](../pragmatic-tdd/SKILL.md) for the
authoritative step-by-step; do not improvise the sequence from memory.
