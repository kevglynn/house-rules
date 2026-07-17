---
name: packet
description: >-
  Author a gate/sprint review packet from a committed blueprint: gather the
  gate's bead evidence and receipts, populate the reader's-own-checklist
  status grid with a divergence strip, a capped FAQ, and exactly three linked
  receipts, carry the decision vocabulary into the reader's repo, then verify
  it headlessly and share the single packet.md markdown file. Use when the
  user says "build the packet", "gate packet",
  "sprint packet", "assemble the G2/G3 packet", or when a gate/sprint reaches
  close and needs a review artifact for a cold reader.
---

# Packet

Encapsulate gate/sprint packet authoring. The blueprint — proven on the Gate 1
packet and its cold-read council — lives as a committed template instead of an
agent's memory, so every packet has the same reader-first shape: the reader's
own checklist answered at a glance, deviations surfaced immediately, evidence
linked not dumped, and a verifier that catches the failure modes (broken
anchors, an overgrown FAQ, missing receipts) before the reader ever sees them.

## When to Use This Skill

Run at a gate or sprint close that needs a review artifact for someone who
was not in the work — a reviewer, a stakeholder, a cold agent. Skip it for
internal checkpoints with no external reader.

**Companion:** `packet-deepdive` validates a drafted packet with parallel
cold-read lanes. Author with this skill; validate with that one.

## Core Process

### Phase 1 — Gather evidence

From the gate and its beads:

1. **The reader's checklist** — the exact wording of what the reader asked
   for (their plan text, the gate's deliverable list). The status grid uses
   *their* words, verbatim — not your restatement.
2. **Gate bead evidence** — `bd show` the gate epic and children, close
   reasons, commit/PR links. Each grid row's verdict must trace to a bead
   outcome.
3. **Receipts** — the three proofs: a double-run/determinism capture, the
   test-gate output, and the PR/merge trail. Store the raw outputs in a
   `receipts/` dir; the packet links them.
4. **Divergences** — where the delivered work differs from the reader's plan
   text, and whether each was pre-registered (a deliberate day-one narrowing)
   or found in review. This is the highest-trust content: surface it, don't
   bury it.

### Phase 2 — Carry the decision vocabulary in

The reader can see the target repo, not the planning workspace where the
decision record (D*/A* tags, amendment log) normally lives. Any tag the
packet references must be explained *in the packet or the target repo*. This
is a hard constraint, not a nicety — a packet that cites `D4-L1` the reader
can't resolve is a dead reference. The overlay names where the vocabulary
import lives; if absent, inline the definitions.

### Phase 3 — Draft against the template

Copy `template.md` and fill it. The blueprint constraints it encodes:

- **Status grid** — one row per reader-checklist item, in their words, with
  the verdict **bold in the cell** and linked evidence.
- **Divergence strip** — a blockquote in the *same eye-span* as the grid, so
  deviations hit before the reader scrolls. If there are none, say so in one
  line rather than omitting the strip.
- **FAQ** — hard-capped at 5. Admission rule: **a named reader voice actually
  asked it** (or would, cold). Do not pad to 5.
- **Prose ≤ 700 words** (tables, code, and the agent on-ramp don't count) —
  a target, warned not enforced.
- **Receipts — exactly 3**, linked, not dumped inline.
- Optional **agent on-ramp** — a paste-in orientation prompt so a cold agent
  reads the packet, not the aspirational design docs.

Write the packet to the consuming repo at `docs/<gate>/packet.md` (per the
packet naming convention).

### Phase 4 — Verify

```bash
python3 <skill-dir>/render.py --in docs/<gate>/packet.md --verify
```

**The share artifact is the markdown file itself** — a single, simple
`packet.md` (reader preference, 2026-07-16: plain markdown over generated
HTML). `render.py --verify` runs checks-only with no output file; the HTML
render (`--out`) remains available as an optional offline view but is no
longer the share step. The verifier runs headlessly (no browser):

- **Blueprint checks** — grid present, FAQ ≤ 5 (error if over), exactly 3
  receipts (error otherwise), divergence strip present (warn), prose ≤ 700
  (warn).
- **Anchor integrity** — every intra-page `#link` resolves to a heading id;
  a dangling cross-link is an error. This is the failure mode a browser would
  hide and a cold reader would hit.

Fix every error before sharing. Warnings are judgment calls (the G1 packet
ran to ~1100 prose words and shipped — a documented, deliberate exception).

> The renderer deliberately does **not** run a browser. Gate packets are
> prose + tables + links; if a packet needs rendered diagrams (mermaid), that
> is the architecture-packet builder's headless-Chromium path, out of scope
> here.

### Phase 5 — Record

- Commit `packet.md` and `receipts/` to the target repo (plus the rendered
  HTML only if the optional render was produced).
- The share the reader receives is the single `packet.md` markdown file.
- **When this skill first lands, update the `gate-packet-blueprint` memory**
  (if the project uses one) to point at the committed template — the template
  is now the single source of truth, not the memory.

## Project Overlay

Reads `.agents/overlay.md` § `packet` in the consuming repo (shared overlay
convention — one file, one section per skill):

| Key | Meaning | Default when absent |
|---|---|---|
| `reader_checklist` | Where the reader's own deliverable wording lives | Ask / infer from the gate bead |
| `decision_vocabulary` | Path to the decision-record tags to carry into the packet | Inline definitions as needed |
| `packets_dir` | Where packets are written | `docs/<gate>/` |
| `receipt_commands` | Commands whose output becomes the receipts | Project's standard test/run |

With no overlay: infer the checklist from the gate bead, inline any decision
tags, write to `docs/<gate>/`.

## Anti-Patterns

- **Restating the reader's checklist in your words.** The grid must use their
  wording verbatim, or they can't map it to what they asked for.
- **Burying divergences.** Deviations go in the strip, in the grid's
  eye-span — not in a section the reader reaches after deciding you're done.
- **Padding the FAQ to 5.** The cap is a ceiling, not a quota. Every entry
  earns its place by being a question a reader actually asks.
- **Dumping receipts inline.** Three linked proofs, not three walls of
  console output. Link the stored capture.
- **Dead decision references.** Citing a `D*/A*` tag the reader can't resolve
  in their repo. Carry the vocabulary in.
- **Shipping on a red verifier.** A dangling anchor or an over-cap FAQ is an
  error for a reason — the cold reader hits exactly those.
- **Hand-writing the HTML.** If the optional HTML view is rendered, it is
  generated from `packet.md`; never hand-edit it (overwritten on every
  render). The share is `packet.md` itself.
