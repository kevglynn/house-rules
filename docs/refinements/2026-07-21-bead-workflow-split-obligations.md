# Bead Workflow Split — Obligations Checklist

**Date:** 2026-07-21
**Bead:** process-kit-n0w (Wave 2, finding F1 of
`docs/refinements/2026-07-19-kit-wide-mechanism-placement.md`)
**Method:** the pragmatic-tdd pilot's content-neutrality proof
(`docs/refinements/2026-07-19-pragmatic-tdd-topology.md` §7), applied to
`cursor/rules/bead-completion.mdc` and `cursor/rules/beads-quality.mdc` in
one pass (one workflow, one destination skill — splitting the checklist
would split the workflow across a pointer, same reasoning as the skill).

Every obligation/prescription in the two pre-split rules (bead-completion
119 lines, beads-quality 105 lines, state at commit `e14b9bb`), mapped to
its destination. **Rule-BC** = the thinned always-on `bead-completion.mdc`;
**Rule-BQ** = the thinned always-on `beads-quality.mdc`; **Skill** =
`skills/bead-authoring/SKILL.md` (new, created by this split);
**graph-planning** = `skills/graph-planning/SKILL.md` (pre-existing);
**session-lifecycle** = `cursor/rules/session-lifecycle.mdc`.

ID namespaces, per the template note in
`docs/refinements/2026-07-21-multi-agent-review-split-obligations.md`:
content that lands in the **newly created** skill uses the shared namespace
**B1–B9** — the same IDs appear in the skill text, so checklist and
destination agree by construction (the pilot's O1–O17 pattern, the
operating-model split's G1–G7 precedent). Everything else uses the
document-local namespaces **BC1–BC25** (bead-completion) and **BQ1–BQ18**
(beads-quality). Placement only, no substance changes.

## Content landing in the new skill (shared IDs)

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| B1 | Dedupe search procedure: `bd search "<topic>"` / `bd list --status=open` commands; related-bead triage (child via `--parent`, dependency via `bd dep add`, or update the existing description); the skip-search escape hatch with the embedded-mode doctor caveat | **Skill** (Phase 1) — the caveat rendered as a pointer to session-lifecycle, see BQ11 |
| B2 | The worked good/bad `bd create` example (loading-indicators bead with full description, ACs, non-goals) | **Skill** (Phase 2, verbatim) |
| B3 | Validation mechanics: `bd create --dry-run`, `bd lint`, `bd config set validation.on-create warn` | **Skill** (Phase 3). The `validation.on-create` prescription survives only skill-side (also enacted by `playbook-init.sh`, which sets it at bootstrap) |
| B4 | Wisp mechanics: `--ephemeral` use cases (heartbeats, exploratory notes, coordination signals), TTL compaction, export exclusion, `bd promote <wisp-id> --reason` | **Skill** (Phase 4) |
| B5 | JIT-verification question list (files/paths still exist? APIs/patterns still match? anything changed affecting the approach?) | **Skill** (Phase 5) — the obligation itself stays Rule-BC, see BC2 |
| B6 | Progress-tracking semantics: `bd note` = decisions (persistent, in `bd show`), `bd comment` = timestamped discussion; context attached to the work item | **Skill** (Phase 6) + **Rule-BC** (one-line obligation, see BC25) |
| B7 | Self-review step list (re-read each AC via `bd show <id>`; verify each is satisfied by the code as written; fix or escalate any unmet AC) | **Skill** (Phase 7) — the obligation itself stays Rule-BC, see BC6 |
| B8 | Close-reason format and the worked good/bad close example ("Done" vs commit-ref + per-AC evidence); `--suggest-next`/`--claim-next` mention | **Skill** (Phase 7) — the flags' canonical home remains Rule-BC (BC15, per the operating-model checklist's OM14 designation); the skill mentions them with the close procedure |
| B9 | The `bd remember` when/when-not manual: the 5-bullet when-to list, the 6-bullet when-NOT list, the worked example (`account-sync-soft-deletes`), and the key-discipline details (kebab-case rationale, `bd memories` check-before-create, one-per-bead rationale) | **Skill** (Phase 8) — litmus test and the one-line key/count law stay Rule-BC (BC20, BC21, BC23) |

