---
name: prose-voice
description: >-
  Voice discipline for human-facing prose — pattern catalog, self-correction
  protocol, and worked examples for killing AI-sounding rhetorical tics.
  Load when writing positioning docs, pre-whitepapers, packets, deck copy,
  primers, emails, briefs, or any prose a human will read or forward.
  Trigger phrases: "prose voice", "writing voice", "check the voice",
  "before I send this", "make it not sound like AI", "voice sweep".
---

# Prose Voice

AI-generated prose converges on a handful of rhetorical moves and uses them
dozens of times per document. Each one is fine once. The twelfth instance
makes the reader's skin crawl. The cumulative effect is a document that
announces "a language model wrote this" on every page.

This skill is the pattern catalog and self-correction protocol. The
always-on `prose-voice` rule is the tripwire that tells you to read this.

## When to Use This Skill

- Writing or editing any prose a human will read or send: positioning docs,
  pre-whitepapers, packets, deck copy, primers, emails, briefs, README
  narratives, design doc prose sections
- Any artifact described as "for Chris," "for Manas," or "ready to send"
- When the user says "voice sweep," "make it not sound like AI," or
  "check the voice"

**Skip when:** writing code comments, commit messages, bead descriptions,
agent-to-agent notes, or scratchpad entries. Those are functional, not
voice-sensitive.

## Banned Patterns

These are banned *habits*, not banned words. Any of them used once in a
2,000-word document is unremarkable. The same move appearing 3+ times is
the failure mode.

### P1 — Contrastive pivot overuse

The "not X — Y" and "X. But Y." two-beat structure where the first half
sets up a straw man and the second half delivers the real point.

Examples:
- "This is not a logging system. It is a proof system."
- "The question isn't whether X — it's whether Y."
- "Others do A. We do B."
- "X is a tool feature. Y is a property of the record."

**Budget: 1 per 1,000 words.** Two is pushing it. Three or more and the
document reads like a TED talk transcript. Rewrite the surplus as direct
statements — say what the thing IS without the theatrical wind-up of what
it ISN'T.

Before:
> This is not an observability trace. It is a durable proof that the
> decision happened the way the record says it did.

After:
> The assembly is a durable record of the decision: what context was
> provided, how it was scored, and what the agent saw. Observability traces
> capture what happened at runtime; the assembly captures what informed the
> outcome.

### P2 — Mic-drop closers

Final sentences or paragraphs designed to land with dramatic weight.

Examples:
- "And that changes everything."
- "No competitor currently claims this."
- "That's the difference."
- "This is stronger than what any competitor claims, and the honest edges
  make the claim credible rather than aspirational."
- One-sentence paragraphs that exist solely for emphasis.

**Budget: 1 per document, max.** The content should carry its own weight.
If the point is strong, it doesn't need a punchline. End sections with
substance, not applause lines.

Before:
> No competitor currently claims to meet all five criteria. The honest
> edges below keep us from overclaiming the same way.

After:
> No competitor currently claims to meet all five. Here's where we stand
> on each, including the gaps.

### P3 — Triplet escalation

Three parallel items presented in escalating importance, especially when
the third item is positioned as the "real" one.

Examples:
- "Re-viewing, re-running, reproducing — only the third survives contact
  with an auditor, a regulator, a court."
- "Invaluable for X. Essential for Y. Required for Z."

**Budget: use when the taxonomy is genuinely three things.** Don't force
content into triplets for rhetorical rhythm. If two of the three are just
setup for the third, say the third directly.

### P4 — Gravitas inflation

Words and constructions that signal "this is important" instead of letting
the reader decide.

Watch list: `unambiguous`, `genuinely`, `fundamentally`, `precisely`,
`critical(ly)`, `the reality is`, `the honest answer is`, `make no
mistake`, `let's be clear`, `full stop`, `the hard truth`, `it bears
repeating`, `cannot be overstated`, `X is real` (as emphasis, not
existence claim).

**Rule: state the fact.** If it's important, the reader will notice.
Bolding a claim doesn't make it true; hedging it with "genuinely" doesn't
make it credible.

