---
name: tier2-handoff
description: >-
  Run a Tier 2 cross-model review handoff on a Tier-1-reviewed chunk of
  work: gather the bead context, changed files, Tier 1 outcomes, and trusted
  boundary; draft the review-focus paragraph; call the deterministic
  assembler to emit a ready-to-paste prompt document for external models;
  then triage the returned findings (accept/reject with reason, conservative
  on disagreement) and emit the close-evidence line. Use when the user says
  "tier 2 review", "cross-model review", "tier 2 handoff", "assemble the
  review prompt", or when a shared-primitive bead has passed Tier 1 and needs
  external-model eyes before close.
---

# Tier 2 Handoff

Encapsulate the Tier 2 cross-model review the multi-agent-review rule
mandates. The toil — embedding files verbatim and scaffolding the prompt
sections byte-identically — is done by a deterministic script (`assemble.py`);
the judgment — what to focus reviewers on, and how to triage what comes back
— stays with the agent. The human-in-the-loop paste step is deliberate and
never automated.

## When to Use This Skill

Run Tier 2 after Tier 1, on changes that meet the multi-agent-review Tier 2
bar — strongly recommended for all structural changes, and **required** for
shared primitives (design-system components, shared hooks), app shell or
navigation, auth/authorization/security boundaries, and state-management
architecture. That bar is owned by the always-on `multi-agent-review` rule;
this skill restates it for standalone invocation — if they ever disagree,
the rule wins.

**Skip it** (and say so) for narrow bug fixes, config/chore/docs, and
mechanical migrations. If Tier 2 is warranted but deferred under pressure,
file a bead to track it before merge — don't silently drop it.

**Prerequisite:** the work is committed and pushed. Tier 2 review references
actual file contents across worktrees/machines; the snapshot under review
must be reproducible. Assemble against the committed state, not an uncommitted
working tree.

## Core Process

### Phase 1 — Gather inputs

From the bead and the branch:

1. **Bead context** — `bd show <id>`: description, ACs, type — plus a
   fresh **change summary** (what was done and why, 2-3 sentences). Both
   feed the spec's `context` field; reviewers must receive the change
   description, not only the component description.
2. **Changed/created files** — the exact set under review (`git diff
   <base>..HEAD --stat` on the feature branch). These become the verbatim
   embeds; keep the list tight (the reviewed surface, not its dependencies).
3. **Tier 1 outcomes** — the *already-addressed* list: what the multi-lens
   Tier 1 pass fixed or accepted, so external models don't re-report it.
   Pull from the bead notes / Tier 1 triage table.
4. **Trusted boundary** — the layers below the change that reviewers should
   *not* re-review (the canonicalizer, the storage trait, etc.), so effort
   lands on the new code.

### Phase 2 — Draft the focus paragraph (agent judgment)

Write the review-focus paragraph — the one section a script cannot generate.
It names the specific failure classes worth hunting in *this* change:
determinism holes, append-only violations, race windows, boundary bugs —
whatever the component's invariants make load-bearing. Concrete beats
generic ("any code path that returns a token when the bucket is empty" >>
"check for bugs"). This is the highest-value part of the handoff; spend the
judgment here.

### Phase 3 — Assemble the prompt (deterministic script)

Write a spec JSON and call the assembler:

```bash
python3 <skill-dir>/assemble.py --spec spec.json --root <repo-root> \
  --out docs/reviews/YYYY-MM-DD-tier2-<subject>-prompt.md \
  --exploit-out docs/reviews/YYYY-MM-DD-tier2-<subject>-exploit.md
```

