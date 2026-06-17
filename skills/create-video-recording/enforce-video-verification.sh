#!/usr/bin/env bash
# PreToolUse(Bash) gate: require a fresh video manifest before `gh pr create`
# when the current diff touches visible UI/report files.

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
node "$script_dir/scripts/check_pr_verification.mjs"
