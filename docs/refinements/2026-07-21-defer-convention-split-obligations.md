# Defer Convention Split — Obligations Checklist

**Date:** 2026-07-21
**Bead:** process-kit-jp9 (Wave 2, findings F1+F4 of
`docs/refinements/2026-07-19-kit-wide-mechanism-placement.md`)
**Method:** the pragmatic-tdd pilot's content-neutrality proof
(`docs/refinements/2026-07-19-pragmatic-tdd-topology.md` §7), applied to
`cursor/rules/defer-convention.mdc` (70 lines at commit `d1c417d`).

This split creates no new skill, so per the template note in
`docs/refinements/2026-07-21-bead-workflow-split-obligations.md` there is
no shared-ID namespace — document-local IDs **DC1–DC13** only.
**Rule** = the thinned always-on `defer-convention.mdc`; **Checker** =
`scripts/defer-lint` (new, created by this split; its `--help` epilog is
the relocation destination for the enumerable data); **ponytail-debt** =
`skills/ponytail-debt/SKILL.md` (pre-existing harvest skill).

The F4 dimension: the rule's one MUST (the no-trigger law) had its
detection regex half-written inside the rule as prose ("Harvesting").
This split converts that MUST from advisory to observable — the checker
exits 1 on any violating defer, is distributed by `playbook-init.sh`, and
drift-checks in `playbook-doctor.sh` (SUMMARY key `defer_lint_drift`).
Placement only, no substance changes; no change to the `defer:` grammar.

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| DC1 | Frontmatter: description + alwaysApply | **Rule** (kept; description gains the checker mention) |
| DC2 | Opening statement: mark deliberate simplifications with a `defer:` comment naming ceiling and trigger | **Rule** (kept, compressed — the ceiling/trigger naming is carried by the format template itself) |
| DC3 | Format template: `defer: <what>. ceiling: <limitation>. upgrade when: <trigger>.` | **Rule** (kept verbatim) |
| DC4 | "Language-appropriate comment prefix (`//`, `#`, `/* */`, `--`)" | **Rule** (kept; gains "may continue on the following comment line(s)" — the pre-split rule's own examples were two-line comments but the multi-line form was never stated; the checker honors it, so the rule now names it) |
| DC5 | Three good examples (config-reload lock, O(n²) duplicate check, naive retry) | **Checker** `--help` epilog (all three retained; the lock and O(n²) examples in their two-line form) |
| DC6 | Two bad examples (no trigger; ceiling without upgrade condition) | **Checker** `--help` epilog |
| DC7 | The defer/TODO/FIXME comparison table (3 rows × 4 columns) | **Checker** `--help` epilog ("marker comparison", one line per marker — the Structure and Rot-risk columns folded into each line) + **Rule** keeps a one-line marker-choice sentence |
| DC8 | "Use `defer:` when you chose the simpler path… TODO for unstructured reminders… FIXME for things that are actually broken" | **Rule** (compressed into the marker-choice line, merged with DC7's rule-side residue) |
| DC9 | Harvesting: the periodic-scan grep command (`grep -rnE '(#\|//) ?defer:' …`) | **Superseded by the Checker** — `scripts/defer-lint` is the detection mechanism (multi-line aware, all four comment syntaxes, noise-dir skipping, `--json`, stable exit codes). `skills/ponytail-debt` § Scan now prefers the checker and retains the grep as the fallback for non-kit repos (F3's defer-harvest dedup, partial — see flagged notes) |
| DC10 | Harvesting: "flag any `defer:` comment that lacks an upgrade-when clause — most likely to rot" | **Checker behavior** (the error finding itself; missing `ceiling:` added as a lesser-severity warning) + ponytail-debt's `no-trigger` tag prose unchanged |
| DC11 | The no-trigger law (`MUST include "upgrade when:"`; "a deferral without a trigger is just a TODO with a fancier name"; permanent-or-investigate closing) | **Rule** (kept verbatim) |
| DC12 | — (new) checker pointer: `scripts/defer-lint` verifies the law mechanically; examples in `--help`; harvesting via ponytail-debt | **Rule** (the split's addition — the address where the relocated data and the enforcement live) |
| DC13 | — (new) scorecard item 35: defer auditing runs through the checker, not a from-memory grep | `docs/rule-effectiveness-scorecard.md` (the mechanism-placement signal, item-26/29/33/34 pattern) |

## Dropped content — with rationale

Nothing law-shaped and no example is dropped. One textual note: the table's
"Rot risk" column values (Low/High/Medium with reasons) survive as the
folded clauses in the epilog's marker-comparison lines ("low rot risk",
"'later' = never", "urgency implied but not quantified").

## Enforcement delta (F4)

| Before | After |
|---|---|
| MUST stated in prose; detection regex half-written inside the rule; nothing runs it | `scripts/defer-lint` exit 1 on violation; behavioral test suite (`scripts/tests/test_defer_lint.py`); distributed by `playbook-init.sh`; drift-checked by `playbook-doctor.sh` (`defer_lint_drift`) |

CI wiring is explicitly out of scope for this bead (Wave 3,
process-kit-gsx): the checker exists and is invocable; nothing yet runs it
on merge.

## Flagged for the coordinator (not changed — substance or out of scope)

- **`sandbox/project/.claude/rules/defer-convention.md`** is a
  point-in-time bootstrap fixture of the old rule; regenerates on the next
  sandbox refresh (same precedent as prior splits).
- **`docs/research/2026-07-21-profile-projection-spike.md`** cites the
  defer-comment grammar as "the regex is literally [in the rule]" —
  historical research record, correctly left stale.
- **F3's defer-harvest triplication** is only partially retired here:
  ponytail-debt now points at the checker (grep demoted to fallback), and
  the rule's Harvesting section is gone. The third copy the audit counted
  (tier1-review's defer mention) is a usage prescription, not a harvest
  procedure — left as is.
- **`operating-model.mdc` § Session Lifecycle and Hygiene** names the
  `ponytail-debt` sweep, not the rule's Harvesting section — no edit
  needed; alignment with the checker is transitive through the skill.
- **`.cursor/agents/*.md` one-line summaries** of defer-convention
  ("`defer:` comments include ceiling + upgrade trigger") remain accurate.
- The task brief placed the docs registration in "`docs/README.md`'s
  scripts table"; that table lives in the root `README.md` (where
  tdd-ledger is registered) — registered there.
