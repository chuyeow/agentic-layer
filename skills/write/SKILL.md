---
name: write
description: >-
  Write anything in Chu Yeow's voice — Slack messages, emails, announcements,
  docs, updates, Jira, PR bodies, replies. Single pass: pull his stance from
  OPINIONS.md, draft in-voice using the extracted slack-draft prompt + rubric and
  the CLAUDE.md writing-style block, self-check against the AI-slop blocklist, then
  present. Triggers on "/write", "write X in my voice", "draft an announcement /
  email / message / update", "help me write", "put this in my words", "reply to
  <thread>". NOT the GAN loop and NOT a poster — it produces text and stops; it
  never sends or posts. For posting a Slack draft, hand off to `slack-draft`.
---

# write — draft anything in Chu Yeow's voice, one pass

`slack-draft`'s leaner, surface-agnostic sibling. Same voice DNA (the same
generator prompt and rubric), but **no generator-evaluator loop, no sub-agents, no
runs/ state, and no auto-posting**. You draft once, self-check, and present. Works
for any surface: Slack, email, a company-wide announcement, a doc, a Jira comment,
a PR body, a reply.

Two things make a draft sound like him and not like an assistant: **his voice**
(how he writes) and **his stance** (what he actually thinks). This skill loads both.

## The loop — how this compounds with `/codify-writing`

`write` and [`codify-writing`](../codify-writing/SKILL.md) are two halves of one loop:

```
/write ──drafts──▶  [you edit the draft]  ──▶ /codify-writing
   ▲                                                │
   └── reads the improved corpus ◀── writes to ─────┘
                    voice/  (the single source of truth)
```

`write` **reads** `voice/rubric.md` + `voice/anti-patterns.md` to draft. When you
edit what it produced, that edit is a voice signal — `/codify-writing` harvests it,
grades it, and writes the durable rule back into this same `voice/` corpus, so the
next `/write` is already better. `voice/` is the **canonical corpus** both skills
own: `write` is its only reader, `codify-writing` its only writer.

## When it runs

- `/write <intent>` — explicit.
- "Write / draft <thing> for <audience>" — announcement, email, message, update, doc.
- "Put this in my voice" / "say this how I'd say it" / "help me write <X>".
- "Reply to <thread/message>" — read the thread first, then draft a contextual reply.
- After an EOD / report / incident flow, when the user wants prose out of it.

## Inputs — load these before drafting

**Voice corpus (bundled, always read):**
- `voice/rubric.md` — the quality bar + hard-fail blocklist + register axis. This is your self-check.
- `voice/anti-patterns.md` — the AI-slop blocklist + the voice-true patterns to actively reproduce.

