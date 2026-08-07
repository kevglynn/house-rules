# 01 — Estimation self-correction

**Kind: live capture (2026-08-07).** The output below is real tool output
from this repo's checker, reproducible from any clone. The committed record
carries close reasons, review records, and session summaries, but no
verbatim agent responses — so there is no historical transcript of an agent
catching itself mid-sentence. What the history does carry is the enforcement
chain that makes the correction happen, and that chain can be run live.

## Context

The `agent-identity` rule bans human-baseline estimation when framing
work-to-be-done: no time units, team sizes, schedule framing, or estimation
verbs. Its self-correction protocol tells the agent to scan its own draft
before finalizing. A kit-wide placement audit found that protocol was
prescribed with no mechanism behind it, so the scanner was built test-first
under bead `process-kit-gsx` and the rule now points at it.

## Before — a draft the rule exists to stop

> Realistically this is a 2-3 week effort for one developer. I'd estimate
> the profile work alone takes a while, and with an aggressive timeline we
> could ship the checkers by end of week as a quick win.

(Fixture paragraph, written for this capture in the style the rule bans.)

## After — the scan, verbatim

```
$ printf '%s\n' "Realistically this is a 2-3 week effort for one developer. I'd estimate the profile work alone takes a while, and with an aggressive timeline we could ship the checkers by end of week as a quick win." | ./scripts/banned-token-scan
<stdin>:1: [team-size] one developer — Realistically this is a 2-3 week effort for one developer. I'd estimate the profile work alone takes a while, and with an aggressive timeline we could ship the checkers by end of week as a quick win.
<stdin>:1: [schedule-framing] by end of week — [...]
<stdin>:1: [schedule-framing] takes a while — [...]
<stdin>:1: [schedule-framing] aggressive — [...]
<stdin>:1: [schedule-framing] quick win — [...]
<stdin>:1: [schedule-framing] timeline — [...]
<stdin>:1: [estimation-verbs] I'd estimate — [...]
Scanned 1 file(s): 7 candidate hit(s). [grammar: /home/kevglynn/process-kit/profiles/conventions.toml]
$ echo $?
1
```

Seven labeled hits across three token classes, exit code 1, catalog read
from the committed conventions profile. Elisions `[...]` trim the repeated
echo of the scanned sentence; the hit lines are otherwise verbatim. The
rule's exception classes (historical facts, product behavior, quotes) are
deliberately not detected — the scan reports, the reader judges.

The corrected form of that paragraph, per the rule, describes complexity,
scope, sequencing, and risk instead — and scans clean (exit 0).

## Receipts

- **Bead:** `process-kit-gsx` — "Checkers: close-reason lint + banned-token
  scan (F4, F10)", closed 2026-08-05. Close reason maps AC2: "banned-token
  scan reports class hits: scripts/banned-token-scan, 27-test suite green
  incl. a 34-token catalog loop pinning every entry to its class."
- **Commits:** `e4f310b` (red test suites first), `09ac541` (both checker
  CLIs), `19b06eb` (agent-identity rule wired to the checker), `d24a8b9`
  (token catalog moved into `profiles/conventions.toml`).
- **Ledger:** `.tdd-ledger.jsonl` carries the red→green pairs for
  `scripts/tests/test_banned_token_scan.py` at commits `ce30ba2` (red,
  2026-08-05) and `e4f310b` (green), with output digests.
- **Rule text:** `cursor/rules/agent-identity.mdc`, "Self-correction
  protocol" section, including the mid-response fix idiom: "a brief
  '— scratch the weeks framing; the scope here is …' is enough."
