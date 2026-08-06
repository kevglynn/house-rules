# Contributing

Thanks for your interest in improving this kit. It is a working toolkit, not a framework: rules, skills, checker CLIs, and distribution scripts that real projects consume. Contributions are judged by whether they make that consumption better.

Contributions are accepted under the same [Apache-2.0 license](LICENSE) that covers the project (inbound = outbound). There is no CLA or DCO process.

## The one convention that matters most: canonical source

Rules exist in two formats, but only one is editable:

- **`cursor/rules/*.mdc` is canonical.** Edit rules here, and only here.
- **`claude/rules/*.md` is generated.** Never hand-edit it. After changing a canonical rule, regenerate with:

```bash
./scripts/sync-rules.sh --format claude --local
```

CI rejects any PR where the generated projection has drifted from the canon, so a hand-edit to `claude/rules/` will fail the build even if it looks harmless.

## Checks a PR must pass

CI runs the gates in `.github/workflows/kit-ci.yml`. Currently that means:

- **Projection drift** — `./scripts/sync-rules.sh --format claude --check --local` must pass (the job also self-tests by seeding drift and asserting the gate catches it).
- **shellcheck** — `shellcheck -S warning scripts/*.sh` must be clean.

Run both locally before opening a PR. Also run the script test suites, which live next to the scripts they cover:

```bash
python3 scripts/tests/test_defer_lint.py
python3 scripts/tests/test_close_reason_lint.py
python3 scripts/tests/test_banned_token_scan.py
python3 scripts/tests/test_tdd_ledger.py
```

Checker CLIs are stdlib-only Python by design — no new runtime dependencies without a decision record making the case.

## Commits, branches, and versioning

- Commit and branch conventions are defined in `cursor/rules/operating-model.mdc` (§ Git Conventions) — typed commit summaries, branch names that carry the work-item ID. Follow what the rule says rather than what this file might restate; the rule is the source of truth.
- The `VERSION` file at the repo root is read by the sync pipeline and stamped into synced artifacts in consuming repos. Bump it (and tag the release) only as part of a deliberate release cut, not incidentally in a feature PR.

## Contributing a skill

Skills live in `skills/<name>/SKILL.md`. The format, authoring guidance, and the submission checklist are in [`skills/README.md`](skills/README.md) — read the checklist before opening a PR. Two points worth repeating:

- Skills must stay **project-neutral**: no project names, people, or consumer-specific parameters in the generic core. Project- or user-specific values belong in overlay files in consuming environments.
- New skills should declare their maturity honestly (incubating vs. battle-tested).

## Decision records

Significant decisions — licensing, naming, publication posture, architectural commitments — are recorded in `docs/decisions/` as numbered markdown files. The convention:

- Records are **append-only**: a decided record is amended with a dated amendment section (`## Amendment (YYYY-MM-DD)`), never rewritten, so the reasoning trail stays legible.
- If your PR reverses or materially reinterprets a recorded decision, it must include the amendment.

## Scope guidance

Small, focused PRs land fastest. If you are proposing a structural change (new rule, new checker, changes to distribution behavior), open an issue first and expect the discussion to center on: what consuming projects gain, what the maintenance cost is, and whether an existing surface already covers it.
