# Refinement Proposal: Kit-wide mechanism-placement audit

**Date:** 2026-07-19
**Initiator:** agent (refinement-initiative session) on behalf of kevglynn — **Reason initiated:** capability-matured + periodic-hygiene triggers (mechanism-side): the operating-surface catalog and the pragmatic-tdd pilot produced a placement doctrine the rest of the kit has never been audited against. Bead: process-kit-l1h.
**Mode:** retrospective · **Refinement object(s):** mechanisms
**Scope:** every operating surface the kit ships or prescribes — all always-on rules (`cursor/rules/*.mdc`), all registered skills (`skills/`), hooks (`.claude/hooks/`), distribution surfaces (init/sync/doctor scripts, safety net, templates), enforcement gaps (permissions, CI), memory/knowledge infra, tracker-usage prescriptions, and docs-governance surfaces. **Out of scope:** the *content* of any discipline (test policy substance, bead-quality standards substance) — this audits representation and placement only, per the pilot's precedent. No reshaping is executed under this proposal's bead; accepted findings become new beads.
**Execution during refinement:** continues — no live epic is paused; this is the first real run of the refinement capability itself.
**Status:** Under review

## 1. Executive summary

Every operating surface the kit ships was audited against the placement
doctrine by four parallel evidence lanes (rules, skills, event/distribution,
tracker/templates). The headline: **the kit's problem is not wrong content
but wrong addresses.** The ~1,008-line always-on rule payload is only ~30%
law — the rest is procedure and enumerable data paying context rent at the
policy address, and where the same content lives in two places it has
already drifted (the always-on review rule mandates three lenses; the skill
it doesn't know exists mandates four). Every "MANDATORY/required/MUST" in
the ruleset resolves to advisory in practice; one hook subsystem is dead
code that has captured zero knowledge while presenting itself as evidence
capture; and the distribution layer re-checks only rules, leaving hooks,
skills, and the AGENTS.md section as silent drift channels. Set against
this, the two surfaces whose placement was *deliberately designed* — the
post-split pragmatic-tdd pair and the doctor's agent contract — are exactly
the ones the audit confirms correct, which is strong evidence the doctrine
predicts outcomes. The recommendation is a three-wave response (correct
broken pointers and prescriptions; replicate the pilot's split topology on
the worst rules; add cheap deterministic enforcement and run the profile
spike), executed as beads only after this proposal's approval gate. Largest
magnitude involved: **major** (cross-cutting).

## 2. Governing intent

Authoritative sources for what the kit's mechanisms are *for*, in precedence
order:

1. **PLAN.md** — the kit is a portable, project-neutral AI-native development
   kit (rules + skills + safety nets + distribution scripts), incubating
   toward open-source publication behind a readiness checklist (IP clear,
   skills stable, second-consumer proof, neutrality audit). Design rule:
   generic core / project overlay; skills never name projects or people.
2. **docs/specs/2026-07-19-refinement-initiative.md** — the governing intent
   frame for this cycle: *evolve, don't remediate*; climb toward the
   abstraction layer where agentic development works best; publish and learn
   fast. Mechanism placement is a first-class concern (CLI-first enforcement
   stack, profile-driven projection pattern).
3. **AGENTS.md / CLAUDE.md** — source-repo conventions: `cursor/rules/*.mdc`
   is canon, `claude/rules/` is a generated projection, skills follow
   `skills/README.md`, marker strings keep the legacy prefix until renaming
   lands as one migration.
4. **docs/refinement/concepts.md + docs/research/2026-07-19-operating-surface-catalog.md**
   — the placement doctrine itself: 10 surface classes, 6 axes, placement
   principles (law on normative surfaces, procedure on-demand, checkable
   facts deterministic, trust boundary outside the harness).
5. **The rule and skill texts themselves** — each artifact's self-declared
   purpose, used where higher sources are silent.

No conflicts detected between sources at this level; conflicts surfaced at
the per-artifact level are recorded as findings.

## 3. Evidence reviewed

- Full text of every `cursor/rules/*.mdc` (per-rule audit lane)
- Full text of every `skills/*/SKILL.md` + references + `skills/README.md`
  registry (skills audit lane)
- `.claude/hooks/*`, `scripts/playbook-init.sh`, `scripts/sync-rules.sh`,
  `scripts/playbook-doctor.sh`, `global-safety-net/`, `templates/`
  (event/distribution lane)
- Tracker prescriptions vs. observed practice in this repo's beads DB
  (`bd count`, `bd lint`, `bd stale`, close-reason sampling), templates and
  docs-governance surfaces, data-shaped-conventions inventory (tracker lane)
- The pilot proposal (`2026-07-19-pragmatic-tdd-topology.md`) as the worked
  precedent, and the trigger-layer spike
  (`docs/research/2026-07-16-trigger-layer-spike.md`) for hook capabilities
- **Wanted but unavailable:** cross-session transcript adherence data for
  most rules (the scorecard has a baseline only for pragmatic-tdd items);
  token-cost measurements per rule (estimated from size, not measured);
  target-repo usage data beyond the single private consumer. Confidence on
  context-cost and adherence findings is capped at *medium* accordingly.

## 4. Assumption ledger

| Assumption (kit design rests on) | Status | Evidence |
|---|---|---|
| A1 — Always-on rules are read and followed by agents in practice | untested, with one observed contradiction | No kit-wide adherence data (scorecard has only the pragmatic-tdd baseline). Rules lane found the TodoWrite prohibition structurally loses a context-priority fight with the harness's own system prompt, which promotes the tool |
| A2 — Law/procedure split (thin rule + skill) preserves adherence while cutting context cost | confirmed for pragmatic-tdd only | Post-split rule verified at ~85% law with all obligation rows present (rules lane); adherence half still awaits scorecard data |
| A3 — `sync-rules.sh` keeps the claude projection drift-free | confirmed for rules; falsified as a general distribution property | Rules drift-check works (doctor tri-state SUMMARY). But rules are the *only* distributed artifact with a re-sync path — see A6. Kit-local `--check --local` exists but no CI runs it |
| A4 — Skills get invoked when their trigger condition occurs | **confirmed weakened** | Skills lane: multi-agent-review.mdc never points at tier1-review/tier2-handoff; ponytail-debt's pointer names the wrong thing ("defer-debt"); ponytail-help/-gain have zero invocation paths. Where a rule obliges invocation (pragmatic-tdd, refinement), routing works |
| A5 — Target repos supply the CI trust boundary the kit's gates need | confirmed, with a last-mile caveat | tdd-ledger-verify.yml ships and self-tests; but it is blocking only if the target marks it a required check, and no kit text mentions that step |
| A6 — init distributes everything doctor re-checks (no unmonitored drift) | **falsified** | Event/distribution lane matrix: hooks + settings.json, skills, and the AGENTS.md section are distributed but never re-checked or re-synced. Hooks are the worst case: executable every session, frozen at bootstrap version |
| A7 — The kit's conventions are mostly judgment-shaped (hence prose rules) | **invalidated** | Tracker lane inventoried ~22 enumerable, checker-amenable conventions across the ruleset; rules lane independently measured ~40% of the always-on payload as enumerable data |

## 5. Findings

Lane reports (full evidence) live in the session's subagent transcripts and
are summarized in bead process-kit-l1h's notes; findings below consolidate
them. Magnitude values use the working scale none/minor/moderate/major
(a deviation from concepts.md's seven-level scale — recorded in §8 as skill
feedback).

### F1 — ~70% of the always-on payload sits at the wrong address

- **Type:** mechanism misplacement (procedure/data at the policy address)
- **Observation:** 11 of 12 rules are `alwaysApply`; the 1,008-line payload
  is ~30% law / ~30% procedure / ~40% enumerable data. Per-rule:
  `operating-model` (235 lines, ~50% data, major), `multi-agent-review`
  (161 lines, ~55% procedure, major — see F2), `bead-completion`,
  `beads-quality`, `defer-convention` (moderate splits), `design-docs`,
  `worktree-awareness`, `parallel-subagent-safety`, `agent-identity`
  (minor). `operating-model` additionally competes with `bd prime` as a
  second source of truth for the bd command surface.
- **Evidence:** rules-lane per-rule composition counts (`wc` + section
  classification); pilot precedent (pre-split pragmatic-tdd was 75%
  procedure).
- **Magnitude:** major (cross-cutting) · **Transformation:** split + relocate
- **Confidence:** high on composition; medium on adherence impact (A1 gap)
- **Why it matters:** every session pays ~8,900 words of context rent, ~70%
  of it for content the surface-responsibility table says belongs elsewhere;
  attention competition degrades the law that remains.

### F2 — The review rule has already drifted from the skills it should govern

- **Type:** mechanism misplacement + competing sources of truth (observed, not predicted)
- **Observation:** `multi-agent-review.mdc` carries the full Tier 1/Tier 2
  procedure inline (lens table, simplify output spec, Tier 2 template) and
  never mentions `tier1-review` or `tier2-handoff`. The rule mandates
  **three** lenses; the skill — updated by the approved pilot — mandates
  **four** (test-signal). The rule's inline Tier 2 template and the skill's
  `assemble.py` skeleton have structurally diverged. An agent following the
  rule literally skips an approved lens.
- **Evidence:** rules lane and skills lane converged on this independently;
  both verified the missing pointer and the 3-vs-4 divergence by grep.
- **Magnitude:** major · **Transformation:** split + relocate + correct
- **Confidence:** high (the highest-confidence finding in the audit)
- **Why it matters:** this is the pilot's F1 pattern reproduced in the
  review domain, with the drift the pilot only predicted now observed in
  the wild — and the split destination already exists, making this the
  cheapest major fix available.

### F3 — Parallel authoritative copies across the core rules and skills

- **Type:** competing sources of truth
- **Observation:** five obligations exist as independently evolvable copies
  across the big-four rules: prohibited task-tracking tools (×2 verbatim),
  the IOU close doctrine (×2), the knowledge-capture litmus (×2), the
  memory-staleness protocol (×2), AC ownership (×4 statements). Beyond the
  rules: the simplify-tag vocabulary lives in three artifacts
  (ponytail-review, multi-agent-review.mdc, tier1 lenses.md) with no
  canonical copy; the defer-harvest procedure lives in three places;
  systematic-debugging restates the pragmatic-tdd bug playbook (already
  missing the ledger step the skill added — drift begun).
- **Evidence:** rules-lane overlap matrix; skills-lane grep verification.
- **Magnitude:** moderate · **Transformation:** merge (designate canonical
  homes, demote the rest to cross-references)
- **Confidence:** high
- **Why it matters:** every copy is a place where an edit strands the
  others; the O1–O17 shared-ID pattern proves the kit already knows the fix.

### F4 — Systematic advisory-presented-as-enforcement

- **Type:** intent-vs-mechanism mismatch
- **Observation:** every "MANDATORY / non-negotiable / required / MUST" in
  the ruleset resolves to advisory. Flagship instances:
  `session-lifecycle`'s banner (nothing runs `bd prime` mechanically in
  Cursor); `multi-agent-review`'s two "required" tiers (nothing detects an
  unreviewed structural merge); `defer-convention`'s MUST (the detection
  regex is half-written *inside the rule*); `subagent-wrapup.sh` emits
  `{"decision":"block"}` it cannot reliably deliver while measuring a proxy
  (prefixed-comment-exists); the shipped CI gate is blocking only if the
  target repo marks it a required check, a step no kit text mentions. The
  only live deterministic backing anywhere: `bd lint`, the setup-worktree
  warning, and the tdd-ledger CI template.
