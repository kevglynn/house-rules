# Operating-surface catalog — research memo

**Date:** 2026-07-19 · **Type:** research memo · **Bead:** process-kit-8va.1
**Status:** DRAFT — external-landscape and MCP/CLI sections pending research-agent synthesis
**Trigger:** post-close discovery on process-kit-ffa — the operating-surface model in
[docs/refinement/concepts.md](../refinement/concepts.md) covers six surfaces
(rule / skill / hook / lens / subagent / human) but omits surfaces the kit
already uses (CLIs, templates, memories, tracker) and surfaces available in
the ecosystem (MCP, CI, scheduled automations). Both the pragmatic-tdd pilot
(process-kit-vvx) and the kit-wide audit (process-kit-l1h) evaluate placement
options against this catalog, so an incomplete catalog truncates the option
space at the two highest-leverage moments.

As a refinement-taxonomy data point: this event classifies as *trigger:
newly discovered requirement (mechanism-side)*, *magnitude: local*,
*transformation: extend* — the first live use of the two-axis scheme.

## Part 1 — Surfaces the kit already uses (internal inventory, verified)

The kit is already operating on ~11 distinct surface kinds; the concepts.md
model names only 6. Everything below exists in this repo today.

| # | Surface | Kit instances | Activation | Enforcement | State | Judgment |
|---|---------|--------------|------------|-------------|-------|----------|
| 1 | Always-on rule | 12 `alwaysApply` `.mdc` files. Kit-synced repos: this surface is kit-exclusive — `sync-rules.sh` stale cleanup deletes local rule files on the next sync; use AGENTS.md sections or skills for repo-local guidance (verified 2026-08-04) | always in context | advisory | none | model |
| 2 | Agent-requestable rule | `ponytail-playbook.mdc` | on-demand (description match) | advisory | none | model |
| 3 | Repo orientation doc | `AGENTS.md`, `CLAUDE.md` | always in context | advisory | none | model |
| 4 | Per-machine safety net | `global-safety-net/*.md` → `~/CLAUDE.md` blocks + Cursor user rules | always, machine-wide (covers un-bootstrapped repos) | advisory | none | model |
| 5 | Skill | 14 skills in `skills/` | on-demand invocation | advisory (procedure) | per-run | model follows procedure |
| 6 | Skill-embedded CLI | `packet/render.py`, `tier2-handoff/assemble.py` | invoked by skill step | **observable/blocking** (deterministic output, exit codes, headless verify) | none | deterministic |
| 7 | Standalone agent-consumable CLI | `playbook-doctor.sh --agent` (SUMMARY key + stable exit codes), `sync-rules.sh`, `playbook-init.sh`, `bd` itself | on-demand | observable→blocking | varies (bd: full DB) | deterministic |
| 8 | Agent-event hook | `.claude/hooks/`: auto-recall (SessionStart), memory-capture, subagent-wrapup, provision-memory + `knowledge-db.sh` maintaining a **SQLite FTS5 knowledge DB** | event-driven | observable (injects context, records evidence) | **yes — persistent DB** | deterministic |
| 9 | Environment-lifecycle hook | `.cursor/worktrees.json` `postCreate` → `setup-worktree.sh`; bd's git-hook shims | event-driven (worktree create, git events) | blocking-capable | none | deterministic |
| 10 | Custom subagent | `.cursor/agents/`: rules-auditor, rule-efficacy-analyst, beads-strategist, docs-automation-architect, x-factor-innovator | on-demand delegation | advisory (independent judgment) | isolated context | model |
| 11 | Review lens | `tier1-review/lenses.md` roster | invoked within review skill | advisory (semantic) | none | model |
| 12 | Work-item system (tracker) | beads: ACs, dependency gating (`bd ready` hides blocked work), `bd lint`, `bd human`, formulas/molecules (validated in trigger-layer spike; none installed here yet) | continuous (workflow substrate) | **blocking for sequencing**; observable for evidence | full DB | deterministic structure, model content |
| 13 | Memory | `bd remember`/`bd prime` + hook-layer knowledge.db | injected at session start | advisory | persistent | model consumes |
| 14 | Template / blueprint | `packet/template.md`, `docs/refinement/proposal-template.md`, `.github/pull_request_template.md`, design-doc template in `design-docs.mdc` | structure-at-authoring-time | advisory→observable (blueprint verify in `render.py` makes template conformance checkable) | none | deterministic structure |
| 15 | Narrative/authoritative docs | scratchpad, `docs/specs/`, `docs/decisions/` | read at session start / on demand | advisory (authoritative for intent) | persistent | model |
| 16 | Measurement / feedback | `docs/rule-effectiveness-scorecard.md` + rule-efficacy-analyst | periodic | observable (detects whether other surfaces work) | recorded scores | mixed |
| 17 | Project overlay | `.agents/overlay.md` convention | read by skills | advisory (parameterization) | none | deterministic keys |

