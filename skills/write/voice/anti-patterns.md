# Anti-patterns — AI slop blocklist

Patterns to hard-avoid in any draft. Calibrated against a real 180d Slack corpus pull. If a pattern appears in the real corpus, it is NOT in this blocklist — that means Chu Yeow actually uses it. (Extracted from the `slack-draft` skill; kept in sync manually.)

Hard-fails = rewrite the span before presenting the draft. Soft-warns = fix if cheap, note if not.

## Hard-fail openers (assistant tone)

- "Sure!" / "Of course!" / "Certainly!" / "Absolutely!" — exclamatory **assistant openers** at start of message. (Peer reactions like "Woah halved the time" / "Nice." / "lol yes" appear in the real corpus and are voice-true — they are NOT this pattern.)
- "I'd be happy to..." / "Happy to help with..."
- "I hope you're doing well" / "Hope you had a good weekend" / "Hope this finds you well"
- "Quick question:" when message is not actually quick

**Not blocked** (real corpus shows usage):
- `hey <@name>` / `hey team` / `Hey team,` / `Hey if any...` — peer + broadcast opener; lowercase in thread replies, Sentence case for top-of-channel broadcasts
- `Hi team <@engineers>,` — leadership broadcast opener
- `sorry guys` — apologetic opener in close-team peer register
- `Important note:` — leadership scoping opener
- `lol yes` / `Woah` / `Nice.` / `Will do ser` — peer enthusiasm reactions (NOT assistant-tone)

## Voice-true patterns to actively reproduce (positives, not anti-patterns)

These appear in the real corpus as recurring signatures. The generator should *include* these where natural:

- **Question-stacking**: 2-4 sequential questions to propose / probe instead of "we should do X"
- **Mid-sentence parenthetical with concrete detail**: "(error msg: '...')", "(fyi we are removing some CS leads too)"
- **Group-mention routing**: ping the right `<@*-geeks>` / `<@engineers>` / `<@*-leads>` group
- **"only if quick one for you, <name>"** politeness when asking favors
- **Personal ownership in leadership comms**: "I made this decision", "I want to own that", "I'd rather you ask me directly"
- **Section labels inline** for long-form: "Why:", "What's next", "What I'd ask of you." — no markdown headers
- **Calibrated promises in high-stakes**: "I won't always have the answer, but I will be honest about which is which"
- **Co-mention**: `Cc <@person> for cost visibility` as concise FYI
- **Deprioritization signature**: "this can wait, low priority vs your other tasks" — when the ask is real but not urgent
- **Collaborative-amendment style**: "I agree with this rubric. I'd just upgrade a few points:" — add to others' work rather than rewriting
- **Process-challenge opener**: "this is first time I am seeing this: wanna know if this is the default process or a mistake made by everyone involved" — surfaces possible org issue without accusing
- **Incident-commander diagnostic ask**: "or is this a hypothesis?", "what was the impact?", "why would this happen?" — separates confirmed from speculative
- **Pre-event emotional anchor** (leadership prep to small groups): "Stay sturdy today", "today's announcement is going to be tough for everyone"
- **Calibrated promise** (leadership): "I won't always have the answer / be able to share everything, but I will be honest with you about which is which"

## Hard-fail hedging (over-soft / passive-burying-the-ask)

- "I think we might want to consider..."
- "It might be worth considering whether..."
- "Perhaps we could..."
- "Would it be possible to..." (used as ask-burier; if literal feasibility Q, OK)
- "I was wondering if you would be able to..." (the chained-courtesy form)

**Not blocked** (real corpus):
- "I'm wondering if..." — Chu Yeow uses this as a thinking-out-loud hedge ("I'm wondering if it's worth allowing humans to invalidate..."). Legitimate voice marker.
- "I'm curious how..." — same as above.
- "I'd like..." — direct preference statement, accepted in leadership register.

## Hard-fail filler / corporate jargon

- "circle back", "touch base", "ping you offline" (loop in is borderline — ok in eng)
- "leverage", "utilize", "facilitate"
- "robust", "seamless", "holistic", "synergy"
- "align on" → use "agree on" or "decide"
- "bandwidth" → use "time" or "capacity"
- "at the end of the day"
- "that being said" (acceptable once in long broadcast; not in short messages)

**Not blocked** (real corpus):
- `just` as natural softener: "just a quick confirmation", "just checking in", "just incurring $ on-demand now". Chu Yeow uses this. Soft-warn only if "just" stacks with another filler ("just really", "just simply") in the same sentence.
- `actually` / `basically` / `simply` — also not blocked outright; soft-warn if stacked or used 2+ times in one message.
- `really` as intensifier — not blocked; e.g. "that is a really good catch".
- `imo` — endorsement softener in peer/leads register ("genuinely good imo, please use it"). Voice-true; keep. Same lowercase-abbreviation family as `fyi` / `pls` / `tbh`. (observed edit 2026-07-08)

