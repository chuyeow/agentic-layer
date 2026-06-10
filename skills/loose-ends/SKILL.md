---
name: loose-ends
description: End-of-session cleanup sweep. Triggers when the user signals they're wrapping up — "what else to wrap up before I end", "wrap up", "done for now", "anything left", "before I end", "loose ends", "clean up". Sweeps for uncommitted/unpushed work, stale branches & worktrees, leftover files & dev processes, ssh-key state, unverified changes, and unsaved knowledge — auto-doing the safe checks, asking before anything that could lose work.
---

# Loose Ends

The pre-shutdown sweep. When the user is about to end a session, catch what gets left
behind: uncommitted work, half-merged branches, scratch files accidentally committed,
dev servers still running, an ssh-agent pointed at the wrong key, knowledge that should
have been written down.

This is NOT [[session-tracker]] (which saves *unfinished* work for `--resume`) nor a
handoff doc (which narrates the session). This is the janitorial pass that leaves the
machine and the repos in a clean state.

## When it fires

The user signals wrap-up. Real trigger phrases observed:
- "what else is there to wrap up before I end this session?"
- "wrap up" / "wrapping up" / "done for now" / "before I end"
- "anything left?" / "loose ends?" / "clean up?"

Don't fire mid-task or after every subtask — only when the user is genuinely closing out.

## The sweep

Run the read-only checks first (they're free), then sort findings into three tiers and
act per tier. Scope to what *this session* touched — don't go reorganizing repos the
user never opened.

### Tier 1 — AUTO (just do it, then report in one line)

Read-only inspection and reversible, no-data-loss actions:

- **Working tree:** `git status` — is it clean? Anything tracked-but-uncommitted, or
  untracked scratch that this session created?
- **Sync state:** `git rev-list --count HEAD..@{u}` and the reverse — ahead/behind upstream?
- **Branches & worktrees:** `git worktree list`, `git branch`. For a PR confirmed
  **merged** this session (`gh pr view <n> --json state,mergedAt`): remove its worktree
  (`git worktree remove <path>`) and delete the local branch (`git branch -d`). Remote
  branch usually auto-deletes on merge — verify, don't assume.
- **Fast-forward main:** if local `main` is behind origin and clean, `git pull --ff-only`
  (can't conflict, can't lose work).
- **CI / running jobs:** `gh run list` / `gh pr checks` — is anything still in flight?
- **Dev processes this session started:** kill the ones you launched. Check ALL of:
  - **Harness background tasks** — anything started with `Bash run_in_background` or
    `Monitor` (CI/PR poll loops, log tails, `until`/`while` watchers). These are NOT
    tmux. List them (`TaskList`) and `TaskStop` any still running — a poll loop whose
    break condition never matched (e.g. `gh run view <id>` without `-R`, returning empty)
    will spin forever. As a backstop, `pgrep -fl 'while :|sleep [0-9]|gh run view'` and
    kill stray watch loops this session spawned.
  - **tmux sessions & dev servers** you started (`tmux list-sessions`, the relevant
    `pkill -f`).
  Don't just check tmux — detached background tasks are the usual leftover, and they're
  invisible to `tmux list-sessions`.

### Tier 2 — ASK FIRST (surface it, propose the action, wait)

Anything that mutates shared state or could lose work:

- **Uncommitted changes** → show them; ask commit / stash / discard. Never decide for them.
- **Unpushed commits** → offer to push (push is fine if non-destructive and the user
  green-lit pushing this session); otherwise flag.
- **Unmerged / stale branches** → list; ask before `git branch -D` (force-delete loses commits).
- **Scratch/throwaway files that got committed** → e.g. a one-off diagnostic HTML swept
  into a commit. Flag it: "this was a throwaway — remove from the repo?" Don't silently delete.
- **Leftover build output / temp dirs** → mention; remove only if asked.
- **Full test suite / expensive verify** → offer; don't run unprompted (slow).
- **Processes you did NOT start, or env-var changes** → ask before touching.

### Tier 3 — INFO ONLY (report, no action)

- Optional idempotent re-runs available (e.g. a backfill that could fill gaps).
- Open browser/preview tabs left around.
- Anything genuinely the user's call with no safe default.

### Also consider

- **Verify gate** (per the user's standing rule): before declaring done, confirm
  lint / typecheck / tests / docs are green — or state plainly what's red/skipped.
- **Surface invisible work:** if PR-tied work happened outside the diff, the
  [[pr-work-log]] comment should be current.
- **Persist knowledge:** non-obvious facts learned this session (operational workflows,
  gotchas, constraints not derivable from code) → write to memory before context is lost.

## Autonomous mode

A `Stop` hook (`loose-ends-gate.sh`) enforces this skill: on a wrap-up signal in the
last user/assistant message it blocks the stop once per session and tells the agent to
run this sweep — so it fires whether a human typed "wrap up" or an autonomous agent
concluded on its own. No env var; mid-work (no signal) stays silent.

When there's no human in the loop, the Tier 2 "ask first" rule can't apply — there's no
one to ask. Resolve it as **safe-default-or-defer**:

- Do every Tier 1 AUTO action as normal.
- For Tier 2 items, take the **reversible, non-destructive** option yourself: commit
  and push completed work, etc. Never run a `git push --force`, `branch -D` of unmerged
  work, file deletion, or any irreversible op on your own judgement.
- For anything that *could* lose work or is irreversible, do **not** block waiting for
  input — leave it untouched and record a **flagged note** (handoff doc or [[pr-work-log]]
  comment) listing exactly what a human needs to decide.
- Then allow the stop. The gate fires once per stop-sequence (`stop_hook_active`), so the
  sweep runs exactly once before the session actually ends.

## Output shape

Lead with a one-line verdict ("Clean and synced — nothing blocking" or "3 things to
decide"). Then in bullet points: what you auto-handled (terse), what needs a decision (Tier 2, with a
proposed action each), and info-only notes last. Keep it scannable — the user is leaving.
