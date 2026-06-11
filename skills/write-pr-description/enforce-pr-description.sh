#!/usr/bin/env bash
# PreToolUse(Bash) gate: enforce the pr-description skill's structure when a PR
# is opened or its body edited. Blocks (exit 2) when the body is missing any of
# the required sections, feeding the reason back to the model. Fails open on
# anything it can't inspect (body-from-file, --fill, template, --web).
#
# Required sections (exact headings): "## Why", "## What changed", "## Verification".
# Pairs with ~/.claude/skills/pr-description/SKILL.md.

set -euo pipefail

input="$(cat)"

# Pull the command string out of the tool input. Prefer jq; fall back to raw.
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
else
  cmd="$input"
fi
[ -z "$cmd" ] && cmd="$input"

# Only police PR-body-bearing commands. Anchor the match to a command
# position — start of string or right after ; & | ( — so text that merely
# mentions the command (a commit message, a heredoc) doesn't trip the gate.
if [[ "$cmd" =~ (^|[\;\&\|\(][[:space:]]*)gh[[:space:]]+pr[[:space:]]+create ]]; then
  :
elif [[ "$cmd" =~ (^|[\;\&\|\(][[:space:]]*)gh[[:space:]]+pr[[:space:]]+edit ]]; then
  # edit only matters when it sets a body
  case "$cmd" in *"--body"*) ;; *) exit 0 ;; esac
else
  exit 0
fi

# Fail open when the body isn't inline / isn't ours to judge.
case "$cmd" in
  *"--help"*|*"--web"*|*"--fill"*|*"--fill-first"*|*"-F "*|*"--body-file"*|*"--template"*)
    exit 0 ;;
esac

missing=()
grep -Fq '## Why'          <<<"$cmd" || missing+=('## Why')
grep -Fq '## What changed' <<<"$cmd" || missing+=('## What changed')
grep -Fq '## Verification'  <<<"$cmd" || missing+=('## Verification')

if [ "${#missing[@]}" -ne 0 ]; then
  printf 'PR description blocked — missing required section(s): %s\n' "${missing[*]}" >&2
  cat >&2 <<'MSG'

Follow the `write-pr-description` skill. The body must have, in order:
  ## Why            — the change's purpose / user impact (no internal issue refs)
  ## What changed   — a table of the changes (one row each)
  ## Verification   — the actual before/after RESULT a reviewer can eyeball

Rules: write only context useful to a reviewer; no session-local references
(e.g. "#2", "the second gap") that mean nothing on the PR; show verification
results, not instructions to verify.
MSG
  exit 2
fi

exit 0
