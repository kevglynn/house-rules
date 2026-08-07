# Demo loops — capture storyboard

Three ~20-second loops, one per transcript moment. Each has a **terminal
take** (deterministic: exact commands with verified output, safe to record
in one pass) and, where it earns the screen time, an **agent take** (a live
prompt to an agent in a bootstrapped repo — real behavior, may need
retakes). The 20-second budget is screen time only; setup and staging don't
count.

## Shared capture setup

- **Terminal takes:** record with [asciinema](https://asciinema.org)
  (`asciinema rec --cols 100 --rows 28 loopN.cast`, stop with `Ctrl-D`),
  then convert with `agg loopN.cast loopN.gif`. Any screen recorder pointed
  at the terminal window works too.
- **Agent takes:** OS screen recorder (macOS: Cmd-Shift-5; Windows/WSL:
  Xbox Game Bar or OBS), cropped to the Cursor or Claude Code chat pane.
- Terminal prep: `cd` to the repo root, dark theme, font 16pt+, shorten the
  prompt (`PS1='$ '`), clear the screen. Stage each command in shell
  history beforehand so on camera it's one up-arrow + Enter.

---

## Loop 1 — The estimate that doesn't survive the scan

**Premise:** an agent drafts "2-3 weeks for one developer"; the kit's
checker returns five labeled hits, and the corrected framing scans clean.

**Start state:** any clone of this repo (or any repo the kit's init has
bootstrapped — the checker is distributed), terminal at the repo root.

**Terminal take (~15s).** Two commands, staged in history:

```
echo "This will take 2-3 weeks for one developer, but with an aggressive timeline we could ship by end of week." | ./scripts/banned-token-scan
```

Expected output (verified 2026-08-07): five hit lines — `[time-units]
weeks`, `[team-size] one developer`, `[schedule-framing] by end of week`,
`[schedule-framing] aggressive`, `[schedule-framing] timeline` — then
`Scanned 1 file(s): 5 candidate hit(s).`, exit 1. Then:

```
echo "Three files change; the profile loader carries the risk; nothing blocks the checker work." | ./scripts/banned-token-scan
```

Expected output: `Scanned 1 file(s): clean.`, exit 0.

**Capture:** start recording on the cleared screen, up-arrow + Enter the
first command, pause two beats on the hits, run the second, stop one beat
after `clean`.

**Agent take (~20s, optional):** in a bootstrapped repo, submit the prompt
`How long will it take to add CSV export? Give me a rough estimate.`
Expected behavior: the agent declines the human-baseline frame and answers
in complexity, scope, sequencing, and risk (the agent-identity rule).
Start recording as the response begins streaming; stop after the reframed
answer's first paragraph. Retake if the response rambles past budget.

---

## Loop 2 — The close that won't take "Done"

**Premise:** a close reason of "Done, will verify later" is flagged as an
IOU with missing evidence; a real evidence-mapped close from this repo's
history passes the same check.

**Start state:** this repo's root (needs the committed beads DB and
`scripts/close-reason-lint`).

**Terminal take (~20s).** Two commands, staged in history:

```
printf '%s' '[{"id":"demo-1","status":"closed","issue_type":"feature","close_reason":"Done. Will be verified later in the PR pass.","acceptance_criteria":"Loading indicator appears during fetch"}]' | ./scripts/close-reason-lint
```

Expected output (verified 2026-08-07):

```
demo-1 (feature): missing commit-ref, ac-mapping; IOU phrase 'verified later' — Done. Will be verified later in the PR pass.
Checked 1 closed bead(s): 1 violation(s), 0 warning(s). [...]
```

exit 1. Then the real close from transcript 02:

```
bd show process-kit-0ei --json | ./scripts/close-reason-lint
```

Expected output: `Checked 1 closed bead(s): clean.`, exit 0.

**Capture:** start on the cleared screen, run the fixture command, hold on
the violation line (the IOU phrase callout is the money shot), run the real
close, stop one beat after `clean`.

**Agent take (~20s, optional):** in a repo with a claimed in-progress bead,
submit `Close <bead-id> with reason "Done".` Expected behavior: the agent
refuses, citing the bead-completion evidence policy, and either gathers the
evidence or leaves the bead in progress with a note. Start recording on
submit; stop when the refusal and its cited rule are on screen.

---

## Loop 3 — The kit deletes its own code

**Premise:** replay the receipts of commit `61547ef`: a field sweep proved
the legacy marker machinery dead, then 216 lines came out and the guard
comment became a sunset record.

**Start state:** this repo's root.

**Terminal take (~20s).** Two commands, staged in history:

```
git show --stat 61547ef
```

Expected output: the commit message `chore: sunset legacy
predecessor-prefix marker recognition (process-kit-26b)` and the stat
block ending `8 files changed, 101 insertions(+), 216 deletions(-)`. Then:

```
git show 61547ef -- scripts/install-aliases.sh | head -30
```

Expected output: the diff hunk where the six-line "keep the legacy
recognition until..." comment is replaced by the four-line "sunset
2026-08-06 (process-kit-26b) after a field sweep showed zero old-marker rc
blocks remaining" record, followed by the deleted `LEGACY_SOURCE_*`
constants.

**Capture:** start on the cleared screen, run the stat command, hold two
beats on `216 deletions(-)`, run the diff command, stop with the
replaced comment centered on screen.

**Agent take:** none. An agent performing a real evidence-gated deletion
doesn't fit in 20 seconds; the historical replay is the honest version of
this moment.
