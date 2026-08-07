# 02 — A close refused for missing evidence, then receipted

**Kind: historical.** Every quote below is verbatim from a committed
artifact in this repo, cited by hash or entry ID.

## Context

The `bead-completion` rule's evidence policy has been law here since the
first commit (`38cf2f3`): a close reason must map evidence to each
acceptance criterion, and deferred verification doesn't count —

> "will be verified later" is an IOU, not evidence

(`cursor/rules/bead-completion.mdc`, "Do not defer AC verification").

On 2026-07-19 that law met its first live test. Bead `process-kit-0ei`
shipped the TDD evidence-ledger CLI; its AC2 required the CI workflow to
"demonstrably fail on a seeded violation." The workflow existed, but the
repo had never been pushed, so no Actions run had happened. The draft close
evidence for AC2 amounted to "it will fail once pushed" — exactly the IOU
shape the rule forbids. The first live four-lens Tier 1 review refused it.

## Before — the refusal, as the session log recorded it

From the session working log (`.cursor/scratchpad.md`, an untracked working
file — session record, not a committed artifact):

> `0ei` CLOSED (commits `515bb21` impl + `92589d6` tier1 fixes). First live
> 4-lens tier1 review completed: 0 Critical / 7 Important / 10 Minor [...]
> AC2 evidence upgraded from IOU to in-workflow gate self-test (seeded
> violation demonstrably fails, verified locally under Actions bash flags)

The committed anchors for the same event are the close reason below (whose
own wording records the upgrade) and the workflow step it produced.

## After — the close reason, verbatim

From `.beads/interactions.jsonl`, entry
`int-459aae0036b0449a9ac12ba32b372112` (committed; also shown by
`bd show process-kit-0ei`):

> AC2: workflow runs suite + verify + a NEW gate self-test step that seeds
> a green-without-red and asserts verify fails — the exact step run locally
> under Actions bash flags: seeded violation exits 1, self-test passes
> (demonstration in-workflow now, not an IOU; actual Actions run pending
> first push, covered by the self-test being part of every future run).

Instead of promising a future CI run, the fix moved the proof into the
workflow itself: a self-test step that plants a violation and asserts the
gate rejects it, run locally under the same bash flags Actions uses. The
step is still in the tree:

```
      - name: Gate self-test — a seeded violation must fail verify
        run: |
          seeded=$(mktemp)
          echo '{"event":"green","test_id":"seeded","bead":"x","output_digest":"d","commit":"c","ts":"2026-01-01T00:00:00+00:00"}' > "$seeded"
          if python3 scripts/tdd-ledger verify --ledger "$seeded"; then
            echo "seeded green-without-red did NOT fail the gate" >&2
            exit 1
          fi
          echo "gate correctly rejects seeded violation"
```

(`.github/workflows/tdd-ledger-verify.yml`, the step added for this close.)

## Receipts

- **Bead:** `process-kit-0ei` — full close reason maps all four ACs;
  the AC2 passage above is quoted unaltered.
- **Commits:** `515bb21` (implementation), `92589d6` (Tier 1 fixes,
  including the self-test step), both resolvable in this repo's history.
- **Ledger:** `.tdd-ledger.jsonl` lines 1–4 — red and green entries for
  `scripts/tests/test_tdd_ledger.py` at commits `21b0201` and `f097103`,
  the CLI proving itself under its own ceremony.
- **Aftermath:** the IOU check was later mechanized — `scripts/close-reason-lint`
  now flags the phrase class directly. Run over this repo's own closed
  beads (70 checked, 2026-08-07) it reports 3 historical violations, each
  dispositioned by `bd note` and left standing as findings.
