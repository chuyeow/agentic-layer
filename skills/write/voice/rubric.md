# Voice rubric — Chu Yeow's writing (self-check)

Apply this as a **self-check pass** on your own draft before you present it — you are not a separate evaluator agent, you grade your own draft and fix the misses first. Extracted from the `slack-draft` skill's evaluator rubric, minus the pass/fail GAN mechanics: the axes and the hard-fail blocklist are the substance worth keeping.

The bar: **voice-match matters most**. A draft with all the right facts but the wrong voice is a failing draft — rewrite it. A slightly-ungrammatical-but-on-voice line beats a polished-and-generic one.

## Voice-match — the most important axis

A 5 reads like a real Chu Yeow message/doc for the same register. A 1 reads like a generic AI assistant.

Concrete markers of Chu Yeow's voice (from `~/.claude/CLAUDE.md` "Writing style" + observed corpus):

- **Minimal filler**, **noun-phrases ok**, **dropped grammar where intent stays clear**. Articles (a/the) often omitted in casual registers. "Looking at payments" not "I'm looking at the payments thing".
- **Decision-forward**: the ask or the conclusion is in the first 8 words when possible.
- **Concrete > abstract**: cites the dashboard, the PR number, the % delta, the channel, the date – not vague "issues" or "things".
- **Lowercase first word** in casual peer/eng registers. Sentence case for leadership and long-form.
- **One-liners preferred** when the message is small. Bullet lists only when ≥3 truly distinct items and prose would obscure structure.
- **No softeners**: no "just" (stacked), "really" (as filler), "basically", "actually", "simply", "I think we might want to", "perhaps we could".
- **En-dashes (–), never em-dashes (—)** – Chu Yeow's signature. Sparingly: one clarifier per short message max. Two-or-more en-dashes in a short message is the slop smell. (Jira is the exception: separator is a colon, not a dash.)
- **Backtick technical terms** in dev contexts: `payments_and_success_rates.csv`, `FBT-1234`, `wego/wego-fares`, repo paths.
- **Surface-native formatting** (see below) – never fight the medium.

A draft with the right facts but wrong voice scores **3 or below** here. That means: rewrite, don't ship.

## Brevity

5 = at or under the natural length for the register, no flab.
1 = 2+ filler sentences ("hope you're well", "wanted to circle back", "as discussed"), or well over the register's natural length.

## Over-writing — the second cut (calibrated from real edits, 2026-07-08)

Chu Yeow's final drafts are shorter than the "already tight" draft. His edits repeatedly cut in five directions — apply these *before* presenting; they're the gap between a draft he sends and one he rewrites. (Evidence: a review-extension follow-up he cut ~110w → ~45w.)

- **Trust the link — don't restate what it says.** Pointing to a guide/doc/note = "please use it", not a paraphrase of its contents. Re-explaining a linked source was the single biggest cut. (A draft that linked Ryan's review guide *and* restated its "evidence over vibes / one growth area / forward-looking" bar → he kept only "genuinely good imo, please use it".)
- **No nag, no moralizing counter-clause.** "do these properly" — not "do these properly, *not to push them to the last night*". State the positive purpose; drop the implied scold.
- **No manufactured urgency or status close.** He cut "I'd like us leads done first" and "please nudge your teams too". Don't add pressure or a competitive frame the intent didn't ask for — let the ask stand and stop. **Carve-out (2026-07-08):** this targets *fake* urgency/status only, NOT genuine warmth. A sincere, specific close is voice-true and must NOT be stripped — see "Recognition & warmth" below. (He replaced a flat "Wishing him the best" with a specific generous gesture; the earlier version of this rule would have wrongly cut it.)
- **Cut elaboration to the bare step.** A 3-step ask with a clause explaining why step 3 matters → two bare steps. If the reader can infer it, cut it.
- **Plain over bold for routine tokens.** He unbolded `*Wed 15 Jul*` → plain. Bold a genuine key term, never a date/name/deadline by default.

Rule of thumb: when you think it's tight, cut it ~half again.

## Ask / point clarity

5 = the primary ask (or the single point) is unmistakable, up front, action-oriented. The reader knows what to do or take away.
1 = no ask, no point, pure narration. (Acceptable only if the piece is explicitly pure FYI.)

## Register-fit

5 = matches the target audience's register. 1 = wrong register entirely (casual reaction into a company-wide announcement, or stiff formality into a peer DM).

**Register axis (transcends surface — the length caps are Slack-calibrated but the register is the same in email/doc):**

- **ack** (≤15w): DM / thread reply. Lowercase fine. Reactions ("Nice.", "Will do") and emoji-only acks OK.
- **peer / eng-thread** (≤100w): eng channels, peer DMs. Lowercase first word standard. Fragments ok. Question-stacking signature.
  - *Sub-register: DM to a close report / lead* – tighter than general peer. Strip soft hooks ("ping if useful"), state the content bare.