## bead-completion.mdc (document-local IDs)

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| BC1 | Frontmatter: description + alwaysApply | **Rule-BC** (kept unchanged) |
| BC2 | JIT verification: before writing code, `bd show --current` and verify the bead's description against reality | **Rule-BC** (kept, compressed) + question list → **Skill** (B5). Section name "JIT verification" preserved — the operating-model checklist (OM10) designates this section canonical |
| BC3 | The three JIT questions | **Skill** (B5) |
| BC4 | Mismatch handling: update the implementation approach, note the discrepancy, proceed; never modify ACs | **Rule-BC** (kept; the "never modify ACs" sentence collapsed into § AC ownership — the pre-split rule stated it twice, in JIT and in AC ownership) |
| BC5 | AC ownership: Planner writes ACs; Executor never modifies; wrong/obsolete/impossible AC → block + escalate; no silent reinterpretation | **Rule-BC** (kept verbatim) — forward obligation 1 from the operating-model split's Tier 1 review: `operating-model.mdc` points at this section as law; it must stay rule-side. Discharged |
| BC6 | Self-review obligation before declaring done | **Rule-BC** (kept, step list compressed into prose) + step list → **Skill** (B7). Section retitled "Self-review before declaring done" (was "Before declaring done — self-review"); no external reference names the old title |
| BC7 | The three self-review steps | **Skill** (B7) |
| BC8 | "Not a separate subagent or reviewer — a deliberate pause by the implementing agent" | **Rule-BC** (kept) |
| BC9 | Evidence policy: every close reason maps evidence to ACs | **Rule-BC** (kept; gains the commit/branch/PR reference requirement moved from beads-quality, see BQ17) |
| BC10 | The evidence table (10 bead-type rows, Bug through Epic) | **Rule-BC** (kept verbatim, Epic row intact) — forward obligation 2 discharged: `skills/graph-planning` G7 points at the Epic row as canonical close-evidence law; not relocated or reworded. **Flagged: this table is the top profile candidate for profile-driven projection** — it is exactly the per-type enumerable-data shape the profile projection prototype (`experiments/profile-spike/profile.yaml`) already models as `close_evidence`. Input to the promotion decision (process-kit-8qv); the close-reason lint checker (process-kit-gsx) would consume the same shape |
| BC11 | Do-not-defer invariant: AC verification before close; IOU framing ("will be re-verified later" indistinguishable from "not verified") | **Rule-BC** (kept verbatim) |
| BC12 | The four legitimate options for an unverifiable AC (do the step / leave in_progress / block / split to follow-up existing at close time) — never a fifth | **Rule-BC** (kept verbatim). Section name "Do not defer AC verification" preserved — beads-quality anti-pattern 6 and CONTRIBUTING.md cite it |
| BC13 | The invariant closing statement ("Later" is not an acceptable close state) | **Rule-BC** (kept verbatim) |
| BC14 | "See `beads-quality.mdc` for close reason format and examples" | **Superseded** — the format/examples relocated to the **Skill** (B8), so the pointer now targets the skill. The old pointer was also mildly wrong-way (close format living in the *authoring* rule); the new topology fixes the address |
| BC15 | `--suggest-next` / `--claim-next` continuation flags | **Rule-BC** (kept, compressed to one line inside § Evidence policy; the standalone "After closing — workflow continuation" header retired). Canonical home per the operating-model checklist's OM14 designation — both flags still live rule-side, satisfying OM14's substance though its section-name citation is now historical. Also mentioned in Skill Phase 7 |
| BC16 | Knowledge-capture pause after close; "most closures produce no memory" | **Rule-BC** (kept) |
| BC17 | The `bd remember` worked example | **Skill** (B9) |
| BC18 | When-to-remember list (5 bullets) | **Skill** (B9) |
| BC19 | When-NOT-to-remember list (6 bullets) | **Skill** (B9) |
| BC20 | The litmus test (fresh agent wastes significant time / wrong assumption) | **Rule-BC** (kept verbatim, block-quoted) |
| BC21 | Requirement: always `--key <area>-<topic>` | **Rule-BC** (one line) + rationale/detail → **Skill** (B9) |
| BC22 | Requirement: `bd memories <keyword>` check before creating; update existing key rather than parallel entry | **Skill** (B9) |
| BC23 | Requirement: one memory per bead, max | **Rule-BC** (one line) + rationale → **Skill** (B9) |
| BC24 | Staleness protocol: `bd prime`-injected memory contradicting the codebase → update (`bd remember --key <existing-key>`) or remove (`bd forget`) immediately; never work around silently | **Rule-BC** (kept verbatim in substance) — session-lifecycle § Extended start points at "the staleness protocol in bead-completion.mdc"; this stays rule-side |
| BC25 | Progress tracking: `bd note` vs `bd comment` | **Rule-BC** (one-line obligation, folded into § JIT verification as the during-work sentence; the standalone "Progress tracking" header retired) + full semantics → **Skill** (B6) |

## beads-quality.mdc (document-local IDs)

