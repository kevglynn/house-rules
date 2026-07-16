<!--
PACKET DEEP-DIVE REPORT TEMPLATE — the dispositions doc.
Lands in the consuming repo at docs/reviews/YYYY-MM-DD-<gate>-packet-deepdive.md,
with the four full lane reports in a sibling YYYY-MM-DD-<gate>-packet-deepdive/ dir.
Fill every {{PLACEHOLDER}} and delete these comments.
-->
# Deep-dive review — {{GATE}} packet (`{{PACKET_PATH}}`)

**Date:** {{DATE}} · **Bead:** {{BEAD}} · **Subject at review time:** branch `{{BRANCH}}` @ `{{COMMIT}}`

<!-- The process note carries the resilience record: how the lanes ran and any orchestrator failure the parent recovered from. -->
**Process note.** A deep-dive orchestrator ran four specialists in parallel —
accuracy-vs-repo, cold-read (simulated {{READER}}), receipts verification, and
navigability/structure — with a phase-2 convergence round between the accuracy
and cold-read lanes. {{IF the orchestrator died: "The orchestrator process was
killed by {{cause}} after all N specialist reports were written; the parent
agent performed the final synthesis and triage recorded here."}} Full
specialist reports: [`{{DATE}}-{{GATE}}-packet-deepdive/`]({{DATE}}-{{GATE}}-packet-deepdive/).

## Verdict

{{One paragraph: receipts state (clean / drifted), link-resolution totals, and
the headline finding counts by severity. State whether all Critical/Important
were fixed before delivery.}}

## Findings and dispositions

### Critical — {{all fixed | N open}}

| ID | Finding | Disposition |
|---|---|---|
| {{ACC-1}} | {{one-line finding}} | **Fixed** — {{exact change, why it's now true}} |

### Important — {{all fixed | N open}}

| ID | Finding | Disposition |
|---|---|---|
| {{ID}} | {{finding}} | **Fixed** — {{change}} |

### Minor — {{fixed | deferred}}

{{Prose run or table: each Minor ID with its one-line disposition. Deferred
minors must name a follow-up bead ID.}}

### Rejected / not applied

| ID | Finding | Reason |
|---|---|---|
| {{ID}} | {{finding}} | {{why it was not applied — a real reason, not a shrug}} |

## Post-fix state

- {{Word count vs target, and the ruling if over (honesty-wins exceptions belong here).}}
- {{Cold-read's post-fix meeting-trigger inventory: what residuals remain and their grade.}}
- {{Share re-rendered from the fixed packet and re-verified (render.py --verify).}}
- {{Receipts state after fixes.}}
