---
name: babysit-pr
description: >-
  Babysit a pull request from creation to merge (or a deliberate hold). Use
  the moment a PR exists — right after `gh pr create`, or when the user says
  "babysit the PR", "watch CI", "watch the PR", "ship #<n>", or gives a PR
  URL/number to shepherd. Auto-rebases the branch onto the default branch when
  it falls behind, watches CI to green via a persistent monitor, fixes failures
  and force-pushes, logs off-PR work, notifies Slack on done/blocker, and asks
  the merge policy per PR. Post-PR-creation only — never merges without asking.
---

# Babysit PR

Carry a freshly-opened PR to merged (or deliberately-held), babysitting CI the
whole way. This is the standing **post-PR-creation** routine — run it without
being re-asked once a PR exists.

Out of scope (these happen BEFORE the PR, not here): `/simplify` on the diff,
writing the PR body to the gold standard (`write-pr-description`), and
`gh pr create` itself — the `ship` skill covers that pipeline. This skill
starts at "the PR is open."

## Operating rules

- **Never merge without asking.** Merge is always a per-PR decision made via
  `AskUserQuestion` (see step 6). Do not enable auto-merge silently.
- **Keep the branch current.** Auto-rebase onto the default branch whenever the
  PR branch is behind it, and resolve merge conflicts best-effort (see step 2)
  — stale/conflicting branches fail merge checks and test against old code.
- **Watch, don't poll by hand.** Use a persistent `Monitor` on `gh pr checks`
  so it survives across turns and respects the shared GitHub API rate limit.
  Prefer `gh pr checks` over `gh run watch`.
- **Never watch a stale SHA.** After any push (rebase, fix, sweep), wait until
  GitHub's PR head SHA matches local `HEAD` before arming the monitor —
  otherwise it reports the previous commit's checks. (See step 3.)
- **Bound the fix loop.** Cap the watch→fix→push→re-watch cycle at **5**
  iterations. On exhaustion, stop — do not loop forever: Slack + surface the
  remaining failures to the user (`AskUserQuestion`) rather than churning.
- **Fix failures, don't just report them.** A red check means: diagnose, fix,
  rebase on latest default branch, `git push --force-with-lease`, re-arm. The
  full diagnose→fix→commit playbook (CI checks + review threads, self-contained
  — no external skill needed) lives in `references/fixing-failures.md`.
- **Report result-first and concise.** En-dashes, real Markdown links (no bare
  URLs), never print tokens.
- Use `gh` for everything GitHub (no web search), even when given a URL.

## Workflow