| # | Pre-split obligation (rule text) | Destination |
|---|---|---|
| BQ1 | Frontmatter: description + alwaysApply | **Rule-BQ** (description updated: "and every close must include evidence" → "close-side law lives in bead-completion.mdc" — truth-in-labeling for the AC3 dedup, not a substance change; the close-evidence obligation itself is unchanged at its canonical home) |
| BQ2 | Self-containment law (picked up cold, no scratchpad/chat history) | **Rule-BQ** (kept verbatim) |
| BQ3 | Description dimensions: What/Where/How/Why | **Rule-BQ** (kept verbatim) |
| BQ4 | ACs required for bug/feature/task/story/spike; epics take Success Criteria; `--acceptance` flag | **Rule-BQ** (kept verbatim) |
| BQ5 | The AC-by-type table (5 rows) | **Rule-BQ** (kept verbatim) |
| BQ6 | Behavioral language; observable outcomes not implementation steps; the loading-indicator example line | **Rule-BQ** (kept, three bullets folded into one sentence — every clause survives) |
| BQ7 | Non-goals line recommended for feature beads | **Rule-BQ** (kept verbatim) |
| BQ8 | Validation: `bd lint`, `bd config set validation.on-create warn`, `bd create --dry-run` | **Rule-BQ** (one-line pointer: lint/dry-run named) + mechanics → **Skill** (B3). The `validation.on-create warn` prescription is skill-side only now — `playbook-init.sh` also sets it at bootstrap, so the always-on copy was redundant |
| BQ9 | Dedupe search before creating (commands) | **Rule-BQ** (kept, compressed — both commands survive) + procedure → **Skill** (B1) |
| BQ10 | Related-bead triage: child / dependency / update-existing | **Rule-BQ** (one clause: "extending, parenting, or depending") + full question → **Skill** (B1) |
| BQ11 | Skip-search escape hatch + embedded-mode doctor caveat ("server mode; in embedded mode doctor no-ops — run `bd lint` and `bd orphans` instead") | **Rule-BQ** (escape hatch kept) — the caveat's inline copy **replaced with a pointer** to `session-lifecycle.mdc` § Extended close, the canonical home (forward obligation 3 from the operating-model split's Tier 1 review — F3 dedup, one of ~5 copies retired). Same pointer used in Skill Phase 1 |
| BQ12 | Worked good/bad `bd create` example | **Skill** (B2, verbatim) |
| BQ13 | Parent-child structure: `--parent`, hierarchical IDs, prefer `--parent` over standalone `bd dep add` for containment, `bd epic status` | **Canonical home designated: `skills/graph-planning` Phase 2** (forward obligation 4 — one home picked, recorded here). Phase 2 already carried the `--parent` mechanics in substance-complete form (paraphrase — it drops the pre-split `bd-epic-123.1` literal example) and Phase 4 (G4) carries `bd epic status`; Rule-BQ § Structure is now a pointer; the bead-authoring skill also points there rather than restating. The graph-planning skill was NOT edited — it already holds the content |
| BQ14 | Wisps: `--ephemeral`, TTL compaction, export exclusion, `bd promote` | **Skill** (B4); Rule-BQ keeps a pointer in § Structure |
| BQ15 | Anti-patterns 1–7 (explosion, graph-free planning, stale accumulation, duplicate creation, orphaned in-progress, evidence-free closes, AC-as-steps) | **Rule-BQ** (all seven kept, compressed to one line each; **numbering preserved** — `skills/graph-planning` cites "anti-pattern 1" and "anti-pattern 2" by number, and the new skill cites 4). Anti-pattern 6 keeps its pointer to bead-completion § "Do not defer AC verification" |
| BQ16 | "When closing beads": `--reason` maps to ACs; see bead-completion for the evidence policy | **Rule-BQ** (reduced to a pure cross-ref — the AC3 dedup; the restated obligation text is gone, the pointer remains) |
| BQ17 | "Reference commit hash, branch name, or PR URL in every close reason" | **MOVED to Rule-BC** § Evidence policy (close law consolidated at the close-law home; this was the one close-side obligation that existed *only* in beads-quality). `experiments/profile-spike/profile.yaml` sources the commit-ref rule from beads-quality "When closing beads" — noted for the coordinator below |
| BQ18 | Worked good/bad close-reason example | **Skill** (B8, verbatim) |

## Dropped content — with rationale

Nothing law-shaped is dropped, and no example is dropped — every worked
example relocated to the skill intact. Two textual consolidations:

