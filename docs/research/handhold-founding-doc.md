# handhold

**Agentic software development with continuous human-model synchronization.**

> Working name. "handhold" is a placeholder taken from the original pitch ("handholds that allow the human practitioner to develop genuine familiarity with the system"). The project will be named before publication; candidates under consideration include backbrief, fieldguide, bearings, docent, and maproom. This draft lives in the house-rules repo until the sibling repo exists.

---

## Part one: the argument

### The gap agents create

Autonomous coding agents are steadily removing humans from the authorship of their own systems. An agent can disappear into a task, restructure seven modules, and return with passing tests, and the human who directed it now owns a system they understand less than they did an hour ago. Multiply that by months of agent-driven development and the practitioner becomes the nominal owner of software they can no longer meaningfully direct: they cannot reason about it, challenge its design, diagnose its failures, or judge whether the next agent's proposal is sound.

The two obvious responses both fail. Requiring the human to review every generated line defeats the purpose of employing agents at all; the economics of agentic development depend on the human not doing that. Accepting the decay instead produces a slower disaster: authority without understanding, an owner who can approve and reject but cannot evaluate.

There is a third option. As the agent increases the distance between the human and the implementation, the system can actively close the corresponding distance between the human and the *understanding* of that implementation. The goal is not to keep the human in the coding loop. It is to keep the human in the understanding and control loop.

### Comprehension debt

Technical debt names the gap between the code you have and the code you should have. Comprehension debt names the gap between the system as it exists and the system as its owner understands it.

The debt accrues in proportion to work performed autonomously beyond the human's observation. Ten lines the human watched an agent modify accrue almost nothing. Forty minutes of unattended restructuring across module boundaries accrues a lot. Like technical debt, it is invisible during normal operation and comes due at the worst moment: an incident the owner cannot diagnose, a security review they cannot conduct, an architectural decision they can no longer make from knowledge instead of trust.

Once the gap has a name and a rough measure, it can drive behavior. The more comprehension debt an agent's work creates, the greater the system's obligation to restore understanding before that work is considered finished.

### What "done" means

Under this model, an agent is not finished when the code is correct. Part of "done" is updating the representation through which the human understands the system. The development process produces two synchronized outputs: the machine implementation, and the human's mental model of it. Every change lands in both or the change is incomplete.

### Why "better documentation" is the wrong frame

Documentation optimizes an artifact: complete, accurate, organized for a generic reader who could be anyone. This system optimizes a person: the fluency of one specific practitioner, relative to what they already know.

The difference is visible in the output. Generic documentation says "the billing service validates entitlements before invoice generation." A fluency-oriented system says "you already understand the billing service and the entitlements store as independent components. This change introduces a synchronous call between them, which breaks the assumption that billing can run when entitlements is down, and creates a new failure mode you have not seen before." The second form requires knowing what the reader knows. That requirement is what makes this a system rather than a writing habit, and it is where the mechanism begins.

---

## Part two: the mechanism

Four components, forming a control loop.

### 1. The practitioner comprehension state

A persistent, per-practitioner model of what the human currently understands about the system. Concretely, it tracks:

- which subsystems and concepts the practitioner has been taught, and at what depth
- the terminology and architectural vocabulary they have already absorbed
- when they last interacted with each area, and through what medium (authored it, reviewed it, was briefed on it, never saw it)
- which parts of their model are stale: areas that have changed since their last contact

This is the load-bearing component. Every downstream behavior (what to explain, how deeply, in what vocabulary) reads from it. Nothing else in the system is novel without it; with it, explanation becomes a function of two arguments, the change and the reader, instead of one.

### 2. Divergence measurement

The signal that turns the state model into a control loop. The system continuously estimates comprehension debt per subsystem from observable inputs:

- volume and structural scope of changes made outside the practitioner's observation
- whether changes altered architecture, dependencies, or invariants, versus local edits within an existing structure
- time and change-count since the practitioner last had contact with the area
- the practitioner's demonstrated fluency, where interactions provide evidence of it

Debt is not uniform, and neither is the required response. The measurement should answer a practical question: which classes of action is the practitioner currently equipped to take on this subsystem, and which have they silently lost? Being able to *extend* the billing subsystem requires more current understanding than being able to *operate* it; a security review requires understanding neither implies. Thresholds attach to action classes rather than to an abstract freshness score.

### 3. Comprehension-relevant change detection

Most diffs do not matter to the human's model. A renamed variable changes nothing the owner needs to know; a new synchronous dependency between two previously independent services changes a lot. The detector classifies agent-produced changes by what they alter in the conceptual layer:

