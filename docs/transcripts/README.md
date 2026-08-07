# Dogfood transcripts

This directory holds excerpts from the kit's own development history — the
repo has been run under its own rules since the first commit, and the
committed record (close reasons in `.beads/interactions.jsonl`, the
`.tdd-ledger.jsonl` evidence ledger, review records, git history) is where
these excerpts come from.

**Traceability guarantee.** Every excerpt is anchored to a commit hash, a
bead ID, or a ledger entry in this repo. Nothing is fabricated or
paraphrased: quoted text is verbatim from the source artifact, trimmed only
for length, with elisions marked `[...]`. Each file states whether it is a
**historical** record (quoted from committed history) or a **live capture**
(real tool output produced on a stated date, reproducible from any clone).
To re-verify: `git show <hash>`, `bd show <bead-id>`, or read the cited
file at the cited line.

## Index

| File | Moment | Kind |
|---|---|---|
| [01-estimation-self-correction.md](01-estimation-self-correction.md) | The banned-token scan catches human-baseline estimation in a draft | Live capture (2026-08-07) |
| [02-evidence-refused-then-receipted.md](02-evidence-refused-then-receipted.md) | A close's AC evidence refused as an IOU, then re-closed with receipts (process-kit-0ei) | Historical |
| [03-graybeard-deletion.md](03-graybeard-deletion.md) | 216 lines of transitional machinery deleted after a field sweep proved them dead (process-kit-26b) | Historical |

[demo-loops.md](demo-loops.md) is the capture storyboard for three ~20-second
demo recordings built on the same three moments.
