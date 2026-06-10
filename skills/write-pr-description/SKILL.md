---
name: write-pr-description
description: >-
  Structure for pull request descriptions. Use when creating or editing a PR
  (running `gh pr create` / `gh pr edit --body`, or writing/revising a PR body).
  Enforces three mandatory sections — Why, What changed, Verification — and the
  deployment/verification gold standard. A PreToolUse hook blocks `gh pr create`
  when a section is missing, so follow this before composing any PR body.
---

# PR description

Every PR body has three **mandatory** sections, in this order: `## Why`,
`## What changed`, `## Verification`. A `PreToolUse` hook
(`enforce-pr-description.sh`, colocated in this skill dir) blocks `gh pr create`
/ `gh pr edit --body` when any heading is missing.

Write **only what a reviewer needs**. They will not read every line of the diff —
the body is how they understand intent and confirm it works without doing so.

## Core rules

- **No session-local / internal references.** Never write "#2", "the second
  gap", "as discussed" — shorthand that only made sense where the work happened.
  A reviewer seeing only the PR has no access to that context. Name the thing.
- **Why = purpose / user impact**, not a restatement of the diff.
- **What changed = a table**, one row per change.
- **Verification = the actual RESULT**, not instructions to verify. Show the
  observed before/after. Mandatory on every PR — if there is genuinely nothing
  to verify (pure docs/comment change), write `N/A — no behavior change` and say
  why.

## Template

```markdown
## Why

<Purpose and user impact. What was broken or missing, what this unlocks.>

## What changed

| Change | Detail |
|--------|--------|
| <area / file / behavior> | <what and, if non-obvious, why> |

## Verification

<The observed result. See "Verification depth" below.>
```

## Verification depth (the gold standard)

Match the depth to the change. A small refactor needs a line; a deployed,
user-facing change earns the full treatment below.

### Before / After

Show the **contrast**, concretely:

- A results table — per case: input → observed value/field → ✅/❌.
- The old value or JSON shape alongside the new one, so the delta is visible.
- Screenshots for UI changes (before vs after).

### Environment-scoped, when the change is deployed

Split verification by environment (`### Staging`, `### Production`). Each block
carries **proof it is actually live**:

- **Commit / branch verified** on that environment (link it).
- **Date / time** verified.
- **Deploy workflow run** link (the successful run).
- **`master` vs deployed branch** diff — e.g. "0 ahead / 0 behind, identical at
  `<sha>`" — proving what is live equals this PR.

### Repro in a collapsible

Put the commands a reviewer could re-run inside `<details>` so the result stays
front-and-center and the body doesn't bloat:

```markdown
<details>
<summary>Reproduction commands</summary>

\`\`\`bash
<curl / CLI the reviewer can paste>
\`\`\`

</details>
```

### Honest caveats

If a result looks odd, explain it and state **what is actually being verified**.
(Gold-standard example: "bot-origin searches return 0 hotels even when rates
exist — the response *shape*, i.e. which fields are present/absent, is what is
verified, and that matches the change.") Never paper over an unexpected number.

### Downstream / consumer impact

Note the effect on consumers and link related PRs — e.g. "frontend types the
field optional, so a `null` simply renders nothing; frontend PRs #x, #y closed
as unnecessary."

## Optional sections

- `## What's kept` — when you intentionally did NOT change something a reviewer
  might expect, say so and why. Kills "did you forget X?" review churn.

## What good looks like

A reviewer reads `## Why`, scans the `## What changed` table, and confirms from
`## Verification` that the behavior is correct and nothing regressed — **without
opening the diff**. If they can't, the body is incomplete.