Before:
> Let's be clear: signing is genuinely new scope, and claiming otherwise
> would fundamentally misrepresent the current state.

After:
> Signing is not built. Content addressing proves the record hasn't
> changed if you trust the fingerprint computation. Cryptographic signing
> proves who produced it, which is separate work.

### P5 — Parallel sentence openers

Starting 3+ consecutive sentences or bullet points with the same syntactic
structure.

Examples:
- "The record proves X. The record captures Y. The record survives Z."
- "Content addressing ships X. Content addressing enables Y."

**Rule: vary the entry point after 2.** Restructure some as dependent
clauses, combine others, or start differently.

### P6 — Complement/complement framing

"These are complements, not competitors" and its siblings: "These are X,
not Y." Used once, it's a clean distinction. Repeated, it becomes a tic.

Before:
> These are complements, not competitors. An execution record without
> provenance shows a file was deleted but not what reasoning produced
> the deletion.

After:
> All three layers are needed for a complete picture. An execution record
> tells you a file was deleted; decision provenance tells you what
> reasoning produced that deletion.

## Self-Correction Protocol

Before finalizing any human-facing prose, run this mechanical scan — not
a vibes check:

1. **Count contrastive pivots** (P1). More than 1 per 1,000 words →
   rewrite the surplus as direct statements.
2. **Count mic-drop closers** (P2). More than 1 in the document →
   cut or fold the point into the preceding paragraph.
3. **Count rhetorical triplets** (P3). More than 1 per 2,000 words →
   collapse to pairs or direct claims.
4. **Scan for gravitas words** (P4). Three or more in a single paragraph →
   the paragraph is trying too hard. Restate plainly.
5. **Check for parallel openers** (P5). Three or more consecutive →
   restructure.
6. **Count complement framings** (P6). More than 1 in the document →
   rewrite the extras.
7. **Word-count the draft against its channel ceiling** (P8). Over the
   ceiling → cut whole items and hold them in reserve for a follow-up.
   Do not get there by trimming the surviving sentences into fragments.
8. **Scan punctuation against the user's fingerprint** (P9). Any em dash
   in prose drafted in the user's voice → replace it (comma, colon,
   parentheses, or sentence split). Ellipses stay in casual registers
   and out of formal ones.

If you catch the pattern mid-draft, fix it inline and keep going. The
reader never sees the first draft.

## What Good Looks Like

- **Varied sentence structure.** Long sentences with subordinate clauses
  next to short declarative ones. Paragraphs that don't all start the
  same way.
- **Direct claims.** "The assembly records every input" rather than
  "This is not a summary — it is a complete record of every input."
- **Substance at section ends.** The last sentence of a section should
  contain information, not a flourish.
- **Earned emphasis.** Bold or italics for terms of art or surprising
  claims, not for rhetorical volume.
- **Honest uncertainty stated flatly.** "Signing is not built" rather
  than "Let's be honest: signing is new scope, and claiming otherwise
  would be..."

## Scope Boundaries

- This skill governs **voice and rhetorical pattern**, not content
  accuracy. Content claims are governed by the claims verifier and the
  competitive-provenance-reality memory.
- Strong claims are fine — theatrical delivery is not. Say the strong
  thing directly.
- Metaphors and analogies are fine when they clarify. They're not fine
  when they exist to sound clever.
- The user may override any part of this skill for a specific document.

## P7 — Evaluative authority framing (messages and emails)

When drafting messages on behalf of the user to peers, co-founders, or
anyone who is not a direct report, do not position the user as the
authority grading the recipient's work.

**Banned forms:**

- "The instinct is right" / "the instinct is correct"
- "This is the right list" / "are the right categories"
- "Good work on X" / "nice job with Y" (manager-to-report register)
- "You're on the right track" / "you're heading in the right direction"
- Any construction where the user implicitly sits above the recipient
  and evaluates their output as passing or failing

**Use instead:**

- "I like this" / "I like the direction"
- "This tracks" / "this makes sense" / "this feels right"
- "Works for me" / "I'm into it"
- Agreement and enthusiasm expressed as personal reaction, not judgment
  from a position of authority

