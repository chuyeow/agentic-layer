# OPINIONS.md — Chu Yeow

## Start here — the essence

The convictions that most define how I think. Detail and sourcing for each is in the catalog below.

1. **Stop reading code; verify behavior.** You'll ship code you didn't read — reading every line doesn't scale and is a *weak* form of verification. Build systems where an objective judge proves behaviour. But you own every bit of what you ship: your name is on the PR, and fundamentals matter *more*, not less.
2. **The "lazy" engineer is the good engineer** — compulsively automate away your own repeated work. We don't have enough of that instinct.
3. **Measuring the right things produces the right actions.** Token counts are a red flag, not a badge; leaderboards find team bottlenecks, not rank people; metrics are diagnostic-never-evaluative and un-gameable; absolute-$ over relative-%, gated by materiality.
4. **Understanding is the new scarce resource** — invest in the human's comprehension as a first-class deliverable.
5. **Wego is the substrate for the user's agent, not a chatbot we impose.**
6. **Intellectual honesty is the discipline.** Report faithfully, grade evidence (confirmed / likely / hypothesis), link every claim, say only what's currently true, never invent. Terse, plain, en-dashes; voice over polish; the data tells the truth.

---

## A. Engineering velocity is a competitive weapon

**A1.** Engineering velocity is a competitive weapon; a slow build loop is a ceiling on business ambition we can't afford against bigger competitors.  ↳ PR-FAQ
---

## B. Verify behavior, not code

**B1.** You *will* — and should — ship code you haven't read. Reading every line doesn't scale, and more importantly **reading code is a weak form of verification.**  ↳ manifesto pt.2
**B2.** **Verify behavior, not code** — the code is an implementation detail. Agents are strongest with an *objective judge*; if a check has to guess, you're back to reading code. Ask: *how would a human verify this? If a human can, so can AI.* (Exception: bleeding-edge tech and foundational architecture — there you still read.)  ↳ manifesto pt.2
**B3.** Tests must verify what you actually *want*, not chase coverage — behaviour-first over implementation-coupled; TDD's red/green/refactor is the natural agent loop. Shape architecture to be **verifiable by AI**: if it's hard for humans to verify, it's hard for agents.  ↳ manifesto pt.2; CONTRIBUTING
**B4.** A proof must show the **whole real interaction**, not jump to the end state — a demo that skips the upload/scroll/read steps proves nothing. And a **single snapshot isn't evidence**: sample over time, or re-check live state, before acting on it.  ↳ Codex history
---

## C. What stays human — judgment, ownership, understanding

**C1.** You own the judgment, verification, and ship decision. The agent is a tool — fast, tireless, sometimes confidently wrong. **Your name is on the PR.**  ↳ manifesto pt.2
**C2.** With agents writing the code, the scarce resource is no longer typing or even verification — it's the **human's live understanding.** Lose it and you lose the ability to steer, so build it deliberately (explainers, micro-worlds, teach-until-mastered) and pace work against it. A faithful model that teaches beats a pretty one that misleads.  ↳ `understanding-first`, `learn-quiz`
---

## D. Adoption: stakes and standards

**D1.** I'll be honest about the stakes because that's a duty, not a threat — I can set conditions but "I can't cross the gap for you; you have to take the step." Fund the experimentation generously and give people whatever they need to climb the learning curve, watching only the aggregate.  ↳ manifesto pt.2; Slack 2025-08-12; Granola: Ross Jul-2
**D2.** Pure vibe coding has limited range with today's LLMs — make AI generate code that meets our standards, don't lower the bar for speed. You're responsible for what you merge; if you can't review and metabolise LLM code, that's a **skills issue**, not an AI problem.  ↳ Slack 2025-04-10, 2025-06-06
---

## E. Measurement is alignment

**E1.** The wrong metrics produce the wrong actions; **measuring the right things produces the right actions.** The measurement work *is* the alignment work — once the dashboard makes real bottlenecks visible, the arguments about what to invest in stop.  ↳ PR-FAQ, HANDOFF
**E2.** Metrics are **diagnostic, never evaluative.**  ↳ HANDOFF; PR-FAQ
---