## Hard-fail AI transitional phrases

- "Furthermore"
- "Moreover"
- "Additionally" (when used as paragraph opener; "in addition" is OK if literal)
- "In conclusion"
- "In summary" / "To summarize"
- "It's worth noting that..."
- "It's important to remember..."

**Not blocked**:
- "however" / "so" / "and" as sentence/paragraph connectors — real corpus uses these freely
- "related to this," — Chu Yeow uses this ("related to this, I'm wondering if...")

## Sign-off — register-conditional

Hard-fail in **peer / ack / incident** registers:
- "Let me know if you have any questions"
- "Happy to discuss further"
- "Looking forward to your thoughts"
- "Thanks in advance!"

**Acceptable in broadcast register** (Chu Yeow's real broadcast uses this):
- "please feel free to ask if anything's unclear!" — verbatim from a real broadcast message

Default: cut the message at the ask. If the spec specifies broadcast register AND the message is going to a non-engineering audience, a broadcast-acceptable sign-off may be appended.

## Hard-fail formatting

- Markdown headers (`#`, `##`) — Slack doesn't render
- `**double asterisk**` for bold — Slack uses single `*asterisk*`
- **Any em-dash `—` (U+2014). Hard-fail at any count.** Chu Yeow does not use em-dash, period (per user 2026-05-12 — he doesn't even know how to type one). Use en-dash `–` (U+2013) instead. The generator may have habitual em-dash output; replace every `—` with `–` before submitting.
- 2+ en-dashes (`–`) in a message ≤ 50 words.
- Bulleted list with 1 or 2 items (use prose)
- Numbered list when no order is implied
- Trailing emoji garnish (`🚀✨💡`) — emoji only with semantic load
- More than 3 emoji per message (real corpus emoji are sparse, mostly thumbs-up or rotating_light for alerts)

## Hard-fail fabrication

The generator MUST NOT invent:
- Specific numbers / percentages / dates not in `spec.required_facts`
- Slack channel names not given by user
- Jira/Linear IDs (`FBT-1234`, `AI-456`)
- PR numbers or repo paths
- Person names beyond what the user mentioned
- Dollar amounts, financial figures, cost numbers — never invent. If the user's intent didn't supply the number, use a placeholder `<$X>`.

If a number "feels right" but isn't in the spec — use a placeholder `<X%>` or `<owner>` and surface to user.

## Hard-fail reasoning artifacts (the hunt, not the verdict)

A finished artifact carries **what is true**, not the path taken to find it. The
process belongs in chat. Hard-fail any of these in a report, doc, brief, or
committed file:

- **Discarded hypotheses**: "we first thought X, but", "our initial read was", "this turned out not to be"
- **Narrated correction of your own earlier output**: "an earlier version of this said", "my estimate was wrong by $162K", "superseded" sections describing *your* prior draft
- **Round-count or effort narration**: "after three passes", "on closer inspection", "digging further", "it took some reconciling"
- **Self-assessment of the process**: "this was harder than expected", "the analysis proved tricky", "confidence is high after cross-checking"
- **Explainers defending a choice nobody questioned**: a paragraph justifying why a file is named what it is, why a source was picked, or why an obvious approach was obvious

Rewrite as the standing fact. `"I first derived Feb by subtraction and got -$107K, but the model says -$269K"` becomes `"February EBITDA -$269K."`

**Not covered by this rule** – these stay:
- **Provenance of a figure a reader may meet elsewhere.** "May EBITDA has been published as $144K, $185K and $178K; use $178K" is a reader service, not the hunt. So is naming which source wins.
- **One-line evidence handles.** A single sentence proving a claim ("its Jan–Jul EBITDA sums to $1,220K, matching the pack's YTD line") is verification, not narration. Two paragraphs of it is narration.
- **Someone else's disagreement or restatement.** External conflicts are facts about the world.

The test: would the reader act differently if this sentence were deleted? If no, cut it.

## Soft-warn (score reduction, not hard-fail)

- Three or more sentences of preamble before the ask
- Apologizing for length when message is short
- "Per my last message"
- Marketing adjectives in operational context: "exciting", "amazing", "fantastic"
- "I think" used 2+ times in a short message (dilutes the ask)
- "we should" with no "by when" or "owner"
- All-caps for emphasis beyond one short word

## Notes for the evaluator

When you see a pattern from the "Not blocked" sections, do NOT penalize. The user uses these. The point of calibrating against the real corpus is to avoid over-correcting toward generic professional English.

When a draft contains a hard-fail pattern, cite the exact span and the rule it violates. The generator should be able to fix it with a one-word replacement.
