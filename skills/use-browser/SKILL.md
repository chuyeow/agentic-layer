---
name: use-browser
description: Default protocol for browser automation. Load this skill FIRST whenever any task requires opening a browser, reading a webpage, filling a form, clicking buttons, taking screenshots, scraping data, or any web interaction. Defines the startup sequence, tool priority, and failure protocol so agents always try the right way first and stop on failure instead of guessing alternatives.
allowed-tools: Bash(agent-browser:*), mcp__claude-in-chrome__*, mcp__chrome-devtools__*
---

# Browser Automation Protocol

This is the **mandatory startup and usage protocol** for all browser automation. Follow it exactly. Do not skip steps. Do not improvise alternatives.

## Decide Path First: Public vs Authenticated

Before any command, classify the task:

- **Public path**: target page works without login (docs, news, public dashboards, search results, any URL that opens correctly in an incognito window). Use the **default path**. **Never pass `--auto-connect`.** Never require the user's Chrome to be running. Fresh headless Chrome handles this.
- **Authenticated path**: target page requires the user's login (their Slack, their GitHub dashboard, their admin panel, their email). Use the **auth path**. `--auto-connect` goes here, not in the default path.

If unsure, try public path first. Only switch to auth path if the page shows a login wall or the user explicitly says "use my session".

## Tool Priority Order

You have four browser tool families:

1. **agent-browser CLI** (primary, public pages) — headless Chrome via CDP. Always available. Use for public pages without login.
2. **browser-harness** (primary, auth pages) — attaches to user's running Chrome via CDP. No debug port flag needed. Use for any task that needs the user's logged-in session, or binary file downloads.
3. **claude-in-chrome MCP** — browser extension in the user's live Chrome. Fallback for auth path.
4. **chrome-devtools MCP** — DevTools protocol against user's Chrome. Fallback for auth path.

**Public page → agent-browser. Auth page → browser-harness.** Only use MCP tools if browser-harness fails and the user tells you to switch.

## Default Path (Public Pages)

### Step 1: Verify agent-browser is available

```bash
agent-browser --version
```

If this fails: **STOP. Tell the user.** Do not install it yourself. Do not use npx, curl a binary, brew, npm, cargo, or any other workaround. Say exactly what failed, then point the user to the "Install Guidance" section below and wait for instructions.

### Step 2: Open the target URL (no `--auto-connect`)

```bash
agent-browser open <url> && agent-browser wait --load networkidle && agent-browser snapshot -i
```

This spawns a fresh headless Chrome. It does **not** need the user's Chrome to be running. It does **not** need `--remote-debugging-port`. If you see "No running Chrome instance with remote debugging found", you accidentally used `--auto-connect` — drop that flag and rerun.

If this fails: **STOP. Tell the user.** Report the exact error. Do not:
- Try launching Chrome manually
- Try Playwright or Puppeteer
- Try curl/wget as a "fallback"
- Try any headless browser you've heard of
- Suggest the user install something else

### Step 3: Work with the page

Use the snapshot refs (`@e1`, `@e2`, etc.) to interact. Re-snapshot after any navigation or DOM change.

## Auth Path (Logged-In Pages)

Only use this path when the task explicitly needs the user's login. Public pages do not belong here.

### Option A: browser-harness (preferred)

browser-harness attaches to the user's running Chrome via a local Unix socket daemon. No debug port flag, no Chrome restart. Requires Chrome to be running.

**Setup (once per machine):**
```bash
git clone https://github.com/browser-use/browser-harness ~/code/browser-harness
cd ~/code/browser-harness
uv tool install -e .
command -v browser-harness   # should print a path
```

Then verify it can attach:
```bash
browser-harness -c "print(page_info())"
```

If Chrome shows an `Allow` dialog on `chrome://inspect`, click Allow. That setting is sticky — you only do it once per Chrome profile.

If the daemon session goes stale (`no close frame` / `Inspected target navigated or closed`):
```bash
cd ~/code/browser-harness && uv run python - <<'PY'
from admin import restart_daemon
restart_daemon()
PY
```

**Basic usage:**
```bash
# Navigate in a new tab (never goto_url first — it clobbers user's active tab)
browser-harness -c "
new_tab('https://app.example.com')
wait_for_load()
print(page_info())
capture_screenshot('/tmp/shot.png')
"
```

**Read the page / find elements:**
```bash
browser-harness -c "
links = js(\"Array.from(document.querySelectorAll('a')).map(el => ({href: el.href, text: el.textContent.trim().slice(0,60)}))\")
print(links)
"
```

**Click by coordinate** (screenshot first, then click):
```bash
browser-harness -c "
capture_screenshot('/tmp/shot.png')   # read image to find target coords
click_at_xy(x, y)
import time; time.sleep(1)
capture_screenshot('/tmp/after.png')  # verify
"
```

