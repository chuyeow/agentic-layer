---
name: persona-reader-site
description: Build a single-file reading site for any person or company from their tweets (ranked by engagement) and long-form writing (blogs, Medium, RSS). Use when the user says "build/refresh a reader site for <person/company>", "scrape <handle>'s tweets and writing into a site", "make Karpathy's writing easier to read", "turn <someone>'s posts into a mini site", or wants a personal index of someone's public output. Backed by Camoufox (stealth Firefox) + a logged-in X profile.
allowed-tools: Bash(curl:*)
---

> **Permissions note**: `allowed-tools` auto-approves `curl` only *while this skill is
> active* (scoped to the skill lifecycle, not session-wide) — used to fetch RSS/HTML for
> writing sources. The `uvx`/`python3` scrape + build steps are intentionally NOT
> pre-approved; they prompt per run. To auto-approve those too, add them here, but note
> they are broad capabilities (arbitrary PyPI execution / arbitrary code).

# persona-reader-site

Builds a self-contained `index.html` reading site for a **subject** (a person or a
company) from two corpora:

1. **Tweets** — scraped from X, ranked by likes, filterable by year, full-text searchable.
2. **Writing** — long-form posts from blogs / Medium / RSS, newest first, with excerpts.

Everything is config-driven. One subject = one JSON config. Re-running refreshes
incrementally (state cached per-slug), so this doubles as a refresh tool.

## When to use

- "Build a reader site for Karpathy / refresh it"
- "Scrape <person>'s tweets + writing into a mini site"
- "Do the same thing for <other person or company>"

## Architecture

```
scripts/reader.py      one CLI, subcommands: x | backfill | writing | build | all
presets/karpathy.json  worked example (person: 2 blogs + Medium + X)
presets/company-example.json  worked example (company: RSS + X)
```

State cache: `~/.cache/persona-reader/<slug>/{tweets,fulltext,writing}.json`
Output: `<out_dir>/index.html` (single file, data embedded, no server needed).

## Config schema

```jsonc
{
  "slug": "karpathy",                 // cache key + default dir name
  "name": "Andrej Karpathy",          // shown in kicker + sources tab
  "title": "Karpathy Reader",         // <h1> + page title
  "subtitle": "…",                    // italic tagline
  "out_dir": "~/code/karpathy-site",  // where index.html lands
  "x": {
    "handles": ["karpathy"],          // [] => no tweets tab; site = writing only
    "tabs": ["profile", "highlights"],// "highlights" = X's own top-tweet curation
    "search_slices": [],              // optional: [{label, query, max_rounds}]
    "backfill_min_len": 250,          // tweets >= this many chars get full-text re-fetch
    "backfill_passes": 4,             // auto-retry passes for rate-limited misses
    "exclude": []                     // any of: "replies", "reposts" (filtered at build)
  },
  "writing": [                        // any mix; runs in order
    { "type": "sitemap", "url": "https://site.com/sitemap.xml", "path_pattern": "/blog/", "limit": 150 },
    { "type": "github_pages", "url": "https://karpathy.github.io/" },
    { "type": "bearblog",     "url": "https://karpathy.bearblog.dev/blog/" },
    { "type": "medium",       "handle": "karpathy" },
    { "type": "rss",          "url": "https://blog.example.com/rss.xml" },
    { "type": "generic",      "url": "...", "link_pattern": "href=\"(/posts/[^\"]+)\"[^>]*>([^<]+)" }
  ]
}
```

**Writing source types** (prefer `sitemap` for full archives, `rss` for a quick recent slice):
- `sitemap` — **best for full archives.** Reads `sitemap.xml` (follows nested sitemap indexes, depth/fetch-capped), keeps URLs matching `path_pattern` (regex, e.g. `/blog/`), newest-first by `<lastmod>`. Options: `limit` (default 100), `fetch_pages` (default false — when true, fetches each page for a real `<h1>` title + excerpt + word count; leave false for large archives, titles are then slug-derived), `sitemap_stem` (override which sub-sitemaps to descend; defaults to the alphanumeric stem of `path_pattern`). Fixes the recency cap that RSS/JS-indexes hit.
- `github_pages` — Jekyll-style index, post links like `/YYYY/MM/DD/slug/`. Date from URL, word count + excerpt from each page.
- `bearblog` — bearblog.dev index (`<time datetime>` + link). Word count + excerpt.
- `medium` — Cloudflare-gated, so uses Camoufox; scrolls the profile, reads post cards.
- `rss` — universal but **usually capped to the latest ~10–20 items** (e.g. WordPress). Good for a quick recent slice; use `sitemap` when you want the whole back-catalogue.
- `generic` — supply a `link_pattern` regex with two groups `(href, title)`. Last resort.

