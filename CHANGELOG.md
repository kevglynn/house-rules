# Changelog

## 0.1.0 — 2026-07-15

Initial extraction. This repo starts with fresh git history; the content was carried from a private predecessor playbook at its v1.2.0, with all organization-specific material removed.

### Carried over
- 12 canonical Cursor rules (`cursor/rules/*.mdc`) and the generated Claude Code format (`claude/rules/*.md`, regenerated to full parity — `defer-convention` and `ponytail-playbook` were missing from the predecessor's generated set)
- Scripts: `playbook-init.sh`, `playbook-doctor.sh`, `sync-rules.sh`, `install-global-safety-net.sh`, `install-aliases.sh`, `setup-worktree.sh`
- Global safety net block sources (`global-safety-net/*.md`)
- Skills: brainstorming, systematic-debugging, ponytail family (audit/debt/gain/help/review)
- Onboarding: WELCOME.md, QUICKSTART.md, sandbox exercise, core docs (concepts, FAQ, glossary, governance, adoption guide, rule-effectiveness scorecard)
- Claude Code hooks (`.claude/hooks/`) and settings template
- Templates: PR template with Assisted-by disclosure

### New
- Migrated `council` and `workspace-kickoff` skills from user-level (`~/.cursor/skills/`) into the versioned `skills/` library
- Standalone identity: README, PLAN, AGENTS, CLAUDE rewritten for the kit under the working name `process-kit`
- `PROCESS_KIT` env var replaces `AI_DEV_PLAYBOOK` in fresh installs (installer marker strings keep the legacy prefix for in-place update compatibility; see `defer:` comments)

### Removed (relative to the predecessor)
- Organization-specific decks, examples, integration docs, and internal audit subagents
- The deprecated `sync-cursor-rules.sh` shim
