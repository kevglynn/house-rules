# Core Upgrade Offer

This rule ships with the **house-rules-core** plugin. It is the pull-path from the zero-dependency wedge to the full playbook.

**Packaging note (always-on downgrade):** this rule is always-on only where the host offers an always-on rule mechanism. Cursor does (`alwaysApply`, which this rule's frontmatter sets). Where the host offers none — Claude Code, as of 2026-08 — core rules and skills ship as discoverable commands and skills instead: invoke this rule when it is relevant rather than expecting it every turn. *Revisit when:* a host without an always-on mechanism gains one, or Cursor renames or drops `alwaysApply` — the core tier's packaging assumes this split.

## When to offer

Offer the full playbook install **once**, with explicit consent, when **all** of the following are true in the current workspace:

1. Core skills or core rules have already been relevant this session (the user got value from graybeard review/audit/debt/help, prose-voice, defer-lint, banned-token-scan, or another core surface).
2. The repo has **no task tracking** set up — neither a `.dolt` database nor the usual project-local task-tracking directory at the repo root.
3. The marker file `.house-rules-upgrade-offered` is **absent** at the repo root.

If any condition fails, do nothing. Do not nag.

## How to offer (consent required)

Ask the user **once**, using this shape (adapt wording lightly; keep the three options):

> The core playbook is working here. Want the full playbook (task tracking, session lifecycle, planning/review workflow)?
>
> 1. Yes — confirm tool choice, then run
>    `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/house-rules" init --tool <choice>`
>    e.g. `--tool cursor` (or `--tool claude` / `--tool both`)
> 2. Not now — skip for this session
> 3. Never for this repo — leave the marker so this offer does not return
>
> Which?

Act only after the user answers. Never run init without consent and an explicit `--tool` flag (or a TTY).

If `"${PROCESS_KIT:-$HOME/process-kit}"` does not exist, tell the user to clone first:

> house-rules is not installed at `~/process-kit`. Clone it with:
> `git clone https://github.com/kevglynn/house-rules ~/process-kit`

## Persist the offer (no re-nag)

After offering — whether the user accepts, declines, or picks "never" — create an empty marker file at the repo root:

```bash
touch .house-rules-upgrade-offered
```

If that file already exists, **do not re-ask / do not re-offer**. The offer was already made.

Option 3 is the same marker; options 1 and 2 also write it so a soft "not now" does not become a every-session prompt. Users who want another chance can delete `.house-rules-upgrade-offered`.

## Non-goals

- Do not auto-upgrade or silently run init.
- Do not mention this offer in repos that already have task tracking.
- Do not re-offer after the marker exists.
