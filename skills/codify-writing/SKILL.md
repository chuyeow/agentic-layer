---
name: codify-writing
description: >-
  Retrospect on a prose editing or /live-review session and codify durable rules
  for the user's personal writing voice into their style guide. Turns the edits
  and inline comments from a session into graded, deduped style rules that compound
  across sessions. Triggers on: "/codify-writing", "codify my writing style",
  "learn my voice", "capture my edits", "what did I change and why", "improve the
  style guide", after a /live-review pass, or after editing markdown/HTML docs.
  Two tiers — voice (holds everywhere) and context (per medium: Jira, slides, PR,
  email). NOT for product code — this is only about how prose gets written. This is
  the learn half of the `/write` loop: it writes the durable rule back into
  `/write`'s `voice/` corpus, so the next `/write` draft is already better.
---

# Codify Writing — compound your voice, one editing pass at a time

Every edit you make to a draft and every `/live-review` comment you leave is a
signal about *your* voice. Left in the session, it evaporates and I re-make the
same mistake in the next draft. This skill captures those corrections while
they're freshest, decides which are worth codifying, and lands durable rules where
they belong — voice rules that hold on any draft in your master style guide,
context rules scoped to a medium. A cross-session **ledger** makes it compound: a
one-off edit becomes a tracked pattern that graduates to "codify now."

It is the **learn half** of the writing loop, paired with
[`/write`](../write/SKILL.md) (the draft half): `/write` reads the `voice/` corpus
to draft; you edit; this skill folds that edit back into the same corpus. So the
default destination for a landed rule is **`/write`'s `voice/` corpus** (see step 1),
not a blank guess.

Read `references/writing-contract.md` once before grading or landing — the two-tier
rule, the medium test, "real over imaginary", "ripe", and the validate/land
discipline. `$SKILL_DIR` below is this skill's own directory.

## When this fits

Run it at the **end of (or right after) a session** where you edited prose or ran
`/live-review` — that conversation is the richest input. Cold-start still works but
degrades to whatever prose diffs and the existing guide you can point it at.
**Not** for product code — this skill only governs how prose gets written.

## The loop

### 0. Preflight

```bash
command -v jq >/dev/null || { echo "codify-writing needs jq" >&2; exit 1; }
bash "$SKILL_DIR/scripts/ledger.sh" ledger-home   # → {ledger_dir, writable}
```

