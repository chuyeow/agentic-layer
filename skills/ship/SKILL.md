---
name: ship
description: >-
  Take a feature branch believed done through quality gates to an open,
  babysat PR. Use when the user says "ship this", "ship it", "ready to
  ship", "take this to a PR", "open a PR for this work", or signals the
  work on the current branch is complete and should go out. Runs simplify
  → verify (end-to-end + edge cases) → design check (UI only) over the
  whole branch diff, flushes and pushes, opens the PR per
  write-pr-description, then hands off to babysit-pr. Pre-PR pipeline —
  if a PR already exists and only needs shepherding, use babysit-pr.
---

# Ship

Pipeline from "feature branch believed done" to a merged (or
deliberately-held) PR. The pre-PR counterpart of `babysit-pr`: gates run
here, shepherding happens there.

## Scope

- **Unit of review is the whole branch diff** — `git diff
  origin/<default>...HEAD` plus anything uncommitted — never just the
  working tree. Work may span many commits, pushes, and sessions before
  shipping; the gates must see all of it.
- Commits are byproducts, not a step. Each gate commits its own fixes;
  by PR time the branch carries whatever history the work produced.
- If a PR is already open for the branch, still run the gates (fixes
  push to the PR), skip creation, and go straight to step 6.

## Operating rules

- **Gates fix, don't just report.** Each gate applies its fixes, re-runs
  the repo's verification gate (tests/lint/typecheck), and commits
  before moving on — one commit per gate, so history shows what each
  pass changed.
- **Tests passing ≠ feature working.** Step 2 drives the change
  end-to-end in the running app; green tests alone never satisfy it.
- **Keep the evidence.** Steps 2–3 produce observed results (outputs,
  before/after, screenshots). Save them — step 5's `## Verification`
  section is built from them, and reconstructing later is rework.
- **Don't churn.** One fix pass per gate. If a gate surfaces something
  unfixable or needing a decision, stop and ask via `AskUserQuestion`
  rather than looping.
- **Never merge here.** Merge policy is `babysit-pr`'s per-PR question.

## Steps

1. **Orient.**
   - Resolve the default branch: `gh repo view --json defaultBranchRef
     --jq .defaultBranchRef.name` (don't assume `main`), then
     `git fetch origin <default>`.
   - If on the default branch with shippable changes, create a feature
     branch first — never ship from the default branch directly.
   - Establish scope: `git status` + `git log origin/<default>..HEAD`
     + `git diff origin/<default>...HEAD`. Empty diff and clean tree →
     nothing to ship; stop and say so.
   - Note the repo's verification gate (e.g. `bun run verify`,
     `npm test`) — every gate below re-runs it after fixes.

2. **Simplify gate.** Run the `simplify` skill over the branch diff —
   reuse, simplification, efficiency, altitude. Apply fixes, re-run the
   repo gate, commit.

3. **Verify gate.** Run the `verify` skill: launch the app and drive the
   change end-to-end, observing real behavior. Then sweep edge cases —
   pick what applies to the change, skip the rest, and record each
   checked item with its observed result:
   - empty / zero / null / missing inputs
   - boundary values (limits, off-by-one, max sizes)
   - error paths: bad input, dependency down, timeout — does it fail
     clean or corrupt state?
   - repeat / concurrent invocation — idempotent? racy?
   - state after a mid-operation failure (partial writes, orphaned rows)
   - reliability: retries, timeouts set, errors logged/observable;
     migrations safe to roll back
   Fixes → re-verify the broken case → repo gate → commit.

4. **Design gate — only if the branch diff touched UI.**
   - Detect: `git diff origin/<default>...HEAD --name-only` against UI
     paths — `*.tsx` `*.jsx` `*.vue` `*.svelte` `*.css` `*.scss`,
     `components/`, `pages/`, `views/`, `templates/`, app routes that
     render. No hits → state "no UI touched, design gate skipped" and
     move on.
   - Hits → run the `impeccable` skill against the changed surfaces;
     capture before/after screenshots (they feed the PR body). Fixes →
     repo gate (design fixes can still break behavior) → commit.

5. **Flush + push.** Commit anything still uncommitted, push the branch
   (`-u` if it has no upstream).

6. **Open the PR.** Compose the body per the `write-pr-description`
   skill — `## Why`, `## What changed`, `## Verification` (the hook
   blocks `gh pr create` otherwise). Build `## Verification` from the
   evidence gathered in steps 3–4: observed results, not instructions.
   Then `gh pr create`.

7. **Hand off to `babysit-pr`.** It owns everything from here —
   rebases, CI to green, review threads, Slack, the merge question.
   Ship ends when babysit starts.