- **Evidence:** rules-lane enforceability column (all 12 rules);
  event/distribution-lane enforcement flags; hook ground truth (three
  Claude-only hooks, none blocking in practice, no Cursor wiring).
- **Magnitude:** moderate-major · **Transformation:** rewrite (state real
  levels) + add-enforcement (cheap checkers)
- **Confidence:** high
- **Why it matters:** overclaimed enforcement trains agents (and readers) to
  discount all claims; concepts.md's own placement principle says state the
  real level or move the claim to a surface that can deliver it.

### F5 — The compound knowledge-capture layer is dead and competes with bd-native memory

- **Type:** execution drift + competing sources of truth
- **Observation:** `memory-capture.sh` watches for `bd comments add` with
  magic prefixes — a form no rule teaches (`bd comment` is the taught
  shorthand), so it has never fired: `knowledge.jsonl` has 0 entries while
  bd-native memories has 3 actively-maintained entries. `auto-recall.sh`
  injects from this empty store in parallel with `bd prime`'s injection.
  Hook remediation text points at the upstream plugin's install path, and a
  hardcoded tag list includes another project's vocabulary (`swift swiftui
  appkit menubar`), violating the neutrality convention.
- **Evidence:** event/distribution lane: regex verified against live bd
  syntax, entry counts observed, wiring read in full.
- **Magnitude:** moderate · **Transformation:** retire (or merge — see §6)
- **Confidence:** high on facts; medium on direction
- **Why it matters:** a capture surface that can never fire manufactures
  false confidence that knowledge is accumulating; two capture vocabularies
  make the documented one look optional.

### F6 — Distribution re-checks only rules; A6 falsified

- **Type:** newly discovered requirement (meta-surface gap)
- **Observation:** init distributes hooks + settings.json, skills, and an
  AGENTS.md section (which carries a version stamp!) that no doctor check
  or sync path ever revisits. Hooks are the worst case: executable every
  session, frozen at bootstrap version — kit-side fixes (e.g. to F5's dead
  regex) would never propagate. Also: the kit's own claude/rules projection
  has no CI drift gate (`sync-rules.sh --check --local` exists, nothing
  runs it — today's stray `.bak` litter in claude/rules/ is the smell);
  `worktree-awareness.mdc` tells target repos to run a script init never
  ships; the PR template exists as two hand-maintained identical copies;
  the Cursor user-rules safety-net paste is unverifiable by any mechanism
  and **observed stale on this machine** (predecessor-version block in this
  very session's context).
- **Evidence:** event/distribution lane's distribute-vs-recheck matrix;
  live observation of the stale user-rules block.
- **Magnitude:** moderate · **Transformation:** extend + add-enforcement
- **Confidence:** high
- **Why it matters:** the kit's value proposition is *distributed*
  governance; unmonitored drift channels quietly turn consumers into forks.

### F7 — Broken tool prescriptions in the rules

- **Type:** execution drift (prescription vs reality)
- **Observation:** `bd doctor --agent` — prescribed as mandatory in four
  rules and three scorecard items — silently no-ops in embedded mode (exit
  0, no diagnostics), the mode this repo actually uses. `bd preflight`
  emits the beads project's own Go checklist, misleading at a gate moment.
  `validation.on-create` is prescribed but set to `none` in the kit's own
  repo. The scorecard's "fill out after each agent session" has no surface
  that ever obliges it (scored exactly once, by a bead whose AC required
  it); the rule-efficacy-analyst description says 20 items, the scorecard
  has 27.
- **Evidence:** tracker lane: live command output for all three; scorecard
  history.
- **Magnitude:** moderate · **Transformation:** correct
- **Confidence:** high
- **Why it matters:** prescriptions that fail silently are worse than no
  prescription — the agent believes the check happened.

### F8 — Orphaned imports and pre-pilot convention debt in the skills library

- **Type:** accumulated debt
- **Observation:** `ponytail-help` is an upstream plugin reference card that
  misorients (marketplace/config flows the kit doesn't have; omits two
  family members; advertises a nonexistent skill). `ponytail-gain` displays
  another project's benchmark figures sourced from a `benchmarks/` dir that
  doesn't exist here. `ponytail-debt`'s only invocation pointer names the
  wrong thing. `council` hardcodes volatile model slugs in its core (one
  already invalid) instead of using the overlay convention. Convention
  compliance (skip conditions, anti-patterns sections) fails only in the
  pre-pilot cohort; every post-pilot skill passes — evidence the submission
  checklist works.
- **Evidence:** skills lane, all verified by grep/filesystem.
- **Magnitude:** moderate (help) / minor (rest) · **Transformation:**
  retire/replace + correct + standardize
- **Confidence:** high

### F9 — Orientation docs drift the moment they fall outside a bead's ACs

- **Type:** newly discovered requirement (pattern-level)
- **Observation:** docs/README.md omits four entire directories (specs/,
  research/, refinements/, decisions/) — exactly the artifacts this
  initiative produces; the glossary lacks the initiative's vocabulary; the
  `refinement/` vs `refinements/` naming needs one explanatory line. The
  pattern: artifacts referenced by acceptance criteria stayed consistent
  through the same fast-moving day; docs outside any AC drifted immediately.
- **Evidence:** tracker lane C1–C4.
- **Magnitude:** minor-moderate · **Transformation:** extend + record the
  pattern (candidate doctor/epic-close check)
- **Confidence:** high on gaps; medium on the pattern (one initiative's data)

### F10 — ~22 kit conventions are data-shaped and live in unenforced prose

- **Type:** opportunity (profile-driven projection)
- **Observation:** the tracker lane inventoried ~22 enumerable conventions
  (git grammar, close-evidence shape, AC-by-type, defer grammar,
  banned-token lists, evidence-requirements table…) paying always-on prose
  rent; the rules lane independently measured ~40% of the payload as data.
  Three internal proofs the pattern works already exist: `bd lint` (AC
  sections), the O1–O17 namespace, the doctor SUMMARY contract. Cheapest
  checkers named: defer-lint (regex is already written in the rule),
  close-reason lint, banned-token scan, commit-grammar check.
- **Evidence:** tracker lane Area D; rules lane §2 inventory (independent,
  convergent).
- **Magnitude:** moderate · **Transformation:** relocate + automate
- **Confidence:** medium-high on the inventory; medium on build sequencing
- **Why it matters:** converts good practice from discipline into structure,
  and is the prerequisite for honest enforcement claims (F4).

### F11 — Confirmations: the doctrine predicts outcomes

- **Type:** confirmation (magnitude: none — record and preserve)
- **Observation:** everything whose placement was deliberately designed
  audits clean: the post-split pragmatic-tdd pair (~85% law, all obligation
  rows present); `ponytail-playbook` as the only correctly on-demand rule;
  the tracker core workflow (all 13 closes evidence-mapped, deps
  load-bearing); the doctor's agent contract; the CI gate's seeded-violation
  self-test; all four `defer:` comments carry ceilings and triggers; the
  packet author/validate pairing; the refinement skill's docs-by-pointer
  discipline. The two rules the audit confirms correct are precisely the
  two that went through deliberate placement design.
- **Confidence:** high

### Routed elsewhere

- Remote-rules distribution (Cursor) as a replacement for file-copy sync —
  spike-worthy, harness details unverified; routed to §8 deferred with a
  reopen trigger rather than expanded here.
- Permission/sandbox config templates — real but second-order gap; routed
  to §8 deferred behind the CI-gate work.

## 6. Change options

The findings share three structural responses, so three combined option
sets (per template §6's combined-set permission):

### Set 1 — Topology (F1, F2, F3): where does content live?

| Option | Benefits | Costs / risks | Work invalidated | Reversibility | Confidence |
|---|---|---|---|---|---|
| Keep as is | zero effort | drift compounds (F2 already live); every session keeps paying ~70% misplaced rent | — | — | high |
| Fix drift only (correct lens count, add rule→skill pointers, dedupe the five copies) | cheap; stops active bleeding | leaves the context-cost problem and the split-pending rules untouched | none | trivial | high |
| Staged split program: multi-agent-review first (destination exists), then operating-model, then bead-completion / beads-quality / defer-convention / design-docs, using the pilot's obligations-checklist method; dedupe copies as each split lands | replicates a proven pattern; each split is independently shippable and reversible; F2's fix is nearly free | multiple beads of work; each split needs its own obligations checklist and review; adherence impact unmeasured until scorecard data exists (A1) | none (content preserved by checklist) | per-split: revert the commit | high for MAR, medium-high for the rest |

### Set 2 — Enforcement honesty (F4, F5, F6, F7): claims vs delivery

| Option | Benefits | Costs / risks | Work invalidated | Reversibility | Confidence |
|---|---|---|---|---|---|
| Keep as is | zero effort | overclaiming persists; dead layer keeps manufacturing false confidence; drift channels stay open | — | — | high |
| Truth-in-labeling only (rewrite claims to real levels; fix broken prescriptions; retire the dead memory layer) | cheap; restores honesty; F7 fixes are one-liners | enforcement stays advisory everywhere | none | trivial | high |
| Truth-in-labeling + cheap deterministic layer: retire dead memory hooks, fix prescriptions, add kit CI (sync-check --local, shellcheck, bd lint), extend doctor (hook/AGENTS-section version checks), ship defer-lint + close-reason lint + banned-token scan, document the required-check last mile | moves the most checkable invariants from advisory to observable/blocking; every piece is small and independent | checker maintenance; risk of proxy-metric theater if checkers outrun the judgment layer (mitigate: pair with existing lenses) | none | per-checker | high on value, medium on exact checker set |

### Set 3 — Hygiene and opportunity (F8, F9, F10)

| Option | Benefits | Costs / risks | Work invalidated | Reversibility | Confidence |
|---|---|---|---|---|---|
| Keep as is | zero effort | orphans misorient; orientation docs stay wrong; profile opportunity unexplored | — | — | high |
| Hygiene only (retire/replace orphaned skills, fix pointers and slugs, extend README/glossary) | cheap, immediate correctness | leaves F10 unexplored | none | trivial | high |
| Hygiene + profile spike: do the hygiene fixes now; run a timeboxed spike that profile-izes the 2-3 highest-leverage conventions (git grammar, close-evidence shape) end-to-end (profile → checker → generated projection) before committing to the full pattern | validates the biggest strategic bet cheaply before scaling it; spike output feeds Set 2's checker choices | spike could show the pattern isn't worth the machinery (that's the point of a spike) | none | spike is disposable | medium-high |

Missing information that would change choices: kit-wide adherence data (A1)
would tell us whether splits change behavior, not just cost — the scorecard
experiment (item 26 target) is already positioned to supply it for the
pilot; extending measurement to the new splits is part of Set 1's work.

## 7. Recommendation

Take the third option in all three sets, sequenced as three waves.
Smallest-sufficient-change is preserved because each wave is made of
independently shippable, individually reversible beads, and nothing below
touches the *content* of any discipline — placement only.

**Wave 1 — stop the bleeding (correctness, all cheap):**
fix `multi-agent-review`'s lens count and add its skill pointers (the F2
minimal fix, folded into its Wave 2 split if that lands immediately);
retire `ponytail-help`/`ponytail-gain` (replace help with a kit-native
family index) and fix the `ponytail-debt` pointer; retire the dead
memory-capture layer and demote `subagent-wrapup` to advisory (or delete);
fix the F7 prescriptions (embedded-mode branch for `bd doctor`, demote
`bd preflight` until config-aware, set `validation.on-create`, correct
scorecard stale references); extend docs/README.md and the glossary; move
council's model slugs to the overlay.

**Wave 2 — replicate the pilot topology (one split at a time):**
`multi-agent-review` first (destination skills exist; obligations checklist
required per the template), then `operating-model` (thin to ~60-70 lines of
law; relocate graph-planning JSON, command catalogs, hygiene tables), then
the moderate trio (`bead-completion`, `beads-quality`, `defer-convention`)
and `design-docs`' template extraction. Dedupe F3's five parallel copies as
each canonical home is touched. Each split gets scorecard items so A1/A2
stop being untested.

**Wave 3 — enforcement and the profile spike:**
kit CI additions (`sync-rules.sh --check --local`, shellcheck, `bd lint`);
doctor extensions (hook-set and AGENTS.md-section version checks); the
three cheap checkers (defer-lint, close-reason lint, banned-token scan);
document the required-check last mile; run the profile spike on git grammar
+ close-evidence shape and decide the full profile question on its results.

**Affected artifacts:** all 12 rule files (2 confirmed, 10 touched across
waves), 5 skills (2 retired/replaced, 3 corrected), 3 hooks (1-2 retired,
1 demoted), doctor + sync + init scripts, kit CI workflows, docs/README.md,
glossary, scorecard.
**Migration steps:** each Wave 2 split follows the pilot's method — thin
rule + skill + obligations checklist proving content-neutrality + Tier 1
review + scorecard items. Wave order within Wave 1 is free; Wave 2 is
strictly one-split-at-a-time; Wave 3's spike gates the full profile build.
**For mechanism refinements — obligations checklist:** required per split at
execution time (each Wave 2 bead), not pre-computed here; the pilot's O1–O17
table is the format.

## 8. Deferred and rejected

- **Remote-rules distribution (Cursor) — deferred.** Could make rules-drift
  structurally impossible for Cursor targets and replace the sync loop, but
  harness details (pinning, offline, alwaysApply support, private-repo
  auth) are unverified and adoption bifurcates the model by harness.
  **Reopen when:** the publication trigger fires or a second Cursor
  consumer onboards — whichever is first.
- **Permission/sandbox config templates — deferred.** Real gap
  (never-force-push etc. rest on prose), but second-order: per-harness
  formats, brittle deny lists, and the true trust boundary is CI.
  **Reopen when:** Wave 3's CI gates land and the remaining un-gated
  invariant list is re-reviewed.
- **Full profile build (all ~22 conventions) — deferred behind the spike.**
  **Reopen when:** the Wave 3 spike ships its 2-3 conventions and the
  proposal's authority reviews the result.
- **Promoting the compound memory layer (option (a) in the lane report) —
  rejected** in favor of retirement: the layer is undocumented, dead, and
  duplicates a documented, working system. Its genuine capabilities
  (FTS5-ranked retrieval, failed-approach boost) are noted as potential
  feature requests against bd. **Reopen if:** bd-native retrieval proves
  insufficient at real memory volumes.
- **Glob/stage-scoped rule activation — deferred.** The catalog names the
  lever, zero rules use it, but harness support for meaningful *process*
  (non-file-scoped) conditions is unproven, and the pilot's F5
  invocation-reliability caution applies. **Reopen when:** scorecard data
  from the Wave 2 splits shows whether thinning alone is sufficient.

**Skill feedback (folded back per Phase 8's obligation):** (1) Evidence
gathering was parallelized across four scoped subagent lanes — not
described in the skill, worked well, and the lane reports slot directly
into §3/§5; fold into the skill as an explicit option for large scopes.
(2) The lanes were instructed with a four-level magnitude scale rather than
concepts.md's seven-level scale — a prompt-construction slip the skill
should guard against by naming the scale in Phase 5. Both folded into
`skills/refinement/SKILL.md` in this cycle.

## 9. Open questions

- [ ] Memory-layer direction: retire (recommended) or promote-and-fix? The
  retrieval capabilities are real but unbenchmarked. (Authority decides at
  the gate.)
- [ ] Should the kit standardize on bd server mode (making `bd doctor
  --agent` real) or ship the embedded-mode branch in the rules? (Affects
  the F7 fix shape.)
- [ ] Scorecard activation: per-milestone hygiene row, or explicitly
  re-scope to experiment windows only? (Its single real use was
  experiment-shaped.)
- [ ] Does Cursor actually execute the `.claude/settings.json` hook wiring?
  (Unverified read-only; determines whether the hook surface has any
  coverage in the primary harness. Cheap to test empirically.)

## 10. Approval

| Finding | Decision | Authority | Date | Rationale |
|---|---|---|---|---|
| F1 | pending | kevglynn | — | — |
| F2 | pending | kevglynn | — | — |
| F3 | pending | kevglynn | — | — |
| F4 | pending | kevglynn | — | — |
| F5 | pending | kevglynn | — | — |
| F6 | pending | kevglynn | — | — |
| F7 | pending | kevglynn | — | — |
| F8 | pending | kevglynn | — | — |
| F9 | pending | kevglynn | — | — |
| F10 | pending | kevglynn | — | — |
| F11 (confirmations) | pending | kevglynn | — | — |

**Resulting work items:** created after approval (Phase 10) — proposed
shape: one epic per wave, 3-6 beads each, wired with `bd dep add`, respecting
the 3-7 decomposition heuristic.
**Traceability:** pre-change state is the repo at the commit containing this
proposal; the pilot proposal and lane evidence (bead process-kit-l1h notes +
session subagent transcripts) are the analysis record.
