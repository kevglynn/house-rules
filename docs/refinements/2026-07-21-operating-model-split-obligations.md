# Operating Model Split — Obligations Checklist

**Date:** 2026-07-21
**Bead:** process-kit-oub (Wave 2, findings F1 and F3 of
`docs/refinements/2026-07-19-kit-wide-mechanism-placement.md`)
**Method:** the pragmatic-tdd pilot's content-neutrality proof
(`docs/refinements/2026-07-19-pragmatic-tdd-topology.md` §7), applied to
`cursor/rules/operating-model.mdc`.

Every obligation/prescription in the pre-split rule (237 lines, state at
commit `b8ad1c4`), mapped to its destination. **Rule** = the thinned
always-on `operating-model.mdc`; **Skill** = `skills/graph-planning/SKILL.md`
(new, created by this split); **session-lifecycle** =
`cursor/rules/session-lifecycle.mdc`; **bead-completion** =
`cursor/rules/bead-completion.mdc`.

ID namespaces, per the template note in
`docs/refinements/2026-07-21-multi-agent-review-split-obligations.md`:
content that lands in the **newly created** skill uses the shared namespace
**G1–G7** — the same IDs appear in the skill text, so checklist and
destination agree by construction (the pilot's O1–O17 pattern). Everything
else uses the document-local namespace **OM1–OM47** (destinations that
pre-exist are not renumbered; placement only, no substance changes).

## Content landing in the new skill (shared IDs)

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| G1 | Decomposition heuristics: 3–7 beads per epic (fewer doesn't justify an epic, more suggests a missing grouping); each bead completable in one agent session; leaf beads max 3 ACs; independent beads should not depend on each other (check with `bd graph`) | **Skill** (Phase 1) |
| G2 | For 3+ bead breakdowns, create the dependency graph atomically with `bd create --graph plan.json` — including the full ~40-line JSON example (nodes with key/title/type/parent_key/description; edges with from_key/to_key/type) | **Skill** (Phase 2, example verbatim) |
| G3 | After creation, `bd graph <epic-id>` to visualize and verify dependency order and identify parallelism before execution; `bd graph --all --compact` for a full project view | **Skill** (Phase 3) |
| G4 | After each child close, run `bd epic status <epic-id>` and report progress | **Skill** (Phase 4) + **Rule** (one item in the compressed per-milestone hygiene line) |
| G5 | Stuck children: if a child is blocked/deferred and no other children remain, decide — (a) defer the epic to match, (b) extract the stuck child and close the epic with adjusted success criteria, or (c) close the child as won't-do with rationale. Do not leave epics in limbo | **Skill** (Phase 4) |
| G6 | Scope expansion: a requirement pushing an epic beyond 7 children → split the epic or create a sibling; never silently grow past the heuristic | **Skill** (Phase 4) |
| G7 | Epic close = success criteria, not child count: before `bd epic close-eligible`, verify success criteria are actually met; unmet criterion → follow-up bead before closing | **Skill** (Phase 4) |

## Everything else (document-local IDs)

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| OM1 | Rule hierarchy: specialized rules are source of truth for their domain; conflict order = project agent rules > specialized rules > this rule > repo docs | **Rule** (kept verbatim; the section header folded into a preamble paragraph) |
| OM2 | Two roles (Planner/Executor); next steps decided from the project scratchpad (`.cursor/scratchpad.md` / `scratchpad.md`); ask which mode when the user doesn't specify | **Rule** (kept) |
| OM3 | Mode switching: autonomous for trivial operational tasks; ask only for substantive planning or implementation work | **Rule** (kept, example list compressed) |
| OM4 | Planner: high-level analysis, task breakdown, success criteria, progress evaluation; document the plan for user review; small tasks with clear success criteria; do not overengineer; revise the scratchpad | **Rule** (kept, compressed) |
| OM5 | Beads created with `--description` and `--acceptance` per beads-quality; dependencies wired (`bd dep add` / `--graph`) | **Rule** (creation law, one line) + **Skill** (graph procedure = G2) |
| OM6 | Design doc for 3+ bead breakdowns or high-risk areas (auth, billing, data loss) per design-docs | **Rule** (kept) |
| OM7 | AC ownership — the rule carried **three** statements (Planner section: "The Planner owns acceptance criteria. The Executor does not modify them"; Executor bullet: "do NOT modify it — mark the bead blocked and escalate"; situation-table row: "Escalate to Planner — do NOT modify the AC") | **Rule** (collapsed to a SINGLE statement in Roles) + canonical home **bead-completion** § AC ownership (pre-existing, carries the full escalation protocol). This is the F3 dedup — see the dedup table below |
| OM8 | Executor: execute tasks (code, tests, implementation details); report progress or raise questions after milestones or blockers | **Rule** (kept) |
| OM9 | `bd ready` for the next unblocked task; claim with `bd update <id> --claim` (atomic: assignee + in_progress in one operation) | **Rule** (kept) |
| OM10 | JIT verification before coding (files/patterns still match reality) | **Rule** (pointer) — canonical **bead-completion** § JIT verification (pre-existing) |
| OM11 | Follow pragmatic-tdd by bead type | **Rule** (pointer, kept) |
| OM12 | Self-review against ACs before declaring done | **Rule** (pointer) — canonical **bead-completion** § self-review (pre-existing) |
| OM13 | On completion: update scratchpad "Current Status / Progress Tracking" with the bead ID; close with `bd close --reason` carrying AC-mapped evidence | **Rule** (kept; evidence policy by pointer to bead-completion, the canonical home of the close-evidence/IOU doctrine) |
| OM14 | `--suggest-next` / `--claim-next` on close | **Demoted from the rule** — canonical **bead-completion** § "After closing — workflow continuation" carries both flags verbatim (pre-existing duplicate; the rule's copy was the redundant one) |
| OM15 | Blocked by a dependency → `bd update <id> --status=blocked`; postponed with no blocker → `bd defer <id>` (optionally `--until=`); deferred beads reappear in `bd ready` | **Rule** (kept in the compressed when-work-can't-proceed law) |
| OM16 | If blocked, update "Executor's Feedback or Assistance Requests" and note the blocker | **Rule** (kept, compressed into the can't-proceed law) |
| OM17 | Human-judgment decisions → `bd tag <id> human` and continue other work; check `bd human list` at session start | **Rule** (tag obligation kept) + the session-start check lands in **session-lifecycle** extended start (moved with OM33) |
| OM18 | Lessons: session-specific context in scratchpad "Lessons"; reusable insights promoted with `bd remember --key <area>-<topic>` | **Rule** (kept, one line, pointer for the full protocol) — canonical **bead-completion** § Knowledge capture (litmus test, when/when-not, requirements; pre-existing). F3 dedup — see below |
| OM19 | "When work can't proceed" situation table (7 rows: dependency block, external outage, defer, human flag, wrong AC, 3+ failures, unsure→blocked/over-signal) | **Rule** (kept, compressed from a 3-column table to law bullets; every situation and its command survive). *Judgment call:* NOT moved to the skill — this is Executor-side status law, not planning procedure; it compresses to 6 lines without losing a row. The wrong-AC row collapsed into the single AC-ownership statement (OM7) |
| OM20 | Error recovery 1: build/test failure → stop, diagnose, fix; out-of-scope fix → new bead + block current | **Rule** (kept, compressed) |
| OM21 | Error recovery 2: tool failure → `bd ping` first; if it succeeds, `bd doctor --agent` (embedded-mode DBs don't support doctor — exits 0 with a note; use `bd lint` + `bd orphans` + `bd blocked` instead); fundamentally broken → note in Feedback + block | **Rule** (kept, embedded-mode branch preserved verbatim in substance — process-kit-qxc correction) |
| OM22 | Error recovery 3: 3+ distinct failed approaches → stop, document what was tried in `bd note`, mark blocked, escalate to Planner | **Rule** (kept, merged with the table's identical row — the pre-split rule stated this twice) |
| OM23 | Error recovery 4: uncertain about correctness → do not ship; flag with specific questions in Feedback | **Rule** (kept) |
| OM24 | Beads is the single source of truth for task state | **Rule** (kept as law) |
| OM25 | Prohibited task-tracking tools (TodoWrite, CreatePlan, TaskCreate, markdown checklists, IDE-native tools; don't persist, invisible to other agents/worktrees) | **Rule demoted to a one-line cross-ref** — canonical **session-lifecycle** § Prohibited task tracking tools (pre-existing verbatim copy). F3 dedup — see below |
| OM26 | Scratchpad is narrative context only (background, analysis, decisions, lessons, feedback) | **Rule** (kept) |
| OM27 | New projects: check for `.beads/`; ask before `bd init` (or `bd init --stealth` for personal repos) | **Rule** (kept) |
| OM28 | Do not run `bd setup <tool>` on playbook-initialized projects (redundant beads.mdc); only for beads-without-playbook projects | **Rule** (kept, compressed) |
| OM29 | `bd prime` at session start or after compaction reloads workflow context | **Rule** (kept, reframed as the live-catalog statement) — the start-step itself is canonically **session-lifecycle** step 1 (pre-existing) |
| OM30 | Scratchpad conventions: fixed section titles; Background/Key Challenges established by the Planner; Breakdown carries bead IDs + success criteria; one task at a time, do not proceed until the user verifies; append don't rewrite; mark outdated instead of deleting; don't delete the other role's records | **Rule** (kept, compressed; one-task-at-a-time verification merged into Workflow) |
| OM31 | Workflow sequencing: new task → Background updated → Planner plans → beads after user approval; Executor implements one task, writes Current Status, closes with evidence; completion announced by the Planner after cross-checking (Executor asks the user for confirmation); Executor notifies Planner before large-scale/critical changes; continue until the Planner declares complete/stopped | **Rule** (kept) |
| OM32 | Session start/close protocol is mandatory, defined in session-lifecycle | **Rule** (kept as a one-line pointer — the pre-split rule already deferred; its "extended reference" preamble is superseded by the move in OM33/OM34) |
| OM33 | Extended session start: review injected memories (contradiction → update/`bd forget`); `bd human list`; fresh clone → `bd bootstrap`; empty `bd ready` → `bd blocked` then report | **MOVED to session-lifecycle** (canonical home of the session protocol; these items had no copy there). The memories item is rewritten as a pointer to bead-completion's staleness protocol rather than restating its commands — F3 dedup, see below |
| OM34 | Extended session close: `bd doctor --agent` health check (embedded mode: doctor unsupported, exits 0 with a note — run `bd lint`, `bd orphans`, `bd blocked` instead); `bd dolt pull && bd dolt push` if remote configured | **MOVED to session-lifecycle** (embedded-mode branch preserved verbatim — process-kit-qxc correction) |
| OM35 | "Finding and Filtering Beads" catalog: `bd ready --explain`, `bd list --status`, `bd search`, `bd query` syntax, `bd blocked`, `bd count --by-status`, `--exclude-type`/`--exclude-label`, `--json`/`--flat`/`--tree` output modes, `bd q` quick capture, aliases (`done`/`view`/`new`) | **REMOVED** in favor of `bd prime` + `bd --help`. **Competing-truth finding:** a prose catalog of a CLI's commands is a second source of truth that rots against `bd --help` — every bd release makes the rule's copy staler, and `bd prime` already injects the live command surface each session. The one behavioral obligation embedded in the catalog ("`bd ready` is the default starting point") survives in the Executor law (OM9) |
| OM36 | "Jawnt MCP vs Local bd" routing table (5 rows), MCP-unavailable fallback, don't-mix-per-query guidance | **REMOVED** as catalog (same competing-truth rationale — the MCP tool list and `daily_brief` names rot against the live MCP surface). The one law-shaped obligation survives in the rule as one line: MCP for cross-project reads, **all writes through local `bd`** (MCP is read-only). The fallback ("works without MCP") is implied by writes-always-local; the don't-mix etiquette is procedural guidance dropped with the catalog |
| OM37 | Per-session hygiene table: doctor (or embedded substitutes) + `bd show --current` | **Absorbed by session-lifecycle** — `bd show --current` is already start-step 2 there (pre-existing); the doctor-with-embedded-branch item is the moved OM34. Nothing unique remained in the table |
| OM38 | Per-milestone hygiene (after 3+ closes or an epic child): `bd stale`, `bd prune --older-than 90d --dry-run` (`--force` only after review — permanent deletion), `bd orphans`, `bd count --by-status`, `bd epic status`, ponytail-audit, ponytail-debt, refinement trigger check | **Rule** (kept, compressed from a 7-row table to one bullet; every command and the prune caution survive; the what-it-checks/action columns compressed into the skill/rule pointers each sweep already owns) |
| OM39 | Pre-PR hygiene: `bd doctor --check=conventions` (embedded: `bd lint` + `bd stale` + `bd orphans`), `bd epic close-eligible` | **Rule** (kept, compressed; embedded-mode branch preserved) |
| OM40 | Do not use `bd preflight` (emits upstream-project checklist content); revisit when it reads per-repo config | **Rule** (kept — a process-kit-qxc prescription correction) |
| OM41 | Commit message grammar: `<type>: <summary>`; types feat/fix/refactor/test/chore/docs; under 72 chars | **Rule** (kept) |
| OM42 | Branch naming: `<type>/<bead-id>-<short-description>` | **Rule** (kept) |
| OM43 | Commit at logical checkpoints; small atomic commits | **Rule** (kept) |
| OM44 | Never force push shared branches without explicit user approval | **Rule** (kept) |
| OM45 | Communication: no answers below full confidence; the user is non-technical; say when unsure | **Rule** (kept) |
| OM46 | Communication: document purpose and results when external information is needed | **Rule** (kept) |
| OM47 | Frontmatter: description + alwaysApply | **Rule** (kept unchanged) |

## Dropped content — with rationale

Nothing law-shaped is dropped. Three data/procedure items do not survive as
text anywhere, all under the competing-truth finding recorded in OM35/OM36:

1. **The bd command catalog (OM35).** Removed, not relocated: its canonical
   live sources are `bd prime` (injected every session) and `bd --help`.
   Relocating it to a skill would just move the rot.
2. **The Jawnt MCP routing table's tool-name inventory (OM36).** Same
   rationale; the single write-path law survives in the rule.
3. **The hygiene tables' "What it checks / Action on findings" prose
   columns (OM37–OM39).** The commands and obligations survive compressed;
   the explanatory columns were command documentation, owned by the tools'
   own help output.

## F3 dedup — the five parallel copies

Canonical-home designations executed by this split.
`operating-model.mdc` is the pointer side for all five.

| Copy | Canonical home | What was demoted / moved |
|---|---|---|
| Session protocol | `session-lifecycle.mdc` | operating-model's "Session Lifecycle" section reduced to a one-line pointer; its **unique** extended start/close content (OM33, OM34 — memories review, `bd human list`, `bd bootstrap`, empty-ready→`bd blocked`, doctor-at-close with embedded branch, dolt sync) **moved into** session-lifecycle as "Extended" subsections rather than deleted |
| Prohibited task-tracking tools | `session-lifecycle.mdc` § Prohibited task tracking tools | operating-model's verbatim copy (OM25) demoted to a one-line cross-ref; the beads-as-single-source-of-truth law itself stays in the rule (it is operating-model law, not a duplicate — session-lifecycle restates it in one closing line, which is its own canonical section's summary) |
| IOU / close-evidence doctrine | `bead-completion.mdc` § evidence policy + "Do not defer AC verification" | operating-model's copy was the light form ("close with evidence mapped to ACs" + `--suggest-next`/`--claim-next`); reduced to the sequencing obligation with a pointer (OM13), flags dropped from the rule (OM14 — bead-completion carries them verbatim). beads-quality's anti-pattern 6 already points at bead-completion and is bead process-kit-n0w's scope — untouched here |
| Knowledge-capture litmus + memory-staleness protocol | `bead-completion.mdc` § Knowledge capture / § Staleness | operating-model's Executor lessons bullet (OM18) reduced to one line + pointer; the extended-start memories item (OM33) rewritten to point at the staleness protocol instead of restating `bd remember --key` / `bd forget` commands; session-lifecycle's close-step-3 capture check gained a pointer to the canonical litmus (it keeps the checklist question — that is the session trigger, not the protocol) |
| AC ownership (×4 statements: 3 in operating-model + 1 in bead-completion) | `bead-completion.mdc` § AC ownership | operating-model's three statements (OM7) collapsed into a single statement in Roles with a pointer; the situation-table row and the Executor bullet now reference that statement instead of restating it |

No copy carried unique content that the canonical home lacked, except the
session-protocol extended items (moved, per row 1).

## Flagged for the coordinator (not changed — substance, not placement)

- **Scorecard section headers now carry stale addresses.** Items 1–7
  ("Session Protocol (operating-model.mdc — Tier 1.1)") and item 17's
  per-session-hygiene wording reference content whose canonical home is now
  session-lifecycle.mdc (and was arguably already there pre-split). The
  bead's scope allows exactly one scorecard item (#33), so the headers were
  left as-is. Cheap follow-up: retitle the section attributions.
- **`bd update <id> --claim` vs `bd claim`.** The rule prescribes the
  long form with a parenthetical explaining its atomicity. If bd has grown
  a first-class `claim` verb, this is a candidate prescription correction —
  not verified here, and changing it would be substance.
- **The "user is non-technical" communication clause** is a per-user fact
  living in project-neutral kit law (the same text ships to every target
  repo). Neutrality question for the kit owner, not a placement move this
  split can make.
- **Duplicate 3+-failures statement in the pre-split rule** (situation
  table row + Error Recovery item 3) was merged into one law bullet (OM22)
  — recorded here since it is technically a wording consolidation, though
  both sources said the same thing.