**Binary file downloads** — `http_get()` in helpers.py decodes as UTF-8 and fails on binary. Use urllib directly with CDP session cookies:
```bash
browser-harness -c "
import urllib.request, gzip

cookies = cdp('Network.getCookies', urls=['https://files.example.com'])
cookie_str = '; '.join(f\"{c['name']}={c['value']}\" for c in cookies.get('cookies', []))

req = urllib.request.Request(url, headers={
    'Cookie': cookie_str,
    'Referer': 'https://app.example.com/',
    'User-Agent': 'Mozilla/5.0',
})
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()
    if r.headers.get('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
open('/tmp/file.zip', 'wb').write(raw)
print('saved bytes:', len(raw))
"
```

If `browser-harness` is not installed: **STOP. Tell the user.** Show the setup steps above and wait.

### Option B: agent-browser --auto-connect (fallback)

```bash
agent-browser --auto-connect snapshot -i
```

Requires Chrome to expose a debug port. If you see `✗ No running Chrome instance with remote debugging found`, do not silently give up. Report the error, then present these options and wait:

1. **Restart Chrome with debug port:**
   ```bash
   # macOS — quit Chrome first, then:
   open -a "Google Chrome" --args --remote-debugging-port=9222
   ```
   After Chrome is up and logged in, say "retry".

2. Switch to claude-in-chrome MCP (Option C).
3. Switch to chrome-devtools MCP (Option D).

Do **not** pick one yourself. Wait for the user.

### Option C: Use claude-in-chrome MCP (if extension is active)

1. Call `mcp__claude-in-chrome__tabs_context_mcp` to check available tabs
2. Use `mcp__claude-in-chrome__navigate`, `mcp__claude-in-chrome__read_page`, etc.

If the MCP tool returns an error or timeout: **STOP. Tell the user.** Report the exact error.

### Option D: Use chrome-devtools MCP

1. Call `mcp__chrome-devtools__list_pages` to check connection
2. Use `mcp__chrome-devtools__navigate_page`, `mcp__chrome-devtools__take_screenshot`, etc.

### Option E: Session persistence (for repeated access)

```bash
# First time: connect to user's browser, save auth state
agent-browser --auto-connect state save ./auth-<service>.json
# Future runs: load saved state
agent-browser --state ./auth-<service>.json open <url>
```

## Failure Protocol

**This is critical.** When browser automation fails at any step:

1. **Report the exact error message.** Copy it verbatim.
2. **State which tool and command failed.**
3. **STOP and ask the user how to proceed.**

### What you MUST NOT do on failure:

- Do NOT try alternative browser tools unless the user tells you to
- Do NOT try to install or reinstall anything
- Do NOT use `curl`, `wget`, `fetch`, or HTTP clients as a "browser fallback"
- Do NOT use `WebFetch` or `WebSearch` as browser substitutes
- Do NOT say "the browser extension doesn't seem to be installed" — you cannot know that
- Do NOT say "the browser appears to be disconnected" and then give up — report the actual error
- Do NOT hallucinate browser tool names that don't exist
- Do NOT try Puppeteer, Selenium, or any framework not listed here

### What you SHOULD do on failure:

- Copy the exact error output
- Tell the user: "agent-browser failed with: [error]. How would you like me to proceed?"
- Wait for the user to choose the fallback approach

## Quick Reference

### Reading a public webpage
```bash
agent-browser open <url> && agent-browser wait --load networkidle && agent-browser snapshot -i
```

### Taking a screenshot
```bash
agent-browser open <url> && agent-browser wait --load networkidle && agent-browser screenshot output.png
```

### Filling a form
```bash
agent-browser open <url> && agent-browser wait --load networkidle && agent-browser snapshot -i
# Read the refs from snapshot output
agent-browser fill @e1 "value"
agent-browser fill @e2 "value"
agent-browser click @e3  # submit button
agent-browser wait --load networkidle && agent-browser snapshot -i  # verify result
```

### Extracting text from a page
```bash
agent-browser open <url> && agent-browser wait --load networkidle
agent-browser get text body
```

### Working with user's authenticated session
```bash
agent-browser --auto-connect snapshot -i
# OR
agent-browser --auto-connect open <url> && agent-browser wait --load networkidle && agent-browser snapshot -i
```

## Re-snapshot Rule

Refs (`@e1`, `@e2`) go stale after any page change. **Always re-snapshot** after:
- Clicking a link or button that navigates
- Submitting a form
- Content loading (modals, dropdowns, AJAX)
- Scrolling to load more content

```bash
agent-browser click @e5
agent-browser wait --load networkidle
agent-browser snapshot -i  # fresh refs
```

## Session Cleanup

Always close the browser when done:

```bash
agent-browser close
```

## Install Guidance (Surface This On Failure — Do Not Run)

When `agent-browser --version` fails or an MCP tool is missing, **do not install anything yourself**. Instead, print this block to the user verbatim and wait:

> **agent-browser is not installed or not on PATH.** See installation options and pick the one that fits your environment:
>
> https://github.com/vercel-labs/agent-browser
>
> After installing, tell me to retry.

For MCP tools (`claude-in-chrome`, `chrome-devtools`):

> **MCP tool `<name>` is not responding.** It may not be configured in your Claude Code setup. Check your MCP server configuration, install/enable the relevant extension or server, then tell me to retry.

The agent's job ends at surfacing these messages. The user reads the docs and decides how to install.
