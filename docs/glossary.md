# Glossary — AI-Native Engineering Operating Model

Quick reference for terminology used in the kit's rules and docs. Designed for anyone encountering these concepts for the first time. For how the pieces fit together, see **[Core Concepts](concepts.md)**.

| Term | What it means |
|------|---------------|
| **Bead** | A structured work item that lives in the repo. Has a title, description, acceptance criteria, dependencies, and priority. Think of it as an issue-tracker sub-task, but designed for agents — persistent, queryable, and dependency-aware. |
| **Beads (bd)** | The CLI tool for creating and managing beads. Developers and agents use it from the terminal. `bd create`, `bd ready`, `bd close`. |
| **Acceptance Criteria (ACs)** | Observable outcomes that define "done" for a bead. Written in behavioral language ("loading indicator appears"), not implementation steps ("add isLoading variable"). |
| **Agent** | An AI coding assistant (Cursor, Claude Code, Copilot, Windsurf, etc.) that reads rules, executes tasks, writes code, and runs tests within a developer's session. |
| **Agent Rules** | Markdown files committed to the repo that teach agents how to behave — test discipline, quality standards, completion checks. Portable across AI tools. In Cursor these are `.mdc` files in `.cursor/rules/`. |
| **Skill** | An on-demand, multi-step procedure an agent reads and follows (a `SKILL.md` file). Rules state what must happen; skills encode how to run it. |
| **Decomposition** | Breaking a story into agent-sized beads with explicit ACs. The agent proposes the breakdown; the developer reviews and approves. |
| **Two-Tier Decomposition** | The org-level pattern: Product/tech leads define epics and stories (human-sized). Developers + agents break stories into beads (agent-sized). |
| **Risk-Tiered Review** | Routing PRs to different review levels based on what changed. High-risk (auth, billing, data model) gets mandatory human review. Medium-risk gets lighter review + CI. Low-risk gets CI-only with sampling. |
| **Code Churn** | How often a file changes. A file modified 50+ times in 90 days usually signals unstable design or shifting requirements. |
| **Lottery Risk** | When 90%+ of a file's commits come from one person. If that person leaves, the knowledge goes with them. Named after "what if they win the lottery?" |
| **Hotspot** | A file that is both complex and frequently changed. Where bugs are most likely to live and maintenance costs compound. |
| **Orchestration** | A layer that coordinates multiple agent sessions — assigning work, monitoring progress, detecting stuck agents, recovering from failures. An emerging capability, not a daily-use default. |
| **Pilot** | A controlled rollout with fixed scope and baseline metrics captured before day 1. Used to validate the operating model before scaling. |
| **Playbook / Kit** | This repo. Contains shared agent rules, skills, scripts, and operating-model docs. The single source of truth for how agentic development runs. |
| **Contract Testing** | Tests that verify two separately-built components agree on their shared interface. Important when agents build pieces independently. |
| **Cost Per Unit of Work** | The API cost (tokens, compute) to complete one bead. Measured during a pilot to model org-wide costs before scaling. |
| **Refinement** | A deliberate, evidence-grounded audit of a project's intent, plan, execution, and operating mechanisms. Most refinements are caused by discovery, not failure. Full model in [Refinement Concepts](refinement/concepts.md). |
| **Refinement Proposal** | The structured output of a refinement: classified findings, options, and a recommendation — or an explicit confirmation that nothing needs to change. It becomes a plan revision only after human approval ("no silent plan mutation"). Format: [proposal template](refinement/proposal-template.md). |
| **Operating Surface** | A place where a capability can live and act on agent behavior — a rule, skill, hook, CI gate, tracker, etc. Each surface has a bounded responsibility and is characterized on six axes (activation, enforcement, statefulness, judgment, portability, context cost). See [Refinement Concepts](refinement/concepts.md). |
| **Surface Class** | One of ten groupings of operating surfaces by bounded responsibility — e.g. normative in-context (rules), procedural on-demand (skills), platform gates (CI). The class tells you what kind of control a surface can actually deliver. Catalog in [Refinement Concepts](refinement/concepts.md). |
| **Magnitude × Transformation** | The two-axis scheme for classifying a proposed change: *magnitude* (none → minor → local → cross-cutting → structural → strategic → existential) and *transformation* (the operation performed: clarify, correct, extend, split, relocate…). Applied per affected dimension, never collapsed into one project-wide "level." Defined in [Refinement Concepts](refinement/concepts.md). |
| **Mechanism Placement** | Refinement aimed at the operating system that governs execution rather than the work itself. The question is not "is the content right?" but "is this capability in the correct artifact, activated at the correct time, with the correct authority and enforcement?" See [Refinement Concepts](refinement/concepts.md). |
| **Obligations Checklist** | The content-neutrality proof required when splitting, relocating, or merging rules, skills, hooks, or lenses: every obligation in the current artifact mapped to its destination surface, proving nothing is lost in the move. Format in the [proposal template](refinement/proposal-template.md). |
