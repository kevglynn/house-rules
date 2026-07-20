---
name: ponytail-help
description: >
  Quick-reference index for the ponytail family: which skill or rule to use
  for over-engineering review, repo-wide audit, defer-ledger harvesting, or
  minimal-implementation mode. One-shot display, not a persistent mode.
  Trigger: "ponytail help", "use ponytail", "which ponytail skill",
  "how do I use ponytail", "what ponytail commands".
---

# Ponytail Help

Display this reference card when invoked. One-shot: do NOT change mode, write
flag files, or persist anything.

The ponytail family is the kit's over-engineering defense: one implementation
mode (a rule) plus review, audit, and ledger lenses (skills).

## The family

| Member | Kind | What it does |
|--------|------|--------------|
| **ponytail-playbook** | Rule (`ponytail-playbook.mdc`) | Implementation mode. The decision ladder for minimal, correct code: YAGNI → stdlib → native → one line → minimum. Use while writing code. Defers to `pragmatic-tdd.mdc` for test discipline. |
| **ponytail-review** | Skill | Over-engineering review of a diff or file set. One line per finding: what to cut, what replaces it. |
| **ponytail-audit** | Skill | Repo-wide scan for dead code, stdlib replacements, and YAGNI abstractions, ranked biggest cut first. |
| **ponytail-debt** | Skill | Harvests `defer:` comments into a debt ledger and flags entries missing upgrade triggers. |
| **ponytail-help** | Skill | This card. |

`ponytail-gain` (a benchmark scoreboard imported from upstream) is retired.
Its honesty boundary — never print a per-repo savings number, because the
unbuilt version was never written — now lives in ponytail-audit.

## Picking the right member

- Writing (or about to write) code → activate the **ponytail-playbook** rule.
- Reviewing a diff or PR for complexity → **ponytail-review**.
- Periodic hygiene pass over the whole repo → **ponytail-audit**.
- "What did we defer?" / ledger review → **ponytail-debt**.

## Activation

These are kit skills and rules — there is no plugin marketplace, config file,
or environment variable involved:

- **Skills:** invoke by name ("run ponytail-audit") or have the agent read
  the skill file directly (`skills/<name>/SKILL.md` in the kit, or the copy
  installed in the project).
- **Rule:** `ponytail-playbook.mdc` is agent-requestable — say "use
  ponytail-playbook" and the agent loads it for the session.

Updates arrive through the kit's normal distribution: `sync-rules.sh` for
rules, `playbook-init.sh` for skills.
