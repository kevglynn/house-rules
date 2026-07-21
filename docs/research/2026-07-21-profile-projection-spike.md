# Profile-projection spike: git grammar + close-evidence shape (F10)

**Date:** 2026-07-21
**Bead:** process-kit-vgz (spike, epic process-kit-iow, Wave 3)
**Spec context:** docs/refinements/2026-07-19-kit-wide-mechanism-placement.md (F10);
docs/research/2026-07-19-operating-surface-catalog.md Part 5 (the pattern's
first-party reference implementation)
**Prototype:** `experiments/profile-spike/` — NOT production-integrated (per AC)

## Question

Does the profile-driven projection pattern — one machine-readable profile,
with the checker and the rule text both projected from it — make drift
between rule and checker structurally impossible for the kit's data-shaped
conventions, and at what cost? Go/no-go for profile-izing the remaining ~20
conventions.

## Answer up front

**Go — with a narrowed scope.** The round trip works exactly as the pattern
promises: one profile edit changed both the checker verdict and the
generated rule text with no second edit, so rule↔checker drift is
structurally impossible *for what the profile encodes*. The honest boundary
found by building it: roughly half of each convention's prose is
data-shaped and projects cleanly; the other half is judgment that must stay
prose, and the profile has to say so explicitly or it overclaims. Cost was
low (~475 lines total for two conventions, most of it reusable
infrastructure). Recommendation and ordering in the final section.

## What was built

All under `experiments/profile-spike/`:

| File | Lines | Role |
|---|---|---|
| `profile.yaml` | 129 | Machine-readable encoding of commit grammar, branch grammar, and close-evidence shape per bead type (12 types), with source pointers into the prose rules and explicit `judgment:` lists for the non-checkable parts |
| `conventions` | 242 | Python CLI (tdd-ledger conventions: argparse, JSON stdout, exit codes 0/1/2/3, non-interactive). Subcommands: `check-commit`, `check-branch`, `check-close --type`, `render-rule` |
| `demo-cases.sh` | 78 | 20 demonstration cases — real commits from `git log`, real close reasons from `bd show`, synthetic negatives. All 20 behave as expected |
| `round-trip-demo.sh` | 27 | Reproducible round-trip evidence (below) |

The profile encodes only what the prose prescribes today. Two conventions:

1. **Git grammar** (operating-model.mdc § Git Conventions): commit format
   `<type>: <summary>`, the six allowed types, the under-72-char summary
   cap; branch format `<type>/<bead-id>-<short-description>`.
2. **Close-evidence shape** (bead-completion.mdc evidence table +
   beads-quality.mdc): per-bead-type required elements (commit ref, AC
   mapping, N/A markers, findings summary, children-closed statement), plus
   the IOU-phrase ban with its one sanctioned exemption
   (`deferred to bead <id>`).

## Round-trip evidence

`round-trip-demo.sh`, run against the committed profile:

```
BEFORE: check-commit "spike: profile-ize git grammar end-to-end (process-kit-vgz)"
  → {"ok": false, violations: [commit-type: `spike` not in allowed types]}
  render-rule → "types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`"

THE EDIT (one line in profile.yaml):
  types: [feat, fix, refactor, test, chore, docs]
  → types: [feat, fix, refactor, test, chore, docs, spike]

AFTER (same checker binary, same generator, zero code edits):
  → {"ok": true, violations: []}
  render-rule → "types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `spike`"
```

Both surfaces updated from the single edit. Neither the checker nor the
generator contains the type list — only the profile does. Drift between the
rule text and the checker is structurally impossible, **provided** the
committed rule fragment is regenerated (the reference implementation closes
that last gap with a CI drift gate: fail if rendered output ≠ committed
fragment; this spike did not build the CI gate, but tdd-ledger's existing
gate is the template).

### Generated fragment vs. current prose (git section)

Current prose (`cursor/rules/operating-model.mdc` lines 227–232):

```227:230:cursor/rules/operating-model.mdc
## Git Conventions

