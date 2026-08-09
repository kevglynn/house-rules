# Tier 1 review — process-kit-jjj (init overwrite safety)

State reviewed: commit `63e58b9`. Fixes landed in `f1f13ca`.

Four lenses ran in parallel on the same model, each with the full context
package and no sight of the others' findings until triage: code-reviewer,
architect-reviewer, simplify, test-signal.

Raw verdicts: code-reviewer 0 Critical / 2 Important / 8 Minor;
architect-reviewer 0 / 3 / 4; test-signal 1 / 4 / 4; simplify (no severity
scale) 16 tagged findings and 5 structural observations.

## Triage

| # | Lens(es) | Severity | Finding | Disposition |
|---|---|---|---|---|
| 1 | test-signal, code-reviewer | Critical | Every fixture ran `--tool cursor` with no `--skills`, so the Claude rules loop and the skills walk were never executed; reverting either to a bare glob `cp` left all 22 cases green | fixed in `f1f13ca` — coverage rebuilt as pattern-class: install the full surface, edit every delivered file, demand one `.bak` per edited file |
| 2 | simplify, architect, code-reviewer | Important | Backup *policy* still triplicated: `safe_backup` and an inline block in `sync_claude_to` alongside the lib's `backup_before_overwrite`, with `diff -q` and `cmp -s` asking the same question two ways | fixed in `f1f13ca` — both sync sites route through `backup_before_overwrite` |
| 3 | code-reviewer, architect | Important | `AGENTS.md` marker refresh rewrites kit-owned bytes inside a project-owned file with no `.bak`, on every version bump, while help text and `operations.md` read as exhaustive | fixed in `f1f13ca` — backs up before the rewrite; docs name all three postures |
| 4 | architect | Important | Both fake kits in `test_sync_cleanup.sh` lack `scripts/lib/`, silently degrading sync to command-not-found backups across 51 existing cases | fixed in `f1f13ca` — fixtures copy the lib; sync guards the source |
| 5 | test-signal | Important | Counter rename, summary line, and safe-mode exit code unasserted; deleting the increment would empty the summary with every suite green | fixed in `f1f13ca` — both asserted |
| 6 | test-signal, simplify | Important | AC2's structural half asserted by anchored greps that a rename, a leading space, or `function backup_file {` defeats | fixed in `f1f13ca` — behavioral sourcing check plus a definition count across `scripts/` |
| 7 | test-signal | Important | `install_file`'s abort-on-failed-backup path — the strongest claim in the change — had no test | fixed in `f1f13ca` — mirrors scenario 10 of the sync suite |
| 8 | architect, code-reviewer | Minor | Doctor prints `cp -f` remediation exactly when the file differs from the kit's; its line-307 comment became false | comment fixed in `f1f13ca`; remediation deferred to **process-kit-39i** |
| 9 | code-reviewer | Minor | Symlinked destination: `cp` writes through and may escape the repo; the `.bak` is filed against the link | deferred to **process-kit-2xd** |
| 10 | code-reviewer | Minor | `\|\| true` on the sync-targets rewrite swallows a read error, then `mv` truncates the user's list | deferred to **process-kit-0ck** |
| 11 | code-reviewer | Minor | `bd hooks install` can replace a project's pre-commit hook, unbacked | deferred to **process-kit-1qe** |
| 12 | code-reviewer, simplify | Minor | "no .mdc rules found" reported for a directory full of rules when one entry is not a regular file, after a partial install | fixed in `f1f13ca` via `install_rules_dir` |
| 13 | code-reviewer | Minor | Directory-shaped destination: `cp` lands the file inside it, returns 0, and the count line inflates | fixed in `f1f13ca` |
| 14 | code-reviewer | Minor | Backup-then-`cp`-fails message reads as "nothing was written" | fixed in `f1f13ca` |
| 15 | code-reviewer | Minor | Suite leaked five temp trees (`CLEANUP` append inside a command substitution); `read -r` split on a spaced `TMPDIR` | fixed in `f1f13ca` |
| 16 | code-reviewer | Minor | Skills walk drops symlinks and empty directories that `cp -rf` carried | accepted — no skill ships either; restriction documented at the loop |
| 17 | architect, simplify | Minor | Duplicate `SAFE_BACKUP_COUNT` resets; lib outside the shellcheck glob; missing source directive | fixed in `f1f13ca` |
| 18 | architect | Minor | `scripts/lib/` layer undocumented now that it has two members and a distribution boundary | fixed in `f1f13ca` — README section |
| 19 | simplify | Minor | Drop `\|\| exit 1` after `install_file`; `set -e` already covers it | **rejected** — accurate about errexit, but explicit propagation on a data-loss guard should not rest on semantics that a later `if`-wrap silently disables |
| 20 | simplify | Minor | Comment volume, unused `out_lacks`, redundant paired checks | fixed in `f1f13ca` |

## Correction to the original evidence

The red-first tally reported at implementation was 15 of 22 failing; the
test-signal lens recounted 16 of 22. It also observed that "the rule itself is
restored to the kit's bytes" passes on unfixed code — a bare `cp` restores kit
bytes fine — so it is a regression control, not red-first evidence, and should
not have been counted among the failures either way.

## Mutation evidence after the fixes

The first mutation round (five mutations, all killed) missed the complement of
its own M5: it reverted the profile and CLI sites while leaving rules
protected, and never reverted the sites no fixture reached. Seven mutations
were re-run against the rebuilt suite, including the four the lenses predicted
would survive:

| Mutation | Result |
|---|---|
| N1 Claude rules loop reverts to a bare glob `cp` | killed (1) |
| N2 skills walk reverts to `cp -rf` | killed (1) |
| N3 counter increment deleted | killed (1) |
| N4 `install_file` ignores a failed backup | killed (3) |
| N5 a second copy of the primitive under a new name | killed (10) |
| N6 `AGENTS.md` refresh backup removed | killed (2) |
| N7 `SAFE_MODE` honored for rules, ignored for the profile | killed (1) |

## Note on the root skip

The abort-on-failed-backup case guards on `id -u` and skips as root, matching
the sync suite. Inside this workspace's sandbox `id -u` reports 0, so the case
silently skipped on the first runs; run unsandboxed it reports 1000 and the
case executes. The same skip hid a real defect during process-kit-1nj. All
counts above are from unsandboxed runs where the case actually ran.
