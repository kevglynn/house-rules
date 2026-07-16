# Welcome — From Returning Coder to Agent-Native Builder

You used to ship code. You've been away. You don't have time to relearn everything from scratch — you want a sensei that accelerates the rate of learning by orders of magnitude.

That's what this is. **This doc is the intake. Your agent is the sensei.** The repo's rules and skills have already taught the agent how to teach you. Your job is to show up and follow the order.

## Two ground rules for the rest of this onboarding

1. **Claim novice status, out loud.** You haven't coded in years. Don't pretend otherwise — it slows everything down. Say *"explain like I haven't coded in 5 years"* without shame. The rules in this repo have already told your agent to expect exactly this and to meet you there. Asking basic questions does not cost you respect; pretending you remember does.

2. **Trust the order.** The steps below are sequenced for a reason. **Step 3 (the sandbox) is the inflection point** — where everything before it clicks into place. Don't skip it. Don't tell yourself you'll come back to it. You won't, and the rest of the onboarding will land at half-strength.

After your first guided session, you'll see the loop. After a handful of working sessions, it'll feel natural. Promise.

---

## Step 1 — Get the tools (one-time setup)

You need three things on your machine:

1. **A coding agent IDE.** Pick one to start:
   - **[Cursor](https://cursor.com)** — desktop app for Mac/Windows/Linux. Easiest if you want to see the agent edit files in real time. **Start here if you're unsure.**
   - **[Claude Code](https://docs.anthropic.com/en/docs/claude-code)** — terminal-based agent. Great if you live in the CLI.
   - You can have both later. They share this playbook's rules.

2. **`git`, `node`/`npm` (optional), and `brew`.** If you have an old developer Mac, you probably already have these. If `brew` is missing, install it from [brew.sh](https://brew.sh). Your agent can debug install errors — just paste them in chat.

3. **`bd` (beads)** — the task tracking tool agents use here:
   ```bash
   brew install beads
   ```

Then clone this playbook and run the per-machine setup:

```bash
git clone https://github.com/kevglynn/process-kit ~/process-kit
bash ~/process-kit/scripts/install-global-safety-net.sh
bash ~/process-kit/scripts/install-aliases.sh
```

Both installers are safe for agents to run on your behalf. **If anything fails, that's your first agent-as-sensei exercise.** Paste the error into a chat with your agent and ask: *"Walk me through fixing this. Explain as you go — I'm rusty."* Don't debug it yourself. The whole point is to feel what it's like to have the agent do the work while you learn.

---

## Step 2 — Open the playbook in your IDE and ask the agent to acclimate you

Open the `~/process-kit` folder in Cursor (or `cd ~/process-kit && claude` for Claude Code), start a new chat, and paste this prompt:

> I'm new to this playbook and to agent-native development. I used to be a proficient coder but I've been away for years.
>
> Please:
> 1. Read `README.md`, `QUICKSTART.md`, `docs/concepts.md`, and the rule files in `cursor/rules/` (or `claude/rules/`).
> 2. Give me a guided tour: what is this repo for, what loop will I be working in day-to-day, and what are the 5–6 concepts I need to internalize?
> 3. At the end, quiz me with 3 plain-English questions so I can check my understanding.
> 4. Suggest the best next prompt I should send you to keep learning.

Take your time reading the response. Ask follow-ups. If something is jargon, ask: *"Explain that like I haven't coded in 5 years."*

You're not trying to memorize anything. You're building intuition for the loop.

---

## Step 3 — Do the hands-on sandbox (the most important step in this guide)

> **Do not skip this.** This is the inflection point. Reading about agent-native development versus *watching the agent plan a task, write a failing test, implement, and close with evidence on your machine* — those are different universes. Every other step in this guide assumes you've done this one.

The repo ships with a throwaway practice project for exactly this purpose. `sandbox/README.md` describes it as a ~45-60 minute exercise:

```bash
cd ~/process-kit/sandbox/project
bash ~/process-kit/scripts/playbook-init.sh --tool cursor --stealth
```

Then open that folder in your IDE and follow [`sandbox/WALKTHROUGH.md`](sandbox/WALKTHROUGH.md). The code is trivial on purpose — the point is the *workflow*. You'll watch the agent plan, claim tasks, write tests first, implement, and close with evidence.

When you finish, you'll know what "Planner mode", "Executor mode", "beads", and "scratchpad" actually mean — because you'll have used all of them, not read about them.

---

## Step 4 — Start your own project

Now that the sandbox has put the loop in your hands, apply it to something you actually care about. Paste this prompt into a fresh chat:

> I want to start a new project: **[describe what you want, e.g. "a CLI that tracks the books I'm reading" or "a small web app that does X"]**.
>
> Walk me through:
> 1. Where to create the project folder (which directory) and what to name it.
> 2. How to bootstrap it with this playbook — which `playbook-init.sh` flags should I use and why?
> 3. Which tool you recommend (Cursor or Claude Code) for this kind of project.
> 4. Whether we should start with a design doc, jump straight to beads, or do a quick spike first. Justify the choice using the rules in this playbook.
> 5. The next 3 prompts I should send you, in order.
>
> Don't implement anything yet — just plan and explain. I'll say "go" when I want execution to start.

Follow the agent's tips. It will create beads (tasks with acceptance criteria), maybe a design doc, and tell you the next prompt to run.

---

## Step 5 — Your day-to-day loop

Each working session, in order:

1. **Start the session** —
   > "Run `bd prime` and tell me what's in progress and what's ready to work on. Anything blocked needing my input?"

2. **Pick the next task** —
   > "Show me the top-priority ready bead. What are its acceptance criteria? Anything that needs clarification before we start?"

3. **Execute** —
   > "You're in Executor mode. Implement bead <ID>. Follow `pragmatic-tdd`. Show me the test output before you close the bead."

4. **End the session** —
   > "Anything worth `bd remember`-ing from this session? Commit and push the work with a clean message, then summarize what's done and what's left."

That's the whole loop. Most days are 2–3 cycles of #2 → #3.

---

## Step 6 — Prompts to keep in your back pocket

Bookmark these. They unstick you fast:

| When you... | Say this |
|---|---|
| Don't know what to do next | *"What's ready in `bd ready`? Show me everything blocked too, and tell me what I should pick up next."* |
| Don't understand the agent's plan | *"Walk me through this plan as if I were a senior engineer hearing it for the first time. What's the risk?"* |
| Want to make sure you're following the playbook | *"Audit my workflow on this bead. Is there anything I'm missing per the rules in `.cursor/rules/` (or `.claude/rules/`)?"* |
| Are nervous about a change | *"Before I let you do this, summarize the blast radius and the rollback plan in plain English."* |
| Want a deeper review | *"Run a Tier 1 multi-agent review on these changes. Use `code-reviewer`, `architect-reviewer`, and `simplify` lenses. Then triage findings as Critical / Important / Minor."* |
| Forgot a command | *"Remind me how to <do X> using `bd` and the playbook. One example, no theory."* |
| Are stuck and don't know why | *"I'm stuck on <X>. Run `bd doctor --agent`, `git status`, and `bd show --current`, then tell me what you see."* |
| Hit a confusing error | *"Here's the error: <paste>. Explain what's happening, what you'd try first, and the safest order to try things."* |
| Want a knowledge check | *"Quiz me on the last bead we closed. 3 questions about why we did it the way we did."* |

---

## Step 7 — Habits that make you dangerous (in the good way)

Build these reflexes:

- **End every chat with:** *"What's the best next prompt for me?"* — the agent will hand you the next move.
- **Before a big change:** *"Plan first. Don't implement until I say go."* — separates thinking from doing.
- **When you feel out of depth:** *"Which concept from this playbook applies here? Explain it like I'm rusty."* — uses the agent as your refresher tutor.
- **When the agent does something that seems off:** *"Why did you do that? Cite the rule it came from."* — keeps the agent accountable to the playbook.
- **At the end of a working session:** *"Commit, push, and tell me what changed and what's left."* — no orphaned work.

---

## Step 8 — Level-up pattern: multi-agent collaboration (advanced)

> **Heads up: this pattern costs more — in both time and real dollars.** Save it for decisions where being wrong is expensive. **But you do need to learn it.** It's the skill that separates good agentic work from great agentic work.

You've done the sandbox. You've shipped something with the day-to-day loop. Here's the pattern that takes you from "the agent gave me an answer" to "I'm confident the answer is right":

**The pattern:** Before committing to a non-trivial decision or change, fan the work out to multiple agents in parallel — each with a different lens, or even a different underlying model — then have them synthesize their findings for you. **Don't move forward until they've convinced you.**

The playbook formalizes this in the [`multi-agent-review`](cursor/rules/multi-agent-review.mdc) rule. Two flavors:

- **Same-model, multi-lens** (cheaper): one model, three independent review passes with different framing — correctness, architecture, simplicity. Catches the blind spots of any single framing.
- **Cross-model** (more expensive): the same change reviewed by different model families (Claude, GPT, Gemini, etc.). Different architectures have different blind spots — getting them to agree is strong signal.

### When to use it

- Architectural decisions or structural refactors
- Anything touching shared components, auth, billing, or data integrity
- Plans you're nervous about, or where the cost of being wrong is high
- A code change that's about to ship to users you can't easily roll back

### When NOT to use it

- Daily small tasks (typo fixes, single-file edits, mechanical changes)
- Reversible experiments or spikes
- When you already did a similar review recently and nothing material has changed

### The cost reality — be honest with yourself

This pattern is genuinely expensive:

- **Dollars:** Each parallel agent is real API cost. A 3-agent same-model review is roughly 3x a single pass. A cross-model review with paid frontier models on both sides can be 5-10x. This adds up *fast* if you make it your default.
- **Time:** Synthesis isn't free. After the parallel runs return, you spend real effort triaging findings as Critical / Important / Minor before deciding what to fix.
- **Cognitive overhead:** You read 3 reviews instead of 1. Without discipline, you'll cherry-pick the one you already agree with and ignore the rest — which gives you the worst of both worlds (high cost, no upside).

Use it on things that matter. Don't burn it on routine work. The fastest way to lose trust in your own judgment is to over-apply this — you'll start second-guessing everything.

### Try it

When you have a substantive change you're nervous about, paste this:

> Before I commit this, run a Tier 1 multi-agent review on the changes. Three parallel passes, each in independent context:
>
> 1. **code-reviewer lens:** correctness, edge cases, error paths, race conditions
> 2. **architect-reviewer lens:** pattern consistency, component boundaries, reusability, architectural drift
> 3. **simplify lens:** over-engineering, premature abstraction, dead code, gold-plating
>
> Don't let them see each other's findings until synthesis. Then triage everything as Critical / Important / Minor, and tell me which I must address before shipping. I won't move forward until I've read your synthesis and I'm convinced.

For the highest-stakes work — architectural decisions, anything touching production data, structural refactors of shared code — escalate to a **Tier 2 cross-model review**: take the Tier 1 output and have a *different* model family critique it independently, then bring those findings back. The [`multi-agent-review`](cursor/rules/multi-agent-review.mdc) rule documents the full protocol.

### The mental model that matters most

The point isn't "more agents = better." The point is **adversarial collaboration**: forcing your agent's first-pass answer to survive scrutiny from independent perspectives before you act on it. Once you internalize this, you'll notice when an agent's single-pass answer feels too neat, and you'll instinctively ask for the council before you commit. That instinct is the skill.

---

## Step 9 — When you want to go deeper

Read in this order, on your own time:

- [`docs/concepts.md`](docs/concepts.md) — The *why* and the 5 components.
- [`docs/glossary.md`](docs/glossary.md) — Plain-English definitions of every term you'll hear.
- [`docs/faq.md`](docs/faq.md) — Real questions from real adopters.
- [`QUICKSTART.md`](QUICKSTART.md) — All setup flags and options.
- [`README.md`](README.md) — Repo structure, what's in each folder.

You don't need to read these to get going. They're there when you have a *specific* question.

---

## A note on what's different about coding now

If you stepped away around 2018-2022, here's the shift:

- **You're not the typist anymore.** You're the director and reviewer.
- **The agent has memory** — beads, scratchpad, `bd remember`. It can pick up where it left off, even across sessions, even across machines.
- **Quality comes from structure, not heroics.** The rules in this repo make agents follow good engineering practice automatically. You enforce them by reading the agent's output, not by writing every line yourself.
- **You don't need to know everything.** You need to know enough to evaluate what the agent shows you. If you can read the diff and ask one good follow-up question, you're effective.

You'll feel rusty at first. That's expected. Lean into the agent. Ask "explain like I'm rusty" liberally. The reasoning muscles come back faster than the typing ones.

---

## You're set

Open Cursor (or Claude Code), point it at this repo, and paste the Step 2 prompt. Everything else flows from there.

Welcome back.
