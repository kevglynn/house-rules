# 03 — A graybeard deletion: 216 lines removed on evidence

**Kind: historical.** Quotes are verbatim from commit `61547ef` and bead
`process-kit-26b`.

## Context

The kit's installers once recognized two marker prefixes: the current
`house-rules:` markers and the legacy prefix left behind by the
predecessor playbook, so old machines could be migrated in place. That
dual recognition was transitional by design — and a Tier 1 architect
review caught what usually happens to transitional code. From the bead's
description (`bd show process-kit-26b`):

> Why: Tier 1 architect review of process-kit-0em found the sunset
> condition lived only in prose comments with no tracking artifact, making
> the transitional code permanent accretion by default; this bead is the
> tracking artifact.

## Before — the gate: prove it's dead first

The bead's first acceptance criterion required a zero-hit field sweep
BEFORE any deletion. From the close reason:

> AC1 (zero-hit sweep BEFORE deletion): field sweep 2026-08-06
> pre-deletion — HOME artifacts (~/CLAUDE.md, .bashrc/.zshrc/.profile,
> ~/.playbook-aliases.sh): zero hits; all 15 ~/.playbook-sync-targets
> repos (AGENTS.md + CLAUDE.md): zero hits after the unlock pass [...]
> doctor spot-checks on segnolabs + dolt: SUMMARY ok, section current
> v0.2.0.

## After — the deletion

```
$ git show --stat 61547ef
    chore: sunset legacy predecessor-prefix marker recognition (process-kit-26b)

 .beads/interactions.jsonl              |   2 +
 .github/workflows/kit-ci.yml           |  12 +--
 AGENTS.md                              |   2 +-
 scripts/install-aliases.sh             |  55 +++---------
 scripts/install-global-safety-net.sh   |  52 +++---------
 scripts/playbook-doctor.sh             |  16 ++--
 scripts/playbook-init.sh               |  29 ++-----
 scripts/tests/test_marker_migration.sh | 149 ++++++++++++---------------------
 8 files changed, 101 insertions(+), 216 deletions(-)
```

The comment that had been carrying the sunset condition became the record
of its execution. From the diff in `scripts/install-aliases.sh`:

```
-# Marker prefix is "house-rules:" (final kit name, decision 0001 A1). Rc
-# files on machines set up by the predecessor playbook carry the legacy
-# "ai-dev-playbook:" prefix, so the block scans below recognize BOTH prefixes:
-# a legacy block is rewritten in place under the new markers, never
-# duplicated. Keep the legacy recognition until no machine still carries an
-# old-marker rc block.
+# Marker prefix is "house-rules:" (final kit name, decision 0001 A1).
+# Recognition of the predecessor playbook's legacy marker prefix was
+# sunset 2026-08-06 (process-kit-26b) after a field sweep showed zero
+# old-marker rc blocks remaining.
 SOURCE_BEGIN="# BEGIN house-rules:aliases"
 SOURCE_END="# END house-rules:aliases"
-LEGACY_SOURCE_BEGIN="# BEGIN ai-dev-playbook:aliases"
-LEGACY_SOURCE_END="# END ai-dev-playbook:aliases"
```

What stayed is as deliberate as what went: the malformed-marker refusal
guards survived the deletion because they protect current-marker files
too, and the close reason accounts for them —

> AC3 (guards + fixtures remain, shellcheck clean): test_marker_migration.sh
> retires migration/mixed cases, keeps all malformed-marker guards
> converted to current markers plus fresh-install idempotency — 24/24 pass
> [...]

## Receipts

- **Commit:** `61547ef` — 8 files, +101/−216, all four installers plus the
  fixture suite.
- **Bead:** `process-kit-26b` — description names every constant, branch,
  and helper to delete; close reason maps all three ACs (sweep before
  deletion, machinery removed, guards remain).
- **Durable record:** `AGENTS.md` "Identity conventions" carries the
  one-line summary: sunset 2026-08-06 after a field sweep showed zero
  old-marker artifacts; the malformed-marker guards stayed.
