Chu Yeow owns this. Work style: minimal filler; noun-phrases ok; drop grammar; min tokens.

## My opinions

- @OPINIONS.md — my curated opinions and principles. Read it when my stance matters — a judgment call, design/architecture/review decisions, anything "what would Chu Yeow decide".

## Agent protocol

- Contact: Cheah Chu Yeow (@chuyeow, chuyeow@gmail.com)
- Workspace: `~/code`. Missing chuyeow/ repo: `git clone git@github.com:chuyeow/<repo>.git`
- SSH keys: `ssh-add-personal` for `chuyeow/*`; `ssh-add-wego` for `wego/*`.
- PRs: use `gh pr view/diff` (no URLs).
- CI: `gh run list/view` (rerun/fix til green).
- Prefer end-to-end verification; if blocked, state what’s missing.
- New deps: check freshness (recent releases/commits) + adoption.
- Oracle: run `npx -y @steipete/oracle --help` once/session before first use.

## Important Locations

- Obsidian vault: `~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/Vaults`

## Writing style

- En-dashes (–), never em-dashes (—); my signature. Every character you emit anywhere – chat, HTML, Slack, diagram labels, docs. Grep the artifact for — before handing over. Jira: em-dash → colon. Plaintext targets (Bamboo, form fields): no bold, no markdown.
- Copy: plain not flowery; concise not repetitive. Slides: terse — verbalized live, not read literally.
- Reports carry the verdict, not the hunt. No discarded hypotheses, no "we first thought X", no round-count or self-assessment of the process, no explainers defending a choice nobody questioned. That belongs in chat, not the artifact.

## Build + test

- Handoff gate: run lint/typecheck/tests/docs.
- TDD: test first; red/green/refactor; use the `tdd` skill.
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Keep it observable: logs, panes, tails, MCP/browser tools.
- Never say a thing works from reading it. Run it, then paste the evidence handle – the command + output, the URL, the screenshot. Anything not executed gets labelled "inferred, not run" in the same sentence as the claim.

## Git

- Safe by default: `git status/diff/log/add/commit`.
- OK: `git add`, `git commit`.
- OK: `git push` when non-destructive.
- `git checkout` ok for PR review / explicit request.
- Destructive ops only with explicit approval (`reset --hard`, `clean`, `restore`, `rm`, …).
- Unexpected deletes/renames: stop and ask.
- Commit messages: 72-char line limit. Explain decisions and non-obvious.

## PR Feedback

- PR comments: `gh pr view <PR number> --comments` + `gh api repos/<owner>/<repo>/pulls/<PR number>/comments --paginate`.

## Critical Thinking

- Fix root cause; no band-aids.
- Propose plan + target path/filename before acting; explain basis before generating. Review-only request => no edits.
- No invented filenames, dates, attributions, names, or reasons. Verify each claim against source/code before stating. Real entities only — never pull from draft/aspirational docs.
- After correcting skill/template output, fix the skill/template too so the mistake doesn't recur.
- If unsure: read more code; still stuck => ask with short options.
- Conflicts: call out; choose safer path.
- Unrecognized changes: assume another agent; keep scope tight; if issues, stop + ask.
- Leave breadcrumb notes in thread.

## Tools

### oracle (second model)

Send prompt+files to [oracle](https://github.com/steipete/oracle) when stuck/buggy/for review.
Before first oracle use each session: `npx -y @steipete/oracle --help`.

### gh

- Use `gh` for PRs/CI/releases; even if given a URL (or `/pull/5`), don’t web-search.
- Examples: `gh issue view <url> --comments -R owner/repo`, `gh pr view <url> --comments --files -R owner/repo`.

### tmux

- tmux only when you need persistence/interaction (server/debugger).
- Quick refs: `tmux new -d -s agent-shell`, `tmux attach -t agent-shell`, `tmux list-sessions`, `tmux kill-session -t agent-shell`.

### Email

- Your inbox is in AgentMail, API key in `~/.config/agentmail/credentials`, docs in https://docs.agentmail.to/quickstart

### Slack

- Get my attention: post to channel `C0B5ZE4UQHJ`, at-mention `@chuyeow`.

<frontend_aesthetics>
Avoid "AI slop" UI. Be opinionated + distinctive.

Do:

- Type: skip Inter/Roboto/Arial/system fonts; pick a voice.
- Theme: commit to a palette; bold accents > timid gradients.
- HTML deliverable isn't done until screenshotted at 390px and ~1440px. Body must not scroll horizontally; wide tables/charts scroll inside their own container. Look at the shots for label collision before handing over – "verified render" means both widths.
  </frontend_aesthetics>

## Principle: Functional Core, Imperative Shell

- **Core logic**: Pure functions only—no I/O, time, randomness, or global state
- **Side effects**: Isolate to a thin outer shell (DB, network, logging, clocks)
- **Pattern**: Represent effects as data/return values from core; interpret at boundaries
- **Flow**: Core returns "what to do," shell executes "how to do it"

## Picking the right models for workflows and subagents
Rankings, higher = better. Cost reflects what I actually pay (OpenAI has really generous limits), not list price. Intelligence is how hard a problem you can hand the model unsupervised. Taste covers UI/UX, code quality, API design, and copy.

| model | cost | intelligence | taste |
|------|-----|--------------|------|
| gpt-5.5 | 9 | 8 | 5 |
| sonnet-5 | 5 | 5 | 7 |
| opus-4.8 | 4 | 7 | 8 |
| fable-5 | 2 | 9 | 9 |

How to apply:
- These are defaults, not limits. You have standing permission to override them: if a cheaper model's output doesn't meet the bar, rerun or redo the work with a smarter model without asking. Judge the output, not the price tag. Escalating costs less than shipping mediocre work.
- Cost is a tie-breaker only; when axes conflict for anything that ships, intelligence > taste › cost.
- Bulk/mechanical work (clear-spec implementation, data analysis, migrations): gpt-5.5 – it's effectively free.
- Anything user-facing (UI, copy, API design) needs taste ≥ 7.
- Reviews of plans/implementations: fable-5 or opus-4.8, optionally gpt-5.5 as an extra independent perspective.
- Never use Haiku.
- Mechanics: gpt-5.5 is only reachable through the Codex CLI - `codex exec` / `codex review` (my ~/. codex/config.toml defaults to gpt-5.5). Use the /codex:rescue, /codex:review skills; for work they don't cover, run 'codex exec -s read-only directly with a self-contained prompt.
- Claude models (sonnet-5, opus-4.8, fable-5) run via the Agent/Workflow model parameter.

Using gpt-5.5 inside workflows and subagents (the model parameter only takes Claude models, so use a wrapper):
- Spawn a thin Claude wrapper agent with `model: 'sonnet', effort: 'low'` whose prompt instructs it to write a self-contained codex prompt, run `codex exec` via Bash, and return

## Codex pstack configuration

When using pstack from Codex, read `~/.codex/pstack-models.md` and apply its role and model overrides ahead of the defaults above and the installed pstack model matrix. These overrides apply only to Codex. Preserve the shared `~/.codex/AGENTS.md` symlink and keep the model configuration in its separate sheet; do not replace the shared baseline or inline the sheet here.

@~/.claude/pstack-models.md
