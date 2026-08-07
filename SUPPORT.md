# Support

house-rules is maintained by one person and the agents he works with.
Support is best-effort: file a GitHub issue and you'll get an answer when
the maintainer gets to it. There is no SLA, no response-time promise, and
no paid tier.

[File an issue](https://github.com/kevglynn/house-rules/issues). There's
no issue template yet — describe what you ran, what you expected, and
what happened. Output from `house-rules doctor` helps a lot.

## What's supported

| Surface | Status |
|---|---|
| Linux, macOS | Supported. The scripts are bash and run on both. |
| Windows | WSL or Git Bash only; not independently tested. |
| bash, zsh | Supported — `install-aliases.sh` detects and handles both. |
| fish | Documented workaround only: the installer prints a snippet to paste into `config.fish` and exits without writing. |
| Cursor, Claude Code | The two target tools. Rules ship in both formats; `house-rules init --tool` picks. |
| Core plugin tier (`house-rules-core`) | Supported as a plugin install: the standalone rules, the graybeard and prose-voice skills, and two checker CLIs. No `bd` required. |
| Full kit (`house-rules init`) | Supported; requires the beads CLI (`bd`) on PATH. |

One surface is unverifiable by design: the Cursor User Rules paste.
Cursor either auto-imports `~/CLAUDE.md` behind a settings toggle whose
state can't be read from disk, or it needs the manual paste — no tooling
can check which happened on your machine. `house-rules doctor` prints a
reminder instead of a pass/fail; treat that reminder as the check.

## Explicitly unsupported

Doing these puts you outside what the maintainer will debug:

- **Editing files in synced rule directories.** On kit-synced repos,
  `.cursor/rules/` and `.claude/rules/` are kit-owned. The sync
  overwrites local edits to kit files (a timestamped `.bak` is kept by
  default) and **deletes any file it doesn't recognize — no backup** —
  including rules another tool placed there. Details and the supported
  alternative (your repo's `AGENTS.md`/`CLAUDE.md` sections, or a
  skill): [docs/operations.md](docs/operations.md).
- **Editing the distributed `profiles/conventions.toml`.** It
  drift-checks byte-for-byte against the kit copy; local edits surface
  as `profile_drift` and are overwritten by the recommended fix. Change
  conventions in the kit and re-sync.
- **Hand-editing `~/.house-rules-aliases.sh`.** Regenerated on every
  installer run.
- **Running full-tier tooling against a core-tier install.** The core
  plugin ships a subset of the kit; `house-rules doctor` checks for the
  full rule set and will report the rest as missing. Core-tier installs
  are managed by your plugin client, not by the doctor.
- **The beads CLI itself.** `bd` is an upstream project
  ([steveyegge/beads](https://github.com/steveyegge/beads)). The kit
  supports its integration points; bugs in `bd` go upstream.

## Compatibility promises

What MAJOR and MINOR mean for a repo that syncs from the kit, how rule
renames are deprecated, and how to pin to a release:
[docs/versioning.md](docs/versioning.md).
