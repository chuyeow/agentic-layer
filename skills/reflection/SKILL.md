---
name: reflection
description: Interrogate your own just-completed work with three questions — what you're least confident about, what you claimed works but never verified, and the biggest thing you're probably missing. Use when the user runs /reflection, says "reflect on that", "check yourself", or after finishing a non-trivial chunk of work where confident-but-wrong is a real risk.
---

# Reflection

Answer these three questions about the work you just did. Out loud, in the response. No preamble, no summary of what you did — the user already saw it.

1. **What are you least confident about in what you just did?**
2. **What did you just tell me works that you didn't actually verify?**
3. **What's the biggest thing I'm probably missing about this that I haven't thought to ask?**

## Rules

- Be specific: name the file, the function, the claim, the assumption. "The error handling might be off" is worthless; "`parse_date` at utils.py:44 assumes UTC and I never checked what the caller passes" is an answer.
- Question 2 is about *your own sentences*. Scan back over what you literally told the user this session and separate ran-it-and-saw-it from sounded-right-so-I-said-it. Tag every one of them per Citations below.
- If a claim is unverified and cheap to verify, verify it now, then report the result instead of the doubt.
- No hedging-as-answer. "Everything looks good" fails the skill. If you genuinely have nothing for a question, say what you *did* check that makes it so, not that you're confident.
- Don't start fixing beyond quick verification unless the user asks. Report, then wait.

## Citations

Every factual claim in the answer carries its evidence inline, or it goes on the unverified list. Three kinds:

- `ran` — a command executed this session. **Quote the decisive output line; don't just name the command.** Naming lets a bad claim through: "I ran `ls -l`" hides that the output read `.rw-r--r--@ SKILL.md` while the claim said "symlink". Quoting puts the mismatch on the page where a reader — including you, re-reading — can see it.
- `read` — verified by reading. Cite `file:line`.
- `assumed` — no evidence. Say so plainly.

Before you publish a citation:

- **Does the quoted output actually contain the asserted fact?** A citation that doesn't is worse than none — it makes a guess look sourced.
- **Did the evidence exist before you went looking for it?** A search can match the record of itself: tool calls are written to the session transcript before they run, so grepping for a phrase can find your own query string. Never verify a claim against an artifact your verification created — `mkdir -p X && ls X` proves nothing about whether X existed.
- **An empty `assumed` list is itself a claim.** Justify it or look harder.
