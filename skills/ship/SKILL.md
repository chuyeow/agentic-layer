---
name: ship
description: >-
  Take a feature branch believed done through quality gates to a merged
  (or deliberately-held) PR. Use when the user says "ship this", "ship
  it", "ready to ship", "take this to a PR", "open a PR for this work",
  or signals the work on the current branch is complete and should go
  out. Runs simplify → verify (end-to-end + edge cases) → design check
  (UI only) over the whole branch diff, pushes, opens the PR per
  write-pr-description, then runs babysit-pr through to merge or a
  deliberate hold. If a PR already exists and only needs shepherding,
  use babysit-pr directly.
---

# Ship

## Operating rules

- **Review the whole branch diff** — `git diff origin/<default>...HEAD`
  — never just the working tree; the work may span many commits, pushes,
  and sessions.
- **Gates fix, don't just report.** Each gate applies its fixes, re-runs
  the repo's verification gate (tests/lint/typecheck), and commits — one
  commit per gate.
- **Tests passing ≠ feature working.** The verify gate drives the change
  end-to-end in the running app; green tests alone never satisfy it.
- **Keep the evidence.** The verify and design gates' observed results
  (outputs, before/after, screenshots) become the PR body's
  `## Verification`.
- **Don't churn.** One fix pass per gate (repo-gate breakage from that
  pass included). Anything unfixable or needing a decision →
  `AskUserQuestion`.
- **Stage by path, never blanket.** No `git add -A` / `git add .`. A
  file you don't recognize (another agent's edit, scratch output,
  secrets) is never committed silently — ask.
- **Never merge here.** Merge policy is `babysit-pr`'s per-PR question.

## Steps

1. **Orient.**
   - Preflight: `gh auth status` — fail here, not after three gates.
   - Resolve the default branch (`gh repo view --json defaultBranchRef
     --jq .defaultBranchRef.name`), then `git fetch origin <default>`.
   - On the default branch with shippable changes → create a feature
     branch first (short kebab-case).
   - Establish scope: `git status` + `git log origin/<default>..HEAD`
     + `git diff origin/<default>...HEAD`. Empty diff and clean tree →
     nothing to ship; stop and say so.
   - Triage anything uncommitted now: this work's changes → commit, so
     the gates review committed state; unrelated or unrecognized files
     → leave out and ask.
   - Note the repo's verification gate (e.g. `bun run verify`,
     `npm test`).

2. **Simplify gate.** Run the `simplify` skill over the branch diff.
   Fixes → commit.

3. **Verify gate.** Run the `verify` skill: drive the change end-to-end
   in the running app. Then sweep edge cases — pick what applies, record
   each checked item with its observed result:
   - empty / zero / null / missing inputs
   - boundary values (limits, off-by-one, max sizes)
   - error paths: bad input, dependency down, timeout — fail clean or
     corrupt state? state after a mid-operation failure?
   - repeat / concurrent invocation — idempotent? racy?
   - reliability: retries, timeouts set, errors observable; migrations
     safe to roll back
   Fixes → re-verify the broken case → commit.

4. **Design gate — only if the branch diff touched UI** (`--name-only`
   against `*.tsx` `*.jsx` `*.vue` `*.svelte` `*.css` `*.scss`,
   `components/`, `pages/`, `views/`, `templates/`). No hits → skip,
   say so. Hits → run the `impeccable` skill on the changed surfaces;
   capture after-screenshots (and before, when still obtainable) for
   the PR body. Fixes → commit.

5. **Push** the branch (`-u` if no upstream). Nothing should remain
   uncommitted by now; if something does, triage it as at orient.

6. **Open the PR.** Body per the `write-pr-description` skill, with
   `## Verification` built from the gate evidence. `gh pr create` — or,
   if a PR was already open for the branch, `gh pr edit <PR> --body` to
   refresh it (the gates still ran; their fixes already pushed).

7. **Run the `babysit-pr` skill to the end** — rebases, CI to green,
   review threads, Slack, the merge question. Ship is done when babysit
   closes out: PR merged or deliberately held.