If `writable` is false (the ledger home isn't writable), warn that ledger writes
won't persist — the codification still runs, but recurrence tracking won't survive
the session. The ledger lives at `~/.agentic-layer/writing-ledger.jsonl` by default
(override with `$CODIFY_WRITING_DIR`).

### 1. Resolve the style-guide destination (so rules are durable)

**Default destination: the [`/write`](../write/SKILL.md) skill's `voice/` corpus** —
the operational guide `/write` actually reads. Resolve its path once (find the
`write` skill dir; it's a sibling of this one), then route by what the rule is:

- a **voice/context rule** (how to phrase, what to cut, register) → `write/voice/rubric.md`.
- an **anti-pattern / voice-true marker** (a blocklist item, or a "not blocked" positive like `imo`) → `write/voice/anti-patterns.md`.
- a **rare signature-level rule** that belongs at the very top of *everything* (e.g. "en-dashes, never em-dashes") → the user's global `~/.claude/CLAUDE.md` "Writing style" block, in addition.

Only ask the user for a path if the `write` corpus isn't reachable (e.g. running
outside this layer). Confirm the target before step 6; `$GUIDE` below is what you
resolve here.

### 2. Harvest — corrections first, then the existing guide

- **(a) This session's edits & comments (PRIMARY).** Reflect on what actually
  changed: every inline `/live-review` comment is an *explicit* correction (the
  strongest signal); every edit you accepted to a draft is a *preference*. Diff my
  draft against your final text and name each change concretely.
- **(b) The existing guide (corroboration + dedup).** Read `$GUIDE` (and any
  `plain-writing` rules) so you don't re-propose a rule already codified, and so you
  can spot a new edit that *contradicts* an old rule (surface the conflict).

### 3. Distill candidates

Each candidate = `{rule, tier, scope, grade, evidence}`. Turn a raw edit into a
**generalizable rule** — but per the contract, **don't over-generalize a single
edit**: one edit is `grade:suspected` until it recurs OR you stated it as an
explicit rule. Grade `real` only when a concrete observed edit/comment is cited in
`evidence.signal` — `ledger.sh append` refuses a `grade:real` with no signal (the
shared `evidence.sh` gate). Never invent a signal to clear the gate; downgrade to
`suspected` instead.

### 4. Classify each candidate (required)

Apply the medium test (`references/writing-contract.md`):
- **voice** (holds in any medium) → `tier:"voice"`, `destination` = `$GUIDE`.
- **context** (specific to a medium/audience) → `tier:"context"`, `scope` = the
  medium (e.g. `jira`, `slides`, `pr-body`, `email`), `destination` = that section.

Reclassify or split anything that fails the test — a medium quirk must never enter
the voice tier.

### 5. Record in the ledger

Append each candidate (one JSON object; dedup is by `.rule`, which bumps the
recurrence `count`):

```bash
echo '{"rule":"...","tier":"voice|context","scope":"...","destination":"...","severity":"high|med|low","grade":"real|suspected","fix":"...","evidence":{"session":"<id-or-date>","doc":"<file/title>","medium":"<where>","signal":"<the edit/comment observed — required when grade:real>"}}' \
  | bash "$SKILL_DIR/scripts/ledger.sh" append --from -

bash "$SKILL_DIR/scripts/ledger.sh" digest    # grouped by tier; RIPE flagged (count >= 2 OR high severity)
```

### 6. For each RIPE rule — validate, confirm, land

- **(a) Validate.** Re-apply the rule to the passage it came from **and at least one
  other sample** of the user's past prose; show the before/after. Optionally hand
  the rewrite to a fresh reviewer (a subagent with no context on the edit) to judge
  whether it still reads as the user's voice from the text alone. If it distorts
  meaning, fights an existing rule, or doesn't generalize →
  `ledger.sh mark <rule> deferred "<why>"` and stop.
- **(b) Confirm.** Show the exact edit to `$GUIDE` and get an explicit yes — this
  skill changes how I write *for you*.
- **(c) Land.** Append the rule to `$GUIDE` (voice section, or the context's
  section); `ledger.sh mark <rule> shipped`. Leave the edit uncommitted and offer
  to commit if `$GUIDE` is in a repo.

Never land without an explicit confirmation.

### 7. Report

Summarize: corrections harvested, ripe rules by tier, what landed/deferred where,
any contradictions surfaced, and the current `ledger.sh digest` — it prints each
rule's `evidence.signal`, so every `real` rule shows its observation and a
`suspected` hunch reads as unproven, never as an established rule.

## Scripts & references

| Path | Purpose |
|---|---|
| `scripts/ledger.sh` | `append` / `digest` / `list` / `mark` / `ledger-home` — the cross-session writing-style ledger (home-anchored at `~/.agentic-layer/writing-ledger.jsonl`; gitignored). Voice/context tiers, worktree-free. |
| `scripts/lib.sh` | ledger path + tier config; sources the vendored helpers below |
| `scripts/lib/lock.sh` | advisory file lock (`with_lock`) around ledger read-modify-write |
| `scripts/lib/dispatch.sh` | CLI usage / verb-dispatch helpers (`unknown_verb`) |
| `scripts/lib/evidence.sh` | the grade:real evidence gate — a `real` rule must carry `evidence.signal` |
| `references/writing-contract.md` | the two-tier rule, medium test, real-over-imaginary, ripe, validate/land |
