# Agentic Layer

Reusable *agentic layer*: the new ring around your codebase where you *teach your agents* to operate your application on your behalf as well and even *better than you and your team* ever could.

## Visualize it

```text
                    feature.md   chore.md   new_api_endpoint.md   update_api_endpoint.md   test_new_api_endpoint.md
                        \           |             |                      |                        /
                         \          |             |                      |                       /
     bug.md  ------------->[ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]<-------------  agents/
                          [ ]                                             [ ]<------------ review.md
    plan.md ------------->[ ]          [##] [##] [##]   [##] [##]         [ ]<------------ code-review.md
   build.md ------------->[ ]          [##] [##] [##]   [##] [##]         [ ]<------------ test-fe.md
pull_ticket.md ---------->[ ]                 APP / CODEBASE              [ ]<------------ start-apps.md
document.md  ------------>[ ]          [##] [##] [##]   [##] [##]         [ ]<------------ test-be.md
                          [ ]                                             [ ]<------------ reproduce.md
   CLAUDE.md  ----------->[ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ] [ ]<-------------  prime_w_tools.md
                           /    /      /       /
                      AGENTS.md  mcp.json   skills/   (task templates, runbooks, reviews)
```

## Claude Code mods

`mods/<name>/` holds Claude Code mods (hooks-module plugins). `./install-configs.sh` symlinks each into `~/.claude/skills/<name>/`, where Claude Code auto-loads and hot-reloads it.

- `highlight-me` – draws your own prompts in a round sunset box under a `★ YOU ★` tag.
- `compact-diffs` – folds Edit/Write/Bash diffs to a one-line `+n −m` summary; ctrl+o expands one, `/diffs` toggles all. Bind it in `~/.claude/keybindings.json`: `"ctrl+alt+d": "command:diffs"` (Chat context).

Check a mod with `claude plugin validate mods/<name>` and `claude plugin test mods/<name>`.
