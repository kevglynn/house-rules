---
name: graybeard-debt
description: >
  Harvest every `defer:` comment in the codebase into a debt ledger, so the
  deliberate shortcuts and deferrals get tracked instead of rotting into "later
  means never". Use when the user says "graybeard debt", "/graybeard-debt",
  "what did we defer", "list the shortcuts", "debt ledger", or "what did we
  mark to do later". One-shot report, changes nothing.
---

Every deliberate shortcut is marked with a `defer:` comment naming its ceiling
and upgrade path. This collects them into one ledger so a deferral can't
quietly become permanent.

## Scan

Where the checker is distributed (kit-bootstrapped repos), start with it —
it handles all comment prefixes, multi-line continuation clauses, and noise
dirs, and supplies the totals and the rot rows:

`scripts/defer-lint --json`

Its `findings` array lists only the rot rows (missing trigger or ceiling);
`defer_comments` is the total. The compliant rows — the bulk of the ledger —
still come from the grep:

`grep -rnE '(#|//) ?defer:' .`  (skip `node_modules`, `.git`, build output;
add other comment prefixes if your stack uses them; also the full fallback
where the checker isn't distributed)

Each grep hit is one ledger row. The comment prefix keeps prose that merely
mentions the convention out of the ledger.

## Output

One row per marker, grouped by file:

`<file>:<line>, <what was simplified>. ceiling: <the limit named>. upgrade: <the trigger to revisit>.`

The convention is `defer: <what was simplified>. ceiling: <known limitation>. upgrade when: <trigger condition>.`,
so pull the ceiling and the trigger straight from the comment. Want an owner
per row too? add `git blame -L<line>,<line>`.

Flag the rot risk: any `defer:` comment that names no upgrade path or trigger
gets a `no-trigger` tag, those are the ones that silently rot.

End with `<N> markers, <M> with no trigger.` Nothing found: `No defer: debt. Clean ledger.`

## Boundaries

Reads and reports only, changes nothing. To persist it, ask and it writes the
ledger to a file (e.g. `DEFER-DEBT.md`). One-shot. "stop graybeard-debt" or
"normal mode" to revert.
