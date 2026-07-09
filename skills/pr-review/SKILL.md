---
name: pr-review
description: Review a PR/diff for whether it actually achieves its stated goal, not just whether the lines look fine. Use when reviewing a pull request, diff, or branch — especially when the change instruments, transforms, routes, or tags data over a set of inputs, or claims to do something "for all X". Complements correctness/style review with a goal-conformance pass.
---

# PR review: goal-conformance first

The lens that catches real bugs is not "are these lines clean" — it's **"does this achieve its stated purpose, for every input?"** Run this pass before nitpicking.

## 1. Restate the goal in one line, then test against it

Write the PR's goal as a single sentence (from the description/title). Every check below serves that sentence. If you can't state it, ask the author — a review without a goal is just style opinions.

## 2. Run the core function over the FULL real input set

The author's examples are a biased sample — usually the happy path. Find the real, complete input domain (the actual config list, all routes, every enum value, the whole file set) and **execute the change's core function over all of it.** Throwaway script beats eyeballing.

Then look at the *outputs as a set*: count distinct results, diff against input count, hunt collisions / gaps / duplicates.

- N inputs should give N distinct outputs? Count them. `57 files → 53 tags` is a bug you cannot see in the diff.
- A mapping/tag/key/route derived from a path or field? Feed it every real value and check for two inputs colliding onto one output.

## 3. For "X happens for ALL Y" claims, prove the negative

Any universal claim — "every write increments", "all requests are authed", "each event is routed" — is only verified once you've searched for the **bypass** and found none.

Enumerate every alternate path around the instrumented one and grep for each: sibling methods (`.info`/`.<<`/`.add` when `.log` is the intended choke point), other classes doing the same job, raw calls that skip the wrapper. Confirming the happy path is not proof; the absence of a bypass is.

## 4. Verify before you flag — deletion claims need a bug-claim's evidence

"Delete this, it's unnecessary" must clear the same bar as "this is broken." Before flagging code (a lock, a guard, a dependency, a retry) as redundant, **confirm the library/platform/runtime behavior you're assuming** against docs or a quick test — including the exact version in the lockfile. Cheap way to be confidently wrong: assume old semantics for a library that changed them.

## Re-review: when the author says "addressed" — don't take their word

Trust nothing you didn't re-check. On any "fixed it" / "addressed your comment":

1. **Read the author's replies on the threads you opened, first.** They often answer the exact open question you flagged (a caveat, an unknown) or point at evidence — read the reply and the diff of their new commits before you re-review. If you haven't done both, you haven't started. (Don't wait to be told the reply exists.)
2. **Re-verify the fix yourself, don't trust the reply's numbers.** Re-run technique #2 — the core function over the *full* real input set — against the new code. Confirm the choke-point / no-bypass proof (#3) still holds after their change.
3. **Grade the regression test they added.** It must (a) *fail on the old buggy code* — a test that passes both before and after guards nothing — and (b) cover the property, not one happy example. When the real input set is enumerable, assert the whole set (N inputs → N distinct outputs), not a single pair.

## Report

Label each finding with which failure it is — don't conflate them:
- **breaks at runtime now**
- **emits/stores wrong data** (no crash, wrong meaning)
- **fails a not-yet-built consumer** (latent)

Make findings demonstrable: a trace or a repro the author can run, not an assertion.
