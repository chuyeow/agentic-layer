---
name: live-review
description: Review an HTML file from Claude with inline comments. Spins up a Claude Code custom channel that serves the HTML with a commenting widget; the reviewer's comments are pushed into a dedicated reviewer Claude session that edits the file and replies in-page. Use when the user produces or has an HTML report/draft/output and wants to comment on it, mark it up, or iterate on it visually — triggers on "review this HTML", "let me comment on", "open for review", "live review", or finishing a draft HTML file. Also triggers whenever the user asks to "create an HTML" (or build/generate/make an HTML file/page/report): after producing it, proactively SUGGEST opening it in live-review — offer the command, don't auto-launch.
allowed-tools: Bash
---

# live-review

Turn any HTML file Claude produced into a commentable draft. Select text or hover a
block → leave a comment → a dedicated reviewer Claude edits the file and replies in the
page. Built on a Claude Code **custom channel**.

## How to run

```bash
bash ~/.claude/skills/live-review/start.sh /abs/path/to/output.html
```

That single command: installs deps (first run), launches a **second `claude` session in
tmux** with the channel loaded, auto-confirms the dev-channels prompt, serves the file
with the comment widget injected, and opens the browser. It prints the viewer URL and the
tmux session name.

Then tell the user:
- Open the viewer URL (also opened automatically).
- **Comment**: select any text (the passage stays highlighted; a ⧉ Copy button is in the
  form), or hover a block and click the ＋. Type, Send.
- Each comment is pushed to the reviewer session, which **edits the HTML and replies
  in-page** (the viewer hot-reloads on every edit).
- Watch the reviewer work: `tmux attach -t <session>` (detach: Ctrl-b then d).

Re-running on the same file reuses its session/port and just reopens the browser.

## When to invoke

Invoke this skill when the user produces an HTML report/dashboard/draft and wants to
review, annotate, or iterate on it — or asks to "open it for review" / "let me comment".
Pass the absolute path of the HTML file as the only argument.

## Suggest after creating HTML (don't auto-launch)

When the user asks to **create / build / generate / make an HTML** file, page, or report,
do the creation as normal — then **offer** live-review; do not start it unprompted. After
writing the file, add a one-liner like:

> Want to comment on this live? `bash ~/.claude/skills/live-review/start.sh <abs-path>` —
> opens it in the browser with inline commenting; I'll edit + reply to your notes.

Only run `start.sh` if the user says yes. Rationale: spinning up a tmux + `claude`
reviewer session is heavyweight and shouldn't fire on every HTML you produce — the user
decides when a draft is worth reviewing. (For true auto-launch on file write, see the
opt-in PostToolUse hook below.)

## Important: what is and isn't automatable

A Claude Code channel can only be loaded **at session startup** — a running session
cannot turn itself into a channel receiver. So:

- ✅ **Fully scripted spin-up.** The skill launches everything with no manual steps.
- ⚠️ **The reviewer is a *separate* Claude** (the tmux session), not the session you
  invoked the skill from. This is by design and keeps your main chat free.
- ⚠️ Uses `--dangerously-load-development-channels` (channels are a research preview,
  Claude Code v2.1.80+). Auto-confirm of that prompt is best-effort via tmux send-keys;
  if the prompt wording changes, attach to the session and press Enter once.
- 🔒 **Default keeps you in the loop**: the reviewer session prompts before each edit /
  reply — attach to the tmux session to approve. For hands-off auto-apply (edits applied
  without prompting), run with `LR_AUTO=1 bash start.sh <file>` — only for HTML you trust.

Requires: `bun`, `tmux`, `claude` on PATH.

## Stopping & listing

```bash
bash ~/.claude/skills/live-review/start.sh --stop <file.html>   # tear down session + free port
bash ~/.claude/skills/live-review/start.sh --list               # list active review sessions
```

Comments persist in the skill's own `.run/` dir (keyed by a hash of the target path), so
stopping and restarting keeps the panel — and nothing is ever written into the directory
of the file under review.

## Resolved comments

The reviewer's `reply` tool takes an optional `resolved` flag. When Claude has fully
addressed a comment (made the edit or answered the question), it replies with
`resolved: true`; the widget then greys + strikes that comment and flips its in-page
marker to ✓. Open comments stay highlighted so the loop is visually closed.

If the reviewer rewords the exact block a comment was anchored to, the widget re-finds it
by the quoted passage; if it can't, the comment shows `⚠ moved` rather than silently
detaching.

## Optional: auto-trigger on draft HTML (opt-in hook)

To spin up review automatically whenever Claude writes a draft HTML file, add a
PostToolUse hook to `~/.claude/settings.json`. It only fires on files whose name contains
`draft` (adjust the grep to taste) so it doesn't launch on every HTML write:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "f=$(jq -r '.tool_input.file_path // empty'); case \"$f\" in *draft*.html) nohup bash ~/.claude/skills/live-review/start.sh \"$f\" >/dev/null 2>&1 & ;; esac"
          }
        ]
      }
    ]
  }
}
```

Leave this out if you prefer to invoke review explicitly — auto-launching a tmux+claude
session on every matching write is intentionally aggressive.

## Files

- `start.sh` — orchestrator (launch / reuse / open).
- `channel.ts` — the channel MCP server: serves the target HTML with the widget injected,
  pushes comments as `<channel>` events, exposes the `reply` tool, hot-reloads, persists,
  CSRF-gated.
- `assets/widget.js` / `assets/widget.css` — the comment overlay injected into any page.