- **broadcast** (≤300w): team-wide updates, `#engineering-updates`, cross-team ops. Leader voice + operational. Sentence-case opener ("Hi team", "Hey team"). Numbered lists with sub-bullets ok. Sign-off "let me know if you disagree and your reasons" / "please feel free to ask if anything's unclear!" is voice-true here.
- **senior leadership / company-wide** (≤1500w): `#leadership-*`, `#slt-*`, org changes, hard news, announcements. Sentence case throughout, complete sentences, first-person ownership. Section labels as informal inline mini-headers ("Why:", "What's next"), no markdown headers. Emoji only at the very end for emotional weight, if at all. **Too consequential for autonomous send – always show the user before anything leaves.**
- **incident** (≤100w): timestamped UTC facts, "confirmed" vs "suspected" called out, ping owners, append-only.

Surfaces map onto this: an **email** is usually broadcast or leadership register; a **doc / announcement** is leadership/long-form; a **PR/commit body** follows `write-pr-description`; **Jira** uses colons not dashes.

## No-slop

5 = nothing from `anti-patterns.md`. Watch the subtler slop the hard-fail list won't catch: em-dash drift, hedging without a keyword, generic transitions ("Additionally", "Furthermore", "In summary").

## Hard-fail checks (any one present = fix before presenting)

Calibrated against the real corpus – patterns that appear in the corpus are deliberately NOT here (see `anti-patterns.md` for the "not blocked" carve-outs). Case-insensitive:

- `^(sure!|of course!|certainly!|absolutely!|happy to help|i'd be happy)` at start – exclamatory assistant openers. (`Sure, …` / `Of course, …` mid-sentence OK.)
- `(i hope|hope you're) (well|doing well)` / `hope this finds you` – pleasantry opener.
- `\b(furthermore|moreover|in conclusion|in summary|to summarize|it's worth noting|it's important to remember)\b` – AI transitional slop.
- `\b(leverage|utilize|facilitate|robust|seamless|holistic|synergy|circle back|touch base)\b` – corporate jargon.
- `let me know if (you have|there's anything|i can)` / `happy to discuss further` / `looking forward to your thoughts` – sign-off slop in **peer/ack/incident only** (permitted in broadcast).
- `\bi think we might want to consider\b` / `\bit might be worth considering whether\b` / `\bperhaps we could\b` – chained-hedge slop. (`i'm wondering if`, `i'm curious how`, `i'd like` are NOT blocked – voice-true.)
- **Any em-dash `—` (U+2014), any count. Replace every one with en-dash `–` (U+2013).** Chu Yeow does not use em-dashes.
- **Fabricated fact** not given to you (numbers, %, ticket IDs, PR numbers, names, dollar amounts). Use a placeholder `<X%>` / `<owner>` and surface it – never guess.

Slack-only formatting hard-fails (when the surface is Slack): markdown headers `#`, `**double-asterisk bold**` (Slack uses single `*`), >3 emoji.

## Voice-true patterns to actively reproduce

From the corpus (see `anti-patterns.md` for the full list) – *include* these where natural, they read as authentically him:

- **Question-stacking**: 2–4 sequential questions to probe instead of "we should do X".
- **Mid-sentence parenthetical with concrete detail**: "(fyi we are removing some CS leads too)".
- **Personal ownership in leadership comms**: "I made this decision", "I want to own that".
- **Section labels inline** for long-form: "Why:", "What's next" – no markdown headers.
- **Calibrated promise** (leadership): "I won't always have the answer, but I will be honest about which is which".
- **Deprioritization signature**: "this can wait, low priority vs your other tasks".
- **Collaborative amendment**: "I agree with this. I'd just upgrade a few points:" – add to others' work rather than rewrite.

## Recognition & warmth (calibrated from real edits, 2026-07-08)

Warmth is not slop — under-doing it is its own failure mode. From a farewell announcement he edited (my draft came out too cool):

- **Don't flatten sincere appreciation to lukewarm.** When the brief says "appreciate but not too strongly", that means *don't rank the person above the room* — it does **not** mean be bland. Name the competence and the personal note: he restored "took on more over time *very capably*", "enjoyed working with him *and learning from him*", "*clear on his current life goals*". Cool-and-generic is a miss.
- **Recognize the successor too, not just the leaver.** A handover has two people. He added "Congratulations to both Cuong and Redho on new responsibilities that will surely grow you guys!" — frame the transition as growth for both, don't spotlight only the one departing.
- **End on a specific, generous gesture, not a generic well-wish.** "Wishing him the best" → "please share how we can stay in touch, how to follow you and how to support your business(es) – as much as you are willing to share, of course." A concrete offer + the low-pressure "as much as you're willing" hedge. This is the *genuine* close the over-writing "no manufactured urgency" rule explicitly carves out.
