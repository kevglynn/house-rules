---
name: council
description: >-
  Convene a council of diverse AI voices to analyze a task from multiple
  perspectives using different models. Each voice operates as a full-capability
  generalPurpose subagent (reads, shell, MCPs) with its own analytical lens.
  Synthesizes perspectives rather than ranking them. Use when the user says
  "convene a council", "council on this", "get perspectives", "multi-voice",
  "diverse review", or wants adversarial/collaborative analysis from multiple
  models.
---

# Council

Convene parallel subagents — each a distinct analytical voice running on a
different model — to examine a shared task. Synthesize their perspectives
into a unified briefing.

## Input Contract

The user provides:
1. **Task/artifact** — what to analyze (a file, a plan, a question, a PR, etc.)
2. **Voices** (optional) — which perspectives to include. Defaults to the Standard Council (see below).
3. **Models** (optional) — which model to assign each voice. Defaults per voice archetype.

Invocation examples:
- "Convene a council on this PR"
- "Council: should we use Redis or Postgres for this queue?"
- "Get perspectives on the migration plan from skeptic, advocate, and simplifier using opus, gemini, gpt"

## Parsing

If the user specifies voices and/or models explicitly, use those.
Otherwise, use the **Standard Council** (3 voices):

| Voice | Default Model | Role |
|-------|---------------|------|
| Advocate | `claude-opus-4-7-thinking-xhigh` | Steelmans the approach. Finds strengths, identifies what's working, extends the idea. |
| Skeptic | `gemini-3.1-pro` | Stress-tests assumptions. Finds failure modes, edge cases, hidden costs. |
| Simplifier | `gpt-5.5-medium` | Asks "is this necessary?" Finds complexity that can be removed. Proposes the minimal path. |

For expanded councils (user requests more voices), draw from the
[Extended Voices](voices.md) reference.

## Workflow

### 1. Parse the request

Extract:
- The **task** (what they want perspectives on)
- Any **voice overrides** (names or descriptions)
- Any **model overrides** (mapped positionally to voices)
- Any **context** the voices need (files to read, URLs to check, MCPs to query)

### 2. Launch voices in parallel

For each voice, launch a `generalPurpose` Task subagent with:
- `model`: the assigned model slug
- `run_in_background`: true
- `subagent_type`: "generalPurpose"
- Full tool access (NOT readonly) — voices can read code, run commands, call MCPs

**Subagent prompt template:**

```
You are the {VOICE_NAME} on a council of advisors.

Your role: {VOICE_ROLE_DESCRIPTION}

Your analytical lens:
{VOICE_LENS}

## Task
{TASK_DESCRIPTION}

## Context
{ANY_RELEVANT_CONTEXT}

## Instructions
- Analyze the task through your specific lens
- Use available tools to gather evidence (read files, run commands, query MCPs)
- Be thorough — investigate, don't just opine
- Structure your response as:
  1. **Position**: Your core take (2-3 sentences)
  2. **Evidence**: What you found that supports your position
  3. **Risks/Concerns**: What worries you from your perspective
  4. **Recommendations**: Concrete suggestions

Do NOT try to be balanced or cover all angles — that's what the other
council members are for. Lean into your perspective fully.
```

### 3. Synthesize

After all voices complete, the parent agent produces a **Council Briefing**:

```
## Council Briefing: {TASK_SUMMARY}

### Consensus
[Points where all voices agree]

### Tensions
[Points of genuine disagreement, with each voice's position]

### Surprises
[Unexpected findings — things a single-voice analysis would miss]

### Recommendations
[Synthesized path forward that accounts for all perspectives]
```

## Key Constraints

- **No ranking.** Voices are not competing. The synthesis honors all perspectives.
- **Full tool access.** Each voice runs as `generalPurpose` (not `explore`, not `readonly`). They can read files, run shell commands, call MCPs.
- **Namespaced scratch.** If a voice needs to write a temporary file, it uses `.council/{voice-name}/` relative to the workspace root.
- **Parallel launch.** All voices launch in a single message (multiple Task calls). Do not serialize them.
- **Model diversity matters.** The value comes from different models seeing the same problem differently. Avoid assigning the same model to multiple voices unless the user explicitly requests it.

## Extended Usage

For the full list of available voice archetypes and their model affinities,
see [voices.md](voices.md).

For custom voice definitions, the user can describe any persona inline:
- "Add a voice that thinks like a database administrator"
- "Include a security-focused voice on kimi"
