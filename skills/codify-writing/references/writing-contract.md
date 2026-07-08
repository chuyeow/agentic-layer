# The writing-codification contract

The rules that keep `codify-writing` from polluting your style guide with
one-off preferences dressed up as laws. Read this before grading or landing anything.

## The two tiers (the core discipline)

Every rule is **exactly one** of:

- **voice-tier** — true of *your* prose regardless of medium, audience, or length.
  Lands in the **master style guide** (the durable home you resolve at step 1).
  Example: *"en-dashes, never em-dashes"* — holds in a Slack message, a PRD, and a
  blog post alike.
- **context-tier** — depends on *this* medium, audience, or channel. Lands in that
  context's **own section** of the guide. Example: *"Jira: em-dash → colon"* or
  *"slides are terse — verbalized live, not read literally"* — only true for that
  surface.

Why the split matters: a voice rule is a standing instruction applied to every
draft, so a context-specific quirk that leaks in becomes a wrong default
everywhere (turning every Slack message into slide-terse fragments). Keeping the
voice tier medium-agnostic is what lets it be trusted on any draft; context facts
belong with their surface so the next draft there starts already correct.

### The medium test (apply to every candidate)

Ask: *"Would this rule still be right in a totally different medium — a text
message, a formal doc, a landing page?"*
- **Yes** → voice-tier.
- **No** → context-tier.
- **Reclassify, don't force.** If a candidate you called "voice" smuggles in a
  medium/audience specific, it is context-tier — or **split** it: the *general
  principle* is voice-tier, the *specific rendering* is context-tier. (E.g. "prefer
  a clean separator over a dash" is voice; "in Jira that separator is a colon" is
  the context value.) A voice rule that can't be stated medium-agnostically does
  not enter the master guide.

## Real over imaginary

Only codify rules for preferences with **real evidence** in the ledger. A change
you actually made to a draft, a `/live-review` comment you actually left, or a rule
you explicitly stated is real. A stylistic preference you *assume* the user holds
but never observed is not — do not codify it. Evidence lives in each ledger entry's
`evidence[]`; the correction itself (the *why*) is the strongest evidence, the
recurrence count corroborates.

**Don't over-generalize a single edit.** One edit ("cut *basically* here") is a
data point, not yet a law — it's `suspected` until it recurs across drafts OR you
state it as a rule ("I never want hedging words"). Promoting one edit into a
sweeping rule is the prose equivalent of building for imaginary friction: it makes
the guide confidently wrong.

## Ripe = worth codifying now

A rule is **ripe** when `count >= 2` (the same correction recurred across sessions)
**OR** `severity == "high"` (you stated it as a hard rule, so one occurrence is
enough). Until ripe, a candidate just accumulates in the ledger — codifying
premature one-offs is how a style guide bloats into contradictions no one follows.

## Validate before codifying

A rule lands only after a **concrete** check shows it's genuinely your voice and
doesn't distort meaning:
- **re-apply it to the passage it came from AND to at least one other sample** of
  your past prose, and
- **show the before/after** and confirm it reads as *you* — not a mechanical
  rewrite that flattens intent.

If applying the rule changes meaning, fights another rule already in the guide, or
you can't confirm it generalizes, `mark deferred` with the evidence rather than
codifying a half-right rule. A rule that only works on the one sentence it came
from is context-tier at best, noise at worst.

## Durable destination, human confirms

- voice-tier → the master style guide you resolved at step 1 (never hardcode a
  path — ask when unknown).
- context-tier → that medium's section of the same guide.
- Neither is silently written, and **every landing is confirmed by you first** —
  this skill edits how I write *for you*, so it asks before each change.
