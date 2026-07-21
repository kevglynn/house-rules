# Multi-Agent Review Split — Obligations Checklist

**Date:** 2026-07-21
**Bead:** process-kit-k5m (Wave 2, finding F2 of
`docs/refinements/2026-07-19-kit-wide-mechanism-placement.md`)
**Method:** the pragmatic-tdd pilot's content-neutrality proof
(`docs/refinements/2026-07-19-pragmatic-tdd-topology.md` §7), applied to
`cursor/rules/multi-agent-review.mdc`.

Every obligation/prescription in the pre-split rule (161 lines, state at
commit `50bf6bb`), mapped to its destination. **Rule** = the thinned
always-on `multi-agent-review.mdc`; **Skill-T1** = `skills/tier1-review/`
(SKILL.md unless noted); **Skill-T2** = `skills/tier2-handoff/SKILL.md`;
**lenses.md** = `skills/tier1-review/lenses.md`. The "Exists?" column
records whether the destination artifact already carried the content before
this split (it did in every case — the skills were built post-pilot and are
supersets of the rule's procedure).

ID namespace: **M1–M29**, document-local. The pilot's shared-ID pattern
(O1–O17 appearing identically in rule, skill, and lens) is *not* replicated
here because the destination skills predate this split and renumbering
their content is out of scope (placement only, no substance changes).

| # | Pre-split obligation (rule text) | Destination | Exists? |
|---|---|---|---|
| M1 | Framing: structural changes need multiple independent perspectives; a single reviewer has blind spots; two-tier protocol | **Rule** (kept) | — |
| M2 | Required-when triggers: component decomposed; shared component created/significantly changed; structural refactor touches 3+ production files (excl. tests/docs/generated/mechanical renames); change affects accessibility, state management, or CSS architecture | **Rule** (kept verbatim) | — |
| M3 | Not-required exemptions: narrow bug fixes; config/chore/docs beads; token substitutions / mechanical migrations; test-only or docs-only changes | **Rule** (kept, condensed to one line) | — |
| M4 | Lifecycle sequencing: implement → self-review vs ACs (bead-completion.mdc) → Tier 1 → fix+commit → Tier 2 → fix+commit → close with evidence | **Rule** (kept, condensed) | — |
| M5 | Tier 1 supplements the self-review, never replaces it | **Rule** (kept) | — |
| M6 | "Three independent review passes" — the lens **count** | **Superseded** — roster ownership moves to **Skill-T1** (Phase 2: four lenses, test-signal conditional). The count is deliberately absent from the rule; the rule now says "dispatch the full lens roster the skill defines." This is the F2 drift fix — the count was already wrong (3 vs the approved 4). | ✓ |
| M7 | Lens table: code-reviewer / architect-reviewer / simplify, focus + catches columns | **Skill-T1** (Phase 2 table — superset, adds test-signal) | ✓ |
| M8 | Launch concurrently when parallel subagents are supported; otherwise sequentially | **Skill-T1** (Phase 2 dispatch + fallback) | ✓ |
| M9 | Each pass runs with independent context; no pass sees another's findings until triage | **Rule** (one line) + **Skill-T1** (Phase 2 + "Shared-context dispatch" anti-pattern) | ✓ |
| M10 | Per-tool launch mechanics (Cursor: Task tool, one subagent per lens, single message; Claude Code: separate invocations; fallback: sequential with findings written to a file before the next pass to prevent anchoring) | **Skill-T1** (Phase 2 — tool-neutral generalization: "launch the subagents in a single message"; fallback with scratch file is verbatim-equivalent) | ✓ |
| M11 | Context for each pass — five mandatory elements: bead description+ACs; full file contents; bead type; shared components depended on; brief change summary | **Skill-T1** (Phase 1 five-element context package — superset, adds sourcing instructions) | ✓ |
| M12 | Simplify output Section 1: tagged-findings format `<file>:L<line>: <tag> ...`; the five tags (`delete:` `stdlib:` `native:` `yagni:` `shrink:`); `net: -<N> lines possible.`; `Lean already. Ship.` | **lenses.md** (simplify template) — designated the **canonical home of the simplify-tag vocabulary** by this split | ✓ |
| M13 | Simplify output Section 2: free-form structural observations; often highest-value; must not be suppressed by the tag format | **lenses.md** (simplify template) + **Skill-T1** ("Simplify-lens suppression" anti-pattern) | ✓ |
| M14 | Simplify scope boundary: over-engineering only; correctness/security/performance routed to the other lenses | **lenses.md** (simplify template, "Out of scope" block) | ✓ |
| M15 | After collecting results: categorize findings Critical / Important / Minor | **Skill-T1** (Phase 3 — superset: severities plus per-finding dispositions) | ✓ |
| M16 | Fix Critical and Important findings immediately | **Rule** (one line) + **Skill-T1** (Phase 4.1) | ✓ |
| M17 | Create beads for Minor/deferred findings per beads-quality.mdc | **Rule** (tracking clause, M29) + **Skill-T1** (Phase 4.4 + "Deferral IOUs" anti-pattern) | ✓ |
| M18 | Commit review fixes as a separate commit, not amended into the original | **Rule** (one line) + **Skill-T1** (Phase 4.2 + anti-pattern) | ✓ |
| M19 | Tier 2 rationale: different models have different architectures/training/failure modes; same-model review misses model-specific blind spots | **Rule** (kept as the section's framing line) + **Skill-T1** (Phase 2 "cross-model diversity is Tier 2's job") | ✓ |
| M20 | Tier 2 strongly recommended for all structural changes; if deferred under time pressure, create a tracking bead before merge | **Rule** (kept) + **Skill-T2** (When to Use) | ✓ |
| M21 | Tier 2 **required** (not deferrable) for: shared primitives; app shell/navigation; auth/authorization/security boundaries; state-management architecture | **Rule** (kept verbatim) + **Skill-T2** (When to Use) | ✓ |
| M22 | Prerequisite: work committed and pushed before Tier 2 handoff (cross-worktree visibility, reproducible snapshot) | **Rule** (one-line obligation) + **Skill-T2** (Prerequisite + "Assembling against an uncommitted tree" anti-pattern) | ✓ |
| M23 | Agent provides a ready-to-paste prompt with: change summary; file list; review focus areas; what Tier 1 already caught | **Skill-T2** (Phases 1–3 + spec schema: `context`/`focus`/`files`/`already_addressed` — superset) | ✓ |
| M24 | The inline Tier 2 prompt template (fenced markdown skeleton) | **Superseded** — **Skill-T2**'s `assemble.py` fixed skeleton is canonical and carries all four M23 elements plus more (trusted layers, rules, report format). The rule's inline copy had already structurally diverged from the skeleton (F2); retiring it removes the competing source of truth. Content-neutral because every element of the inline template maps into the skeleton. | ✓ |
| M25 | Human sends the prompt to 2–3 different models, collects findings; agent triages with the same Critical/Important/Minor framework | **Skill-T2** (deliberate human paste step; Phase 4 triage — accept/reject dispositions with C/I severity on accepted findings; default model set Grok/Gemini/GPT) | ✓ |
| M26 | When models disagree: start from the more conservative finding; document the disagreement; conflicting findings never cancel out | **Rule** (kept as its own section — applies to both tiers) + **Skill-T1** (Phase 3) + **Skill-T2** (Phase 4.2) | ✓ |
| M27 | Close evidence: `bd close --reason` notes whether Tier 1 ran + finding categories addressed; whether Tier 2 was completed / deferred (with tracking bead ID) / not required; additive to bead-completion.mdc evidence | **Rule** (kept) + both skills' Phase 5 close-evidence lines | ✓ |
| M28 | Knowledge capture: pattern-level insights (hidden coupling, undocumented convention, recurring anti-pattern) → `bd remember --key <area>-<topic>` after resolution | **Rule** (kept, one line) + **Skill-T1** (Phase 5.2) + **Skill-T2** (Phase 4.7) | ✓ |
| M29 | Tracking: all deferred findings from both tiers become beads with descriptions and ACs per beads-quality.mdc | **Rule** (kept) + both skills (Phase 4.4 / Phase 4.5) | ✓ |

## Dropped content — with rationale

Only two items do not survive as text, and both are deliberate F2 fixes,
not lost obligations:

1. **The lens count "three" (M6).** Dropped from the rule because it was
   the observed drift: the approved roster has four lenses (test-signal,
   conditional). The obligation "run the full multi-lens roster" survives
   in the rule; the roster itself is owned solely by the skill.
2. **The inline Tier 2 template body (M24).** Retired as a divergent
   duplicate of `assemble.py`'s fixed skeleton. Every element it carried
   (change summary, files, focus areas, already-addressed, the
   "accept or reject each finding with a reason" instruction) exists in
   the skill's skeleton and Phase 4 triage protocol.

## Related dedup executed with this split (F3 slice)

The simplify-tag vocabulary previously lived in three artifacts. After this
split: `skills/tier1-review/lenses.md` is the single canonical home;
`cursor/rules/multi-agent-review.mdc` no longer carries the tags at all
(the rule points at the skill, which points at lenses.md);
`skills/ponytail-review/SKILL.md` names the five tags and points at
lenses.md for their definitions (its worked examples remain — they
demonstrate usage, they don't define the vocabulary).

## Flagged for the coordinator (not changed — substance, not placement)

- **Trigger-wording divergence between rule and skill.** The rule's
  required-when list (M2) names "accessibility, state management, or CSS
  architecture"; `tier1-review` SKILL.md's "When to Use" restates the
  triggers with a different fourth bullet ("load-bearing boundary the
  project treats as high-risk: state management, auth, data integrity,
  public API surface"). These are different substantive trigger sets.
  Reconciling them is a policy decision, out of scope for a
  placement-only split. The thinned rule keeps the original rule wording
  unchanged.
