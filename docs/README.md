# Docs — Orientation

Reference material for the kit. If you're new, read in this order:

| # | Document | What it covers | Time |
|---|----------|----------------|------|
| 1 | **[Core Concepts](concepts.md)** | Why the kit exists and how the five components (beads, roles, rules, scratchpad, governance) work together. | ~10 min |
| 2 | **[FAQ](faq.md)** | Common questions from real adopters — Cursor vs Claude, multiple agents, what is a bead, how to migrate. | ~5 min |
| 3 | **[Quick Start](../QUICKSTART.md)** | Set up the kit in your project (one command or manual steps). | ~5 min |
| 4 | **[Onboarding Sandbox](../sandbox/)** | Hands-on 45-minute exercise teaching the full workflow by doing. | ~45 min |

## Reference

| Document | What it is |
|----------|-----------|
| [Glossary](glossary.md) | Plain-English definitions of all terminology. |
| [Operating the Kit](operations.md) | Distribution semantics, drift checking, worktree setup, versioning mechanics. |
| [Governance](governance.md) | How the Agentic Covenant fits into the kit. |
| [Agentic Covenant Adoption Guide](adoption-guide.md) | Step-by-step governance adoption for teams. |
| [Rule Effectiveness Scorecard](rule-effectiveness-scorecard.md) | Measuring whether rule changes improve agent behavior. |
| [Refinement Concepts](refinement/concepts.md) | The refinement control loop, trigger/findings taxonomies, magnitude × transformation classification, operating-surface model. |
| [Refinement Proposal Template](refinement/proposal-template.md) | The package format a refinement produces; proposal becomes plan revision only after approval. |
| [Blog draft: Agentic Covenant](blog-agentic-covenant.md) | Draft post on why open source needs the Covenant (publication candidate). |

## Directory index

| Directory | Purpose |
|-----------|---------|
| [releases/](releases/) | Release notes per version, starting with v0.2.0. |
| [specs/](specs/) | Design docs for multi-bead initiatives — architecture, trade-offs, non-goals (see the design-docs rule). |
| [research/](research/) | Research memos and spike findings that inform specs and refinements. |
| [refinements/](refinements/) | Dated refinement proposals — the output of individual refinement runs. |
| [decisions/](decisions/) | Numbered decision records for open project-level choices (naming, license, publication). |

Naming note: `refinement/` (singular) holds the refinement *method* — concepts and the proposal template — while `refinements/` (plural) holds the *instances*: dated proposals produced by applying that method.

## Key concepts (30-second version)

**Beads** — Structured, dependency-aware work items agents can read, claim, and close from the terminal. Acceptance criteria in, evidence out.

**Agent Rules** — Enforced standards that travel with the repo. Test discipline, AC verification, evidence-based completion. Portable markdown — works with any AI tool.

**Skills** — On-demand procedures for recurring multi-step tasks (reviews, debugging, kickoff). The rules say *what must happen*; skills encode *how to run it*.

**Crawl / Walk / Run** — Maturity model. Crawl = agent decomposes + executes within guardrails, human reviews. Walk = agents handle low-risk work autonomously with CI gates. Run = constrained autonomy with orchestration infrastructure. Phases are earned by evidence, not by calendar.