## F. Org design

**F1.** Engineering work should be **pulled** by legible problems tied to business outcomes ("gravity"), not pushed top-down — "business outcome at stake" comes first, always.  ↳ `problems/README.md`
**F2.** Shift quality **left** — phase out manual QA as a function; developers own their code's quality.  ↳ Slack 2026-05-08
---

## G. Fix the root cause

**G1.** Fix the **root cause**, not the symptom — and a review/gate/monitor that only *reports* is half-done: it must apply the fix, re-verify, and commit.  ↳ `ship`, `babysit-pr`, `upskill`; CLAUDE.md
---

## H. How I disagree

**H1.** Write disagreement **directly and specifically** (concrete gaps, concrete rewrites) but framed as **collaborative, not adversarial** — "a friendly rewrite of the same workstream, not a rejection."  ↳ *agent-native-wego-response*
---

## I. Agent-native product & platform strategy

**I1.** Wego's AI product should be the **substrate the user's own agent acts on** — never a Wego-built chatbot that imposes Wego's preferences. The "horseless carriage" (our own one-size-fits-all bot) is the wrong build.  ↳ *agent-native-wego-position*
**I2.** The win isn't "we shipped an API" — it's Wego being the **default an agent reaches for.** **Discoverability** (machine-readable APIs, MCP, robots.txt, agent-auth) is a first-class requirement — "dead on arrival" without it. Sequence **capabilities first, then doors**; build only what agents can use almost immediately.  ↳ *agent-native-wego-position*; Granola: Ross Jun-11
**I3.** State speculative bets explicitly as **hypotheses** (e.g. paying agents a rev-share to prefer Wego) rather than deferring monetization to "later" — a material reason beats a merely technical one.  ↳ *agent-native-wego-position*
**I4.** The model itself is a **commodity; the durable advantage is the internal platform** — "Anyone can buy Claude; this is the part you build." AI/virtual-employee roles are built around **the outcome a role owns** (a pricing VE owns margin on the top 50 routes), each with a **named accountable human owner**; company-wide rollout is sequenced by a readiness × opportunity × impact score, department by department.  ↳ *wego-ai-ares*
**I5.** PRDs aren't the bottleneck — **alignment is.** AI should draft most of the PRD; the artifact engineers need is a rough **prototype as a discussion-starter**, not a pixel-perfect mockup. Keep specs/prototypes a couple of sprints ahead, and mine years of Jira/Slack/Confluence/Figma prior art so nothing is re-argued.  ↳ Granola: Ross Jul-2
---

## J. Monitoring from the customer's perspective

**J1.** SLOs/monitors are designed from the **end-customer and downstream-consumer** perspective across the whole lifecycle — not just latency — and must catch slow week-over-week degradation.  ↳ Slack #payments-dev 2026-07-02
---

## K. Product shaping (adopted — Shape Up / Ryan Singer)

*A framework I chose and use, not one I originated. It reflects my taste.*

**K1.** Separate the problem from the solution; decide fit with a **binary** check — ✅/❌ only, no "partially"; an unknown (⚠️) fails, because ✅ is a claim of knowledge.  ↳ `shaping`
---

## L. Meta-principles — how the whole system is built

**L1.** **Skills must compound** — when a run hits a blocker, fix the skill so the mistake can't recur; never silently retry a broken approach twice across runs.  ↳ 8+ skills; CLAUDE.md
**L2.** Build **closed loops, not one-shot dumps** — a brief checks yesterday's commitments; a catalog tracks claim/status; a denylist learns. Systems that feed back on themselves.  ↳ `morning-brief`, `slack-draft`, `error-monitor`
---

## M. Working-style defaults (self-stated in CLAUDE.md)

**M1.** TDD by default; simplest code that passes; complexity emerges from refactoring, not initial implementation. 
**M2.** When unsure: read more code; still stuck → ask with short options. Conflicts → call out and choose the safer path. 