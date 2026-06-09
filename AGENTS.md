Chu Yeow owns this. Work style: minimal filler; noun-phrases ok; drop grammar; min tokens.

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

- Prose: en-dashes (–) not em-dashes (—); my signature. Jira: em-dash → colon.
- Copy: plain not flowery; concise not repetitive. Slides: terse — verbalized live, not read literally.

## Build + test

- Handoff gate: run lint/typecheck/tests/docs.
- TDD: test first; red/green/refactor; use the `tdd` skill.
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Keep it observable: logs, panes, tails, MCP/browser tools.

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
  </frontend_aesthetics>

## Principle: Functional Core, Imperative Shell

- **Core logic**: Pure functions only—no I/O, time, randomness, or global state
- **Side effects**: Isolate to a thin outer shell (DB, network, logging, clocks)
- **Pattern**: Represent effects as data/return values from core; interpret at boundaries
- **Flow**: Core returns "what to do," shell executes "how to do it"
