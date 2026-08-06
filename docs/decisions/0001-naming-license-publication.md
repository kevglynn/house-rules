# 0001 — Naming, license, publication posture, and predecessor relationship

**Date:** 2026-07-16
**Status:** Accepted
**Decider:** Kevin Glynn
**Bead:** segnolabs-5f1

## Context

`process-kit` was extracted on 2026-07-15 as a standalone repository with fresh
git history from a private predecessor playbook (the `ai-dev-playbook`, which
lived in a Pryon Bitbucket repo and a private `kevglynn/ai-dev-playbook` GitHub
mirror). The extraction removed all organization-specific content so the kit
could be shared and potentially open-sourced without entanglement.

At extraction time the kit carried five open decisions — final name, license,
publication posture, the relationship to the predecessor copy, and packaging.
This record resolves all five so that "maybe open-source it someday" rests on
settled ownership, license, and content boundaries rather than choices
discovered at publish time. It does **not** execute publication; landing the
LICENSE file, flipping the repo to public, and announcements are follow-on work
gated on the readiness checklist below (tracked separately).

## Decisions

### D1 — Name: keep the working name `process-kit` for now

The repo, remote, and docs use `process-kit`. A final brand name is deferred to
the publication trigger. The installer marker strings deliberately retain the
legacy `ai-dev-playbook:` prefix (see `defer:` comments in `scripts/`), and one
rule (`ponytail-playbook.mdc`) still names the predecessor in its body; both are
left byte-identical so synced consumers show zero drift and are migrated in the
same change that lands the final name.

**Rationale.** The rename is cheap and already fenced to a single controlled
change, so there is no cost to deferring the brand decision — and a name lands
better once the kit is proven than as a guess at v0.1.0.

### D2 — License: Apache-2.0

The kit will be licensed **Apache-2.0** (single license for the whole repo,
covering both the scripts as code and the rules/skills as prose).

**Rationale.** Permissive licensing maximizes the kit's core value — being
copied into other people's repos — while Apache-2.0's explicit patent grant and
contributor terms are cheap insurance for something that may see external
contributors or corporate adoption. MIT was the runner-up (simpler, but no
patent clause). Copyleft and source-available licenses were rejected: they fight
adoption for a kit whose purpose is wide reuse. The kit already adopts the
open-source Agentic Covenant as its governance layer, so a permissive code
license is consistent with the existing posture.

### D3 — Publication posture: gate the public flip on a readiness checklist

The kit stays private until a **readiness checklist** is met — not a calendar
date and not "when I feel like it." All of the following must hold before the
public flip:

- [ ] **IP clear** — confirmed (see D4).
- [ ] **Skills stable** — the four process skills prove out through at least the
      first real gate run (the G2 packet), APIs settled.
- [ ] **Second-consumer proof** — the kit synced into one more project with the
      generic-core / overlay boundary verified to hold.
- [ ] **LICENSE landed** — the Apache-2.0 `LICENSE` file committed (D2).
- [ ] **CONTRIBUTING present** — contribution and versioning discipline documented.
- [ ] **Neutrality audit passes** — no overlay/consumer-specific content (packet
      vocabulary, reader personas, receipts, project names) in the public core.

**Rationale.** Publishing now would ship moving APIs and invite issues on
unproven work; gating on a proof-and-hygiene checklist ships something real. A
checklist beats a date because readiness is the actual constraint.

### D4 — Predecessor relationship: predecessor is defunct; `process-kit` is the sole home

Pryon is in receivership with its assets being auctioned; it no longer exists as
an entity and there is no downstream consumer of this content. The predecessor
copies (the Pryon Bitbucket repo and the `kevglynn/ai-dev-playbook` mirror) are
therefore dead — frozen, not maintained, not synced. `process-kit` is the sole
standalone home and canonical source going forward. The IP is clean to license
and publish (D3 checklist item 1 satisfied).

**Rationale.** With no surviving predecessor entity or consumer, the
"one-way-upstream vs divergence vs retirement" question is moot — there is
nothing to sync back to. The clean-history extraction already severed the
lineage; this decision records that the severance is permanent.

### D5 — Packaging: plain repo for v1, plugin bundle deferred

v1 ships as a plain git repository consumed via the existing
`install-*` / `playbook-init` scripts. A Claude Code plugin bundle (skills +
agents + hooks as an installable unit) is deferred and revisited only if there
is demand.

**Rationale.** The plain-repo path is what every installer already assumes;
adding a plugin bundle is a distinct distribution format to maintain and buys
nothing until there are consumers asking for it.

## Consequences / follow-on work

- Landing the `LICENSE` file, `CONTRIBUTING`, the repo-visibility flip, and any
  announcement are execution steps gated on the D3 checklist — tracked as a
  separate publication bead, not done here.
- The final-name migration (D1) and its legacy-marker cleanup happen in one
  change at the publication trigger.
- `PLAN.md`'s "Open decisions" table is superseded by this record.

## Amendments

### A1 — 2026-08-05 — Final name: `house-rules` (supersedes D1's deferral)

The publication trigger fired (bead process-kit-8nx); per D1, the deferral
expires. Kevin's decision: the kit's final public name is **house-rules**
("House rules for AI coding agents").

Basis (research recorded on bead process-kit-myp): `process-kit` is
compromised — an active same-niche project (`projectious-work/processkit`,
agentic skill packages), a commercial ProcessKit SaaS, and an archived PyPI
`process-kit` all hold the name; `house-rules` has no GitHub occupant in the
agent space (largest exact-name holders: a game-mod framework at 48 stars and
a dead sbt plugin), fits the kit exactly (the rules of the house that agents
working in a repo must follow; per-project overlays are each house's own
rules), and is the owner's natural vocabulary.

Repo/remote mechanics: the public repository will be named `house-rules`
(hyphenated). Whether that happens by renaming this repo or by clean-cut
export to a fresh repo is the git-history exposure decision (D-history,
tracked on bead process-kit-zta) — the marker migration (new prefix
`house-rules:`, bead process-kit-0em) proceeds independently of that choice.

### A2 — 2026-08-05 — History exposure: publish as-is, rename this repo

Kevin's decision (bead process-kit-zta): the existing repo publishes with its
full history — `house-rules` is born by **renaming this repo**, not by
clean-cut export.

Basis (review recorded in the zta session before deciding): the repo was
already clean-cut extracted on 2026-07-15 (`38cf2f3`), so the history is 80
commits of post-extraction kit work. `.beads/interactions.jsonl` is bd's
event ledger (42 entries — status changes and close reasons, the same content
as the beads), not session transcripts; a sensitive-string scan found no
other-project names, paths, emails, or secrets in it. Residue accepted: one
commit message referencing a `segnolabs` bead ID (`0fcdb1d`), and `pryon` in
this decision record's own D4 rationale (deliberate — the IP provenance
story). HEAD-file `segnolabs` mentions are handled by the neutrality audit
(process-kit-dd5) regardless. Deciding factor: the kit's evidence model cites
commit hashes throughout (close reasons, CHANGELOG, specs); as-is publication
keeps every citation resolvable, and the history itself — 80 commits
following the kit's own conventions — is dogfood evidence.

Execution follow-up: bead process-kit-r4w (release cut — rename, flip
public, tag v0.2.0), gated on both the publication-readiness and Tier 1
profile-projection epics closing.
