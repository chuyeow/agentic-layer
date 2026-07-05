# Micro-worlds — build a system you can inhabit

A micro-world is a small, runnable artifact that lets a human **inhabit** a system
and build intuition by poking at it, rather than reading about it. Seymour Papert
called it "living in Mathland." The insight (Geoffrey Litt): *agents can write bits
of code that help humans understand other code.*

An explainer (see `explain-diff-html.md`) narrates a change. A micro-world simulates a
system so you can drive it, break it, and watch it react. Reach for a micro-world when
the thing to understand is **behavior over time or under different inputs** — a state
machine, a pipeline, a protocol, a scheduler, a data flow, a lifecycle — not a static
snapshot a diagram would capture.

## Format — pick what fits the system (never Notion)

- **Self-contained HTML file** — the default. Best when state is visual: dashboards,
  pipelines, wiring diagrams, before/after UI, anything with panels that light up.
  One file, inline CSS+JS, no external fetches. Save dated + outside the repo.
- **TUI app** — great when the system *is* a terminal/loop/REPL, or when stepping
  through execution frame by frame matters (a debugger, an interpreter, a state
  machine you single-step). Reach for a tiny curses/ink/textual-style program.
- **CLI app** — great when the system is a sequence of commands or transformations
  and the lesson is "what each command does to the state" — a scriptable sandbox the
  user runs verb by verb and inspects output between steps.

Choose by asking: *what would the user most naturally poke to feel how this works?*

## Design principles

- **Inhabit + intuit.** The user drives; the world reacts visibly. State changes must
  be legible at a glance (a pill, a count, a rendered view flipping) — visible effects,
  per Litt's "AI HUDs" idea.
- **Wrong paths teach.** Let the user do things out of order or with bad inputs, and
  surface the *real* error the system would produce. Hitting the failure is often the
  fastest way to learn the dependency/constraint. (e.g. seed-before-migrate → the
  actual "relation does not exist" error.)
- **Real data, real facts.** Use the codebase's actual names, ports, values, sample
  rows. A faithful model teaches; a generic one misleads. Explore the code first.
- **Graduated complexity.** Intuition and a one-line mental model before detail. Let
  the reader skip background they already have.
- **Comprehension checkpoint.** Where it fits, end with a few interactive questions
  (Litt's "speed regulator") — understanding should pace the work, not lag it.
- **A reset.** Always let the user return to a clean starting state and try again.

## Reference patterns

- **Step-through debugger** — visualize execution of a tricky algorithm/interpreter
  frame by frame (Litt's Prolog debugger). TUI or HTML.
- **Command center** — side-by-side old/new during a migration or refactor, updating
  as changes land (Litt's framework-migration UI). HTML.
- **Pipeline simulator** — stages with live state panels; run each stage, watch data
  flow through and errors appear when prerequisites are missing. HTML or CLI.

## Output convention

Match the explainer skill: write the artifact to a global location **outside the code
repo**, filename prefixed with today's date `YYYY-MM-DD-` so files stay time-sorted and
out of version control (e.g. `/tmp/2026-07-05-microworld-dev-env.html`). For HTML,
publish via the Artifact tool so it's viewable/shareable. For TUI/CLI, leave a one-line
run command.
