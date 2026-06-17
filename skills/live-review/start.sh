#!/usr/bin/env bash
# live-review: spin up a Claude Code channel session that serves an HTML file with a
# comment widget, and handles comments by editing the file + replying in-page.
#
#   start.sh /abs/path/to/output.html     # start (or reopen) a review
#   start.sh --stop  /abs/path/to/file    # tear down that review (session + port)
#   start.sh --list                       # list active review sessions
#
# Fully scripted: launches a SECOND `claude` session in tmux (channels can only load at
# startup, so the reviewer loop is a separate Claude instance — by design), auto-confirms
# the dev-channels prompt, opens the browser. Prints the tmux session name + viewer URL.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# stable session name + port per target file (re-running the same file reuses them)
sid()   { echo "lr-$(basename "${1%.*}" | tr -c 'a-zA-Z0-9' '-' | sed -E 's/-+/-/g' | cut -c1-24 | sed -E 's/-+$//')"; }
sport() { echo $(( 4300 + $(echo -n "$1" | cksum | cut -d' ' -f1) % 200 )); }
abspath() { echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; }

case "${1:-}" in
  --list)
    echo "active live-review sessions:"
    tmux ls 2>/dev/null | grep '^lr-' || echo "  (none)"
    exit 0 ;;
  --stop)
    f="${2:-}"; [ -z "$f" ] && { echo "usage: start.sh --stop <file.html>"; exit 1; }
    f="$(abspath "$f")"; s="$(sid "$f")"; p="$(sport "$f")"
    tmux kill-session -t "$s" 2>/dev/null && echo "stopped session $s" || echo "no session $s"
    lsof -ti:"$p" 2>/dev/null | xargs kill 2>/dev/null && echo "freed port $p" || true
    exit 0 ;;
esac

TARGET="${1:-}"
[ -z "$TARGET" ] && { echo "usage: start.sh <file.html> | --stop <file> | --list"; exit 1; }
TARGET="$(abspath "$TARGET")"
[ -f "$TARGET" ] || { echo "no such file: $TARGET"; exit 1; }
DIR="$(dirname "$TARGET")"

# deps
[ -d "$SKILL_DIR/node_modules/@modelcontextprotocol" ] || ( cd "$SKILL_DIR" && bun install >/dev/null 2>&1 )

PORT="$(sport "$TARGET")"
SESSION="$(sid "$TARGET")"

# already running for this file? just reopen.
if tmux has-session -t "$SESSION" 2>/dev/null && curl -s -o /dev/null "http://localhost:$PORT/_lr/whoami"; then
  echo "already running · session=$SESSION · http://localhost:$PORT"; open "http://localhost:$PORT" 2>/dev/null || true; exit 0
fi
lsof -ti:"$PORT" 2>/dev/null | xargs kill 2>/dev/null || true
tmux kill-session -t "$SESSION" 2>/dev/null || true

# per-run MCP config pointing at the channel server, with TARGET/PORT in env
RUN="$SKILL_DIR/.run"; mkdir -p "$RUN"
CFG="$RUN/$SESSION.mcp.json"
cat > "$CFG" <<JSON
{ "mcpServers": { "live-review": { "command": "bun", "args": ["$SKILL_DIR/channel.ts"],
  "env": { "TARGET": "$TARGET", "PORT": "$PORT", "LR_DIR": "$SKILL_DIR", "SESSION": "$SESSION" } } } }
JSON

# By default the reviewer session asks before each edit/tool use — attach to approve, so
# a human stays in the loop. Opt in to hands-off auto-apply (edits applied without
# prompting) ONLY for HTML you trust, by exporting LR_AUTO=1.
AUTO_FLAGS=""
if [ "${LR_AUTO:-0}" = "1" ]; then
  AUTO_FLAGS="--permission-mode acceptEdits --allowedTools mcp__live-review__reply"
  echo "⚠️  LR_AUTO=1 — reviewer will auto-apply edits without prompting."
fi

tmux new-session -d -s "$SESSION" -x 220 -y 50 -c "$DIR"
tmux send-keys -t "$SESSION" \
  "claude --mcp-config '$CFG' --dangerously-load-development-channels server:live-review --add-dir '$DIR' $AUTO_FLAGS" Enter

# auto-confirm startup prompts (best-effort), wait for the channel to register
for _ in $(seq 1 12); do
  sleep 1.5
  P="$(tmux capture-pane -t "$SESSION" -p 2>/dev/null || true)"
  echo "$P" | grep -q "Channels (experimental)" && break
  # only confirm the two specific startup prompts — don't blanket-Enter arbitrary screens
  echo "$P" | grep -Eq "I am using this for local development|New MCP server found|Use this MCP server" && tmux send-keys -t "$SESSION" Enter
done

# nudge the reviewer session into action (channel instructions already loaded)
tmux send-keys -t "$SESSION" "Ready. Watch for live-review comments and handle each per your channel instructions." Enter
sleep 1; tmux send-keys -t "$SESSION" Enter

open "http://localhost:$PORT" 2>/dev/null || true
echo "live-review up"
echo "  file:    $TARGET"
echo "  viewer:  http://localhost:$PORT"
echo "  session: $SESSION   (attach: tmux attach -t $SESSION)"
