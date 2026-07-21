# Changelog

## Unreleased

### Fixed
- **packet skill:** `render.py --verify`'s divergence-strip check scanned a fixed 1800 characters past the grid heading, false-WARNing template-conformant packets whose grid rows carry rich linked evidence (found live on the G2 packet, segnolabs-cga). The window is now structural — the "Status at a glance" section through the end of the grid table plus a margin — and accepts the strip above or below the grid. Behavioral tests added at `skills/packet/tests/test_render_verify.py`.

### Carried over (identity refresh)
- **Maintenance subagents** in `.cursor/agents/`: `rules-auditor`, `rule-efficacy-analyst`, `beads-strategist`, `docs-automation-architect`, `x-factor-innovator` — rewritten for process-kit (12 rules, no predecessor/org-specific references); documented again in CONTRIBUTING
- **`docs/blog-agentic-covenant.md`** — org-neutral Agentic Covenant blog draft, with draft-status note for publication readiness

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
