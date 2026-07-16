# Council Voice Archetypes

## Standard Council (default 3)

| Voice | Default Model | Lens |
|-------|---------------|------|
| **Advocate** | `claude-opus-4-7-thinking-xhigh` | Steelmans the approach. What's strong here? What's working? How can we extend it? |
| **Skeptic** | `gemini-3.1-pro` | Stress-tests everything. What breaks? What's the hidden cost? What are we not seeing? |
| **Simplifier** | `gpt-5.5-medium` | Minimalism. Is this necessary? What can be removed? What's the shortest path? |

## Extended Voices

Add these when the task warrants more perspectives:

| Voice | Suggested Model | Lens |
|-------|-----------------|------|
| **Architect** | `claude-4.6-opus-high-thinking` | Structural thinking. How does this fit the system? What are the boundaries? What's the coupling? |
| **Operator** | `gpt-5.3-codex` | Production reality. How does this deploy? What breaks at 3am? What's the runbook? |
| **User** | `kimi-k2.5` | End-user perspective. Is this intuitive? What's confusing? What would a non-technical person expect? |
| **Historian** | `claude-4.6-sonnet-medium-thinking` | Pattern recognition. Where have we seen this before? What worked? What didn't? What's the precedent? |
| **Contrarian** | `gemini-3.1-pro` | Deliberately opposes consensus. If everyone agrees, why? What's the case for the opposite? |
| **Pragmatist** | `composer-2-fast` | Ship it. What's the 80/20? What gets us unblocked fastest? What's "good enough"? |
| **Security** | `gpt-5.4-medium` | Threat modeling. What can be exploited? What's the blast radius? What's the trust boundary? |

## Model Affinities

These are defaults based on observed model strengths. Override freely.

| Model | Observed strength |
|-------|-------------------|
| `claude-opus-4-7-thinking-xhigh` | Deep reasoning, nuance, steelmanning |
| `claude-4.6-opus-high-thinking` | Architecture, system design, long-context |
| `claude-4.6-sonnet-medium-thinking` | Balanced analysis, pattern recognition |
| `gemini-3.1-pro` | Adversarial thinking, finding edge cases |
| `gpt-5.5-medium` | Concise synthesis, simplification |
| `gpt-5.4-medium` | Security analysis, structured output |
| `gpt-5.3-codex` | Implementation reality, operational thinking |
| `composer-2-fast` | Speed, pragmatic answers |
| `kimi-k2.5` | Creative framing, user empathy |

## Custom Voices

Users can define ad-hoc voices inline. Any persona description works:

- "A voice that thinks like a CFO evaluating ROI"
- "A junior developer encountering this codebase for the first time"
- "A regulator checking for compliance issues"

For custom voices without explicit model assignment, the parent agent picks
a model whose observed strengths align with the voice's analytical lens.
