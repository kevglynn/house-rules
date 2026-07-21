# Worktree Awareness

## Git worktrees are isolated

Each git worktree is a separate checkout of the same repo. They share the git object store but have **independent working directories**. This has consequences agents must understand:

- **Untracked/uncommitted files in worktree A do not exist in worktree B.** This is not a bug — it's how git works. A file created but not committed in one worktree is invisible to every other worktree.
- **Staged but uncommitted changes are also invisible** across worktrees.
- **Only committed content is shared** (after the other worktree checks out or pulls that commit).

## Do not accuse fabrication

If you're reviewing work and a referenced file "doesn't exist," **check whether you're in a different worktree** before concluding the file was never created. The most common explanation is worktree isolation, not fabrication.

Before reporting missing files:
1. Confirm which worktree you're in (`git rev-parse --show-toplevel`)
2. Check whether the file might exist in the worktree where the work was done
3. Check `git log --all --oneline -- <path>` to see if the file was committed on any branch

## Commit artifacts early

If other agents or reviewers need to see your work:
- **Commit deliverables immediately**, even as drafts — `git add <file> && git commit -m "wip: <description>"`
- Do not wait until work is "done" to commit. Uncommitted files are invisible to collaborators in other worktrees.
- Spec files, runbooks, and design docs especially — these are useless if only you can see them.

## Beads DB is shared across worktrees

All worktrees share a single beads database via a redirect file (`.beads/redirect`) that points to the main repo's `.beads/` directory. This means:
- `bd list` returns the same beads in every worktree
- A bead created in any worktree is visible to all others
- There is one Dolt server instance, not one per worktree

**How it works:** Create worktrees with `bd worktree create <name>` — it handles the redirect natively. (The process-kit repo itself additionally wires an IDE `postCreate` hook in `.cursor/worktrees.json` that runs its local `scripts/setup-worktree.sh`. That script is **not** distributed by `playbook-init.sh` — do not expect it in target repos unless the repo manually adopted it per the kit README.)

**If `bd list` fails in a worktree:** Run `bd doctor --agent` for diagnostics with remediation commands (server mode only — in embedded mode doctor no-ops; check `.beads/redirect` and run `bd where` instead). If the redirect is missing, recreate the worktree with `bd worktree create`.

**Do not run `bd init` in worktrees.** That creates a separate isolated database, which is the opposite of the shared model. If a worktree already has a local DB from a previous `bd init`, remove or migrate it so the redirect can take over (`bd where` shows which database is active).

## Native beads worktree management

Beads has built-in worktree support:
- `bd worktree create <name>` — creates worktree with automatic beads redirect
- `bd worktree list` — list all git worktrees
- `bd worktree info` — show current worktree details
- `bd worktree remove <name>` — remove with safety checks
- `bd where` — show active beads location (useful for debugging redirects)

Prefer `bd worktree create` over raw `git worktree add` — it is the only path that sets up the beads redirect in target repos.

## Fresh clone setup

For new clones or when the beads DB is missing: `bd bootstrap` auto-detects the right setup action (non-destructive). Prefer this over `bd init` which is for first-time initialization only.

## Worktree checklist

When starting work in a worktree:
- [ ] Confirm the agent rules directory has the expected rule files
- [ ] Confirm `bd list` works (if not, run `bd where` to inspect the redirect; recreate with `bd worktree create` if broken)
- [ ] Pull latest from the branch you need (`git pull` or `git checkout <branch>`)

When handing off or requesting review:
- [ ] Commit all artifacts the reviewer needs to see
- [ ] Note which worktree path the work lives in
