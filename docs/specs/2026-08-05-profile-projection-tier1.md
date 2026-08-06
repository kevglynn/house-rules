# Profile-driven projection — Tier 1 adoption

**Date:** 2026-08-05
**Beads:** epic process-kit-tlp — children process-kit-ouc (gate, first), process-kit-ywq (close-reason-lint), process-kit-kjz (defer grammar), process-kit-8dx (token catalog), process-kit-k6k (TDD obligations), process-kit-vr2 (distribution, last)
**Status:** Approved (decision recorded on process-kit-8qv, 2026-08-05)
**Sources:** docs/research/2026-07-21-profile-projection-spike.md (GO verdict, Recommendation);
docs/refinements/2026-07-19-kit-wide-mechanism-placement.md F10 + §8 (reopen trigger now fired);
prototype at experiments/profile-spike/

## Decision being implemented

Kevin's call (2026-08-05, on process-kit-8qv): **GO, Tier 1 only.** The three
adoption policy calls that the spike surfaced:

1. **Commit-type list:** `spike` is sanctioned as an allowed commit type.
   (`wip:` from worktree-awareness's example is NOT sanctioned — see open
   questions.)
2. **Profile format:** TOML parsed with stdlib `tomllib` (Python ≥ 3.11), not
   PyYAML. Kit scripts stay stdlib-only; the spike's `profile.yaml` converts
   to TOML at promotion.
3. **Checker mode:** advisory in target repos (doctor-style report, non-zero
   exit only where a target's own CI opts in), blocking in kit CI (the regen
   gate and convention checks fail the build).

Tier 2 (bead-AC requirements coordinated with `bd lint`, scratchpad/SUMMARY
tables) and the stay-prose judgment items are explicitly out of scope.

## Architecture and component overview

One machine-readable profile is the single source of truth for the kit's
data-shaped conventions. Two projections come off it: **rule text** (generated
fragments committed inside the canonical rules) and **checker behavior**
(the checkers read the profile at runtime instead of embedding the data).
A CI regen gate makes the committed fragments impossible to leave stale —
that gate is what upgrades "round trip works in a demo" to "drift is
structurally impossible," so it lands first and nothing else starts before it.

Components:

- **`profiles/conventions.toml`** — the profile. Schema carries forward the
  spike's structure (per-convention sections, element library with detectors,
  per-type `requires` lists, explicit `judgment` lists for what a checker
  cannot verify) with two extensions the gsx Tier 1 review identified:
  - **Pattern-plus-flags entries.** Composed patterns (team-of-N,
    roughly-N-unit, N-engineers) carry regex structure plus per-entry flags
    (e.g. ETA is case-sensitive-uppercase-only). Token entries are
    `{pattern, flags}` tables, not bare strings.
  - **A content-side exclusion contract for data files.** banned-token-scan's
    self-exclusion idiom (token literals assembled from parts so the checker's
    own source never self-flags) does not survive projection into a plain-data
    profile: a profile that lists banned tokens is itself token-laden, and
    every distributed copy would self-flag. The profile format therefore
    defines how checkers exclude profile data files by contract (a declared
    marker/section the scanner recognizes), not by path coincidence.
- **`scripts/conventions`** — the projection CLI, promoted from
  `experiments/profile-spike/conventions`. Subcommands as in the spike
  (`check-commit`, `check-branch`, `check-close --type`, `render-rule`),
  ported to tomllib, following the kit CLI conventions (argparse, JSON
  stdout, exit codes 0/1/2/3, non-interactive).
- **Generated rule fragments** — committed in place inside the existing
  canonical rules between `GENERATED from profiles/conventions.toml — DO NOT
  EDIT` markers. Tier 1 fragment homes: `operating-model.mdc` (git
  conventions), `bead-completion.mdc` (evidence table),
  `defer-convention.mdc` (defer grammar), `agent-identity.mdc` (banned-token
  catalog), `pragmatic-tdd.mdc` (obligations-by-type table). Claude
  projections regenerate through the existing `sync-rules.sh` pipeline
  unchanged — the fragment is just rule text by the time sync sees it.
- **CI regen gate** — new job in `.github/workflows/kit-ci.yml`: render every
  fragment from the profile, diff against the committed rule text, fail on
  any mismatch. Includes a seeded-drift self-test, same pattern as the
  existing projection-drift job (edit a fragment, assert the gate fails,
  restore).
