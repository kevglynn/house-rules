---
name: graybeard-help
description: >
  Quick-reference index for the graybeard family: which skill or rule to use
  for over-engineering review, repo-wide audit, defer-ledger harvesting, or
  minimal-implementation mode. One-shot display, not a persistent mode.
  Trigger: "graybeard help", "use graybeard", "which graybeard skill",
  "how do I use graybeard", "what graybeard commands".
---

# Graybeard Help

Display this reference card when invoked. One-shot: do NOT change mode, write
flag files, or persist anything.

The graybeard family is the kit's over-engineering defense: one implementation
mode (a rule) plus review, audit, and ledger lenses (skills).

## The family

| Member | Kind | What it does |
|--------|------|--------------|
| **graybeard-playbook** | Rule (`graybeard-playbook.mdc`) | Implementation mode. The decision ladder for minimal, correct code: YAGNI → stdlib → native → one line → minimum. Use while writing code. Defers to the pragmatic-tdd rule (where installed) for test discipline. |
| **graybeard-review** | Skill | Over-engineering review of a diff or file set. One line per finding: what to cut, what replaces it. |
| **graybeard-audit** | Skill | Repo-wide scan for dead code, stdlib replacements, and YAGNI abstractions, ranked biggest cut first. |
| **graybeard-debt** | Skill | Harvests `defer:` comments into a debt ledger and flags entries missing upgrade triggers. |
| **graybeard-help** | Skill | This card. |

A benchmark-scoreboard member imported from the upstream project (see the
credit in `graybeard-playbook.mdc`) is retired. Its honesty boundary — never
print a per-repo savings number, because the unbuilt version was never
written — now lives in graybeard-audit.

## Picking the right member

- Writing (or about to write) code → activate the **graybeard-playbook** rule.
- Reviewing a diff or PR for complexity → **graybeard-review**.
- Periodic hygiene pass over the whole repo → **graybeard-audit**.
- "What did we defer?" / ledger review → **graybeard-debt**.

## Activation

Activation needs no config file or environment variable:

- **Skills:** invoke by name ("run graybeard-audit") or have the agent read
  the skill file directly (`skills/<name>/SKILL.md` in the kit, or the copy
  installed in the project).
- **Rule:** `graybeard-playbook.mdc` is agent-requestable — say "use
  graybeard-playbook" and the agent loads it for the session.

Updates arrive through whatever channel installed the family: `house-rules
sync` for rules and `house-rules init` for skills in kit-bootstrapped
repos, or the plugin's own update path where installed as a plugin.
