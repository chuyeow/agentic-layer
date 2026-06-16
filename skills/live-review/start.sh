#!/usr/bin/env bash
# live-review: spin up a Claude Code channel session that serves an HTML file with a
# comment widget, and handles comments by editing the file + replying in-page.
#
#   start.sh /abs/path/to/output.html
#
# Fully scripted: launches a SECOND `claude` session in tmux (channels can only load at
# startup, so the reviewer loop is a separate Claude instance — by design), auto-confirms
# the dev-channels prompt, opens the browser. Prints the tmux session name + viewer URL.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"
[ -z "$TARGET" ] && { echo "usage: start.sh <file.html>"; exit 1; }
TARGET="$(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"   # absolutize
[ -f "$TARGET" ] || { echo "no such file: $TARGET"; exit 1; }
DIR="$(dirname "$TARGET")"

# deps
[ -d "$SKILL_DIR/node_modules/@modelcontextprotocol" ] || ( cd "$SKILL_DIR" && bun install >/dev/null 2>&1 )

# stable port + session per file (re-running the same file reuses them)
H=$(echo -n "$TARGET" | cksum | cut -d' ' -f1)
PORT=$(( 4300 + H % 200 ))
SESSION="lr-$(basename "${TARGET%.*}" | tr -c 'a-zA-Z0-9' '-' | cut -c1-24)"

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
  "env": { "TARGET": "$TARGET", "PORT": "$PORT", "LR_DIR": "$SKILL_DIR" } } } }
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
for i in $(seq 1 12); do
  sleep 1.5
  P="$(tmux capture-pane -t "$SESSION" -p 2>/dev/null || true)"
  echo "$P" | grep -q "Channels (experimental)" && break
  echo "$P" | grep -Eq "development channels|Use this MCP|trust|❯ 1|Yes" && tmux send-keys -t "$SESSION" Enter
done

# nudge the reviewer session into action (channel instructions already loaded)
tmux send-keys -t "$SESSION" "Ready. Watch for live-review comments and handle each per your channel instructions." Enter
sleep 1; tmux send-keys -t "$SESSION" Enter

open "http://localhost:$PORT" 2>/dev/null || true
echo "live-review up"
echo "  file:    $TARGET"
echo "  viewer:  http://localhost:$PORT"
echo "  session: $SESSION   (attach: tmux attach -t $SESSION)"