- **Checker retrofits** — the three distributed checkers keep their names,
  JSON contracts, manifest rows (`scripts/distributed-clis.list`), and test
  suites, but their embedded convention data moves to the profile:
  `defer-lint` (defer grammar), `banned-token-scan` (token catalog),
  `close-reason-lint` (close-evidence shape — it becomes the production
  consumer of the profile's `close_evidence` section rather than shipping a
  second close checker alongside `conventions check-close`). `tdd-ledger`
  gains profile-read for the per-type test-obligations table (F10's
  parameterization note).

## Data flow and key interfaces

```
profiles/conventions.toml
  ├─ render → GENERATED fragments in cursor/rules/*.mdc   (committed)
  │             └─ sync-rules.sh → claude/rules + target repos (unchanged)
  ├─ runtime read → scripts/conventions, defer-lint,
  │                 banned-token-scan, close-reason-lint, tdd-ledger
  └─ CI: kit-ci.yml regen gate — render ≠ committed ⇒ fail (blocking)
        target repos — checkers advisory (doctor-style)
```

Profile path resolution for checkers: repo root of the repo being checked
(`profiles/conventions.toml`), so the distributed copy in a target repo is
found the same way as the kit's own. The profile distributes to targets with
the checkers (playbook-init) and is drift-checked by playbook-doctor like the
CLIs themselves.

## Trade-offs and decisions

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| YAML + PyYAML | Spike prototype already parses it | First non-stdlib dependency in kit scripts | **Rejected** — TOML + tomllib (Kevin, 8/5) |
| TOML + tomllib | stdlib-only holds; Python 3.11+ floor already met (3.12 here) | One-time YAML→TOML conversion; tomllib is read-only (fine — renderer emits markdown, never writes the profile) | **Adopted** |
| Blocking checks everywhere | Maximum enforcement | Targets did not opt into kit-strictness; advisory matches doctor posture | **Advisory in targets, blocking in kit CI** (Kevin, 8/5) |
| Generated fragments as separate included files | Clean separation | Cursor/Claude rules are single flat files; include mechanics don't exist | **In-file marked regions**, renderer/gate verify region content |
| New close checker (`conventions check-close`) shipped alongside close-reason-lint | No refactor of existing CLI | Two overlapping close checkers in targets; manifest and doctor confusion | **close-reason-lint becomes the profile consumer**; `conventions` keeps check-close for kit-CI use |
| Sanction `spike` commit type | Resolves spike finding 2 (the grammar bans messages the kit itself mandates) | Type list grows | **Adopted** (Kevin, 8/5) |

## Non-goals

- **Tier 2 conventions** (bead-AC requirements / `bd lint` coordination,
  scratchpad section names, scorecard item lists, doctor SUMMARY tables) —
  profile when touched next, not proactively.
- **Judgment-shaped content stays prose.** Roles, escalation ladders, review
  triage policy, the zero-signal taxonomy's application. The profile's
  `judgment` lists keep these visible; no attempt to encode them.
- **Full rule replacement.** Generated fragments state the law compactly; the
  why-paragraphs, worked examples, and anti-pattern narratives stay
  hand-written around them.
- **Semantic truth verification.** The close checker verifies shape, not that
  cited hashes exist or tests ran (cross-checking hashes against `git
  cat-file` is a noted cheap extension, not in this epic).
- **Blocking enforcement in target repos.**

## Risks and open questions

- [ ] **Profile self-flagging (gsx retrofit note).** The token-list section
  makes the profile a token-laden data file; the content-side exclusion
  contract must be designed so distributed copies don't self-flag while the
  scanner still catches tokens in real prose. Owned by the token-list child;
  the contract design is its first AC.
- [ ] **Generated-prose fidelity.** The renderer writes prose; wording
  differences from the current hand-written rule text need one human review
  pass at first generation (spike's own branch-naming line differed slightly).
- [ ] **Distributed contract stability.** defer-lint / banned-token-scan /
  close-reason-lint JSON contracts and exit codes are pinned by test suites
  and consumed by target repos; retrofits must keep suites green and change
  behavior only where the profile deliberately changes policy (spike type).
- [ ] **`wip:` commit type** (worktree-awareness's example uses it) remains
  unsanctioned — only `spike` was decided. Revisit if the checker flags real
  `wip:` usage on kit branches; that is a Kevin call, not an executor call.
- [ ] **Python floor in targets.** tomllib needs Python ≥ 3.11; playbook-init
  targets with older interpreters would break checker runtime. Doctor should
  report interpreter version if this bites; not expected on current machines.
- [ ] **Ambiguous branch grammar** (spike finding 3) stays as-is: the checker
  validates the checkable envelope; the grammar's bead-id/description
  boundary ambiguity is documented, not fixed, in Tier 1.
