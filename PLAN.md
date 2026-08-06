# PLAN — process-kit

**Status:** Incubating (extracted 2026-07-15, fresh history, v0.1.0)

## What this repo is

The standalone home for a portable AI-native development kit: versioned agent rules, a curated skills library, per-machine safety nets, and the init/sync/doctor scripts that distribute them to project repos. Extracted from a private predecessor playbook with all organization-specific content removed, so the kit can be shared — and potentially open-sourced — without entanglement.

## Current initiative: the skill layer

The rules state the law; skills encode the procedures. Four process skills are being incubated here and battle-tested against a private consumer project before being considered stable:

| Skill | Encapsulates | Status |
|-------|--------------|--------|
| `tier1-review` | Same-model multi-lens review: dispatch, Critical/Important/Minor triage, close evidence | Incubating (shipped, battle-testing) |
| `tier2-handoff` | Cross-model review handoff: deterministic prompt assembly (`assemble.py`), response triage | Incubating (shipped, battle-testing) |
| `packet` | Gate/sprint packet authoring: committed blueprint template, evidence gathering, share render (`render.py`) | Incubating (shipped, battle-testing) |
| `packet-deepdive` | Packet validation: four specialist lanes + convergence, orchestrator-wrapped, resilience protocol | Incubating (shipped, battle-testing) |

Design rule for all skills: **generic core / project overlay**. Skill cores never name a project, a person, or a project-specific parameter. Reader rosters, model assignments, tone rules, and repo paths live in a single per-project overlay file (`.agents/overlay.md`, one section per skill — convention documented in `skills/README.md`); each skill documents the overlay keys it reads and behaves sensibly when no overlay exists.

Work is tracked in the consuming project's issue tracker during incubation, not in this repo.

## Decisions

Resolved in [docs/decisions/0001-naming-license-publication.md](docs/decisions/0001-naming-license-publication.md) (2026-07-16):

| Decision | Resolution |
|----------|------------|
| Kit name | Final name decided 2026-08-05: **house-rules** (0001 A1); `process-kit` remains the working name until the release-cut rename (process-kit-r4w) |
| License | Apache-2.0 (landed at publication, not before) |
| Publication posture | Private until a readiness checklist is met (IP clear, skills stable, second-consumer proof, LICENSE + CONTRIBUTING, neutrality audit) |
| Predecessor relationship | Predecessor is defunct (receivership); its copies are dead; `process-kit` is the sole canonical home |
| Packaging | Plain repo for v1; Claude Code plugin bundle deferred |

Marker strings in the installers deliberately keep the legacy `ai-dev-playbook:` prefix until the final name lands (see `defer:` comments in `scripts/`) — renaming them requires a legacy-marker migration in the same change. One rule (`ponytail-playbook.mdc`) also mentions the predecessor name in its body; it is left byte-identical so synced consumers show zero drift, and gets renamed in the same future change.

## Backlog (after the first four skills prove out)

- ~~Second-consumer proof: sync the kit into a second project and verify the overlay boundary holds~~ — declared **met** 2026-08-05 (0001 A3): 15 sync targets consume the core unmodified; overlay exercised where needed (segnolabs); neutrality audit (process-kit-dd5) completes the boundary verification
- Trigger layer: lifecycle automation (hooks, tracker formulas) so process fires without being asked
- Session-close ceremony hooks; council harvest upgrade; planning-ritual skill; decision-record template
