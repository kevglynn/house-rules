<!--
GATE / SPRINT PACKET TEMPLATE — the committed blueprint.

Fill every {{PLACEHOLDER}} and delete the HTML comments before rendering.
The blueprint constraints (enforced by render.py --verify):
  - Status grid uses the READER'S OWN checklist wording verbatim, with the
    status verdict (bold) IN the cell, plus linked evidence.
  - The divergence strip is a blockquote in the SAME EYE-SPAN as the grid —
    deviations from the reader's expectations surface immediately, not buried.
  - FAQ is HARD-CAPPED at 5. Admission rule: a named reader voice actually
    asked it (or would, cold). Do not pad to 5; fewer is fine.
  - Prose target <= 700 words (excludes tables, code, the agent on-ramp).
  - Receipts = EXACTLY 3 linked proofs: double-run, test gate, PR trail.
    Link them; do not dump their contents inline.
  - Carry the decision vocabulary (D*/A* tags, etc.) INTO this repo — the
    reader cannot see the planning workspace where it normally lives.
-->
# {{GATE}} — week {{X}} of {{Y}} · `{{REPO}}` · {{DATE}}

<!-- One-line status: verdict · where the evidence lives (commit/PR links) · blocker count into the next gate. -->
**{{STATUS: e.g. CLOSED — N/N checklist deliverables}}** · {{evidence: commits @ links · PRs merged · CI state}} · {{N}} blockers into {{NEXT GATE}}.

## Status at a glance

<!-- One row per item on the READER'S checklist, in their words. Verdict bold IN the cell. Link the proof. -->
| Your checklist item | Status |
|---|---|
| {{reader's checklist item 1, verbatim}} | **{{VERDICT}}** — {{what shipped, with a [link](#anchor-or-url)}} |
| {{reader's checklist item 2, verbatim}} | **{{VERDICT}}** — {{...}} |

<!-- DIVERGENCE STRIP — same eye-span as the grid. Deviations from the reader's plan text, surfaced now. If there are none, state that in one line instead of deleting the strip. -->
> **{{N}} deliberate divergences from your plan text:** {{one-clause each}}. {{Which were pre-registered vs found in review}}. **[The why ↓](#the-divergences)**

{{One sentence orienting the reader to the rest: what reproduces from source, and where the open threads are.}}

## The divergences

<!-- Delete this whole section if the strip said "no divergences". Otherwise: one entry per divergence — the forcing constraint and what it defers, with the deferral's revisit point named. Carry the decision-record tags (D*/A*) in here. -->
**1 — {{divergence}}.** {{forcing constraint}}. Deferred by name: {{...}} ({{tag}}). Revisit: {{trigger}}.

<details>
<summary>{{amendments / decisions, one line each}}</summary>

| # | Date | What it changed |
|---|---|---|
| {{A1}} | {{date}} | {{one line}} |

</details>

## FAQ

<!-- MAX 5. Each question is one a named reader voice asked or would ask cold. Bold the question. -->
**{{Question a reader actually asked?}}**

{{Answer — direct, evidence-linked, no hedging.}}

## Point an agent at this

<!-- Optional but recommended: a paste-in orientation prompt so any agent with repo access onboards from the packet, not the aspirational design docs. Keep it in a fenced block (excluded from the prose count). -->
```text
{{Orientation prompt: what to read in order, verify commands with expected output, a self-test.}}
```

## Receipts

<!-- EXACTLY 3 proofs. Link stored outputs; do not paste them wholesale. -->
The proofs reproduce from {{source ref}}. Stored outputs in [`receipts/`](receipts/).

**{{Double-run / determinism proof}}** ({{[link](receipts/...)}}) — {{one line: what it shows}}.

**{{Test gate}}** ({{[link](receipts/...)}}) — {{the pass/fail claim}}.

**{{PR / merge trail}}** — {{provenance: PRs merged, review posture, clean-room note}}.

## Open threads (none block {{NEXT GATE}})

<!-- Items that proceed on a stated default unless the reader objects. Each names the default. -->
1. **{{thread}}** — {{the risk/decision}}. {{The default that engages if the reader says nothing.}}
