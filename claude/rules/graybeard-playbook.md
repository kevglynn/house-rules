# Graybeard-Playbook: Implementation Ladder

Concept adapted from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) (MIT); reimplemented and extended for this kit. Governs how you build — test discipline belongs to the pragmatic-tdd rule (see "Test discipline" below).

## The ladder

Stop at the first rung that holds:

1. **Does this need to exist at all?** Speculative need = skip it, say so in one line. (YAGNI)
2. **Already in this codebase?** A helper, util, type, or pattern that already lives here — reuse it. Look before you write; re-implementing what's a few files over is the most common slop.
3. **Stdlib does it?** Use it.
4. **Native platform feature covers it?** `<input type="date">` over a picker lib, CSS over JS, DB constraint over app code.
5. **Already-installed dependency solves it?** Use it. Never add a new one for what a few lines can do.
6. **Can it be one line?** One line.
7. **Only then:** the minimum code that works.

The ladder runs *after* you understand the problem, not instead of it. Read the task and the code it touches, trace the real flow end to end, then climb. Two rungs work — take the higher one and move on.

## Bug fix = root cause, not symptom

A report names a symptom. Before you edit, grep every caller of the function you're about to touch. The lazy fix IS the root-cause fix: one guard in the shared function is a smaller diff than a guard in every caller — and patching only the path the ticket names leaves every sibling caller still broken. Fix it once, where all callers route through.

## Rules

- No unrequested abstractions: no interface with one implementation, no factory for one product, no config for a value that never changes.
- No boilerplate, no scaffolding "for later" — later can scaffold for itself.
- Deletion over addition. Boring over clever — clever is what someone decodes at 3am.
- Fewest files possible. Shortest working diff wins — but only once you understand the problem.
- Complex request? Ship the lazy version and question it in the same response: "Did X; Y covers it. Need full X? Say so." Never stall on an answer you can default.
- Two stdlib options, same size? Take the one that's correct on edge cases.
- Mark deliberate simplifications with a `defer:` comment (see defer-convention.md).

## Output

Code first. Then at most three short lines: what was skipped, when to add it. If the explanation is longer than the code, delete the explanation. Explanation the user explicitly asked for is not debt — give it in full.

## When NOT to be lazy

Never simplify away:
- **Understanding the problem** — read fully, trace the real flow before picking a rung. A small diff you don't understand is the dangerous kind of laziness.
- **Input validation at trust boundaries**
- **Error handling that prevents data loss**
- **Security measures**
- **Accessibility basics**
- **Anything explicitly requested** — user insists on the full version, build it.

## Test discipline — defer to pragmatic-tdd

This rule does NOT govern test policy. That belongs to the pragmatic-tdd rule — follow it where installed; where it isn't, apply its short form:
- Bug fixes: test-first, always (reproduce the bug before fixing)
- Features: ACs become tests (write failing tests from acceptance criteria)
- Refactors: safety net first (behavioral tests before changing structure)

The ladder governs implementation code; test discipline governs test code. They are complementary: the ladder produces minimal implementation, test discipline ensures that minimal implementation is verified.

## Intensity

| Level | What changes |
|-------|-------------|
| **lite** | Build what's asked, but name the lazier alternative in one line. User picks. |
| **full** | The ladder enforced. Stdlib and native first. Shortest diff, shortest explanation. Default. |
| **ultra** | YAGNI extremist. Deletion before addition. Ship the one-liner and challenge the rest of the requirement in the same breath. |

## Boundaries

This rule governs what you build, not how you talk. Deactivate with "stop graybeard-playbook" or "normal mode." Level persists until changed or session end. Default: **full**.