The assembler embeds each file verbatim (picking a code fence longer than any
backtick run inside the file, so source containing ``` still embeds cleanly),
scaffolds every established section, and emits byte-identical output on
repeated runs. It reads nothing from the clock, environment, or network — the
`date` in the filename is caller-supplied, so re-running never churns the file.

`--exploit-out` is optional but **emit it whenever the change is a security or
untrusted-input boundary** (see the reviewer-lane policy below). It writes a
companion prompt — same verbatim embeds, same context/rules/already-fixed
sections — but swaps the review mandate for an adversarial-verification one:
the deliverable is a demonstrated invariant violation (exact inputs +
line-level code path) or a per-property proof that none exists, never "looks
fine". It goes to a *separate* model instance from the review lanes so its
output is not anchored by review framing.

The emitted prompt is phrased in **counterexample terms, not attack/exploit
terms** — same analytical demand, deliberately worded to avoid tripping
provider safety filters tuned for offensive-security requests (Fable 5's
guardrail did exactly this once, mid-generation). The `--exploit-out` flag
name is historical; the output says "adversarial verification", "invariants
to test", and "demonstrated violation", not "attack" or "exploit".

**Spec schema** (JSON object):

| Field | Req | Meaning |
|---|---|---|
| `subject` | ✓ | short subject line, e.g. `rate limiter + token bucket` |
| `bead_id` | ✓ | the bead id, rendered in the title |
| `language` | ✓ | e.g. `Rust`, `TypeScript` |
| `artifact_noun` | ✓ | e.g. `token-bucket module`, `write path` |
| `focus` | ✓ | the Phase 2 focus paragraph (one string) |
| `context` | ✓ | what the component is + what was done and why (change summary) + spec references |
| `files` | ✓ | list of paths relative to `--root`, in embed order |
| `models` | | reviewer names; default `["Grok", "Gemini", "GPT"]` |
| `trusted_layers` | | the "do not re-review" boundary description |
| `rules` | | list of domain rules the code must uphold |
| `already_addressed` | | list of Tier 1 outcomes; "don't re-report" |
| `report_format` | | override the default response-format ask |
| `out_of_scope` | | default `Style and performance polish` |
| `discipline` | | override the built-in review-discipline rules |
| `exploit_focus` | | attack charter for `--exploit-out`; defaults to `focus` |

The emitted review document has this fixed skeleton: title → paste header →
`---` → review instruction with the focus paragraph → `## Review discipline`
→ `## Context` (+ trusted layers) → `## Rules this layer must uphold` (if
given) → `## Already addressed` (if given) → `## Files` (verbatim embeds) →
`## Report format`.

The `## Review discipline` block is emitted into every prompt (override with
`discipline`). Its three default rules exist because triage history showed the
same failure modes recurring: clean verdicts issued with no verification, real
findings self-rejected as "out of scope", and packet claims taken on faith.
The rules are, in order: **verdicts require quoted-code evidence (a clean pass
included)**; **scope objections are findings tagged out-of-scope, never
self-rejections**; **the packet's own claims are assertions to verify, and
disproving one is a finding**.

Review the drafted prompt once, then hand the file(s) to the human to paste —
the review prompt into each reviewer lane, the exploit prompt (if emitted)
into its own separate instance.

### Phase 4 — Triage the responses (agent judgment)

When the external-model responses come back:

1. Record every finding with an **accept/reject disposition and a reason** —
   never rubber-stamp, never pad.
2. **On disagreement between models, start from the more conservative
   position** and document the tension; don't let opposite findings cancel.
3. Cross-check against the Tier 1 acceptances: a model re-flagging an already
   accepted ceiling is a reject-with-reason (point at the documented
   rationale), not a new finding.
4. Fix accepted Critical/Important findings; land them as a **separate commit**
   (`fix: tier-2 review — <themes> (<bead-id>)`), re-run the quality gate.
5. File beads for accepted-but-deferred findings, at triage time, with ACs.
6. Record dispositions in the bead: `bd note <id> "Tier 2 (<models>): ..."`.
7. **Pattern-level insight check:** capture systemic findings with
   `bd remember --key <area>-<topic>`.

### Phase 5 — Close evidence

Emit the line for `bd close --reason`:

```
Tier 2 (<models>): N accepted (fixed in <commit> | deferred to <bead-ids>),
N rejected-with-reason. Dispositions in notes.
```

## Project Overlay

Reads `.agents/overlay.md` § `tier2-handoff` in the consuming repo (shared
overlay convention — one file, one section per skill):

| Key | Meaning | Default when absent |
|---|---|---|
| `models` | Default reviewer set for the spec's `models` field | `Grok, Gemini, GPT` |
| `reviews_dir` | Where prompt docs are written | `docs/reviews/` |
| `quality_gate` | Command(s) to re-run after fixes | Project's standard test/lint |
| `reviewer_lanes` | Per-model effort/routing/probation policy | none — treat all `models` equally |
| `exploit_lane` | Which lane runs the `--exploit-out` mandate | none — emit only when the change is a security boundary |

With no overlay: the defaults above, and no per-lane policy.

**Reviewer-lane policy.** When the overlay carries a `reviewer_lanes` block,
honor it: browser/desktop reviewers only earn their keep at maximum thinking
effort (fast modes revert silently — confirm before a round), a lane may be
*routed* (used only on the change classes where it has a track record) or on
*probation* (dropped after N more net-negative rounds), and the exploit lane
runs the companion prompt from `--exploit-out`. This policy is data, not
dogma — it should trace to a scorecard of past rounds, and the triage note
records which lanes ran so the scorecard stays current.

## Anti-Patterns

- **Hand-assembling the prompt.** The verbatim-embed + scaffold step is pure
  toil and error-prone (a dropped file, a broken fence, a stale paste). Let
  the script do it; that's why it exists. Five hand-built prompt docs
  (5,000+ lines) is the friction this skill retires.
- **Assembling against an uncommitted tree.** External reviewers can't see
  your working copy; the snapshot must be committed and pushed so the review
  is reproducible.
- **Auto-sending to models.** The paste-and-collect step stays human. This
  skill produces the prompt and triages the response; it does not call
  external model APIs.
- **Generic focus paragraphs.** "Check for bugs" wastes the reviewers. Name
  the failure classes the component's invariants make dangerous.
- **Re-reporting churn.** Omitting the already-addressed list means models
  re-surface everything Tier 1 already handled. Always include it.
- **Rubber-stamp triage.** "All findings accepted" or "all rejected" with no
  per-finding reason is not triage. Each finding gets a disposition and a
  sentence.
- **Cancelling disagreements.** When two models conflict, the conservative
  finding is the default, not a wash.
