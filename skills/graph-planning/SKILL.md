---
name: graph-planning
description: Planner playbook for multi-bead breakdowns — decomposition heuristics, atomic dependency-graph creation with bd create --graph, graph verification, and mid-flight epic management (stuck children, scope expansion, honest epic close). Trigger phrases: "plan this epic", "break down this initiative", "graph planning", "bd create --graph", a Planner breakdown reaching 3+ beads, or an in-flight epic needing a management decision.
---

# Graph Planning

Planner-side procedure for turning an approved breakdown into a beads dependency graph and steering the resulting epic to an honest close. The `operating-model` rule states the obligations; this skill is how the Planner meets them.

The G-IDs below are shared with the split's obligations checklist in the kit repo.

This skill reads no overlay keys.

## When to Use This Skill

- A Planner breakdown produces **3+ beads** (and the `beads-quality` rule makes wired dependencies or a graph mandatory at 4+)
- An epic is in flight and a child is stuck, scope is expanding, or the epic looks close-eligible

**Skip when:** the work is 1–2 beads — plain `bd create` (plus `bd dep add` if needed) is enough, and an epic isn't justified. Skip for Executor-side work: picking up, verifying, and closing individual beads is the `bead-completion` rule's domain. (Exception: Phase 2 also serves single-bead `--parent` use — the `beads-quality` rule and the bead-authoring skill point here for parent-child mechanics.)

## Core Process

### Phase 1 — Decompose (G1)

Apply the decomposition heuristics before creating anything:

- **3–7 beads per epic.** Fewer than 3 doesn't justify an epic. More than 7 suggests a missing intermediate grouping.
- **Each bead completable in one agent session.** If it takes multiple sessions, split it.
- **Leaf beads: max 3 ACs.** More than 3 usually means the bead is doing too many things.
- **Independent beads should not depend on each other** — check for unnecessary serialization in Phase 3.

Every node still needs a full description and acceptance criteria per the `beads-quality` rule (What/Where/How/Why, observable outcomes, non-goals); the bead-authoring skill's Phase 2 has the worked example.

### Phase 2 — Create the graph atomically (G2)

For 3+ beads, use `bd create --graph plan.json` to create the entire dependency graph in one operation:

```json
{
  "nodes": [
    {
      "key": "epic",
      "title": "Add loading indicators to beads-ui",
      "type": "epic",
      "description": "Tab switching shows misleading empty state during load."
    },
    {
      "key": "store",
      "title": "Track subscription loading state",
      "type": "task",
      "parent_key": "epic",
      "description": "Store exposes isLoading getter that is true while fetching."
    },
    {
      "key": "spinner",
      "title": "Create loading spinner component",
      "type": "task",
      "parent_key": "epic",
      "description": "Spinner renders/unmounts based on boolean prop."
    },
    {
      "key": "integrate",
      "title": "Wire spinner into tab views",
      "type": "feature",
      "parent_key": "epic",
      "description": "Switching tabs shows spinner while loading. Empty state shows after load."
    }
  ],
  "edges": [
    {"from_key": "integrate", "to_key": "store", "type": "blocks"},
    {"from_key": "integrate", "to_key": "spinner", "type": "blocks"}
  ]
}
```

For hierarchy without a graph file, `bd create "Sub-task A" --parent=<epic-id> --type=task` gives children auto-generated hierarchical IDs; prefer `--parent` over standalone `bd dep add` for true containment relationships.

### Phase 3 — Verify the graph (G3)

After creation, run `bd graph <epic-id>` to visualize and verify dependency order and to identify parallelism opportunities before execution starts. Use `bd graph --all --compact` for a full project view. Fix at this stage:

- Unnecessary serialization (independent beads chained by habit)
- Missing edges (a bead that will actually block another, unwired)
- Orphan nodes (no parent, no edges — probably belongs in the epic or shouldn't exist)

### Phase 4 — Mid-flight epic management (G4–G7)

Planner responsibilities while the epic executes:

- **Progress (G4):** after each child close, run `bd epic status <epic-id>` and report progress.
- **Stuck children (G5):** if a child is blocked or deferred and no other children remain, decide: (a) defer the epic to match, (b) extract the stuck child to a standalone bead and close the epic with adjusted success criteria, or (c) close the child as won't-do with rationale. Do not leave epics in limbo.
- **Scope expansion (G6):** if a new requirement would push an epic beyond 7 children, split the epic into two or create a sibling epic. Do not silently grow epics past the decomposition heuristic.
- **Close = success criteria, not just child count (G7):** before closing an epic via `bd epic close-eligible`, verify the epic's success criteria per the Epic row of the `bead-completion` rule's evidence table — that row is the canonical close-evidence law; this bullet is the Planner-side trigger.

## Anti-Patterns

- **Graph-free multi-bead planning.** Creating 4+ beads with no dependency structure produces an unsequenced grab-bag (`beads-quality` rule, anti-pattern 2). If you created more than 3 beads, wire them or use `--graph`.
- **Bead explosion.** 8+ beads for work that could be 3 (`beads-quality` rule, anti-pattern 1); a bead whose only AC is "file X exists" is too small — fold it into a sibling.
- **Serializing the independent.** Chaining beads that don't actually block each other hides parallelism; Phase 3 exists to catch this.
