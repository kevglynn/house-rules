# Adoption Plan v1 — readiness and launch

**Date:** 2026-08-07
**Beads:** process-kit-03c (readiness epic: 733, 4cn, pon, wsi, 12q, 4bg, 5qs) · process-kit-ndu (launch epic: 2lh, aos, 59p, 5vq)
**Status:** Approved

## Architecture and component overview

Goal: convert agent-native solo devs (Cursor / Claude Code power users) from discovery to retained adopters to contributors. Strategy decided by the owner 2026-08-06: a zero-dependency wedge at the top of the funnel, with the integrated beads workflow as the power-user upgrade.

A seven-voice council review (2026-08-06, transcripts summarized in the plan doc and scratchpad) reshaped the original plan. Council-driven verdicts adopted here:

- **Wedge ships as platform-native plugin manifests, not an installer flag.** Two plugins with declarative manifests: `house-rules-core` (the standalone rule subset + graybeard skill family + checker CLIs) and `house-rules-full` (beads workflow, session lifecycle, planning skills). Three surfaces: `.claude-plugin/marketplace.json` + `plugin.json` (Claude Code), `.cursor-plugin/plugin.json` (Cursor), root `plugin.json` (`npx skills add`). Rationale: less code than a `--lite` branch through init.sh, no HOME writes or shell installers at first touch (trust barrier), the tier boundary is declarative (maintainer cost), and it puts the kit on the discovery surfaces where the class winner (obra/superpowers, one marketplace command) got an order of magnitude more adoption.
- **Checkers travel with the wedge.** They are single-file stdlib Python and the differentiator; a prose-only wedge argues on the competitors' turf.
- **The aha is pre-install.** First README code fence: pipe a "this will take 2-3 weeks" sentence into `banned-token-scan` via curl + python3 — no clone, no install, ten labeled hits. Demo assets are three ~20-second loops plus real dogfood transcripts (`docs/transcripts/`), not one staged film.
- **Upgrade is pull, not push.** An in-agent trigger in the core plugin offers the full install once, with consent, after core skills have fired in a repo with no task tracking. Direct answer to the wedge-cannibalization risk.
- **Measure installs and second-session return, not stars.**
- **Positioning language:** category = "versioned engineering playbook for AI coding agents"; "checkable," never "enforced"; complement to AGENTS.md and beads; honest overlap with superpowers. Longer-term differentiator to surface: `profiles/conventions.toml` as a shareable, forkable profile.
- **Lighthouse track:** direct outreach to 1-2 design partners running the full stack on real work, gathering adoption receipts (bootstrap succeeded, evidence closes on real work, checker used operationally, retained by choice). Soft parallel track — launch claims stay within what receipts support; not a hard gate.

## Data flow and key interfaces

Funnel: discovery (article, one launch post, registry listings) → README try-it block (no install) → core plugin install (marketplace / npx) → first-session behavior change → in-agent upgrade offer → full kit (init.sh, beads, sandbox) → power user (sync, profiles, checkers in CI) → contributor.

Reality at authoring time (verified 2026-08-07, post v0.3.0):

- The brand-cohesion wave shipped: `playbook-*` script names are gone from all active docs (bead bzk, commit 5927a72); v0.3.0 tagged and released (bead df6, commit b2cf7a9). The council's "front door 404s" finding is resolved; its "rot recurs — mechanize the check" recommendation stands.
- Still stale: clone path split (README `~/house-rules` vs QUICKSTART/WELCOME `~/process-kit`), PLAN.md header ("Incubating … v0.1.0"), AGENTS.md claim that hooks live in `.claude/hooks/` (directory absent).
- Repo surface: Discussions disabled, default social preview, empty homepage URL.
- No plugin manifests exist anywhere in the tree; all 17 `SKILL.md` files carry valid frontmatter.
- Rule inventory for the core tier: only 4 of 13 rules are standalone as written (`agent-identity`, `defer-convention`, `prose-voice`, `parallel-subagent-safety`); `graybeard-playbook` is opt-in and close; core curation is real editing (strip `bd` references), not file selection.

## Trade-offs and decisions

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| `--lite` flag on init.sh | One entry point | Bash branch through 600+ lines; keeps clone+trust barrier; permanent second config in imperative code | Rejected |
| QUICKSTART paragraph with manual `cp` | Near-zero build | No discovery-surface presence; no doctor/tier story; wedge invisible | Rejected (kept as fallback text) |
| Plugin manifests, core/full | Declarative tier; no HOME writes; registry discovery; less code | Two plugins to keep in sync; marketplace review queues | **Adopted** |
| Cancel wedge, teams-only + lighthouse gate (council contrarian) | Protects integrated-product identity | Loses the locked audience decision; gates launch on factors outside control | Rejected; lighthouse kept as soft parallel track, checkers bundled into core to protect identity |
| Demo film (90s) | Single polished asset | "Demo theater" objection; can't re-cut per channel | Replaced by three 20s loops + real transcripts |
| Stars as headline metric | Easy | Demonstrably noise in this category | Installs + second-session return |

## Non-goals

- No issue templates, metrics snapshot script, SHOWCASE.md, power-user tour doc, seeded good-first-issues, or multi-platform launch cadence until their triggers fire (first issue filed, manual Insights check becomes annoying, first adopter, first contributor, first conversion — respectively).
- No new hard gate on the broad launch from the lighthouse track.
- No enforcement claims in any copy ("checkable," not "enforced").
- No renaming or history rewriting (publication decisions 0001/0002 are settled).

## Risks and open questions

- [ ] Wedge cannibalization: core-tier users may never upgrade. Mitigations: checkers in core, in-agent upgrade trigger. Watch for it in early signal.
- [ ] Marketplace/registry mechanics (exact manifest schemas, review queue behavior) verified against vendor docs at implementation time, not from this spec.
- [ ] Recording the demo loops and posting content require the owner; beads carrying those steps are tagged `human` where applicable.
- [ ] `sync-rules.sh` deletes adopter-local rules in synced dirs — must be documented loudly before strangers arrive (folded into policies bead).
