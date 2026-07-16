---
name: packet-deepdive
description: >-
  Validate a drafted gate/sprint packet with a four-lane deep-dive:
  accuracy-vs-repo, cold-read (the overlay's reader persona and access
  boundary), receipts verification (re-run every count/string/exit-code live),
  and navigability/structure — with a phase-2 convergence round between
  accuracy and cold-read, wrapped around the deep-dive-orchestrator subagent,
  emitting the findings-and-dispositions review doc. Use when the user says
  "deep-dive the packet", "validate the packet", "packet review", "cold-read
  the gate packet", or after the packet skill drafts a packet that needs
  validation before it reaches the reader.
---

# Packet Deep-Dive

Encapsulate the packet-validation deep-dive. A packet is a trust instrument:
the failure modes are a false claim the reader checks in ten seconds, a dead
reference to something the reader can't see, a receipt that doesn't reproduce,
or a broken link the reader hits. Four independent lanes hunt exactly those,
a convergence round reconciles the truth-and-wording conflicts, and the output
is a dispositions doc that maps every finding to a fix or a reasoned rejection.

## When to Use This Skill

Run on a drafted packet before it reaches the reader — the validation half of
the packet workflow (author with the `packet` skill; validate with this one).
This is the multi-agent-review Tier 2 equivalent for packets. Skip it only for
throwaway internal checkpoints.

## Core Process

### Phase 0 — Prepare

1. **Pin the state.** The packet must be committed; note `{repo}@{commit}` and
   branch. Lanes review that exact state.
2. **Load the overlay** (`.agents/overlay.md` § `packet-deepdive`): the reader
   persona, the reader's access boundary (what they can and cannot see), and
   the receipt commands. The access boundary is load-bearing — the largest
   finding class in practice is references to artifacts the reader cannot
   reach.

### Phase 1 — Dispatch four lanes (independent contexts)

Wrap the **deep-dive-orchestrator** subagent to run four lanes in parallel,
each with its own context and only its own mandate (templates in `lanes.md`):

| Lane | Hunts |
|---|---|
| **accuracy-vs-repo** | every factual claim vs the actual repo (commits, PRs, code behavior, attribution, counts, "already in place") |
| **cold-read** | the reader's timed experience: grid honesty, FAQ preemption, dead-vocabulary audit, tone, meeting-triggers, word budget |
| **receipts** | re-runs every count/string/exit-code live; double-run determinism; no mutation |
| **navigability/structure** | heading→slug inventory, every link/anchor resolves, render correctness, lint, phone width |

Fill each template's `{...}` from the overlay and the pinned state. Each lane
reports findings with severity, exact line refs, and exact fixes — no lane
fixes anything.

### Phase 2 — Convergence (accuracy × cold-read)

Give a convergence lane both the accuracy and cold-read reports in full. It
produces combined exact-wording rewrites, resolving conflicts under one
standing rule: **a fix never softens or breaks a factual claim — honesty
wins.** A cold-read wording fix that would entrench a falsehood accuracy found
is withdrawn and superseded. It re-ranks findings by meeting-trigger risk and
keeps an own-findings ledger (upgrades/downgrades/withdrawals). Receipts and
structure are factual lanes and don't need convergence — fold their findings
straight into triage.

### Phase 3 — Synthesize and triage

Collect all lane reports (+ convergence) and write the dispositions doc from
`report-template.md`:

- **Process note** (how the lanes ran + any resilience recovery)
- **Verdict** (receipts state, link totals, finding counts)
- **Critical / Important / Minor** tables, each finding with a disposition
- **Rejected / not applied** table, each with a real reason
- **Post-fix state**

Fix all Critical and Important findings in the packet, re-render and re-verify
the share (`packet` skill's `render.py --verify`), and file beads for any
deferred minor. Land the dispositions doc in the consuming repo's
`docs/reviews/`, with the four full lane reports in a sibling dir.

## Resilience Protocol

Long parallel orchestrations fail in characteristic ways. Handle them, don't
restart from zero:

1. **Orchestrator death mid-run.** If the orchestrator process is killed
   (infrastructure/DNS failure, timeout) *after* lane reports are written, the
   **parent agent performs the final synthesis and triage directly** — do not
   re-run the lanes. Record the death and the parent-synthesis fallback in the
   dispositions doc's process note. (This happened twice on the first real
   run; the reports survived and the parent finished the job.)
2. **Harvest the longest assistant message**, not the last. A lane's final
   turn is often a brief wrap-up; the actual report is the longest message in
   its transcript. Extract that.
3. **Relaunch stalled lanes.** A lane that returns tiny output after its first
   tool call (no-turn-ended) has stalled — relaunch it with its original
   prompt; do not accept the stub.

## Project Overlay

Reads `.agents/overlay.md` § `packet-deepdive` in the consuming repo (shared
overlay convention — one file, one section per skill):

| Key | Meaning | Default when absent |
|---|---|---|
| `reader_persona` | Who the cold-read lane simulates | A cold external reviewer with repo access only |
| `reader_access` | What the reader can see | This repo on the code host |
| `reader_blind` | What the reader cannot see | The planning workspace, tracker, decision record |
| `receipt_commands` | Commands the receipts lane re-runs | The commands quoted in the packet |
| `reviews_dir` | Where the dispositions doc lands | `docs/reviews/` |

With no overlay: cold-read simulates a repo-access-only reviewer; receipts
re-runs the packet's own quoted commands.

## Anti-Patterns

- **Sharing lane context.** Lanes must run independent — a lane that sees
  another's findings anchors on them and stops hunting. Convergence is the
  only place they meet.
- **Re-running lanes after an orchestrator death.** The reports survive the
  process; synthesize from them. Re-running discards the analysis and burns
  the run.
- **Harvesting the last message.** The report is the longest message, not the
  final wrap-up.
- **Letting wording soften truth in convergence.** Honesty wins, always. A
  prettier sentence that entrenches a false claim is withdrawn.
- **A rejected finding with no reason.** "Not applied" needs a real reason
  (settled by design, would falsify a receipt, advice-only) — not a shrug.
- **Skipping the access boundary.** Without the reader's blind set, the
  cold-read lane misses the dead-vocabulary findings that are the packet's
  most common and most damaging defect class.
- **Fixing in a lane.** Lanes report; the synthesis step fixes. A lane that
  edits the packet corrupts the pinned state the other lanes review.
