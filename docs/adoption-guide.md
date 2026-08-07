# Agentic Covenant Adoption Guide

Step-by-step guide for teams adopting the Agentic Covenant in projects bootstrapped with this kit.

## What you're adopting

The [Agentic Covenant](https://github.com/gastownhall/beads/blob/main/CODE_OF_CONDUCT.md) is a Code of Conduct for communities where humans and AI agents collaborate. It has five parts:

| Part | What it covers | Can adopt standalone? |
|------|---------------|----------------------|
| I. Community Standards | Expected behavior for humans and agents | Yes |
| II. Principal-Agent Framework | Operator accountability for agent actions | Yes |
| III. Agent Operating Standards | Self-identification, scope, graceful failure | Requires Part II |
| IV. Contributor Protection | First-mover priority, attribution preservation | Yes |
| V. Enforcement | Violation handling and consequences | Requires Parts II + III |

Most teams adopt all five parts. If you want to adopt incrementally, start with Parts I + II + IV.

## Step 1: Bootstrap with house-rules init

If you haven't already:

```bash
bash ~/process-kit/scripts/house-rules init --tool cursor|claude|both
```

This copies `CODE_OF_CONDUCT.md` into your project automatically, along with a `.github/pull_request_template.md` that includes the `Assisted-by` disclosure convention.

If you already bootstrapped but don't have the PR template:

```bash
mkdir -p .github
cp ~/process-kit/.github/pull_request_template.md .github/pull_request_template.md
```

## Step 2: Customize the Code of Conduct

Open `CODE_OF_CONDUCT.md` in your project and customize these sections:

### Enforcement contact

Replace the kit maintainer contact with your team's escalation path:

```markdown
## Reporting

Report conduct issues to [YOUR TEAM'S CONTACT].
For org-internal projects, use [YOUR ESCALATION PATH].
```

### Rate limits

The defaults (3 open PRs per principal, 5/day) work for most teams. Adjust if your workflow is different:

```markdown
- **Rate limits**: [X] open PRs per principal, [Y] per day
```

### Scope

Define which spaces the Covenant applies to:

```markdown
- **Scope**: [Your project's repo], [chat channel(s)], [issue tracker project], [other spaces]
```

## Step 3: Set up the PR template

The kit ships a PR template at `.github/pull_request_template.md` that includes:

- Summary and test plan sections
- `Assisted-by` disclosure (required by the Agentic Covenant)
- Bead reference field

If your project already has a PR template, add the `Assisted-by` section to it:

```markdown
## AI Disclosure

<!-- Required by the Agentic Covenant. Check one: -->
- [ ] No substantial AI assistance used
- [ ] AI-assisted (describe tool and scope below)

**Assisted-by:** <!-- e.g., "Claude Code — implemented feature, wrote tests" -->
```

## Step 4: Reference from CONTRIBUTING.md

If your project has a `CONTRIBUTING.md`, add a governance section:

```markdown
## Code of Conduct

This project is governed by [The Agentic Covenant](CODE_OF_CONDUCT.md).
AI-assisted contributions are explicitly welcome. Disclose substantial
AI assistance using the `Assisted-by` convention in your PR.
```

## Step 5: Communicate to your team

Key points to share:

1. **AI-assisted contributions are welcome.** The Covenant explicitly supports this.
2. **Disclose, don't hide.** The `Assisted-by` convention is a safe harbor — transparency can never be used against you.
3. **You're accountable.** "My AI wrote that" is not a defense. Understand and be able to maintain what you submit.
4. **Review on merits.** Evaluate PRs based on quality, not on how they were produced.

## Verifying adoption

Run `house-rules doctor` to check governance status:

```bash
bash ~/process-kit/scripts/house-rules doctor
```

It checks for:
- `CODE_OF_CONDUCT.md` presence
- Agentic Covenant content
- Project in `~/.house-rules-sync-targets` for future updates

## Rolling out across projects

To add the Covenant to every project in your sync targets:

```bash
while IFS= read -r project; do
  [ -d "$project" ] || continue
  if [ ! -f "$project/CODE_OF_CONDUCT.md" ]; then
    cp ~/process-kit/CODE_OF_CONDUCT.md "$project/CODE_OF_CONDUCT.md"
    echo "Added: $project"
  fi
  if [ ! -f "$project/.github/pull_request_template.md" ]; then
    mkdir -p "$project/.github"
    cp ~/process-kit/.github/pull_request_template.md "$project/.github/pull_request_template.md"
    echo "Added PR template: $project"
  fi
done < ~/.house-rules-sync-targets
```

Then customize each project's enforcement contact and scope.

## Further reading

- [Governance overview](governance.md) — how governance fits into the kit
- [The Agentic Covenant (full text)](https://github.com/gastownhall/beads/blob/main/CODE_OF_CONDUCT.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute to the kit itself
