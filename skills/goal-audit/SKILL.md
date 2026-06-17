---
name: goal-audit
description: Audit a goal against the six qualities of a well-formed goal and rewrite it if it falls short. Triggers whenever the user states a goal, objective, or "what done looks like" for a task — phrases like "the goal is", "I want to", "make this better", "my objective is", "get X working", "build/fix/improve Y" — and whenever the user runs /goal-audit. Use this BEFORE starting work on any non-trivial task so the goal is auditable and has a real finish line, not just when the word "goal" appears. A vague goal gives no completion condition; this skill catches that early.
---

# Goal Audit

A goal worth pursuing tells you when you're done and how you'll know. A vague goal ("make this better", "fix the dashboard") gives no completion condition — work drifts, scope creeps, and "done" becomes a vibe. This skill audits a stated goal against six qualities, then rewrites it if it's missing any.

Based on the six-element model from OpenAI's [Using goals in Codex](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex).

## When to run

- The user runs `/goal-audit` (with or without a goal as argument).
- The user states a goal for a task you're about to start — explicitly ("the goal is…") or implicitly ("I want to get X working", "make this faster", "fix the flaky test").

When the goal is implicit, audit it silently first. If it already has all six qualities, don't interrupt — just proceed. Only surface the audit when something's actually missing, or when `/goal-audit` was invoked explicitly.

## When to skip

One-off edits, simple explanations, or tasks with no clear finish line (open-ended exploration, "just look around"). A goal with these doesn't help — say so briefly and move on. Don't force the ritual onto work that doesn't have a terminal state.

## The six qualities

A well-formed goal defines all six:

1. **Outcome** — what should be true when the work is done.
2. **Verification surface** — the test, benchmark, report, artifact, command output, or source that *proves* the outcome. Without this, "done" is unfalsifiable.
3. **Constraints** — what must not regress while the work happens.
4. **Boundaries** — which files, tools, data, repos, or resources may be used.
5. **Iteration policy** — how to decide what to try next after each failed attempt.
6. **Blocked stop condition** — when to stop and report that no defensible path remains, instead of thrashing forever.

The target: **narrow enough to audit, broad enough to let the executor choose the next action.** A goal that scripts every step isn't a goal, it's a procedure. A goal with no verification surface isn't a goal, it's a wish.

### Shape to aim for

> `<desired end state>` verified by `<specific evidence>` while preserving `<constraints>`. Use `<allowed inputs, tools, boundaries>`. Between iterations, `<how to decide the next best action>`. Stop and report if `<blocked condition>`.

Not every goal needs all six spelled out at full length — a small task may fold constraints and boundaries into one clause. But every one should be *answerable*. If you can't say what proves it's done, that's the gap to fix first.

### Research / open-ended goals

For research or investigation, the verification surface is an evidence standard, not a passing test. Define up front how findings get graded — separate **confirmed**, **approximate/reconstructed**, **blocked**, and **uncertain**. Don't let the goal flatten different levels of support into one "success" claim; epistemic honesty is part of the outcome.

## Audit procedure

1. Restate the goal as you understood it, in one line. (Catches misread intent before anything else.)
2. Walk the six qualities. For each: present? If yes, quote the part of the goal that satisfies it. If no or weak, name what's missing and *why it matters for this specific task* — not a generic complaint.
3. If all six hold, say so plainly and proceed — no rewrite needed.
4. If any are missing, write a suggested goal in the shape above, filling gaps with concrete, task-specific content (real file paths, real commands, real thresholds you can infer from context — never invented placeholders like `<some test>`). Where you genuinely can't infer a value, ask a short, pointed question rather than guessing.

## Output format

Use this structure:

```
**Goal as stated:** <one-line restatement>

**Audit:**
- Outcome — ✅ <quote> | ❌ <what's missing, why it matters here>
- Verification surface — ...
- Constraints — ...
- Boundaries — ...
- Iteration policy — ...
- Blocked stop condition — ...

**Suggested goal:**
> <rewritten goal in the target shape>
```

If the goal passes clean, collapse to: `**Goal is well-formed** — <one-line why>, proceeding.`

## Examples

These are the examples from the OpenAI article, verbatim.

**Weak input:** "Reduce p95 latency below 120 ms without regressing correctness tests"

**Well-formed goal:**
> Reduce p95 checkout latency below 120 ms, verified by the checkout benchmark, while keeping the correctness suite green. Use only the checkout service, benchmark fixtures, and related tests. Between iterations, record what changed, what the benchmark showed, and the next best experiment to try. If the benchmark cannot run or no valid paths remain, stop with the attempted paths, the evidence gathered, the blocker, and the next input needed.

What changed: pinned the verification surface (the checkout benchmark), the constraint (correctness suite green), the boundary (checkout service + fixtures + tests), an explicit iteration log, and a concrete blocked stop condition.

---

**Weak input:** "Reproduce Buehler et al., 'Deep Hedging'"

**Well-formed goal:**
> Produce the strongest evidence-backed reproduction of Buehler et al., "Deep Hedging," using the available paper materials and local resources. Attempt every headline result, verify the outputs, and end with a report that separates reproduced mechanics, approximate trained results, blocked exact replay, and remaining uncertainty.

What changed: turned "reproduce" into a graded evidence standard — the report must distinguish what was reproduced, what's approximate, what's blocked, and what's uncertain, instead of flattening everything into one "done" claim.
