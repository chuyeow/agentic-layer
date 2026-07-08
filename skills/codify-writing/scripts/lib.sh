#!/usr/bin/env bash
# Shared helpers for the codify-writing skill. Source this; don't execute it.
#
# codify-writing harvests the corrections you made in an editing / live-review
# session, grades them, and lands durable VOICE rules in your style guide. The
# cross-session LEDGER is HOME-anchored — not tied to this skill's install path —
# so it accumulates across every session and every repo you edit prose in. The
# skill dir is symlinked into ~/.claude/skills and copied into ~/.codex/skills;
# a path relative to the script would put the ledger in a different place for each
# install (and each repo you invoke from), so we pin it to $HOME instead. Override
# with $CODIFY_WRITING_DIR.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Vendored family helpers — real files inside this skill (never cross-skill
# symlinks), so the whole skill dir ports, copies, and symlinks as one unit.
# shellcheck source=lib/lock.sh
source "$SCRIPT_DIR/lib/lock.sh" # with_lock
# shellcheck source=lib/dispatch.sh
source "$SCRIPT_DIR/lib/dispatch.sh" # usage_exit / need / unknown_verb (exit 2 on usage)

# Durable, cross-session ledger — home-anchored so it survives reinstalls and is
# the SAME file whether the skill runs from the ~/.claude symlink or the ~/.codex
# copy, and no matter which repo you're editing prose in.
LEDGER_DIR="${CODIFY_WRITING_DIR:-$HOME/.agentic-layer}"
# shellcheck disable=SC2034  # consumed by ledger.sh, which sources this lib
LEDGER="$LEDGER_DIR/writing-ledger.jsonl"
# The two tiers of a prose rule (see references/writing-contract.md). Overridable
# so the ledger engine stays domain-agnostic; the digest/unclassified checks read it.
# shellcheck disable=SC2034
LEDGER_TIERS="${LEDGER_TIERS:-voice context}"
mkdir -p "$LEDGER_DIR"