**Surfaces referenced but not present:** MCP (operating-model.mdc describes
Jawnt MCP for cross-project reads — external, read-only); CI gates (repo has
only a PR template; no workflows) — a genuine gap, not just a catalog gap.

**Observations from the inventory:**

1. **The kit already trusts deterministic executables at its most
   quality-critical moments.** `assemble.py` exists because deterministic
   prompt assembly beats agent improvisation; `render.py` does headless
   blueprint/anchor verification; `playbook-doctor.sh --agent` was explicitly
   designed for agent consumption (SUMMARY keys, stable exit codes). "CLI"
   isn't a hypothetical surface for this kit — it's a proven pattern that the
   concepts.md model failed to name.
2. **Hooks here are already beyond nudges.** The knowledge-db hook layer
   holds durable state and performs evidence capture — contradicting the
   working assumption (from the trigger-layer spike's framing) that hooks are
   only reminder/gate surfaces. The spike's ceiling claim was about *bd*
   events, not about what hook scripts can do.
3. **The tracker is the strongest enforcement surface in daily use** —
   dependency gating mechanically hides blocked work; nothing else in the kit
   blocks anything during a session.
4. **Several surfaces exist to make *other* surfaces work** (measurement,
   memory, overlay, safety net). The catalog needs a way to say "this surface
   governs the governing mechanisms" — meta-surfaces.

## Part 2 — External landscape verification (research-agent synthesis)

Verified against current docs as of 2026-07-19. Full per-surface attribute
detail (activation/enforcement/state/judgment/portability/context-cost with
sources) is in the research-agent transcript; this section keeps what changes
kit decisions.

### Cursor surfaces

Rules (4 activation modes + nested AGENTS.md + team rules that admins can
make non-disableable + remote rules imported from GitHub repos — a
distribution channel directly relevant to this kit); skills (open
agentskills.io standard, progressive disclosure, reads `.claude/` and
`.codex/` dirs too); commands (`/name` markdown prompts); hooks (~21 events,
pre-hooks return allow/deny/ask, **command or prompt handlers** — the latter
is model judgment at a deterministic trigger); custom subagents (`readonly`
is a mechanical restriction); **Automations** (scheduled + world-event
triggers: PR events, CI completion, Slack, Linear, PagerDuty, webhooks; with
persistent Memories); plugins/marketplaces (bundle rules+skills+agents+
commands+hooks+MCP; team marketplaces with install review); sandbox +
permissions (`sandbox.json` network/path confinement is mechanically
blocking; Auto-review classifier is the model-judgment-gate hybrid); SDK
(headless agents, custom tools, `local.autoReview`).

### Claude Code surfaces

CLAUDE.md tree + `.claude/rules/` with path scoping; **auto memory**
(`MEMORY.md`, 200-line prefix loaded every session — agent-written, poisoning
risk); skills (slash **commands have merged into skills**; `context: fork`
runs a skill in a subagent; hooks embeddable in skill frontmatter); hooks
(~30 events, **5 handler types: command / http / mcp_tool / prompt / agent**;
exit-2 blocking; input/output rewriting; async with session wake); plugins
(+ LSP servers, private marketplaces, SHA pinning); output styles
(system-prompt level); permissions (deny-anywhere-is-final merge; managed
settings that users cannot override; sandbox `failIfUnsandboxed`); Agent
SDK / headless / Managed Agents; **agent teams** (experimental —
`TaskCreated`/`TaskCompleted` hooks can mechanically gate task closure);
**scheduled tiers** (`/loop` + cron tools, Desktop scheduled tasks, cloud
Routines); **Channels** (world events pushed *into* live sessions via MCP
notifications).

### MCP status — timing matters

Current ratified spec is **2025-11-25**. The **2026-07-28 revision lands
nine days after this memo** and is the largest since launch: stateless core,
server-initiated requests replaced by MRTR, tasks moved to an extension, and
**roots, sampling, and logging deprecated**. Elicitation (form + URL modes;
mechanically blocking human-in-the-loop inside a tool call) survives.
Consequence: **do not build MCP governance surfaces this month**; anything
we make should target the new revision. Reinforces Part 3's defer-MCP
verdict on independent grounds.

### Tool-agnostic layers

Git hooks (client-side bypassable via `--no-verify` — and agents do; only
server-side hooks truly block); branch protection/rulesets + required checks
+ merge queues (platform-enforced regardless of who pushes); agent-CLI design
specs (clispec.dev et al. — formalizing what `playbook-doctor.sh --agent`
already does); linters at three points with escalating strength
(editor advisory → hook observable → CI blocking); tests-as-executable-spec
(blocking in CI; only as strong as review of the tests — the zero-signal
problem); devcontainers ("a convention rather than an enforcement boundary"
per Claude's own docs); repo templates/scaffolds (act before any session
exists; no drift enforcement after day one — why they pair with
doctor/sync); **AGENTS.md as the cross-tool floor** (28+ tools, Linux
Foundation stewardship).

### Taxonomy upgrades the landscape forces

1. **Enforcement is four levels, not three:** advisory →
   **model-judgment-at-deterministic-trigger** (prompt hooks, Auto-review,
   `auto` permission mode — the governed model doesn't choose whether the
   check runs, but the checker can misjudge) → observable → blocking.
2. **Activation needs two more values:** *scheduled* and *world-event-driven*
   (Automations, Routines, Channels) — distinct from agent-lifecycle hooks.
3. **Distribution is its own surface class:** plugins, marketplaces, remote
   rules, templates, sync scripts — governance of the governance supply
   chain, with both vendors adding review/pinning mechanisms this year.

## Part 3 — MCP and CLI as governance surfaces (research-agent synthesis)

**Headline:** for a shell-capable toolkit, the winning stack is **CLI as the
sanctioned mutation/evidence path + hooks as in-session feedback + CI as the
non-bypassable backstop**. MCP earns its keep only for shell-less clients,
protocol-native human approval, credential withholding, or cross-project
aggregation. The flagship precedent is beads itself: its own MCP README
recommends the CLI + hooks over its MCP server wherever a shell exists
(~1-2k tokens vs 10-50k of MCP schema).

### MCP findings

- **Elicitation is real and current** (MCP spec 2025-06-18, URL-mode added
  2025-11-25): a server can pause a tool call and demand schema-validated
  human input — the protocol-native "deployment gate" pattern. Client must
  advertise the capability; well-built gates fail closed without it.
- **Working governance precedents exist**: HumanLayer (approval lifecycle in
  SQLite, `request_permission` tool injected into sessions), Shrimp Task
  Manager (server refuses invalid task state transitions — no completion
  without a verification score; completed tasks immutable), Microsoft Agent
  Governance Toolkit / MCP Visor / mcp-firewall (policy gateways with
  hash-chained audit logs — enterprise-scale, wrong fit here).
- **What MCP mechanically enforces that rules can't**: argument schema
  validation, refusal of invalid state transitions, un-skippable server-side
  logging, in-protocol human sign-off, credential withholding, durable
  cross-session state.
- **The bypass problem is structural**: MCP governs one execution path; an
  agent with a shell reaches the same outcome another way (`sed -i` on
  PLAN.md defeats an `amend_plan` tool). Forcing file edits through MCP
  requires per-harness deny-lists — brittle, not maintainable for a small
  kit. Plus token cost (schema bloat → context rot), server lifecycle, and
  cross-client `mcp.json` config drift (a whole tool genre exists just to
  sync it).

### CLI findings

- **Agent-friendly CLI design has formalized** (clispec.dev, cli-agent-spec,
  agent-native-design): `{ok, data, error}` JSON envelopes, named exit codes
  with machine-readable retry/side-effect semantics, non-interactive by
  default with structured refusal naming the bypass flag, `--dry-run` →
  `--confirm` flows. `playbook-doctor.sh --agent` already follows the
  pattern; the specs are its formalization.
- **Red-then-green evidence has near-precedents but no exact one**:
  TDD Guard / Probity persist test-run output and block implementation edits
  when no failing test exists (Probity's `requireCommand` gates a command on
  a prior one in session history — a commit-gate over process evidence, one
  config across Claude Code/Codex/Copilot). But **no off-the-shelf CLI
  records a durable failing-before/passing-after ledger** — a genuine, small
  gap the kit could fill, converting `bd close --reason` evidence from prose
  into checkable data.
- **Plan traceability precedent**: OpenSpec — every change is a
  `changes/<name>/` folder with proposal + delta specs that merge into the
  source-of-truth only on archive. Enforced by directory convention +
  commands, not blocking; violations become visible in `git diff`.
- **Hooks compose but are not a trust boundary**: Cursor executes Claude
  Code-format hooks (one hook set can serve both harnesses); PreToolUse
  can block. But documented harness bugs have silently ignored deny
  decisions — CI/pre-commit is the only layer outside the harness.

### Comparative verdicts (the two kit-relevant capabilities)

| Capability | Winning combination |
|---|---|
| Red-then-green TDD evidence | CLI records failing/passing runs to a committed JSONL ledger (timestamp + content hash); skill/rule instructs the call; CI verifies ledger presence/order for bug beads; hook gate optional UX |
| No silent plan mutation | CLI verb applies the edit + appends the change record atomically (OpenSpec delta shape); ~20-line pre-commit/CI diff check: plan file changed ⇒ matching record in same commit; blocking hook as immediate-feedback supplement |

**General principle:** make the honest path the cheap path (CLI), make
deviation visible (ledger + git), make one late gate non-bypassable (CI).
In-the-moment blocking (hooks, MCP) is a UX optimization, never the trust
boundary — the harness is the least reliable link and the shell is always
there.

**Adopt / skip recommendations for the kit** (to be confirmed in Part 4):
adopt CLI-first formalization of kit scripts, an evidence-ledger verb set,
a plan-amend verb + diff check, one shared hook set for both harnesses.
Skip: MCP policy gateways, cryptographic attestation (adopt the structure,
not the PKI), governance-MCP-as-primary-surface, MCP-as-sole-file-mutation
path. Future MCP trigger: the kit targeting shell-less clients — then wrap
the existing CLI in a thin MCP layer exactly as beads did.

## Part 4 — Synthesis: amended surface model and impact

### The amended model (applied to docs/refinement/concepts.md)

The six-surface model survives as *responsibility roles* but sits inside a
larger catalog of ten surface classes, each classifiable on six axes.
The full amended model lives in
[docs/refinement/concepts.md](../refinement/concepts.md) — summary:

**Axes:** activation (always-in-context / on-demand / agent-event /
world-event / scheduled / gate-at-boundary) · enforcement (advisory /
model-judgment-at-deterministic-trigger / observable / blocking) ·
statefulness · judgment (deterministic vs model) · portability · context
cost.

**Surface classes:** normative in-context · procedural on-demand ·
deterministic executable · MCP tool-surface · event & schedule ·
delegated judgment · platform & environment gates · human authority ·
work-item system · meta-surfaces (distribution, measurement,
parameterization, persistence).

**Placement principles** (the operational core): make the honest path the
cheap path (CLI); make deviation visible (evidence + git); make one late
gate non-bypassable (CI/platform); treat in-the-moment blocking (hooks,
MCP) as UX optimization, never the trust boundary. CLI-first wherever a
shell exists; MCP only for shell-less clients, in-protocol elicitation,
credential withholding, or cross-project aggregation.

### Impact on the refinement initiative

| Artifact / bead | Change |
|---|---|
| `docs/refinement/concepts.md` | Operating-surface section replaced with the amended model (this bead) |
| `process-kit-vvx` (pragmatic-tdd pilot proposal) | Option sets must draw from the full catalog — specifically: evidence-ledger CLI + CI verification as the observable/blocking layer for red-then-green evidence (the gap Part 3 found no off-the-shelf tool for), with Probity-style hook gating as optional in-session UX. Description updated. |
| `process-kit-l1h` (kit-wide audit) | Coverage extends beyond rules/skills/hooks to: distribution surfaces (playbook-init, sync-rules, safety net), permission/sandbox configs (none shipped — gap), CI layer (absent — gap), memory infra, tracker usage, templates. Audit uses the 4-level enforcement axis; flag any surface claiming enforcement it cannot deliver. Description updated. |
| `process-kit-tl1` (refinement skill) | No description change — its mechanism-audit reference consumes the foundations docs, which now carry the amended model |
| Spec non-goals | Unchanged: TDD *hooks* stay deferred. An evidence-ledger *CLI* was never excluded and is now a live option for the pilot proposal to weigh |

### Proposed follow-ups (proposed here, not pre-created — per bead non-goals)

1. **Evidence-ledger CLI** — not a spike; it enters as an *option* in the
   pilot proposal (vvx). If the proposal recommends it and the user accepts,
   it becomes a bead then.
2. **Single shared hook set for both harnesses** — Cursor executes Claude
   Code hook format, so the kit's `.claude/hooks/` could serve both. A
   candidate finding for the kit audit (l1h), not new work now.
3. **World-event/scheduled trigger layer** (Automations, Routines, Channels)
   — extends the 2026-07-16 trigger-layer spike's deferred auto-fire
   question with surfaces that didn't exist then. Revisit after the kit
   audit; upgrade trigger from the spike stands.
4. **MCP wrapper for shell-less clients** — defer. Upgrade when: the kit
   targets a shell-less client, AND the 2026-07-28 spec revision has
   settled. Pattern when triggered: thin MCP layer over the existing CLI,
   exactly as beads did.

### Corrections to prior kit assumptions (refinement findings in their own right)

1. The trigger-layer spike's "hooks are nudge/gate only" framing was about
   *bd's* event surface; it silently generalized. Hooks are blocking-capable
   in both harnesses (with documented reliability caveats that are exactly
   why CI stays the trust boundary). Finding type: *invalidated assumption*,
   magnitude: minor, transformation: correct.
2. The concepts.md six-surface model omitted surfaces the kit itself already
   relies on (CLIs, templates, tracker, memory, distribution). Finding type:
   *newly discovered requirement*, magnitude: local, transformation: extend.

## Part 5 — The profile-driven projection pattern (cursor-takehome-assignment)

Added 2026-07-19 (bead process-kit-8va.1 follow-up, process-kit-8va.2), from
a first-party reference implementation: `~/cursor-takehome-assignment`
("Engineering Onboarding Copilot"). It demonstrates a pattern the catalog
above names only abstractly — and partially corrects one of our own
placement heuristics.

### The verified mechanics

One team-owned YAML profile (`profiles/scikit-image.yaml`: approved/forbidden
paths, deprecated APIs with replacements, test conventions, docstring style,
contribution checklist, naming/import conventions, a `rule_prefix` namespace
for violation IDs, scaffold routing keywords, role-brief templates) is the
single source of truth. Four surfaces project from it:

| Projection | Mechanism | Enforcement |
|---|---|---|
| Cursor rule (`scikit-image-conventions.mdc`, glob-scoped to `*.py`) | **Generated** by `scripts/render_rules.py` with a "DO NOT EDIT" header; **CI fails if the rendered rule drifts from the profile** | advisory, but drift-proof |
| CLI (`ob scaffold/check/brief`) | Reads the profile **at runtime**; 100% deterministic, zero LLM calls (ADR-001) | observable→blocking |
| MCP server (FastMCP: 7 convention resources + a `check_workspace` tool) | Thin layer over the same engine, reads the same profile (ADR-002) — the wrap-the-CLI pattern from Part 3, implemented | observable |
| CI | Runs the *same* `ob check` + the rule-drift gate | blocking |

Three design details carry most of the value:

1. **Shared violation namespace.** The generated rule instructs the agent to
   report violations "using the SAME rule IDs the `ob check` CLI emits, so
   the editor and CI agree" (`SK-D-001`, `SK-T-002`, …). The advisory surface
   and the deterministic surface *agree by construction* — the "competing
   sources of truth" misplacement smell is fixed mechanically, not by
   discipline. Even the ID namespace is profile-owned (`rule_prefix`), so
   swapping profiles re-themes the whole rule catalog (proven with a
   `diffusers.yaml` stub: same violating workspace yields 5 `SK-*` findings
   under one profile, 2 `DIFF-*` under the other).
2. **Teaching and enforcement are projections of the same spec.** The
   onboarding layer (scaffold, role briefs) and the guardrail layer (check,
   CI) read one file. "Onboarding paradigm that is really an enforcement
   layer" is exactly right — they can't diverge because neither owns the
   conventions.
3. **Stage-scoped rule activation.** The workspace's SDLC rules attach by
   glob (planning on `PLAN.md`, implementation on `skimage/**/*.py`, testing
   on `test_*.py`, review on `BRIEFS.md`) — near-zero context cost when the
   stage isn't active. The kit, by contrast, carries ~12 `alwaysApply` rules.

### What it corrects in our model

concepts.md said: introduce a canonical specification "only when drift
between projections is actually observed." That heuristic is right for
**prose** specs — a fourth hand-maintained document is pure overhead until
drift proves the need. It is wrong for **data-shaped** conventions. When the
canonical layer is machine-readable and projections are *generated or read
at runtime* with a CI drift gate, the spec isn't a fourth document to keep
in sync — it's the only document, and drift is structurally impossible.
The economics invert. (Finding type: *planning weakness* in our own model;
magnitude: minor; transformation: correct + extend. concepts.md amended.)

The boundary that keeps this honest: profiles fit conventions that are
**enumerable as data** — paths, naming schemes, API lists, checklists,
required sections, evidence requirements. Judgment-shaped policy ("prefer
the smallest sufficient change") stays prose. A profile trying to encode
judgment becomes config nobody can evaluate; prose trying to carry data
becomes context bloat that nothing enforces.

### Implications for the kit (routed to the audit, not actioned now)

1. **Which kit conventions are data-shaped?** Candidates living in always-on
   prose today: commit-message format and branch naming (operating-model),
   the evidence-requirements-by-bead-type table (bead-completion), defer-
   comment format (defer-convention), scorecard items, bead AC requirements
   (partially machine-checked by `bd lint` already — the tracker is halfway
   to a profile). Each is a candidate for profile + deterministic checker +
   thin generated rule. → added to process-kit-l1h's audit questions.
2. **Stage/glob-scoped activation** as a context-cost lever for the 12
   always-on rules. → already within l1h's context-cost analysis.
3. **For the pragmatic-tdd pilot (vvx):** the test-policy-by-bead-type and
   evidence-requirements tables are data-shaped; if the pilot recommends the
   evidence-ledger CLI, a profile section could parameterize it (which bead
   types require red-then-green, what counts as evidence). Noted as an
   option-shaping input, not a scope change.
