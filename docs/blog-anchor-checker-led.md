# My agent told me how long it would take. I wrote a linter that rejects that sentence.

**Status:** Draft. Publication candidate for the adoption funnel top.
**Publication target:** Owner blog primary; cross-post to dev.to / Medium secondary.

---

My coding agent opened a planning reply with a human-baseline estimate: calendar units, headcount, and a ship-by claim dressed as confidence. I stopped reading the plan and wrote a checker that flags that sentence class on exit code 1.

That checker is `banned-token-scan`. It is one stdlib Python file. You can run it without installing the rest of the kit.

## The artifact first

[Try it without installing](../README.md#try-it-now-no-install): curl the script, pipe a fixture sentence, watch labeled hits land (time-units, team-size, framing, estimation-verbs) and the process exit 1.

The rule behind it is simple. When an agent frames work-to-be-done, human-baseline estimation is banned. Describe complexity, scope, sequencing, and technical risk instead. The checker is the mechanism: it reports candidate hits from a versioned token catalog in `profiles/conventions.toml`. Exception judgment (historical facts, product timeouts, quoted references) stays with the reader. The scan reports; it does not pretend to understand intent.

This is the category claim in one move: a **versioned engineering playbook for AI coding agents**, where process knowledge is **checkable**. The model still has to follow the rule. The checker makes the miss visible.

## What that looks like in the dogfood record

The kit has been run under its own rules since the first commit. The excerpts below are from committed history and a live capture, not staged demos. Full receipts live in [`docs/transcripts/`](transcripts/).

### 1. Estimation corrected by a scan

[Transcript 01](transcripts/01-estimation-self-correction.md) is a live capture (2026-08-07). A fixture paragraph in the banned style is piped into `./scripts/banned-token-scan`. The tool returns seven labeled hits across three token classes and exits 1. The corrected form describes complexity and risk; it scans clean (exit 0).

Receipts: bead `process-kit-gsx`, commits `e4f310b` / `09ac541` / `19b06eb` / `d24a8b9`, and the red→green pairs in `.tdd-ledger.jsonl`.

### 2. A close refused as an IOU, then receipted

[Transcript 02](transcripts/02-evidence-refused-then-receipted.md) is historical. Bead `process-kit-0ei` had an acceptance criterion that required CI to fail on a seeded violation. The workflow existed, but the repo had never been pushed, so the draft close evidence was "it will fail once pushed." The first live four-lens Tier 1 review refused that shape. The completion rule already said deferred verification is an IOU, not evidence.

The fix moved the proof into the workflow: a self-test step that plants a violation and asserts the gate rejects it, run locally under the same bash flags Actions uses. The close reason maps the upgraded evidence. Later, `close-reason-lint` mechanized the IOU phrase class itself.

Receipts: bead `process-kit-0ei`, commits `515bb21` / `92589d6`, ledger lines for the CLI's own ceremony.

### 3. Deletion after a zero-hit field sweep

[Transcript 03](transcripts/03-graybeard-deletion.md) is historical. Transitional installer code recognized a legacy marker prefix so old machines could migrate in place. A Tier 1 architect review caught that the sunset condition lived only in prose. Bead `process-kit-26b` required a zero-hit field sweep across HOME artifacts and sync targets before any deletion. The sweep came back clean. Commit `61547ef` removed 216 lines across eight files. Malformed-marker guards stayed because they still protect current-marker files.

Receipts: commit `61547ef`, bead `process-kit-26b`, one-line summary in `AGENTS.md`.

## What the playbook is (after the receipts)

**house-rules** (working name process-kit until the release cut) is a versioned engineering playbook for AI coding agents: markdown rules, on-demand skills, and stdlib checker CLIs that travel with the repo. Cursor and Claude Code today; plain files so nothing locks you to a vendor.

It sits next to things you may already have:

- **AGENTS.md / CLAUDE.md** tell an agent how this repo works. The playbook adds checkable obligations (identity, deferrals, close-reason shape) and the CLIs that report when those obligations are missed.
- **beads** is structured task tracking for agents. The full playbook uses it; the core wedge does not require it. Stack them when you want the full loop.
- **obra/superpowers** and similar skill packs overlap on TDD ceremony, debugging, and review habits. Some procedures look familiar on purpose. What we ship in the wedge is the checkers plus a versioned conventions profile you can fork.

The wedge is pre-install. The aha is the try-it fence. Platform plugins (`house-rules-core`, then the full upgrade) are the install path. The integrated beads workflow is the power-user layer, offered once in-agent after core skills have already earned their keep.

Philosophy, if you want one sentence: process for agents fails when it lives only in prompt memory. Version the rules. Put a CLI on the parts that should be checkable. Keep the rest as skills the agent loads when the job needs them.

## Try it

[Run the README try-it block](../README.md#try-it-now-no-install). No clone, no plugin, no account: curl, python3, labeled hits, exit 1.

That is the only landing step this post asks for. Install paths, plugins, and the full playbook are linked from there when you want them.

---

*Kevin Glynn. Dogfood transcripts and checker receipts are in this repo under `docs/transcripts/`.*
