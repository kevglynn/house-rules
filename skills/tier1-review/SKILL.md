---
name: tier1-review
description: >-
  Run a Tier 1 same-model multi-lens review of a completed chunk of work:
  dispatch independent review subagents (code-reviewer, architect-reviewer,
  simplify, and — when the change involves tests or a no-test claim —
  test-signal) in parallel with a complete five-element
  context package, triage findings into Critical/Important/Minor with a
  disposition per finding, land fixes as a separate commit, file beads for
  deferred minors, and emit a close-evidence line. Use when the user says
  "tier 1 review", "run tier 1", "three-lens review", "multi-lens review",
  or when a feature/refactor bead reaches the self-review-done stage and the
  change meets the multi-agent-review trigger criteria.
---

# Tier 1 Review

Dispatch the multi-lens same-model review that the multi-agent-review rule
mandates, so every run is dispatch-complete (no lens forgotten, no context
element dropped) and triage-consistent (every finding gets an explicit
disposition). The rule states the law; this skill is the procedure.

## When to Use This Skill

Run Tier 1 when the change meets the multi-agent-review trigger criteria.
The criteria are owned by the always-on `multi-agent-review` rule; this
skill restates them for standalone invocation — if they ever disagree, the
rule wins:

- A component was decomposed (split into multiple production files)
- A shared component was created or significantly changed
- A structural change touches 3+ production files (excluding tests, docs,
  generated files, mechanical renames)
- The change affects a load-bearing boundary the project treats as high-risk
  (state management, auth, data integrity, public API surface)

**Skip it** (and say so) for: narrow bug fixes, config/chore/docs beads,
mechanical migrations, test-only changes. Do not run Tier 1 as ceremony on
work that doesn't meet the bar — a skipped review with a stated reason is
correct behavior.

**Sequencing:** Tier 1 runs *after* the implementing agent's self-review
against ACs and *before* the Tier 2 cross-model handoff. It supplements the
self-review; it never replaces it.

## Core Process

### Phase 1 — Assemble the context package

Build the five-element package every lens receives. All five are mandatory;
an incomplete package is the most common cause of shallow reviews.

1. **Bead description + acceptance criteria** — from `bd show <id>`
2. **Full file contents** of every changed/created file (not diffs alone —
   lenses need the surrounding code to judge boundaries and edge cases).
   Embed the contents in the prompt, or — when reviewers have file access —
   give exact paths with a read-completely instruction and a note pinning
   the state under review (branch/commit; confirm the working tree matches)
3. **Bead type** (feature/refactor/bug) — calibrates review depth
4. **Shared components the change depends on** — so reviewers can check
   integration, not just the new code in isolation
5. **Change summary** — what was done and why, 3-6 sentences, written fresh
   (do not paste the bead description as the summary)