1. **The duplicated never-modify-ACs sentence (BC4).** The pre-split
   bead-completion stated it in both § JIT verification and § AC ownership;
   the thinned rule states it once, in § AC ownership (the section
   operating-model points at).
2. **The embedded-mode doctor caveat's inline copy (BQ11).** Replaced with
   a pointer to its canonical home (session-lifecycle § Extended close).
   The caveat's substance survives there (the canonical copy is a superset
   of the retired inline wording — it adds `bd blocked` and the exit-0
   explanation).

## Cross-rule dedup executed by this split (AC3 / F3 slice)

| Duplicate | Canonical home | What was demoted |
|---|---|---|
| Close-evidence restatement in beads-quality § "When closing beads" (BQ16) | `bead-completion.mdc` § Evidence policy | beads-quality's copy reduced to a cross-ref; its unique commit-ref clause moved to the canonical home (BQ17) |
| Embedded-mode doctor caveat (BQ11) | `session-lifecycle.mdc` § Extended close | beads-quality's inline copy replaced with a pointer. Copies in `worktree-awareness.mdc` are out of this bead's scope — flagged below |
| Parent-child mechanics (BQ13) | `skills/graph-planning` Phase 2 | beads-quality's § Parent-child structure reduced to a pointer; the bead-authoring skill points rather than restates |
| Never-modify-ACs duplicate inside bead-completion (BC4) | `bead-completion.mdc` § AC ownership | the JIT-section restatement collapsed |

## Forward obligations from prior splits — discharge record

1. **AC ownership stays rule-side** (operating-model split review): discharged — BC5 kept verbatim in the thinned rule.
2. **Epic evidence-table row stays rule-side and intact** (graph-planning G7 dependency): discharged — BC10, row unmodified.
3. **Embedded-mode caveat → pointer to session-lifecycle**: discharged for beads-quality — BQ11. (worktree-awareness's copies untouched, out of scope.)
4. **One canonical home for parent-child/graph mechanics**: discharged — `skills/graph-planning` Phase 2 designated, recorded at BQ13.

## Flagged for the coordinator (not changed — substance or out of scope)

- **`experiments/profile-spike/profile.yaml` and `.../conventions` cite pre-split addresses.** The profile's `close_evidence` block sources the commit-ref rule from `beads-quality.mdc "When closing beads"` — that clause now lives in `bead-completion.mdc` § Evidence policy (BQ17). The spike is a frozen prototype (process-kit-vgz output), so its comments were left as-is; any profile work following the promotion decision (process-kit-8qv) should re-source from the post-split addresses. The evidence table itself did not move, so `bead-completion.mdc#evidence-policy` references remain correct.
- **`.cursor/agents/*.md` rule summaries** (beads-strategist, rules-auditor, rule-efficacy-analyst) describe beads-quality as covering "parent-child, ephemeral, validation config" — now pointer/skill content. Descriptions are still truthy at the summary level; retitling is a docs touch-up, not done here.
- **`docs/research/2026-07-19-operating-surface-catalog.md` and the placement audit** describe the pre-split composition of both rules — historical records, correctly left stale.
- **`sandbox/project/.claude/rules/*.md`** are point-in-time bootstrap fixtures of the old rules; they regenerate on the next sandbox refresh, not edited here.
- **QUICKSTART.md / README.md one-line rule descriptions**: QUICKSTART.md's remains accurate. README.md's beads-quality row said "evidence on close" — exactly the obligation this split moved out of beads-quality (BQ16/BQ17); caught by the Tier 1 code-reviewer lens (the original entry here falsely recorded it as verified) and corrected during review to mirror the rule's new frontmatter.
- **`scripts/playbook-init.sh` validation-config comment** attributed the `validation.on-create warn` prescription to beads-quality.mdc; post-split it lives skill-side (B3). Caught by the code-reviewer lens; comment re-attributed to the bead-authoring skill during review.

## Tier 1 review corrections (post-split fix commit)

The review pass also tightened the skill against re-drift: the Anti-Patterns
table (all rows restated phases or cited rules) was removed, and the four
paraphrased law copies (AC ownership, litmus test, "most closures produce
no memory", staleness protocol) were reduced to section-name citations.

**Template note for future splits:** a skill phase cites the law by
section name, full stop — it never re-summarizes the law's content after
the citation. Paraphrased law copies in skills are the same drift family
the splits exist to retire, just at lower rent. Likewise, a skill's
Anti-Patterns section exists only when it names failure modes the phases
don't already state (see `skills/README.md` submission checklist).
Rule citations inside skills are extension-neutral ("the `beads-quality`
rule", never `.mdc`/`.md`) because one skill file distributes to both
Cursor and Claude Code targets.