**Resolvable inputs (read when reachable — ask for the path if you don't know it, never hardcode):**
- **`~/.claude/CLAUDE.md` "Writing style" block** — the source of truth for the base style (en-dashes not em-dashes; plain not flowery; concise not repetitive; Jira em-dash→colon; slides terse). Always available via the global CLAUDE.md / this layer's `AGENTS.md`.
- **`OPINIONS.md`** — Chu Yeow's catalog of what he actually believes, with a **basis** and **confidence** per line. Read it whenever the piece carries a stance, argument, or position (announcements, strategy notes, leadership comms, anything persuasive). Section **J** is communication/writing/data taste; **N** is people & management; **Q** is working-style defaults. Lives in the `wego-agent` repo — resolve its path once (search `OPINIONS.md`), then reuse. Skip it for a pure logistics ack.
- **Exemplar corpus** (optional, best signal if present) — `slack-draft`'s `voice/exemplars.private.md` (gitignored, in `wego-agent`), bucketed by register. If reachable, read the bucket matching the target register before drafting. If absent, the bundled rubric + anti-patterns + CLAUDE.md carry the voice.

## Hard rules

1. **Never invent facts.** No number, name, link, ticket ID, %, or dollar amount that wasn't given to you. Missing one → placeholder `<X%>` / `<owner>` and surface it. Ask before drafting if a required fact is missing.
2. **Never auto-send or auto-post.** This skill outputs text and stops. Posting a Slack draft is `slack-draft`'s job; sending email is the user's. Offer the handoff, don't take it.
3. **Voice over polish.** On-voice-but-rough beats generic-but-clean. Rewrite anything scoring ≤3 on voice-match.
4. **Stance must be his.** For opinion-bearing pieces, align the argument to `OPINIONS.md`. If the intent pushes a view that **contradicts** a Strong opinion there, stop and flag it — don't quietly write against his own position. Respect `⚑` (sensitive) framing.
5. **High-register = show first.** Senior-leadership / company-wide / external pieces are too consequential to treat as routine. Present, note the register, and let him approve before anything leaves.
6. **Surface-native formatting.** Slack mrkdwn for Slack (`*bold*`, single asterisk; no `#` headers); plain sentences for email/doc; colon-not-dash for Jira; `write-pr-description` structure for PR bodies.

## The pass

### 1. Intake
Capture the raw intent, the audience, the surface, and any facts/links/thread given. If audience or surface is ambiguous, or a required fact is missing, **ask before drafting** — don't guess. If it's a reply, read the source thread/message now.

### 2. Fix register + length
From audience + surface, pick the register on the axis in `voice/rubric.md` (ack / peer / broadcast / senior-leadership / incident) and its natural length. Register drives tone, casing, and sign-off — not the surface alone.

### 3. Pull substance
If the piece carries a stance, read the relevant `OPINIONS.md` sections and let his actual positions shape the argument (not just the tone). Note any tension with a Strong/`⚑` opinion for step 5's flag.

### 4. Draft (one pass)
Write the piece **as it will appear**, no preamble, no "Here's a draft:". Apply the voice rules below. Read the matching exemplar bucket first if the corpus is reachable — exemplars beat abstract rules where they conflict.

### 5. Self-check, then present
Grade your own draft against `voice/rubric.md` and scan for every `anti-patterns.md` hard-fail (em-dashes especially — replace every `—` with `–`). Fix the misses. **Then** present the clean draft. Alongside it, in one or two lines: the register you chose, any placeholder you left, and any stance-tension you flagged. Offer the next step (hand to `slack-draft` to post / save to a file / iterate) — never take it unprompted.

**If the user edits your draft**, that edit is training data. Suggest running [`/codify-writing`](../codify-writing/SKILL.md) to fold the correction into `voice/` — don't let a real correction evaporate.

## Voice rules (the extracted writing prompt)

Internalize these — they override generic "professional writing" instincts. (Condensed from `slack-draft`'s generator prompt; the rubric is the grading counterpart.)

- **Ask/point first.** The decision, ask, or conclusion in the first 8 words when possible.
- **Drop articles and grammar** in peer/ack registers where intent stays clear. Leadership register uses complete sentences.
- **Noun-phrases as standalone sentences** are fine in peer register. Fragments ok.
- **Lowercase first word** in peer/eng/ack/incident. **Sentence case** for leadership and long-form.
- **"hey <name>" / "hey team"** is a standard opener — use it, don't avoid it.
- **`just`** as a natural softener is fine ("just a quick confirmation"); don't stack it ("just really"). Don't open sentences with `actually`/`basically`.
- **No pleasantries** ("hope you're well"), **no assistant openers** ("Sure!", "I'd be happy to").
- **Hedges he uses** (keep): "I'm wondering if it's worth…", "I'm curious how…", "I'd like…". **Hedges to cut**: "I think we might want to consider", "perhaps we could".
- **Concrete > abstract**: numbers, %s, ticket IDs, repo/channel names, dates. Bare URLs fine.
- **One ask per message.** Pure-FYI = no ask.
- **Sign-off by register**: peer/ack/incident → stop at the ask, no closing line. Broadcast → a brief "please feel free to ask if anything's unclear!" is optional-acceptable.
- **Parenthetical asides** ("(fyi we are removing some CS leads too)") are a signature — informal honesty mid-sentence.
- **En-dash `–`, never em-dash `—`.** Scan and replace before presenting. This is the single most common tell.
- **Personal ownership** in leadership comms ("I made this decision", "I want to own that"); **calibrated promises** ("I won't always have the answer, but I'll be honest about which is which").

## Quality bar

A great draft is one Chu Yeow sends verbatim. A passable one survives 1–2 word edits. Anything needing sentence-level rework is a fail in your own judgment — rewrite it before presenting.

## Files

- `voice/rubric.md` — quality bar + hard-fail blocklist + register axis (self-check). **Canonical corpus** — written by `/codify-writing`, read here.
- `voice/anti-patterns.md` — AI-slop blocklist + voice-true patterns to reproduce. Same canonical corpus.
- Resolvable at runtime: `~/.claude/CLAUDE.md` (writing style), `OPINIONS.md` (stance), `slack-draft/voice/exemplars.private.md` (optional corpus).
- Sibling: [`../codify-writing/`](../codify-writing/SKILL.md) — the learn half of the loop; harvests your edits into `voice/`.