The test: if you swap the names (recipient says it to the user), does
it sound condescending? If yes, rewrite.

## P8 — Length inflation

Every pattern above governs how a sentence is shaped. This one governs
whether it should exist. A draft can clear all seven checks — varied
openers, one pivot, no mic-drop, peer register — and still run twice the
length its channel deserves, which is how prose nobody finishes gets
written.

**Channel ceilings.**

| Channel | Ceiling | Shape |
|---|---|---|
| Chat, Slack, text | 150 words, aim under 100 | One ask or one answer. If the reader has to scroll, it wanted to be a doc with a link to it. |
| Email | 250 words | Lead with the ask. Detail past that belongs in an attachment or a linked doc, not in the body. |
| Document, packet, spec | None | Ungated on total length, but every section still faces the cut test. Thorough is the job; self-indulgent is not. |

Comprehensive material does sometimes have to travel by message. That is
the exception and should be announced as one ("long one — summary up
top"), never the default.

**The cut test.** For each sentence, ask whether the reader would do
anything differently if they never saw it. If not, cut it. Classes that
reliably fail:

- Restating what the recipient already knows — their own words, their own
  plan, a decision they made
- Narrating your own process ("two things came out of writing this,"
  "having reviewed the docs")
- Pre-answering objections nobody raised
- Supplying the evidence chain for a claim the reader can check in one
  click
- A second example that makes the same point as the first
- Runway in front of a request — the request survives, the approach does
  not

**Hold the rest in reserve.** Depth is held, not deleted. Send the
version that lands, keep the supporting detail ready, and let the reader
pull it. A message that provokes "tell me more about the second one" did
its job; a message that answers that question pre-emptively never got
read that far.

**Do not compress the survivors.** Economy means fewer sentences, not
shorter ones. Fragments, arrow chains (`A → B → fails`), dropped
articles, and invented abbreviations all make prose harder to absorb,
which is the thing this pattern exists to prevent. Cut whole items and
write the remaining ones as full sentences.

Before (~95 words):
> On the mockup item — that's already in the plan, Week 2 is the design
> review with the customer, so nothing new is needed there. One thing
> worth flagging before you take it in front of him: the deck's
> trust-scores panel needs to come out, because we ratified no numeric
> score anywhere, on his own objection that a 90 and a 70 don't mean
> anything different to him, and tiers now express as evidence with the
> promotion history behind them instead of as a number.

After (~40 words):
> The mockup item is already Week 2. One heads-up before the deck goes in
> front of him: the trust-scores panel has to come out. No numeric score
> anywhere, his own objection ("what's the difference between a 90 and a
> 70").

Both carry the same ask. What went: a restatement of the schedule the
recipient set himself, the reasoning behind a decision he was party to,
and "nothing new is needed there."

## P9 — Punctuation fingerprint

Punctuation is a voice signature the same way word choice is, and model
defaults are recognizable: em dashes chained through every paragraph are
the single most-cited AI tell. The law is generic. Match the user's own
fingerprint, never the model's default. The parameters below belong to
this kit's owner; drafting for a different principal means learning
theirs first, and if the kit ever grows more users these lines move to a
per-user overlay.

**Owner parameters:**

- **Em dashes: banned outright in prose drafted in the user's voice.**
  Replace each one with a comma, a colon, parentheses, or a sentence
  split, whichever the sentence wants. No budget, no exceptions; the
  reader knows the user doesn't write them.
- **The ellipsis is the user's native connector in ad hoc registers**
  (chat, texts, quick emails). Leave it alone in casual messages, and
  keep it out of formal register: documents, packets, specs, anything
  ready to forward.

Scope: this pattern governs prose drafted in the user's voice. The
catalog's own explanatory text and agent-to-agent output are exempt (the
skill-wide skip list already covers them), but the worked good-examples
above do follow the owner parameters.

## When Reviewing Other Agents' Work

Fix the patterns in the edit pass. Don't add comments explaining the fix.
The goal is prose that reads as if a thoughtful human wrote it, not prose
with "[AI pattern removed]" annotations.
