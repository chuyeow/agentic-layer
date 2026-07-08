#!/usr/bin/env bash
# dispatch.sh — shared CLI usage / verb-dispatch helpers. SOURCE this (don't execute);
# defines functions only, sets no shell options, runs no top-level code.
#
# House I/O contract (AGENTS.md): machine output is JSON on stdout, logs/human text
# and errors on stderr, exit 0 ok / 1 runtime / 2 usage. The concise `${N:?msg}` idiom
# self-documents a required arg but bash fixes a `:?` failure's status at 1, so a script
# that must honor "usage = 2" parses args explicitly and calls these helpers.
#
# API:
#   usage_exit <msg...>            → print <msg> to stderr, exit 2 (usage error).
#   need <val> <msg...>            → exit 2 with <msg> when <val> is empty (required arg).
#   unknown_verb <verb> [known...] → verb-dispatch failure: name the bad verb + the
#                                    accepted set, to stderr, exit 2.

# usage_exit <msg...>
usage_exit() {
  printf '%s\n' "$*" >&2
  exit 2
}

# need <value> <msg...> — e.g.  need "${1:-}" "usage: foo.sh <bar>"
need() { [ -n "${1:-}" ] || usage_exit "${*:2}"; }

# unknown_verb <verb> [known-verb ...]
unknown_verb() {
  local verb="${1:-}"
  shift || true
  printf 'unknown verb: %s\n' "$verb" >&2
  [ "$#" -gt 0 ] && printf 'expected one of: %s\n' "$*" >&2
  exit 2
}
