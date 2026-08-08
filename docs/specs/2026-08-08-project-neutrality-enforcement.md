# Project-Neutrality Enforcement

**Date:** 2026-08-08
**Beads:** epic TBD (children: Jawnt leak, tier2 de-vendoring, distributed-text hygiene, neutrality checker)
**Status:** Draft

## Background

`AGENTS.md` declares project neutrality as law: "Skill and rule content must stay
project-neutral: no project names, people, or project/user-specific parameters in
the generic core." The kit has no checker for it, and a manual sweep of the
distributed surface on 2026-08-08 found four violations, one of which had been
shipping in an always-on rule to every sync target.

| # | Finding | Location | Class |
|---|---------|----------|-------|
| 1 | `Jawnt MCP` directive in an always-on rule | `cursor/rules/operating-model.mdc:48`, `claude/rules/operating-model.md:43` | private tool name |
| 2 | `DEFAULT_MODELS = ["Grok", "Gemini", "GPT"]` | `skills/tier2-handoff/assemble.py:51`, `SKILL.md:116,186` | vendor model lineup |
| 3 | `Kevin` attribution in distributed data file | `profiles/conventions.toml:40,53` | personal identifier |
| 4 | `Claude Code has no Cursor alwaysApply` with no revisit trigger | `cursor/rules/core-upgrade-offer.mdc:10`, `claude/rules/core-upgrade-offer.md:5` | time-decaying vendor claim |

Finding 2 demonstrated live failure: the emitted Tier 2 prompt for
`process-kit-3mr` instructed the operator to paste into Grok and Gemini, two
lanes the operator had already dropped for underperformance. The default fired
because this repo has no overlay and the spec omitted the `models` field. No test
failed. The tool was confidently wrong and silent about it.

## Architecture and component overview

Two halves: **remediation** of the four findings, and a **mechanism** that keeps
them from recurring.

The remediation pattern is uniform and already has a reference implementation in
the repo. `skills/council/SKILL.md` describes reviewer diversity by capability
archetype ("strongest available reasoning model", "a capable model from a
different family", "your judgment against the models currently available") and
names no vendor. `skills/tier1-review/SKILL.md` does the same for its lenses.
Generic content keeps capability-level language; the concrete parameter moves to
the two-scope overlay documented in `skills/README.md` (per-project
`.agents/overlay.md`, machine-global `~/.agents/overlay.md`).

The mechanism is a new kit-CI checker, `scripts/neutrality-scan`, generalized
from the term-scanning helpers already in `scripts/tests/test_core_manifest.py`.
That test's `grep_targets` / `find_unclean` pair is a neutrality scanner with a
single hardcoded term class (`\bbd\b|\bbeads?\b`) applied to a single scope (the
core manifest). This work widens both axes: a configurable term-class list, and
the full distributed surface as scope.

## Data flow and key interfaces

```
profiles/neutrality-terms.toml   (term classes + allowlist)
              |
              v
scripts/neutrality-scan  --json | --explain
              |
      scope resolution
              |
   cursor/rules/**  claude/rules/**  skills/**
   templates/**  global-safety-net/**  profiles/**
              |
              v
   findings: (file, lineno, class, term, line)
              |
              v
   exit 0 = clean · exit 1 = findings · CI job fails
```

Term classes, initial contents:

- **`vendor_model`** — reviewer-lane and third-party model names: Grok, Gemini,
  GPT, Codex, Opus, Sonnet, Fable, plus version-suffixed slugs.
- **`personal`** — maintainer names and handles.
- **`private_tool`** — known private project and tool names.
- **`private_tool_heuristic`** — structural rather than listed: a
  capitalized-word-plus-`MCP` bigram (`\b[A-Z][a-z]+ MCP\b`). This catches
  *unlisted* leaks, which is the only way the checker survives contact with tool
  names nobody has thought of yet. It is what would have caught finding 1.

## Trade-offs and decisions

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Distribute as a CLI to target repos (defer-lint precedent) | Adopters can check their own overlays | Neutrality is a property of *kit-authored* content; target repos are *supposed* to name their own projects | **Rejected.** Kit-CI-only, following the `test_core_manifest.py` precedent |
| Single regex, like the existing bd-clean check | Trivial to build | Cannot express per-class allowlists or the platform-name boundary | **Rejected** |
| Term list in code | No extra file | Every new term is a code change plus test churn | **Rejected** |
| Term list in `profiles/neutrality-terms.toml` | Terms evolve without touching logic; matches the `conventions.toml` precedent | One more profile file to keep from drifting | **Accepted** |
| Ban all vendor names including Cursor and Claude | Maximally strict | Unusable. Those are the kit's two declared host platforms and appear legitimately on nearly every page | **Rejected.** Host platforms are explicitly out of the `vendor_model` class |
| Scan `docs/` too | Wider net | `docs/decisions/`, `docs/specs/`, and `docs/reviews/` are dated historical records where names are correct and load-bearing | **Rejected.** Out of scope |
| Fixes first, checker last (checker depends on all three fix beads) | Checker lands green and locks the door behind the fixes | Delays discovery of leaks the manual sweep missed | **Accepted**, with the checker's ACs requiring a zero-finding scan; anything it surfaces beyond the four known findings becomes a follow-up bead |

The last row is the sequencing decision: the three remediation beads are mutually
independent and may run in parallel; the checker bead blocks on all three.

## Non-goals

- Not distributed to target repos, and not added to `distributed-clis.list`.
- Not scanning `docs/**`, `scripts/**` implementation, `CHANGELOG.md`, or the
  scratchpad. Installer scripts legitimately hardcode the canonical repo URL.
- Not auto-fixing. The checker reports; a human or agent decides whether a hit is
  rot or a legitimate platform reference.
- Not resolving whether Tier 1 and Tier 2 should become core-tier-eligible. That
  question surfaced in the same conversation and is deliberately separate: it is
  a packaging question, not a neutrality question.
- Not building the reviewer-lane scorecard. Making lane choice evidence-driven is
  a distinct initiative; this work only stops the kit from asserting a lineup.

## Risks and open questions

- [ ] **False-positive load is the make-or-break risk.** If the `vendor_model`
      class is drawn too wide it fires on legitimate host-platform prose and the
      checker gets disabled. Mitigation: narrow initial class, explicit host
      platform exclusion, and a per-term allowlist with a required reason field.
- [ ] **The heuristic class will have false positives** by construction (any
      capitalized word before "MCP", including a legitimately generic example).
      Accept them: an allowlist entry is cheap, an undetected leak shipping every
      turn is not.
- [ ] **Overlay-dependent behavior needs a sensible no-overlay path.** After
      finding 2 is fixed, `assemble.py` with no overlay and no spec `models`
      field must emit archetype language rather than either crashing or silently
      picking vendors. Council's wording is the model to copy.
- [ ] Whether `profiles/neutrality-terms.toml` should be drift-checked by
      `doctor` like `conventions.toml` is. Leaning no, since it is kit-internal
      and never lands in a target repo.