**Tweet quality knobs**:
- `exclude: ["replies","reposts"]` — drop the account's replies and/or reposts (filtered at *build* time from cached `social`/`reply` flags, so toggling just needs a rebuild, no re-scrape). Useful for noisy brand/active accounts. Note: reposts of *other* people are already excluded by handle-matching; this mainly catches replies and self-quote noise.
- `backfill` auto-retries rate-limited misses across `backfill_passes` passes and records genuine no-text tweets (media/quote) in `nofull.json` so they aren't chased forever or flagged as "truncated". No more manual re-runs.

## Prerequisites

- **Camoufox** installed (stealth Firefox): `uv tool install "camoufox[geoip]"` then `python3 -m camoufox fetch`.
- **A logged-in X profile** at `~/.camoufox-x-profile` (one-time, manual). Tweet scraping reads this profile's session — without it X shows an auth wall.

### One-time X login (only needed for the `x`/`backfill` steps)

Run a headed Camoufox against the persistent profile, log in by hand, then close:

```bash
uvx --from "camoufox[geoip]" --with "playwright==1.55.0" python - <<'PY'
import os
from camoufox.sync_api import Camoufox
with Camoufox(headless=False, persistent_context=True,
              user_data_dir=os.path.expanduser("~/.camoufox-x-profile"),
              os=("macos",)) as ctx:
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://x.com/login")
    input("Log in (incl. 2FA) in the window, then press Enter here to save + close…")
PY
```

Session persists in the profile dir; reuse it indefinitely for any subject.

## Run

**Always pin `playwright==1.55.0`** for the Camoufox steps — newer Node drivers crash
on X's uncaught page errors. `build` and RSS/github/bearblog `writing` also run fine
under plain `python3`.

```bash
cd ~/.claude/skills/persona-reader-site

# full pipeline for a subject
uvx --from "camoufox[geoip]" --with "playwright==1.55.0" \
    python scripts/reader.py all --config presets/karpathy.json

# or step-by-step (each is resumable / checkpointed):
uvx --from "camoufox[geoip]" --with "playwright==1.55.0" python scripts/reader.py x        --config presets/karpathy.json
uvx --from "camoufox[geoip]" --with "playwright==1.55.0" python scripts/reader.py backfill --config presets/karpathy.json
python3 scripts/reader.py writing --config presets/karpathy.json   # no camoufox unless source includes medium
python3 scripts/reader.py build   --config presets/karpathy.json
```

The `x` and `backfill` steps are long (minutes) and hit X rate limits — run them
**in the background**. `backfill` now auto-retries misses across `backfill_passes`
passes (resuming from the checkpoint) and stops once it makes no progress, so a single
invocation is enough. Then `build`.

## Refreshing

Just re-run. `x`/`backfill` only fetch tweets/full-text not already cached;
`writing` re-scrapes (sources are small); `build` always regenerates with today's date.
To force a clean rebuild, delete `~/.cache/persona-reader/<slug>/`.

## Add a new subject

1. Copy a preset, edit `slug`/`name`/`title`/`subtitle`/`out_dir`.
2. Set `x.handles` (or `[]` for writing-only).
3. List `writing` sources — try `rss` first; fall back to a typed scraper if no feed.
4. Run `all`. Screenshot to eyeball, then `open <out_dir>/index.html`.

## Notes / gotchas

- X **search** is often blocked for the scraping account ("Something went wrong"). The
  scraper retries, but if it stays empty, rely on `profile` + `highlights` tabs (the
  default). `highlights` is X's own curation of the account's top tweets — good
  popularity signal for older years the timeline won't scroll back to.
- Tweets longer than ~280 chars are truncated in timeline DOM; `backfill` opens each
  status page for full text. Genuine media/quote tweets (no longer text) are recorded in
  `nofull.json` and NOT flagged "truncated"; only true unresolved fetches get the flag.
- Camoufox's `emulate_media(color_scheme=...)` errors on this build — to screenshot dark
  mode, set `document.documentElement.style.colorScheme='dark'` via `page.evaluate`.
- Design: warm-paper kissaten palette, Newsreader + JetBrains Mono, `light-dark()` auto
  theme. Edit `TEMPLATE` in `reader.py` to restyle.
