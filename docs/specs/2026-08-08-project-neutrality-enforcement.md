# Project-Neutrality Enforcement

**Date:** 2026-08-08
**Beads:** epic `process-kit-4wh` (children: `ei0` private-tool leak, `dmm` tier2 de-vendoring, `9mf` distributed-text hygiene, `pi6` neutrality checker)
**Status:** Implemented, then revised by Tier 1 review. All four findings
remediated; the checker ships as `scripts/neutrality-scan` with
`profiles/neutrality-terms.toml` and the `neutrality-gate` job in kit CI. Open
questions resolved below; two design decisions were reversed — see "Tier 1
revisions".

## Tier 1 revisions

The first implementation passed its own tests and reported the surface clean.
Review found that "clean" had several silent paths to it, and that the class
advertised as the safety net was the weakest part of the design.

**The declared-terms region is gone.** The catalog solved its own
self-matching problem by wrapping its body in `:begin`/`:end` markers that the
scanner honored in *any* scanned file. That made suppression a property of
content — any rule or skill could open a region and silence the rest of itself
with the gate still green, and an unterminated region silenced everything
after it with no warning in the mode CI runs. The scanner now skips the
catalog it loaded, by resolved path, and offers no in-file suppression at all.
Exemption lives only in `[[allow]]`, which is in the catalog and requires a
written reason. Guarded by `test_no_in_file_marker_can_suppress_scanning`.

**The heuristic was widened after being measured.** `\b[A-Z][a-z]+ MCP\b` was
written against the single leak on hand and shipped described as "the only
class that catches a leak nobody has enumerated." Against five real MCP server
names it caught one: internal capitals (`GitHub`), all-caps (`AWS`), digits
(`S3`), camel case (`OpenAI`), and multi-word names (`Chrome DevTools`) all
passed clean. The token shape is now `[A-Z][A-Za-z0-9]*` with a run of up to
four tokens, plus a leading stopword lookahead so a capitalized sentence-opener
is not absorbed into the match — without it the reported term was `Use GitHub
MCP`, which is useless as an allowlist entry, and generic prose like "An MCP
plan" false-positived. `TestUnlistedToolHeuristic` pins all five shapes.

Also corrected: an unresolvable scope root now errors instead of being skipped
in silence (a renamed directory would have gone unscanned with the gate green
forever); an undecodable byte no longer makes a whole file report clean; class
overlap resolves by declared precedence rather than match width, so a listed
name reports with "this name is never legitimate" instead of the heuristic's
softer "allowlist it"; the config suffixes (`.yml`, `.yaml`, `.json`) are
scanned, which brought the CI workflow template — the most literally
distributed file in the kit — into scope for the first time; and the error
envelope now matches the rest of the checker family rather than a private
shape. `--explain` was deleted and the remedy always prints.

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

- [x] **False-positive load is the make-or-break risk.** Measured before the
      checker was written: across the six roots, the only hits were six
      instances of the maintainer handle inside the canonical clone URL — zero
      vendor-model, zero heuristic. Handled with a per-class context exemption
      (a handle inside `github.com/<owner>/` is project identity, not
      attribution) rather than six line-pinned allowlist entries that move
      whenever surrounding prose is edited. Host platforms stayed out of the
      vendor class, and that decision is now pinned by test: adding `Cursor` to
      the class fails both the host-platform fixture and the real-surface scan.
- [x] **The heuristic class will have false positives** by construction.
      Accepted as specified. Zero fired on the real surface, so the allowlist
      shipped empty; the shape is documented in the catalog for the first entry
      that needs it.
- [x] **Overlay-dependent behavior needs a sensible no-overlay path.** Done in
      `dmm`: with no overlay and no spec `models` field, the assembler emits
      archetype language copied from council's wording, and `--json`-free
      behavior is pinned by `test_tier2_assemble`.
- [x] Whether `profiles/neutrality-terms.toml` should be drift-checked by
      `doctor`. **Resolved: no.** The catalog never lands in a target repo, so
      there is no target-side copy to drift from. Adding a doctor check would
      mean adding a `SUMMARY` key and precedence slot for a file no adopter
      has. The catalog is instead guarded where it can actually break: the
      checker errors (exit 3) on a missing, unreadable, or invalid catalog
      rather than silently scanning with a different one, and that path is
      tested.

## Outcome

The checker was validated against history rather than only against fixtures:
reconstructing the pre-fix versions of all four findings from git and scanning
them produces 17 findings across three classes — the private-tool directive by
the heuristic, the vendor lineup in both the `.py` and the `.md`, and the
personal attribution in the profile.

Finding 4 (a vendor-behavior claim with no revisit trigger) is **not** term
detectable and is not claimed as covered. It was a judgment defect, not a
term: the words were all legitimate, and only the absence of a trigger made it
rot. The defer convention's no-trigger law is the mechanism for that class, and
it applies to code comments rather than rule prose. Whether to extend
trigger-required discipline to time-decaying claims in rule prose is a
separate question this work does not answer.
