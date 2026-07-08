#!/usr/bin/env bash
# evidence.sh — the family's shared evidence-discipline validator (vendored: one copy
# in lib/, symlinked into each skill's scripts/). It is the GENERIC form of
# review-pr's post-review.sh rules 1-2: a claim labelled PROVEN must carry evidence,
# and a claim labelled UNPROVEN must carry a verify step — otherwise the emit/post is
# refused. Every skill that surfaces findings/verdicts/claims to the user or to a
# durable artifact (PR comment, issue body, report, ledger) pipes them through this
# BEFORE they land, so the fact/guess boundary is machine-enforced, not conventional.
# (review-pr keeps its own post-review.sh, which predates and inspired this.)
#
# Usage:
#   evidence.sh validate [opts]     # read a JSON array (or JSONL, or one object) on stdin
#     --status-field   <name>   trust-label field                 (default: status)
#     --evidence-field <name>   proof field: commands+output / [E?] / file:line
#                                                                 (default: evidence)
#     --verify-field   <name>   what would confirm/refute it      (default: verify)
#     --evidence-when  a,b,c    labels that REQUIRE evidence      (default: confirmed)
#     --verify-when    a,b,c    labels that REQUIRE a verify step (default: hypothesis)
#     --label          <text>   name for messages                (default: item)
#   Success  → echoes the input back as a JSON array on stdout (pass-through), exit 0.
#   Violation → prints each offending item to stderr, exit 3 (refuse: a labeling bug
#               is worse than a missing report). Usage error → exit 2.
#
#   evidence.sh block "<lead>"      # wrap stdin text in the house evidence block:
#                                   #   **<lead>**\n```\n<stdin>\n```
#
# House I/O contract: JSON on stdout, logs/errors on stderr, exit 0 ok / 2 usage /
# 3 evidence-violation.
set -euo pipefail
command -v jq >/dev/null 2>&1 || {
  echo '{"error":"evidence.sh needs jq"}' >&2
  exit 1
}

cmd="${1:-}"
shift || true
case "$cmd" in
  block)
    lead="${1:?usage: evidence.sh block \"<lead>\"  (text on stdin)}"
    body="$(cat)"
    printf '**%s**\n```\n%s\n```\n' "$lead" "${body%$'\n'}"
    exit 0
    ;;
  validate) : ;;
  *)
    echo "usage: evidence.sh validate [opts] | block \"<lead>\"" >&2
    exit 2
    ;;
esac

status_field="status" evidence_field="evidence" verify_field="verify"
evidence_when="confirmed" verify_when="hypothesis" label="item"
while [ $# -gt 0 ]; do case "$1" in
  --status-field)
    status_field="${2:?}"
    shift 2
    ;;
  --evidence-field)
    evidence_field="${2:?}"
    shift 2
    ;;
  --verify-field)
    verify_field="${2:?}"
    shift 2
    ;;
  --evidence-when)
    evidence_when="${2?--evidence-when needs a value ('' allowed)}"
    shift 2
    ;;
  --verify-when)
    verify_when="${2?--verify-when needs a value ('' allowed)}"
    shift 2
    ;;
  --label)
    label="${2:?}"
    shift 2
    ;;
  *)
    echo "evidence.sh validate: unknown option '$1'" >&2
    exit 2
    ;;
esac done

# comma lists → JSON arrays
to_json_arr() { jq -cn --arg s "$1" '$s | split(",") | map(select(length>0))'; }
ew="$(to_json_arr "$evidence_when")"
vw="$(to_json_arr "$verify_when")"

raw="$(cat)"
[ -n "${raw//[[:space:]]/}" ] || {
  printf '[]'
  exit 0
} # empty input = nothing to check

# Normalize stdin (array | JSONL | single object) → one JSON array.
items="$(printf '%s' "$raw" | jq -sc 'if (length==1 and (.[0]|type=="array")) then .[0] else . end')" ||
  {
    echo '{"error":"evidence.sh: stdin is not valid JSON"}' >&2
    exit 1
  }

violations="$(printf '%s' "$items" | jq -r \
  --arg sf "$status_field" --arg ef "$evidence_field" --arg vf "$verify_field" \
  --arg label "$label" --argjson ew "$ew" --argjson vw "$vw" '
  def blank($v):
    ($v == null)
    or (($v|type)=="string" and (($v|gsub("[[:space:]]";""))|length==0))
    or (($v|type)=="array"  and ($v|length)==0);
  to_entries[]
  | .key as $i | .value as $it
  | (($it[$sf]) // "" | tostring) as $st
  | (($it.id) // ($i|tostring)) as $id
  | ( if ($ew|index($st)) and blank($it[$ef])
        then "\($label) \($id) [\($st)]: labelled proven but \($ef) is empty — attach the evidence or relabel"
        else empty end),
    ( if ($vw|index($st)) and blank($it[$vf])
        then "\($label) \($id) [\($st)]: labelled unproven but \($vf) is empty — state what would confirm/refute it"
        else empty end)
')"

if [ -n "$violations" ]; then
  {
    echo "evidence.sh: refusing — findings violate evidence discipline:"
    printf '%s\n' "$violations" | sed 's/^/  ✘ /'
  } >&2
  exit 3
fi
printf '%s' "$items"
