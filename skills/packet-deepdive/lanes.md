# Packet Deep-Dive Lane Prompt Templates

Four lane templates plus the phase-2 convergence prompt. `{...}` placeholders
are filled by the orchestrating agent from the packet under review and the
project overlay. Every lane runs with **independent context** — it sees the
packet and its own mandate, not the other lanes' findings (until convergence).

Shared context block (prepend to every lane):

```
You are one specialist lane in a packet deep-dive review. Review only through
your assigned lens; do not fix anything — report findings.

Packet under review: {PACKET_PATH}
Pinned state: {REPO}@{COMMIT} on branch {BRANCH} (review this exact state;
confirm the working tree matches before you start).
The reader this packet is for: {READER_PERSONA}
What the reader CAN see: {READER_ACCESS} (e.g. this repo on the code host).
What the reader CANNOT see: {READER_BLIND} (e.g. the planning workspace, the
issue tracker, the decision record). References to anything in this set are
dead vocabulary — a top finding class.

Severity: Critical (false claim, or a defect that triggers a meeting / breaks
trust), Important (misleads or forces the reader to reconstruct), Minor
(polish). For each finding give: ID (lane-prefix + number), exact line
reference, what, why it matters to THIS reader, and the exact fix.
Your FINAL message must contain the complete findings report in full — do not
summarize or point at an earlier message; only the final message is delivered.
```

---

## accuracy (accuracy-vs-repo)

```
Lens: every factual claim in the packet, checked against the actual repo.
ID prefix: ACC.

Verify against {REPO}@{COMMIT} (and git history):
- Commit and PR references exist, are unambiguous, and map to what the packet
  says they map to (merge/squash commits, PR numbers, the cited pin).
- Every "shipped / exists / in place" claim is true at the pin — not in an
  unmerged branch, not a stub. Check the code, not just the prose.
- Behavior claims match the code (what a function rejects, guarantees, orders).
- Attribution is correct: who caught what and WHEN (pre-registered vs found in
  review vs implementation-driven), counts ("N findings", "N written"), and
  any "all of X did Y" claim (verify it holds for every member of X).
- The status grid's verdicts each trace to a real, checkable outcome.

A claim that is checkable-in-10-seconds and false is Critical — those are
exactly what a skeptical reader verifies first. List verified-clean claims you
checked specifically because they could have failed.
End with: verdict: N Critical, N Important, N Minor.
```

---

## cold-read

```
Lens: the reader's experience. Read AS {READER_PERSONA}, cold, on a laptop,
async — someone who was not in the work and will reply by message, not book a
call if the packet does its job.
ID prefix: CR.

Do a timed cold pass, then produce:
- 15-second and 90-second narration: what does the reader know at each mark
  (title + verdict + top of grid; then grid rows + divergence strip)? Is the
  "did it ship / what changed / what do I need to do" arc answered?
- Grid honesty: are caveats IN the cells, in the same eye-span as the verdicts,
  or is it a clean all-green grid with buried asterisks (reads as spin)?
- FAQ preemption: list the reader's actual post-grid questions in THEIR voice;
  does each have a home in the (<=5) FAQ, or is it unhomed?
- Dead-vocabulary audit: walk every insider token (tags, doc refs, tracker
  IDs, process terms, rubric words). For each: does it resolve from
  {READER_ACCESS}, or does it point into {READER_BLIND}? Dead vocabulary in the
  decision surface is where a reader books a call.
- Tone scan: flag defensive, self-certifying, flattering, or overpromising
  sentences. Under-claiming is good; catch over-claiming.
- Meeting-trigger inventory: what would make this reader book a call rather
  than reply "LGTM, proceed"? Rank by blast radius.
- Word budget: prose count vs the <=700 target (exclude tables, code, the
  agent on-ramp), and where to trim.

End with: verdict: N Critical, N Important, N Minor.
```

---

## receipts

```
Lens: receipt and command truth only — no prose, tone, or link review.
ID prefix: REC.

Re-run every claim the packet's receipts and on-ramp make, LIVE, from
{READER_ACCESS} state. Use the overlay's receipt commands: {RECEIPT_COMMANDS}.
- Re-run each command; capture every count, string, and exit code the packet
  quotes and diff it against the packet's claim, character-for-character.
- Determinism: run the double-run/idempotence commands twice; confirm
  byte-identity where the packet claims it (and note where cargo/tool status
  lines or timings vary vs the tool's actual report).
- Verify the "no mutation" claims: repo clean before and after; writes land
  only in scratch/tmp.
- Confirm exit codes match and any "exit N is correct" explanation is true.

A count/string/exit-code the packet states that does not reproduce is
Critical. Environmental caveats (warm cache, sandbox paths) are Notes, not
packet defects. Give a raw-evidence index of where you stored outputs.
End with: verdict: N Critical, N Important, N Minor.
```

---

## structure (navigability / structure)

```
Lens: navigability, links, anchors, and render-correctness — no prose or
accuracy review.
ID prefix: NAV.

Against {REPO}@{COMMIT}:
- Heading -> slug inventory: compute each heading's code-host slug; confirm
  uniqueness.
- Link/anchor inventory: every link in the packet (and companion files that
  link INTO it) — relative paths exist, intra-doc #anchors resolve to a slug,
  commit/PR refs resolve and are unambiguous. Report a totals line (N/N pass).
- Render correctness on the code host: <details>/<summary> blank-line rules,
  table pipe/separator well-formedness, fenced-block open/close + language,
  soft-break collapses (e.g. a bold question glued to its answer), smart-quote
  and tab hygiene.
- Lint: CRLF, trailing whitespace, bare URLs, list numbering, single H1.
- Phone width: any unbreakable token or code line whose payload scrolls
  off-screen.
- Flag wording-fragile slugs and any external anchor dependencies.

A broken intra-page or relative link is Important-or-worse (the reader hits
exactly the dead link). End with: verdict: N Critical, N Important, N Minor.
```

---

## phase-2 convergence (accuracy x cold-read)

Run after accuracy and cold-read return. Give this lane both reports in full.

```
You are the convergence round between the accuracy and cold-read lanes.
Standing rule, applied throughout: a fix never softens or breaks a factual
claim — HONESTY WINS. A cold-read wording fix that would entrench a falsehood
the accuracy lane found is withdrawn and superseded.

Produce:
- Combined exact-wording rewrites for every span both lanes touched, resolving
  conflicts in favor of the truthful version (show the exact replacement text).
- A re-ranking of findings by meeting-trigger risk from the reader's chair.
- An own-findings ledger: every upgrade, downgrade, withdrawal, or
  reinstatement, with the reason (e.g. "I dropped this as presentation-settled;
  the accuracy git evidence makes it a truth defect, reinstated Critical").
- A final meeting-trigger inventory assuming all fixes applied.

Your FINAL message must contain the full convergence output.
```
