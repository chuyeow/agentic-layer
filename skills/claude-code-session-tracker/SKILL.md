---
name: claude-code-session-tracker
description: Append unfinished Claude Code sessions to a tracker file so they can be resumed via `claude --resume "<session name>"`. Trigger when user signals ending ("done for now", "wrap up", "goodbye"), hits rate/context limit, or asks to save/track the session. Skip short one-offs, clean completions, or trivial Q&A.
---

# Claude Code Session Tracker

Tracks unfinished Claude Code sessions with the exact command to resume them, so work-in-progress never gets lost between sessions.

## Tracker file

Path is configurable:
- `$SESSION_TRACKER_PATH` env var (preferred), OR
- `~/Documents/claude-sessions-tracker.md` (default)

Create the file with `# Sessions` header if it doesn't exist. Entries are **prepended** (newest at top).

## Save or skip

**Save** when any apply:
- Multi-step work with unfinished next steps
- Rate/context limit hit, user paused mid-work
- Plan approved but not fully executed
- Deliverable partially written
- User explicitly says "save this" / "track this"

**Skip** (don't even ask):
- Short session (< ~5 turns) with clean answer
- Single factual question
- Trivial chore completed
- User got what they wanted ("thanks, done")

**Ask once if borderline**: "Save session to tracker? (y/n)"

## Session name + cwd lookup

Session metadata lives at `~/.claude/sessions/<pid>.json` with fields `sessionId`, `name`, `cwd`. Only exists while session process alive, so **this skill must run before the session ends**.

1. Get current session ID from latest jsonl in project dir:
   ```bash
   ls -t ~/.claude/projects/${PWD//\//-}/*.jsonl 2>/dev/null | head -1 | xargs basename | sed 's/\.jsonl$//'
   ```

2. Match against session files:
   ```bash
   jq -r 'select(.sessionId == "<SID>") | "\(.name)\t\(.cwd)"' ~/.claude/sessions/*.json 2>/dev/null | head -1
   ```

3. If `name` is `null` or empty: stop + tell user "Session unnamed. Run `/rename <short-title>` first, then re-invoke this skill."

## Entry format

Prepend new entry at top. Under 20 lines each.

```md
## YYYY-MM-DD — <session name>

**Resume**: `cd <cwd> && claude --resume "<session name>"`
**Objective**: <what user set out to do, 1 line>
**Summary**: <what happened, 1-2 sentences>

### Details
<progress, next steps, blockers — short bullets>

### Artifacts
- `path/to/file`
- https://url
```

Title = session name exactly (so user can grep).

## Execution

1. Decide save vs skip.
2. Get session ID → look up name + cwd.
3. If unnamed, stop + tell user to `/rename`.
4. Resolve tracker path (env var or default).
5. Read tracker (may be empty or have `# Sessions` header).
6. Prepend new entry.
7. Confirm: `Saved "<name>" → <tracker path>. Resume: cd <cwd> && claude --resume "<name>"`

Don't commit. Don't write elsewhere. If updating prior entry (same name), edit its Details in place instead of duplicating.

## Setup

To point the tracker at a custom location, set in your shell rc or `~/.claude/settings.json` env:

```bash
export SESSION_TRACKER_PATH="$HOME/my-notes/claude-sessions.md"
```

Or keep the default `~/Documents/claude-sessions-tracker.md`.
