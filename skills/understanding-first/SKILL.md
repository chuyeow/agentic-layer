---
name: understanding-first
description: >
  Build the user's understanding of code, not just ship it — because with agents
  writing most of the code, human understanding is the bottleneck. Two moves: (1) a
  rich code explainer for a change/diff/branch/PR (via the verbatim /explain-diff
  prompt, HTML output); (2) an interactive micro-world (HTML file, or a TUI/CLI app)
  that lets the user inhabit a system and build intuition by driving it. TRIGGER when
  the user asks to understand a repo, feature, diff, PR, or system new to them ("explain
  this", "help me understand", "how does X work", "walk me through", "I'm lost");
  PROACTIVELY OFFER (don't auto-build) after a substantial amount of work has landed and
  the user may not fully grasp it, or when understanding is high-stakes — an unfamiliar
  codebase, a subtle or wide-reaching change, tricky control flow, or a design they'll
  keep iterating on.
---

<premise>
As AI agents write more of the code, the scarce resource is no longer typing or even
verification — it's the human's live understanding of the system. Without it they lose
the ability to steer. This skill closes that gap on purpose: it produces artifacts whose
only job is to move understanding from the agent's head into the user's, and it paces
that understanding against the work (Litt's "speed regulator"). Source:
geoffreylitt.com — "Understanding is the new bottleneck."
</premise>

<two_modes>
Pick by what the user needs to understand:

- **Explainer** — for a *change*: a diff, branch, PR, commit, or "what did we just do."
  Narrates background → intuition → code → quiz. Invoke the standalone `explain-diff`
  skill (Skill tool) — it's Geoffrey Litt's prompt verbatim and the single source of
  truth. Always HTML (never Notion).

- **Micro-world** — for a *system's behavior*: a feature, subsystem, pipeline,
  protocol, lifecycle, or a repo/area new to the user. A runnable thing they drive and
  poke. See `references/micro-world.md`. Format is HTML, or a TUI/CLI app when that
  lets them inhabit it better (e.g. a step-through debugger as a TUI). Never Notion.

Both can apply — a big PR in an unfamiliar area might get an explainer for the diff and
a micro-world for the subsystem it touches. When unsure which, ask the user in one line.
</two_modes>

<when_to_act>
**On request → build it.** The user asks to understand something ("explain this PR",
"help me understand this repo", "how does the auth flow work", "I don't get this").
Choose the mode, explore the relevant code first, then build.

**Proactively → offer, don't auto-build.** After you finish a chunk of work, judge
whether the user's understanding likely kept pace. Offer an explainer/micro-world (one
sentence, name which and why) when:
  - a substantial or wide-reaching change just landed (many files, new abstraction,
    non-trivial control flow, a migration);
  - the work is in a codebase/area the user is new to;
  - understanding is high-stakes — they'll keep iterating on it, or getting it wrong is
    costly (auth, money, data integrity, concurrency);
  - the user seems unsure ("wait, what does this do", "why did that work").

Don't nag: skip the offer for small, obvious, or throwaway work, and don't offer twice
for the same thing. The bar is "would a HUD here actually change what they do next?"
</when_to_act>

<how_to_run>
1. **Explore first.** Read the surrounding code, not just the diff — the explainer's
   Background section and the micro-world's fidelity both depend on real context,
   names, and data from the codebase.
2. **Explainer:** invoke the `explain-diff` skill via the Skill tool and follow it
   exactly (it is Geoffrey Litt's prompt, verbatim — its formatting rules are hard
   requirements: self-contained HTML, `<pre>`/`white-space: pre-wrap` on code blocks,
   HTML not ASCII diagrams, Kleppmann-style prose, five interactive quiz questions).
3. **Micro-world:** follow `references/micro-world.md` — model real behavior, make
   state visible, let wrong paths surface the real errors, add a reset, end with a
   comprehension checkpoint where it fits.
4. **Output:** write to a global location OUTSIDE the repo, filename prefixed with
   today's date (`YYYY-MM-DD-…`) so artifacts stay time-sorted and out of version
   control. Publish HTML via the Artifact tool and hand back the link; for a TUI/CLI,
   give the one-line run command.
5. **Ground truth over polish.** A faithful model that teaches beats a pretty one that
   misleads — verify facts against the code before asserting them.
</how_to_run>

<references>
- `explain-diff` skill (standalone, invoke via Skill tool) — Geoffrey Litt's /explain-diff
  prompt, verbatim. The canonical explainer for a change. HTML output.
- `references/micro-world.md` — authoring guide for inhabitable simulations (HTML / TUI
  / CLI), design principles, and reference patterns.
</references>
