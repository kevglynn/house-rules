# Publication readiness — public v0.2.0

**Date:** 2026-08-05
**Beads:** epic process-kit-8nx — children process-kit-myp (name, human), process-kit-0em (marker migration, blocked on name), process-kit-dd5 (neutrality/overlay audit), process-kit-zta (history exposure, human), process-kit-czl (LICENSE+CONTRIBUTING), process-kit-8k4 (README+release notes, blocked on name+license), process-kit-zk6 (IP/second-consumer, human)
**Status:** Approved (Kevin fired decision 0001's publication trigger, 2026-08-05; framing agreed in scratchpad entry of the same date)
**Sources:** docs/decisions/0001-naming-license-publication.md (D1–D5 + D3 readiness checklist);
PLAN.md (overlay design rule, marker-migration constraint); `defer:` comments in
scripts/playbook-init.sh, scripts/install-global-safety-net.sh, scripts/install-aliases.sh

## What this initiative is

Kevin's call: public release with visibility, version v0.2.0, with the Tier 1
profile-projection work (epic process-kit-tlp) as the release flagship. This
epic makes the kit *ready* to flip public — every item on decision 0001's D3
readiness checklist resolved with evidence or explicitly amended by Kevin on
the decision record. The actual visibility flip and release cut happen when
both this epic and process-kit-tlp close (agreed framing), and are not
children here.

Three of the children are Kevin's calls, tagged `human`: the final name, the
git-history exposure choice, and IP/second-consumer confirmation. Work
continues around them; only the marker migration and the README/release notes
block on decisions.

## Architecture and component overview

Six lanes, one epic:

1. **Final name decision** (human). 0001 D1 deferred the brand name to the
   publication trigger — which has now fired.
2. **Legacy marker migration.** The three installer `defer:` comments spec it:
   rename the `ai-dev-playbook:` marker prefix and ship a one-shot migration
   that rewrites legacy-marker blocks in place (AGENTS.md sections in target
   repos, `~/CLAUDE.md` safety-net blocks, rc-file alias blocks) so re-runs
   update instead of duplicating. Was blocked on the name decision; unblocked
   2026-08-05 (name: house-rules, 0001 A1 — new prefix `house-rules:`). The
   in-rule predecessor mention this lane originally carried was handled early
   by the graybeard rename (process-kit-8nx.1, added to the epic 2026-08-05):
   that rename's credit-line rewrite removed the `ai-dev-playbook` phrase, so
   0em's scope is the installer markers and target-side migration only.
3. **Neutrality/overlay audit.** 0001 D3's audit item: no overlay/
   consumer-specific content (packet vocabulary, reader personas, receipts,
   project names) in the public core. Known hits: `skills/prose-voice`'s
   trigger line naming two reader personas, and P9's owner parameters (em-dash
   ban, ellipsis register — flagged for overlay extraction at P9 authoring
   time). The per-project overlay convention (`.agents/overlay.md`, PLAN.md
   design rule) exists on paper; the extraction mechanism for *per-user*
   voice parameters does not — this lane builds what's missing and moves the
   hits.
4. **Git-history exposure decision** (human). `.beads/interactions.jsonl` is
   committed throughout the repo's history (session-level interaction logs).
   Choose: clean-cut export to a fresh public repo (predecessor extraction
   precedent) vs publishing history as-is.
5. **LICENSE + CONTRIBUTING.** Apache-2.0 per 0001 D2 (decided — this is
   execution). CONTRIBUTING documents contribution and versioning discipline.
6. **Public README + v0.2.0 release notes.** Outward-facing front door,
   flagship framing for the Tier 1 profile-projection work. Blocked on the
   name and LICENSE lanes.
7. **IP clearance + second-consumer criterion** (human). D4 recorded IP as
   clean; this is the publish-time re-confirmation, plus Kevin's call on
   whether the second-consumer checklist item still applies under the
   fail-fast posture (governing intent: checklist is a sprint target, not an
   indefinite gate).

## Trade-offs and decisions

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Publish git history as-is | Provenance, honest evolution record, zero migration | `.beads/interactions.jsonl` session logs exposed for the repo's whole life | **Kevin's call** (history child, human) |
| Clean-cut export to fresh public repo | Clean history; precedent (the kit itself was extracted this way) | Loses public provenance; remote/consumer re-pointing | Same child |
| Waive vs keep second-consumer criterion | Waiving matches fail-fast; keeping matches 0001 as written | Waiving requires a dated amendment on 0001 | **Kevin's call** (IP child, human) |
| Marker migration in the rename change vs separately | 0001 D1 already fenced them to one change; split risks drift | One larger change | **One change**, per 0001 (marker child) |
| Release cut inside this epic | Single tracking point | Cut is gated on process-kit-tlp closing too — cross-epic coupling | **Excluded**; cut happens when both epics close |

## Non-goals

- **No execution this session** — this spec and the epic are the Planner
  deliverable; children run in later sessions.
- **The release cut itself** (visibility flip, tag, announcement) — follow-on
  gated on both epics closing.
- **Claude Code plugin bundle** — 0001 D5 defers packaging beyond the plain
  repo; unchanged.
- **Skills-stable checklist item** — carried as an epic success criterion to
  confirm at close (the four process skills are marked battle-testing in
  PLAN.md), not a work child.

## Risks and open questions

- [ ] **Marker migration blast radius.** Predecessor-bootstrapped machines and
  target repos carry legacy markers in files the kit does not own
  (`~/CLAUDE.md`, rc files, AGENTS.md); a wrong migration duplicates blocks
  silently — the ceiling text in each `defer:` comment is the test list.
- [ ] **File overlap with process-kit-vr2.** The marker child and the Tier 1
  distribution child both edit `playbook-init.sh`. The epics are otherwise
  disjoint; these two beads must not run concurrently (noted on both).
- [ ] **Per-user vs per-project overlay.** The documented convention is
  per-project (`.agents/overlay.md`); P9's owner parameters are per-user.
  The audit child decides where user-voice parameters live (machine-global
  overlay vs per-project) before extracting.
- [ ] **Unknown neutrality hits.** The audit may find more than the two known
  hits; scope holds as long as fixes are extractions/rewordings — anything
  structural becomes a follow-up bead.