Identify the changed-file set from the work's commits (`git diff
<base>..HEAD --stat` on the feature branch), not from memory.

### Phase 2 — Dispatch the lenses in parallel

Launch the subagents **in a single message**, one per lens, each with
independent context — no lens sees another's findings until triage:

| Lens | Focus | Catches |
|---|---|---|
| `code-reviewer` | Correctness, edge cases, race conditions, error paths | Logic bugs, state issues, missing guards |
| `architect-reviewer` | Pattern consistency, boundaries, reusability | Architectural drift, duplication, wrong abstractions |
| `simplify` | Over-engineering, unnecessary complexity | Gold-plating, dead code, YAGNI, stdlib replacements |
| `test-signal` | Test quality: would each test catch the defect it guards? | Zero-signal tests, ACs with no failing-capable test, helper-only bug tests, non-credible red-first claims |

The first three lenses always run. **Include `test-signal`** for
feature/bug/story/refactor beads whose change set includes test files, or
whose close will claim a no-test exception (the lens judges whether that
exception is legitimate for the bead type). **Omit it** for
docs/chore/config-only changes.

Lens prompt templates live in [lenses.md](lenses.md). Each prompt embeds the
full five-element package — subagents do not share the parent's context, so
nothing may be referenced by allusion.

Defaults: tool-native general-purpose subagents on the **same model as the
parent** (same-model multi-lens is Tier 1's design — cross-model diversity
is Tier 2's job). The overlay may override models per lens.

**Fallback (no parallel subagents):** run the passes sequentially,
writing each pass's findings to a scratch file *before* starting the next,
to prevent anchoring on your own prior findings.

**Recovery:** when collecting results, check each lens's final message
before triage. If it contains a verdict line (or section headers) without
the full findings, resume that subagent once with this fixed prompt — do
not re-run the lens fresh (that discards its analysis):

> Your final message did not contain the findings report — only your FINAL
> message is delivered; earlier messages are invisible. Repeat the COMPLETE
> findings report now, in full, in this message. Do not reference earlier
> messages. End with the verdict line.

In both observed failures to date, this prompt recovered the full report
cleanly on the first resume.

### Phase 3 — Triage

Collect all findings into one table. Every finding gets a severity and an
explicit disposition — no finding is silently dropped:

| # | Lens | Severity | Finding | Disposition |
|---|---|---|---|---|

Severities: **Critical** (correctness/data-loss/security — must fix before
close), **Important** (real defect or design problem — fix now),
**Minor** (polish, diagnostics, style — fix cheaply or defer).

Dispositions (pick exactly one per finding):

- **fixed** — change made, name the commit
- **accepted** — the flagged behavior is intentional; record the rationale
  (and, where the ceiling is real, a `defer:` comment or tripwire test that
  pins the accepted limitation)
- **deferred** — valid but out of scope now; file a bead *at triage time*
  and name it (a deferral without a bead ID is a dropped finding)
- **rejected** — the finding is wrong; record why in one sentence

When two lenses flag the same thing, merge into one row and credit both.
When lenses disagree, start from the more conservative position and document
the tension rather than letting the findings cancel out.

### Phase 4 — Fix, commit, file

1. Fix all Critical and Important findings immediately.
2. Commit fixes as a **separate commit** — never amend the original work.
   Commit message names the review: `fix: tier-1 review — <themes> (<bead-id>)`.
3. Re-run the project's quality gate (tests, lint) after fixes.
4. File beads for every deferred finding, with description and acceptance
   criteria — a bare title is not a filed finding.

### Phase 5 — Record and report

1. Append the triage table (or its summary) to the bead:
   `bd note <id> "Tier 1: <lens results + dispositions>"`. If the table is
   large, commit it as a review doc in the project's reviews directory and
   note the path.
2. **Pattern-level insight check:** if any finding revealed a systemic
   pattern — hidden coupling, an undocumented convention, a recurring
   anti-pattern — capture it with `bd remember --key <area>-<topic>` after
   the finding is resolved. Localized bugs don't qualify; patterns do.
3. Emit the close-evidence line for later use in `bd close --reason`:

```
Tier 1 (N lenses: code-reviewer, architect-reviewer, simplify[, test-signal]):
N Critical / N Important / N Minor — C/I fixed in <commit>,
minors <fixed in <commit> | carried to <bead-ids> | accepted with rationale in notes>.
```

## Project Overlay

Project-specific parameters live in `.agents/overlay.md` in the consuming
repo, under a `## tier1-review` section (shared overlay convention — one
file, one section per skill). Keys this skill reads:

| Key | Meaning | Default when absent |
|---|---|---|
| `models` | Per-lens model overrides, `lens: model-slug` lines | Parent model for all lenses |
| `focus` | Extra project-specific focus areas appended to every lens's context | None |
| `reviews_dir` | Where large triage tables are committed | `docs/reviews/` |
| `quality_gate` | Command(s) to re-run after fixes | Project's standard test/lint invocation |

The skill behaves sensibly with no overlay file: same-model lenses, no extra
focus areas, defaults above.

## Anti-Patterns

- **Shared-context dispatch.** Giving lens 2 the findings of lens 1 anchors
  it. Independence until triage is the point of multi-lens.
- **Diff-only packages.** A lens that can't see the surrounding file judges
  edge cases blind. Full file contents, always.
- **Findings without dispositions.** A triage table with an empty
  disposition column is a list of complaints, not a review. Every row closes.
- **Amending fixes into the original commit.** Destroys the review trail —
  the separate fix commit *is* the evidence that review happened.
- **Deferral IOUs.** "We should fix this later" without a bead ID filed at
  triage time is how findings evaporate.
- **Ceremony runs.** Running three subagents on a two-line bug fix wastes
  cycles and dilutes the signal of real reviews. Honor the skip conditions.
- **Simplify-lens suppression.** The simplify lens's free-form structural
  observations (section 2 of its output) are often the highest-value
  findings. Never harvest only its tagged lines.
