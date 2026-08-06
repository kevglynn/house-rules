## playbook — agent protocol

If the user invokes the playbook ("use the playbook", "bootstrap this repo",
"sync the rules", "run playbook doctor", "check the playbook"):

1. Run `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/playbook-doctor.sh" --agent` to get structured status. The `--agent` mode emits a `SUMMARY: <key>` line and a stable exit code.

2. Branch on the **SUMMARY key**, not the bare exit code, when the exit code is `3` (drift). The SUMMARY carries what drifted so the recommended remediation matches. Do not execute until the user consents.

   | Exit | SUMMARY key | Meaning | Proposed action |
   |------|-------------|---------|-----------------|
   | `0` | `ok` | Healthy | Report status; no action |
   | `2` | `bootstrap_needed` | No rules in this repo | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/playbook-init.sh" --tool cursor\|claude\|both` |
   | `3` | `rules_drift_cursor` | Cursor rules stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/sync-rules.sh" --format cursor` |
   | `3` | `rules_drift_claude` | Claude rules stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/sync-rules.sh" --format claude` |
   | `3` | `rules_drift_both` | Both stale | `bash "${PROCESS_KIT:-$HOME/process-kit}/scripts/sync-rules.sh" --format all` |
   | `3` | `profile_drift` | `profiles/conventions.toml` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/profiles/conventions.toml" profiles/conventions.toml` |
   | `3` | `ledger_drift` | `scripts/tdd-ledger` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/tdd-ledger" scripts/tdd-ledger && chmod +x scripts/tdd-ledger` |
   | `3` | `defer_lint_drift` | `scripts/defer-lint` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/defer-lint" scripts/defer-lint && chmod +x scripts/defer-lint` |
   | `3` | `close_reason_lint_drift` | `scripts/close-reason-lint` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/close-reason-lint" scripts/close-reason-lint && chmod +x scripts/close-reason-lint` |
   | `3` | `banned_token_scan_drift` | `scripts/banned-token-scan` stale vs kit copy | `cp -f "${PROCESS_KIT:-$HOME/process-kit}/scripts/banned-token-scan" scripts/banned-token-scan && chmod +x scripts/banned-token-scan` |
   | `1` | `error` | Generic error | Show the doctor's full text output to the user |

   Drift precedence when several drift at once: rules drift wins the SUMMARY, then `profile_drift`, then `ledger_drift`, then `defer_lint_drift`, then `close_reason_lint_drift`, then `banned_token_scan_drift`; the lower-precedence findings still appear in the doctor's text output, so check them after fixing the reported one. The profile and the profile-reading checkers version together: when the doctor's text output shows both a stale checker and the profile advisory, re-copy both (or re-run `playbook-init.sh`). Some findings are text-only and never affect the SUMMARY or exit code (e.g. a stale AGENTS.md section version stamp, or the unverifiable Cursor user-rules paste) — scan the doctor's warning lines for these, don't rely on the exit code alone.

3. Do not invoke `sync-rules.sh` without `--format` on a Claude-only project. The script defaults to `--format cursor` and will create unwanted `.cursor/rules/` files in the target.

4. Never run bootstrap, sync, or update silently. Always ask before making changes that modify the project or `~/.playbook-sync-targets`.

5. If `"${PROCESS_KIT:-$HOME/process-kit}"` does not exist on this machine, instruct the user to clone the kit: `git clone https://github.com/kevglynn/house-rules ~/process-kit`. Do not attempt to clone on behalf of the user without explicit consent.

The canonical playbook location is `${PROCESS_KIT:-$HOME/process-kit}`.
