# Versioning and Deprecation

house-rules uses semantic versioning: the `VERSION` file names the
current release, git tags (`v0.2.0`, `v0.3.0`, …) mark the cuts, and
[CHANGELOG.md](../CHANGELOG.md) carries the notes. This page is the
compatibility contract for anyone consuming the kit — a synced repo, a
plugin install, or a manual copy.

## What the contract covers

The versioned surface is what the kit distributes and what agents
dispatch on:

- the rules (`cursor/rules/*.mdc` and their generated Claude projections)
- the distributed checker CLIs and `profiles/conventions.toml`
- the doctor's agent contract: exit codes and `SUMMARY:` keys
- the core-tier manifest (`profiles/core-manifest.list`) — what the
  `house-rules-core` plugin contains
- the global-safety-net block interfaces

Kit-internal docs, maintenance scripts, and this repo's own
beads/scratchpad state carry no compatibility promise.

## PATCH, MINOR, MAJOR — from the consumer's side

**PATCH** (0.3.x): fixes and clarifications. Sync freely; nothing
changes shape.

**MINOR** (0.x.0): additive. New rules (they appear in your repo on the
next sync), new skills, new script flags, new doctor checks, new SUMMARY
keys, new profile keys, additions to the core-tier manifest. Existing
files and contracts keep their names and meanings. Sync freely; skim the
changelog for what's new.

**MAJOR** (x.0.0): something you may depend on is removed or renamed.
Any of the following forces a major bump:

- **A rule is removed or renamed.** The sync's stale cleanup deletes the
  old filename from every synced repo on the next sync, so from the
  target's side a rename without warning looks like a deletion.
- **A doctor SUMMARY key or exit-code mapping changes or is removed.**
  Installed agent-protocol blocks (in `~/CLAUDE.md` and Cursor user
  rules, across machines) dispatch on these keys; changing one breaks
  that dispatch with no error anyone sees.
- **The profile schema breaks** — a table or key the distributed
  checkers read is renamed or removed. A stale checker against a new
  profile (or the reverse) mis-scans; the doctor's skew warning exists
  because of this failure mode.
- **Something is removed from the core-tier manifest.** A core plugin
  install loses that rule, skill, or CLI on update.

## Deprecation: renames ship one release as stubs

The release that renames a rule also ships a stub at the old filename —
a short file pointing to the new name. The stub lives for exactly one
release and is removed in the next. This gives synced repos, pinned
repos, and anything that referenced the old name (agent memories,
scratchpads, docs) one release cycle to catch up, instead of the file
vanishing mid-task.

## The CHANGELOG convention

A release that breaks synced repos leads its changelog entry with a
**Breaking for synced repos** section: what disappears or renames in
your repo on the next sync, and what to do about it. An entry without
that section means syncing the release changes nothing out from under
you. The convention applies to releases after 0.3.0.

## Pinning

Syncing from a clone sitting at `main` gives you unreleased changes —
maintainer mode, and advanced mode for everyone else. Two ways to pin:

**Pin the clone (covers everything).** Check the kit clone out at a
release tag; sync, doctor, init, and the checkers then all agree on one
version:

```bash
git -C ~/house-rules checkout v0.3.0
./scripts/house-rules sync --format all
```

Upgrade deliberately: read the changelog entry for the next tag
(especially any Breaking-for-synced-repos section), then check it out
and re-sync.

**Pin the sync only (rules only).** `sync --version` reads rules out of
a git tag without moving your clone:

```bash
./scripts/house-rules sync --version v0.3.0
./scripts/house-rules sync --show-version    # print the current kit version
```

One caveat: this pins the *rules* and nothing else. The
checkers, profile, and safety-net blocks still come from the clone's
working tree, and `house-rules doctor` drift-checks targets against the
clone's current checkout — so a clone at `main` will report your
tag-pinned rules as stale. If you want the doctor to agree with your
pin, pin the clone.