- **Concepts**: new components, entities, or responsibilities
- **Architecture**: boundaries, layering, communication patterns
- **Dependencies and data flow**: who calls whom, what data moves where
- **Invariants and assumptions**: what must remain true, what stopped being true
- **Behavior**: observable outcomes, edge cases, failure modes
- **Operational characteristics**: scaling behavior, cost, security surface, recovery paths
- **Rationale**: decisions made, alternatives rejected, constraints honored

The delta that matters is measured against the practitioner's model rather than the previous commit. If the human never knew two services were independent, their new coupling is not a delta for that person; if the human's whole operational picture rested on that independence, it is the single most important fact of the week.

### 4. Intervention generation and selection

When debt on some subsystem crosses the threshold for an action class the practitioner needs, the system generates and presents artifacts that restore understanding. The artifacts answer a fixed hierarchy of questions:

1. **What exists?** Components, modules, services, data stores.
2. **How does it work?** Control flow, data flow, state transitions, dependencies.
3. **Why is it this way?** Constraints, rejected alternatives, agent rationale.
4. **What changed?** The semantic delta from the practitioner's previous model.
5. **What must remain true?** Invariants and standing assumptions.
6. **Where can it break?** Failure modes and operational boundaries.
7. **How do I change it?** Extension points and safe modification patterns.
8. **How do I control it?** The levers available to the practitioner.

The last question sets the register for all of them. These artifacts are not a textbook about the software; they are a control surface for its owner. Forms vary with the debt: a two-paragraph change brief for a small delta, an architectural map with a guided walkthrough after a large restructure, an invariant register when assumptions moved.

Maps in this system are navigational rather than static. Because the system holds both the implementation and the conceptual layer, the practitioner can traverse between them in either direction: "show me where authentication happens," "what would need to change to support organizations," "show me everything downstream of this schema," "teach me enough about the billing subsystem to confidently modify it." The system constructs the conceptual path by walking the actual code.

### The loop, end to end

An agent performs work. The detector classifies the semantic deltas. Divergence measurement updates comprehension debt per subsystem, weighted by how much of the work the practitioner observed. Where debt crosses an action-class threshold, the system selects interventions, rendered relative to the practitioner's current state. The practitioner engages; the comprehension state updates; debt falls. The obligation scales with the distance: small observed changes produce silence, large unobserved ones produce maps, rationale, changed invariants, and a walkthrough.

---

## What this is not

- **Generated documentation.** Documentation is a stateless artifact for a generic reader. This system is stateful and personal; the same change produces different output for different practitioners, and no output at all for one who watched it happen.
- **Human-in-the-loop code review.** The system does not ask the human to approve implementations line by line. It assumes autonomous execution and concentrates the human's attention where their model has diverged.
- **A codebase tutor.** Tools that explain arbitrary code on request answer question two of the hierarchy, on demand, with no memory of the asker. The mechanism here is the persistent state, the debt signal, and the obligation placed on the development process itself.

## First substrate: house-rules

The mechanism is substrate-agnostic: any development system in which agents emit structured semantic evidence about their work can host it. house-rules happens to be an unusually good first substrate, because its governance already forces agents to produce most of the raw inputs:

- Bead close reasons carry AC-mapped evidence of what changed and why: semantic deltas, already structured, already mandatory.
- Design docs and decision records capture rationale and rejected alternatives at authoring time.
- Session lifecycle hooks and bead-close events are natural interception points for the detector and for debt accrual.
- The kit's memory layer (`bd remember`) already captures knowledge for future *agents*; this project is its mirror image, capturing and maintaining knowledge for the *human*, keyed to the human's state rather than the project's.

What house-rules lacks, and what this project adds, is exactly the inventive core: the practitioner comprehension state, the divergence measurement, and personalized rendering.

## Open questions

- **Representation.** What granularity does the comprehension state need? Per-subsystem freshness is cheap and coarse; per-concept modeling is expressive and hard to maintain honestly.
- **Verification versus inference.** Does the system infer understanding from exposure (the practitioner read the brief, so they know it) or verify it (the practitioner can answer the backbrief question)? Inference is frictionless and self-deceiving; verification is honest and can become homework. The right mix is probably per action class: inference for operating, verification before extending or securing.
- **Calibration.** Thresholds that fire too eagerly turn the system into a nag the practitioner learns to dismiss, which silently recreates the original decay. Debt tuning is a product problem as much as a technical one.
- **Success measurement.** The claim is that the practitioner stays able to direct, diagnose, extend, secure, and scale. Those are testable abilities. A serious version of this project defines fluency probes and measures itself against them.
- **Dignity.** A persistent model of what a specific person does and does not understand is sensitive data. It must belong to the practitioner rather than their employer or tooling vendor.

---

*Draft founding document, 2026-08-06. Tracked as process-kit-dgh in the house-rules repo; relocates when the sibling project is stood up.*
