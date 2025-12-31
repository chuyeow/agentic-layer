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
