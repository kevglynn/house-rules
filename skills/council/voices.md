# Council Voice Archetypes

Model assignments are described as **archetypes**, not concrete slugs — model
rosters change too fast to hardcode. Resolve each archetype against the models
currently available to the Task tool, or against the consuming repo's
`.agents/overlay.md` `## council` roster if one exists (see SKILL.md).

## Standard Council (default 3)

| Voice | Model archetype | Lens |
|-------|-----------------|------|
| **Advocate** | Strongest available reasoning model | Steelmans the approach. What's strong here? What's working? How can we extend it? |
| **Skeptic** | A capable model from a different family than the Advocate's | Stress-tests everything. What breaks? What's the hidden cost? What are we not seeing? |
| **Simplifier** | A concise model from a third family where available | Minimalism. Is this necessary? What can be removed? What's the shortest path? |

## Extended Voices

Add these when the task warrants more perspectives:

| Voice | Model archetype | Lens |
|-------|-----------------|------|
| **Architect** | Strong long-context reasoning model | Structural thinking. How does this fit the system? What are the boundaries? What's the coupling? |
| **Operator** | Code/implementation-oriented model | Production reality. How does this deploy? What breaks at 3am? What's the runbook? |
| **User** | Model with strong conversational/empathetic framing | End-user perspective. Is this intuitive? What's confusing? What would a non-technical person expect? |
| **Historian** | Balanced mid-tier reasoning model | Pattern recognition. Where have we seen this before? What worked? What didn't? What's the precedent? |
| **Contrarian** | Same archetype as the Skeptic, different instance | Deliberately opposes consensus. If everyone agrees, why? What's the case for the opposite? |
| **Pragmatist** | Fast, cheap model | Ship it. What's the 80/20? What gets us unblocked fastest? What's "good enough"? |
| **Security** | Model strong at structured, adversarial analysis | Threat modeling. What can be exploited? What's the blast radius? What's the trust boundary? |

## Resolving Archetypes to Models

Principles, in priority order:

1. **User overrides win.** If the user names a model for a voice, use it.
2. **Overlay roster next.** A `## council` section in the consuming repo's
   `.agents/overlay.md` maps voices to concrete slugs.
3. **Diversity over strength.** Two voices on different mid-tier models
   usually beat two voices on the same top-tier model — the value of a
   council is different models seeing the same problem differently.
4. **Match the lens.** Adversarial lenses (Skeptic, Contrarian, Security)
   benefit from models observed to be good at edge-case hunting;
   synthesis-heavy lenses (Simplifier, Historian) from models that stay
   concise; operational lenses (Operator, Pragmatist) from code-oriented or
   fast models.
5. **Never invent a slug.** Pick only from models the Task tool actually
   offers in the current environment.

## Custom Voices

Users can define ad-hoc voices inline. Any persona description works:

- "A voice that thinks like a CFO evaluating ROI"
- "A junior developer encountering this codebase for the first time"
- "A regulator checking for compliance issues"

For custom voices without explicit model assignment, the parent agent picks
a model whose observed strengths align with the voice's analytical lens.
