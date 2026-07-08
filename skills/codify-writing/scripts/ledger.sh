#!/usr/bin/env bash
# ledger.sh — the cross-session WRITING-STYLE ledger (JSONL, one object per line),
# home-anchored (see lib.sh) so it accumulates across every session and repo you
# edit prose in; gitignored local runtime state. Engine verbs: append / digest /
# list / mark / ledger-home, dedup-by-rule, the shared evidence gate. The tiers are
# voice|context, and it is worktree-free (you edit prose anywhere, not just inside
# one repo).
#
# This is what makes "learn from EVERY editing pass" work: each run appends, and
# dedup-by-`rule` turns a one-off correction into a tracked pattern with a
# recurrence count. A rule is RIPE (worth codifying now) when it recurs (count >= 2)
# OR is high-severity even once (you stated it as a hard rule).
#
# Verbs (bulk payloads via stdin/--from per house convention, never inline JSON):
#   append [--from <file|->]   merge an entry (dedup by .rule); stdin default
#   digest                     grouped-by-tier summary, ripe entries flagged
#   list                       raw ledger (one JSON per line)
#   mark <rule> <status> [note]   set status: open|ripe|validated|shipped|deferred|rejected
#   ledger-home                {ledger_dir, writable} — the home-anchored ledger dir
#                              + a write probe, so SKILL.md never re-derives the path
#
# Entry shape (append input): {rule, tier, destination, scope, severity, grade, fix,
#   validation, note, evidence:{session,doc,medium,signal}}.
#   tier ∈ voice|context. grade ∈ real|suspected (default suspected). A `real` rule
#   MUST carry evidence.signal (the observed edit/comment) — append refuses a
#   grade:real with no signal, via the shared evidence.sh. Record an unproven hunch
#   as `suspected`. Stored shape adds: id, first_seen, last_seen, count, status.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

now() { date -u +%FT%TZ; }
touch "$LEDGER"

cmd="${1:-digest}"
shift || true

case "$cmd" in
  append)
    src="-"
    case "${1:-}" in --from) src="${2:?--from needs a file or -}" ;; --from=*) src="${1#*=}" ;; esac
    raw="$(if [ "$src" = "-" ]; then cat; else cat "$src"; fi)"
    key="$(printf '%s' "$raw" | jq -r '.rule // empty')"
    [ -n "$key" ] || {
      echo "ledger append: entry needs a .rule" >&2
      exit 1
    }
    # Grade must be real|suspected, and a `real` rule must carry evidence (the
    # observed edit/comment) — you cannot record a guess as fact. `suspected` is the
    # honest label for an unproven candidate. Gated through the shared evidence.sh.
    grade="$(printf '%s' "$raw" | jq -r '.grade // "suspected"')"
    case "$grade" in real | suspected) ;; *)
      echo "ledger append: .grade must be real|suspected (got '$grade')" >&2
      exit 1
      ;;
    esac
    if ! printf '[{"id":%s,"grade":%s,"evidence":%s}]' \
      "$(jq -Rn --arg v "$key" '$v')" "$(jq -Rn --arg v "$grade" '$v')" \
      "$(printf '%s' "$raw" | jq -c '.evidence.signal // ""')" |
      bash "$SCRIPT_DIR/lib/evidence.sh" validate --status-field grade --evidence-when real --verify-when "" --label rule >/dev/null; then
      echo "ledger append: a grade:real rule needs evidence.signal (the edit/comment you observed). Mark it grade:suspected until you have it." >&2
      exit 1
    fi
    with_lock "$LEDGER_DIR/.lock"
    ts="$(now)"
    tmp="$LEDGER.tmp.$$"
    exists="$(jq -s --arg p "$key" 'any(.[]; .rule == $p)' "$LEDGER" 2>/dev/null || echo false)"
    if [ "$exists" = "true" ]; then
      # Recurrence: bump count + last_seen, refresh fields, append this evidence.
      jq -c --arg p "$key" --argjson new "$raw" --arg ts "$ts" '
        if .rule == $p then
          .count = ((.count // 1) + 1) | .last_seen = $ts
          | .severity = ($new.severity // .severity)
          | .grade = ($new.grade // .grade)
          | .tier = ($new.tier // .tier)
          | .destination = ($new.destination // .destination)
          | .scope = ($new.scope // .scope)
          | .fix = ($new.fix // .fix)
          | .evidence = ((.evidence // []) + (if $new.evidence then [$new.evidence] else [] end))
        else . end
      ' "$LEDGER" >"$tmp" && mv "$tmp" "$LEDGER"
    else
      # First sighting: create the row with count=1.
      cp "$LEDGER" "$tmp" 2>/dev/null || : >"$tmp"
      jq -nc --argjson new "$raw" --arg ts "$ts" '
        $new + { id: ($new.id // $new.rule), first_seen: $ts, last_seen: $ts,
                 count: 1, status: ($new.status // "open"),
                 evidence: (if $new.evidence then [$new.evidence] else [] end) }
      ' >>"$tmp"
      mv "$tmp" "$LEDGER"
    fi
    jq -c --arg p "$key" 'select(.rule == $p)' "$LEDGER" | tail -1
    ;;

  digest)
    if [ ! -s "$LEDGER" ]; then
      echo "ledger empty: $LEDGER"
      exit 0
    fi
    echo "WRITING LEDGER DIGEST  ($LEDGER)"
    for tier in $LEDGER_TIERS; do
      echo ""
      echo "== ${tier}-tier =="
      jq -rc --arg t "$tier" 'select(.tier == $t)
        | ((.count // 1) >= 2 or (.severity == "high")) as $ripe
        | ((.evidence // []) | last | .signal? // "") as $sig
        | "  [\(.status // "open")]\(if $ripe and (.status//"open"|test("shipped|deferred|rejected")|not) then " RIPE" else "" end) \(.rule)  (x\(.count // 1), \(.severity // "?"), \(.grade // "?"))  -> \(.destination // .scope // "?")\(if $sig != "" then "\n      evidence: \($sig)" else "" end)"' \
        "$LEDGER" 2>/dev/null || true
    done
    # Anything with an unknown/missing tier — surface so it can't hide.
    jq -rc --arg tiers "$LEDGER_TIERS" 'select(($tiers | split(" ")) as $t | ((.tier // "") | IN($t[]) | not))
      | "  [UNCLASSIFIED] \(.rule)"' "$LEDGER" 2>/dev/null || true
    ;;

  list) cat "$LEDGER" ;;

  ledger-home)
    # One resolution, owned by lib.sh (LEDGER_DIR) — reused here so the SKILL.md
    # flow and the ledger location cannot diverge.
    writable=false
    if [ -w "$LEDGER_DIR" ]; then writable=true; fi
    jq -nc --arg d "$LEDGER_DIR" --argjson w "$writable" '{ledger_dir:$d, writable:$w}'
    ;;

  mark)
    key="${1:?mark needs a <rule>}"
    status="${2:?mark needs a <status>}"
    note="${3:-}"
    with_lock "$LEDGER_DIR/.lock"
    tmp="$LEDGER.tmp.$$"
    jq -c --arg p "$key" --arg s "$status" --arg n "$note" --arg ts "$(now)" '
      if .rule == $p then .status = $s | .last_seen = $ts
        | (if $n != "" then .note = $n else . end) else . end
    ' "$LEDGER" >"$tmp" && mv "$tmp" "$LEDGER"
    jq -c --arg p "$key" 'select(.rule == $p)' "$LEDGER"
    ;;

  *) unknown_verb "$cmd" append digest list mark ledger-home ;;
esac
