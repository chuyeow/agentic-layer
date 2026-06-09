---
name: pr-work-log
description: Surface off-PR work on the pull request as a maintained comment. Triggers when, while a PR is open, you do work tied to that PR that the diff does NOT show — dispatching/watching GitHub Actions runs, running a backfill/migration/data job, writing to a database, kicking off manual workflows, validation runs, or anything happening in CI/Actions/a DB/an external system. Keeps a single "Off-PR work log" comment up to date as each step lands.
---

# PR Work Log

Make invisible work visible. A reviewer reading a PR sees the diff — they do NOT see the
GitHub Actions run you dispatched, the backfill you kicked off, the prod DB rows you
upserted, or the validation you ran. This skill maintains one structured comment on the PR
that records that work as it happens.

## When this fires

Trigger when **all** hold:

1. There is an open PR in scope (the current branch's PR, or one the user named).
2. You perform — or are about to perform — an action **tied to that PR's change** that
   leaves no trace in the diff. Examples:
   - Dispatching or watching a GitHub Actions / CI workflow run.
   - Running a data backfill, DB migration, reindex, or one-off data job.
   - Writing to a database or external system (prod or staging).
   - Triggering a manual `workflow_dispatch`, cron, or deploy.
   - A validation / verification step whose result lives outside the repo.
3. That action's existence, status, or result matters to whoever reviews or merges the PR.

Do **not** fire for ordinary in-PR work (editing code, running local tests/lint/typecheck,
reading files) — that's already visible in the diff or expected.

## What to do

1. **Find the PR.** `gh pr view --json number,url` for the current branch, or use the
   number the user gave. If no PR exists yet, note that and surface the log once it does.

2. **Find an existing log comment.** One log per PR — update it, don't spam new comments.
   ```bash
   gh pr view <num> --json comments \
     --jq '.comments[] | select(.body | startswith("## 📋 Off-PR work log")) | .url'
   ```
   - None found → create one with `gh pr comment <num> --body "..."`.
   - Found → rewrite it in place. Get the comment id and `gh api -X PATCH \
     repos/{owner}/{repo}/issues/comments/{id} -f body=@-`. (PR comments are issue
     comments.) Preserve prior entries; append/append-update rather than truncating history.

3. **Write entries.** Use the template below. Every entry that references a run/job/external
   artifact MUST link to it with a full URL (Actions run URL, dashboard, etc.). State status
   plainly: dispatched / running / succeeded / failed / cancelled — quote real outcomes,
   never claim success you haven't seen.

4. **Keep it live.** When a tracked step changes state (run completes, validation passes,
   next phase dispatched), update the same comment. The log should always reflect current
   reality.

## Comment template

```markdown
## 📋 Off-PR work log

Surfacing work tied to this PR that lives outside the diff (CI / Actions / DB / external systems).

### <n>. <Step title> — <status emoji + word>
- **Run / artifact:** <full URL>
- **Command:** `<exact command or workflow + inputs>`
- **Why:** <one line — scope choice, safety rationale, etc.>
- **Result:** <what actually happened; quote counts/errors. Omit until known.>

<repeat per step>

_Last updated: <relative or absolute time>. I'll keep editing this thread as each step lands._
```

Status words: `dispatched`, `▶ running`, `✅ succeeded`, `❌ failed`, `⏹ cancelled`, `⏳ blocked`.

## Rules

- One log comment per PR. Edit it; don't create duplicates.
- Full URLs for every run/artifact — bare `#123` may resolve to the wrong repo on a
  cross-repo reference; use `https://github.com/<owner>/<repo>/...`.
- Report faithfully: a cancelled or failed run stays in the log with its real status, not
  quietly removed. If a step was skipped, say so.
- Don't leak secrets (connection strings, tokens) into the comment.
- Be terse. Each entry is a record, not prose.
