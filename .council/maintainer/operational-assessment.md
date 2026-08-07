# Maintainer-Operator Assessment — Adoption Plan

Read-only council scratch. 2026-08-06.

## Script inventory note
Plan cites `playbook-init.sh` / `playbook-doctor.sh`; repo has `init.sh` / `doctor.sh` + `house-rules` dispatcher. README, global-safety-net, CONTRIBUTING still reference old names. Decision 0002 brand rename in flight — adoption traffic before that lands = broken first-run docs.

## Lite `--lite` blast radius (not implemented)
Must touch: init.sh (bd gate, beads, hooks, scratchpad, CLIs, profile, sync-targets, AGENTS.md stamp), doctor.sh (entire beads/scratchpad/sync sections), possibly global-safety-net session-start (currently assumes full bootstrap), rule manifest (subset vs 13 canonical), skill resolution warnings, upgrade path idempotency.

Forever dual config: lite doctor vs full doctor, lite rule set versioning, friction reports "which tier?"

## CI coverage gaps for adoption
- ubuntu-latest only; no macOS stat/lock, no fish, no WSL matrix
- init tested via bd shim in marker/profile fixtures, not real missing-bd path
- No installer e2e on stranger machine profile

## Support queue predictors at scale
fish (install-aliases exit 1), bd PATH (init hard fail), Cursor paste vs CLAUDE import, sync-rules stale cleanup deleting local rules, profile/checker skew, lite→full upgrade state, version pin vs HEAD sync confusion.