- **Commit messages:** `<type>: <summary>` — types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`. Keep summaries under 72 characters.
- **Branch naming:** `<type>/<bead-id>-<short-description>` (e.g., `feat/gastown-abc-loading-ux`).
```

Generated (`conventions render-rule`, first section):

```markdown
<!-- GENERATED from experiments/profile-spike/profile.yaml — DO NOT EDIT. ... -->

## Git Conventions

- **Commit messages:** `<type>: <summary>` — types: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`. Keep summaries under 72 characters.
- **Branch naming:** `<type>/<bead-id>-<short-description>` — same types; kebab-case bead id + short description (e.g., `feat/gastown-abc-loading-ux`).
```

The commit line reproduces byte-for-byte semantics. The close-evidence
section renders as a three-column table (bead type / machine-checked
elements / judgment obligations) that is arguably *more* honest than the
current prose because it separates what a checker verifies from what the
agent still owes. Two prose bullets do NOT project: "commit at logical
checkpoints, prefer small atomic commits" and "never force push without
approval" — both are judgment/behavior, not data, and stay prose.

## Findings from running against real repo history

These fell out of the demonstration cases and are evidence in themselves
that the prose conventions are currently unenforced:

1. **7 of the last 20 real commits on main violate the repo's own
   summary-length cap** (under 72 chars), including commits by
   rule-following agents (e.g. `0fcdb1d` at 87 chars, `45ce310`, `52b45df`
   sequence-mates). The convention has been prose-only and it shows.
   Nothing else — format and type discipline — was violated in 20 commits.
2. **The commit message mandated for this very spike violates the current
   grammar twice**: `spike:` is not an allowed type, and the summary is 86
   chars. The round-trip demo turns the first half of this into the
   demonstration edit. If the profile goes live, either `spike` (and
   plausibly `wip:` from worktree-awareness.mdc's example) gets added to
   the type list, or coordinators stop mandating out-of-grammar messages —
   the profile forces that decision into the open, which is the point.
3. **The branch grammar is inherently ambiguous**: `<bead-id>` and
   `<short-description>` are both kebab-case, so the boundary is not
   parseable (`feat/gastown-abc-loading-ux` splits three ways). The checker
   validates the checkable envelope (known type + kebab slug with ≥2
   segments). Encoding the convention exposed a latent spec gap that prose
   had hidden.
4. **All 5 sampled real close reasons pass their type's evidence shape**
   (task 815, feature 0ei, spike 2k9, epic 6hx, plus a docs-style N/A
   case), and the checker correctly rejects "Done", missing commit refs,
   and IOU phrases while exempting the sanctioned
   `deferred to bead <id>` form. The close-evidence culture is real; the
   checker would ratify it, not fight it.

## Cost accounting (honest)

- **Schema design:** the dominant cost, and it is a *reading* cost, not a
  writing cost — most of the session's design effort went into deciding
  what the prose actually prescribes (is "under 72" strict? does the cap
  apply to the summary or the whole subject? which close-reason forms are
  sanctioned?). ~129 lines of YAML, roughly half comments documenting
  source pointers and honesty boundaries. This cost recurs per convention
  but shrinks with practice; the element-library shape (detectors + per-type
  requires) generalizes directly.
- **Checker complexity:** low. ~240 lines including argparse plumbing,
  of which the actual check logic is ~90 lines of regex-and-lookup. No
  state, no I/O beyond the profile read. The close-evidence checker is
  the deepest part and it is still just "required elements present +
  banned phrases absent."
- **Generator complexity:** trivial. ~45 lines of string assembly. The
  risk is not complexity but *fidelity drift* — the generator writes prose,
  and prose wording choices (e.g. my branch-naming line differs slightly
  from the original) need one human review pass at adoption time.
- **Integration surface (not built, but scoped):** a CI drift gate
  (rendered-vs-committed diff, same pattern as the tdd-ledger gate in
  `.github/workflows`), a home for the profile (`profiles/` or
  `cursor/profile.yaml`), sync-rules.sh awareness so generated fragments
  distribute to target repos, and a decision about whether checks run as
  advisory (doctor) or blocking (CI/hook). This is the real adoption cost
  — the prototype itself was cheap.
- **New dependency:** PyYAML (already present in the environment; the kit's
  scripts are currently stdlib-only, so this is a real, if small, decision).

## What the pattern does NOT solve

- **Judgment-shaped policy.** "Prefer small atomic commits," "never force
  push without approval," "test output *genuinely* covers each AC," "the
  spike question was *actually* answered" — none of this is data. The
  profile's `judgment:` lists keep these visible per type precisely so the
  checker's green cannot be mistaken for full compliance. A profile that
  tried to encode these would become config nobody can evaluate (the
  catalog's Part 5 boundary, confirmed hands-on).
- **Evidence truthfulness.** The close checker verifies *shape* (a commit
  hash is cited, ACs are referenced), not that the hash exists, the tests
  ran, or the claims are true. Shape-checking still has teeth — it catches
  "Done" — but it is a floor, not a verifier. (Cross-checking cited hashes
  against `git cat-file` is a cheap future extension; semantic truth is not.)
- **Prose that teaches.** The generated fragment states the law compactly;
  it cannot carry the *why* paragraphs, worked examples, and anti-pattern
  narratives that make rules like beads-quality effective. The realistic
  end state is thin generated law + hand-written prose commentary around
  it, not full rule replacement.
- **The last-mile gate.** Round-trip only guarantees no-drift if the
  committed generated fragment is refreshed; without the CI diff gate the
  pattern degrades to "two things to edit" again. The gate is mandatory,
  not optional, in any production adoption.

## Recommendation: GO, in this order

Profile-ization should proceed, ordered by how purely data-shaped each
convention is:

**Tier 1 — profile next (pure data, checker nearly free):**
1. Defer-comment grammar (defer-convention.mdc — the regex is literally
   already written in the rule; `ceiling:`/`upgrade when:` presence check).
2. Banned-token lists (agent-identity.mdc time-units/team-size/schedule
   vocabularies — pure word lists, and the rule already describes itself as
   "a mechanical check").
3. Commit/branch grammar + close-evidence shape — this spike's profile,
   promoted from `experiments/` with the CI drift gate added, after the
   type-list decision (finding 2).
4. Evidence-requirements + test-obligations-by-bead-type tables
   (bead-completion.mdc, pragmatic-tdd.mdc — same per-type table shape as
   close-evidence; could parameterize the tdd-ledger per F10's note).

**Tier 2 — profile later (data core with prose halo):**
5. Bead AC requirements by type (`bd lint` already half-owns this;
   coordinate rather than duplicate).
6. Scratchpad section names, scorecard item lists, doctor SUMMARY-key
   table (enumerable, but consumers are few — profile when touched next,
   not proactively).

**Stay prose (judgment-shaped — do not attempt):** operating-model roles
and escalation ladders, parallel-subagent blast-radius reasoning,
multi-agent-review triage policy, ponytail decision ladder, the zero-signal
test taxonomy's *application* (the class names are data; deciding a test is
zero-signal is not), worktree conceptual model.

One-paragraph justification: the spike delivered the pattern's core claim
at prototype cost — a single profile edit moved both the checker and the
rule text, and the demonstration cases showed the checker ratifying real
repo practice while catching exactly the violations the prose has been
silently tolerating (7/20 commits over the length cap). The costs that
remain are adoption costs (CI gate, profile home, sync distribution, one
type-list policy decision), all of which have existing in-repo templates,
and the pattern's boundary — judgment stays prose — held up cleanly in
practice via the `judgment:` field rather than requiring any redesign.

## Reproducing

```bash
bash experiments/profile-spike/demo-cases.sh      # 20/20 cases
bash experiments/profile-spike/round-trip-demo.sh # round-trip evidence
python3 experiments/profile-spike/conventions render-rule
```
