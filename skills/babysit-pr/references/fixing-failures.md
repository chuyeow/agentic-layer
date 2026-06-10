# Fixing PR failures

Two things block a PR: **failed checks** (CI) and **unresolved review comments**.
Handle both each loop iteration. Read this when step 3 finds red checks or
unresolved threads. Resolve `<owner>`/`<repo>` once: `gh repo view --json
owner,name --jq '.owner.login+" "+.name'`.

**Fix order** (tackle the merge-blocking, fast-signal failures first):
1. Merge conflicts / behind — resolve before anything else (SKILL.md step 2).
2. CI checks — lint/typecheck/tests/build (GitHub Actions): the bulk of failures.
3. Quality gate — SonarQube (coverage, smells, security).
4. Review threads — CodeRabbit + human reviewers (also swept post-green, SKILL.md step 5).

No tool gets a dedicated step beyond this — a preview/deploy build that fails is
handled by the generic row in the triage table below, not a special case.

## A. Failed checks

### 1. Get the actual error — scoped to the current commit
Don't diagnose blind, and don't diagnose a *stale* failure from a prior push.
Scope to `HEAD`:

```bash
sha=$(git rev-parse HEAD)
gh run list --commit "$sha" --status failure --limit 5 --json databaseId,name,workflowName
# for each failing run id:
gh run view <id> --json jobs \
  --jq '[.jobs[]|select(.conclusion=="failure")|{name,failed:[.steps[]|select(.conclusion=="failure").name]}]'
gh run view <id> --log-failed | tail -200   # only failed-step logs, last 200 lines — keeps context small
```

Non-Actions checks (quality gate, preview deploy, external reviewer): open the
check's own detail link — `gh pr checks <PR> --json name,bucket,link`.

### 2. Triage by failure class
| Class | Fix |
|---|---|
| Type error | Read the file at the reported `path:line`; fix the type. |
| Lint / format | Apply the formatter / autofix; don't hand-tweak. |
| **Lockfile mismatch** | Re-run the install command to regenerate — never hand-edit a lockfile. |
| Test failure | Fix the **source**, not the test — unless the test itself is wrong. |
| Build failure | Missing import / config / env; trace the *first* error, not the cascade. |
| Quality gate (coverage, smells, security) | Open the specific issue; fix it, or if intentional, mark/justify it through the gate's own mechanism. |
| Preview / deploy build | Read the build log; usually a runtime/config error that only surfaces at build (edge runtime, dynamic-server, env). |

### 3. Don't burn loop iterations on non-code failures
These aren't fixable by another commit — **flag and stop retrying** (Slack +
surface to the user), don't re-push hoping it passes:
- Infra: runner OOM, network, registry/provider outage.
- Flaky tests: passes on re-run, unrelated to the diff.
- Permissions / missing secrets or tokens.

## B. Unresolved review comments
A green check ≠ comments addressed. Some reviewers' checks always pass — detect
outstanding work via **unresolved threads**, not check status.

### 1. Fetch unresolved threads
```bash
gh api graphql -f query='
  query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){
    pullRequest(number:$n){reviewThreads(first:100){nodes{
      id isResolved comments(first:1){nodes{author{login} path body}}}}}}}' \
  -F o=<owner> -F r=<repo> -F n=<PR>
```
Keep `isResolved == false`. Treat **any non-bot author as a human reviewer** —
do not hardcode org-specific login suffixes. Known review bots (e.g. CodeRabbit)
are addressed the same way; the only difference is tone of reply.

### 2. Address or decline — then RESOLVE
Per unresolved thread:
- **Fix** → make the change.
- **Decline** → only after verifying: jump to the definition (Grep fallback —
  the real impl may be elsewhere), read callers/wrappers, trace the data flow
  end to end. Can't verify all three → fix rather than decline (avoids the
  confidently-wrong decline).
- **Reply** with what changed / why declined:
  - Inline: `gh api repos/<owner>/<repo>/pulls/<PR>/comments -f body="..." -F in_reply_to=<COMMENT_ID>`
  - Top-level: POST `repos/<owner>/<repo>/issues/<PR>/comments` (no threading).
- **Resolve the thread** — it will NOT auto-resolve on re-review or when the
  code is fixed:
  ```bash
  gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=<THREAD_NODE_ID>
  ```
  (`<THREAD_NODE_ID>` is the thread `id` from the query above, not a comment id.)

## C. Commit the fixes
- **Never blind `git add -A`** — it sweeps untracked debris (scratch files,
  logs, agent output) into the PR commit. If untracked files exist *outside*
  source dirs (`src/ apps/ packages/ lib/ test(s)/ __tests__/ .github/
  public/`), stage selectively: all tracked modifications + only the in-tree
  new files. Tracked modifications are always safe to stage.
- **Specific commit message** — name what was fixed; mention conflict
  resolution if it happened. `"fix: type errors + review feedback (babysit
  iter N)"`, not `"address feedback"`.
- `git push --force-with-lease`, then return to step 3 (re-sync the head SHA,
  re-arm the monitor).