1. **Orient on the open PR.**
   - Preflight: `gh auth status` — if not authenticated, stop and say
     "run `gh auth login`". (That's the only hard prerequisite.)
   - Resolve the PR (number from the just-run `gh pr create`, an argument, or
     `gh pr view --json number,url` on the current branch).
   - Note the repo's verification gate (e.g. `bun run verify`, `npm test`) in
     case a CI failure needs a local repro.

2. **Sync with the default branch — behind and conflicting are separate states.**
   - Resolve the default branch: `gh repo view --json defaultBranchRef --jq
     .defaultBranchRef.name` (don't assume `main`).
   - **Behind?** `git fetch origin <default>`, then `git rev-list --count
     HEAD..origin/<default>`. If > 0, rebase automatically: `git rebase
     origin/<default>`. Clean → re-run the verification gate, `git push
     --force-with-lease`.
   - **Conflicting?** A conflict is a merge *state*, orthogonal to checks — a
     PR can be all-green yet `CONFLICTING`. Read `gh pr view <PR> --json
     mergeable,mergeStateStatus`. `mergeable` is `UNKNOWN` transiently right
     after a push — retry a few times (~3, a couple seconds apart) before
     trusting it; treat a stuck `UNKNOWN` as mergeable and let the loop catch a
     real conflict later. If `CONFLICTING`, attempt a best-effort
     resolution (rebase onto the default branch; regenerate lockfiles / derived
     files rather than hand-merging them; re-run the gate), then push. Only if
     it's genuinely unresolvable — real semantic conflicts you'd be guessing at
     — stop and surface the conflicted files via `AskUserQuestion`.
   - Either path that pushes: re-sync the head SHA before re-arming the monitor
     (see step 3).

3. **Watch CI to green — bounded fix loop (max 5 iterations).**
   - **Before arming (and after every push):** wait until GitHub's PR head SHA
     matches local `HEAD` so the monitor never reports a stale commit's checks
     — poll `gh pr view <PR> --json headRefOid` against `git rev-parse HEAD`
     (a few tries, ~5s apart); proceed anyway if it lags.
   - Arm a persistent `Monitor` polling `gh pr checks <PR> --json name,bucket`,
     emitting each check as it settles and stopping when all are non-pending.
     Cover failure states, not just the happy path. Note expected skips
     (`process-submission`, Vercel Agent Review).
   - **A bot-review check (CodeRabbit, etc.) reporting `pass`/green is a *check
     status*, NOT thread resolution** — these bots post unresolved review
     threads while their own check stays green. Never read "CodeRabbit: pass"
     as "comments addressed." Fetch the actual threads (step 5) — that sweep is
     mandatory regardless of how the bot's check reports.
   - On **failure**: read `references/fixing-failures.md` and follow it —
     diagnose from commit-scoped logs (`gh run view --log-failed`), fix by
     failure class, stage without debris, commit with a specific message,
     `git push --force-with-lease`, re-sync the SHA, re-arm. Rebase first if the
     default branch moved (step 2). Fix the PR body if it drifted. One iteration.
     If the failure is infra/flaky/secrets (not code), don't retry — flag it.
   - **Stop after 5 iterations.** If still red, do not keep churning — Slack the
     blocker and surface the remaining failures to the user (step 4 + step 6's
     escalation), then hold.

4. **Log off-PR work + notify.**
   - If the PR triggers work the diff does not show (a dispatched GitHub
     Actions run, a backfill/migration, DB writes), maintain it via the
     `pr-work-log` skill.
   - On completion or any blocker (rate limit, repeated CI failure, needs a
     decision), post a result-first message with the PR link to Slack channel
     `C0B5ZE4UQHJ` (the attention channel). One consolidated message on done;
     a separate one when blocked.

5. **Final sweep — unresolved review comments that don't block checks.**
   - All-green ≠ all-addressed: review threads sit unresolved without failing a
     check, and never auto-resolve. Run section **B** of
     `references/fixing-failures.md` — fetch `isResolved==false` threads, then
     fix/decline-with-reason and **resolve each via the GraphQL mutation**.
   - If the sweep produces file changes, commit (section C), push, re-sync the
     SHA, and go back to step 3 — counts toward the 5-iteration cap. No changes
     → proceed.

6. **Decide the merge — ask, every PR.**
   - Once green, surface mergeability: `gh pr view <PR> --json
     mergeStateStatus,reviewDecision,mergeable`.
   - Then ask via `AskUserQuestion` (header "Merge"), presenting all options:
     - **Auto-merge when green** — `gh pr merge <PR> --auto --merge` (or the
       repo's merge style), then hands-off.
     - **Merge now** — checks are green; merge immediately on confirm.
     - **Wait for a human approver** — hold; do not merge. Report
       `reviewDecision` and re-surface when it flips to approved.
     - **Wait for a specific approver** — ask who; hold until that person
       approves, then re-confirm.
     - **Leave open** — no merge; stop here.
   - Honor the choice exactly. If "wait for approver", keep (or re-arm) a watch
     on `reviewDecision` rather than merging.

7. **Close out.**
   - Lead with the outcome: merged + commit, or held + why + what it's waiting
     on. Include the PR link.
   - Then a scannable per-check summary with counts, e.g.:
     ```
     #271 — held (awaiting @approver)   https://github.com/wego/repo/pull/271
       CI checks    ✓  (lint, types, bun, browser)
       SonarQube    ✓
       CodeRabbit   ✓  (3 fixed, 1 declined)
       Reviews      ✓  (2 fixed, 0 unresolved)
       Iterations   2 / 5
     ```
     Mark anything unresolved ✗ with the reason (infra / flaky / needs-human).

## Notes

- Starts at "the PR is open." If invoked before a PR exists, stop and run the
  `ship` skill instead — it carries the branch through the quality gates,
  opens the PR (`write-pr-description` governs the body), and hands back here.
  Do not create the PR from inside this skill.
