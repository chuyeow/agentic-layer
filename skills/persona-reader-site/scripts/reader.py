#!/usr/bin/env python3
"""
persona-reader-site — build a single-file reading site for a person or company
from their tweets (weighted by engagement) and long-form writing.

Subcommands:
  x        scrape tweets via Camoufox (needs logged-in ~/.camoufox-x-profile)
  backfill re-fetch full text for truncated long tweets
  writing  scrape long-form posts (github_pages | bearblog | medium | rss | generic)
  build    render the self-contained index.html
  all      x -> backfill -> writing -> build

Run (camoufox subcommands MUST pin playwright):
  uvx --from "camoufox[geoip]" --with "playwright==1.55.0" \
      python reader.py all --config presets/karpathy.json

`build` and rss/github/bearblog `writing` work under plain python3 too.
Intermediate state is cached per-slug in ~/.cache/persona-reader/<slug>/,
so re-running is incremental (good for refreshes).
"""
import os, re, sys, json, html as H, argparse, subprocess, datetime

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

# ---------------------------------------------------------------- config / paths
def load_config(path):
    cfg = json.load(open(os.path.expanduser(path)))
    cfg.setdefault("title", cfg["name"])
    cfg.setdefault("subtitle", "")
    cfg.setdefault("out_dir", os.path.expanduser(f"~/{cfg['slug']}-site"))
    cfg["out_dir"] = os.path.expanduser(cfg["out_dir"])
    cfg.setdefault("x", {})
    cfg["x"].setdefault("handles", [])
    cfg["x"].setdefault("tabs", ["profile", "highlights"])
    cfg["x"].setdefault("search_slices", [])
    cfg["x"].setdefault("backfill_min_len", 250)
    cfg.setdefault("writing", [])
    return cfg

def cache_dir(cfg):
    d = os.path.expanduser(f"~/.cache/persona-reader/{cfg['slug']}")
    os.makedirs(d, exist_ok=True)
    return d

def cpath(cfg, name): return os.path.join(cache_dir(cfg), name)
def log(m): print(">>", m, flush=True)

# ---------------------------------------------------------------- camoufox helper
def camoufox(headless=True, profile=None):
    """Lazy import so non-camoufox subcommands run under plain python3."""
    from camoufox.sync_api import Camoufox
    kw = dict(headless=headless, os=("macos",))
    if profile:
        kw.update(persistent_context=True, user_data_dir=os.path.expanduser(profile))
    return Camoufox(**kw)

X_PROFILE = "~/.camoufox-x-profile"

EXTRACT_TL = r"""() => {
  return [...document.querySelectorAll('article[data-testid="tweet"]')].map(a => {
    const t = a.querySelector('time');
    const dt = t ? t.getAttribute('datetime') : '';
    const link = [...a.querySelectorAll('a[href*="/status/"]')]
      .map(x => x.getAttribute('href')).find(h => /\/status\/\d+/.test(h)) || '';
    const id = (link.match(/status\/(\d+)/) || [])[1] || '';
    const un = a.querySelector('[data-testid="User-Name"]');
    const handle = un ? ((un.innerText.match(/@\w+/) || [''])[0]) : '';
    const grp = a.querySelector('div[role="group"]');
    const metrics = grp ? (grp.getAttribute('aria-label') || '') : '';
    const tt = a.querySelector('[data-testid="tweetText"]');
    const body = tt ? tt.innerText : '';
    return {id, dt, handle, link, metrics, text: body || a.innerText};
  });
}"""

EXTRACT_FULL = r"""(tid) => {
  for (const a of document.querySelectorAll('article[data-testid="tweet"]')) {
    const link = [...a.querySelectorAll('a[href*="/status/"]')]
      .map(x => x.getAttribute('href')).find(h => h && h.includes('/status/' + tid));
    const tt = a.querySelector('[data-testid="tweetText"]');
    if (tt && (link || a === document.querySelector('article[data-testid="tweet"]')))
      return tt.innerText;
  }
  return null;
}"""

# ---------------------------------------------------------------- subcommand: x
def cmd_x(cfg):
    handles = [h.lstrip("@").lower() for h in cfg["x"]["handles"]]
    if not handles:
        log("no x.handles in config — skipping tweets"); return
    hset = {"@" + h for h in handles}

    slices = []
    for h in handles:
        if "profile" in cfg["x"]["tabs"]:
            slices.append((f"{h}-profile", f"https://x.com/{h}", 150))
        if "highlights" in cfg["x"]["tabs"]:
            slices.append((f"{h}-highlights", f"https://x.com/{h}/highlights", 80))
    for s in cfg["x"]["search_slices"]:
        q = s["query"].replace(":", "%3A").replace(" ", "%20")
        slices.append((s.get("label", "search"),
                       f"https://x.com/search?q={q}&f=live", s.get("max_rounds", 50)))

    out_path = cpath(cfg, "tweets.json")
    out = {}
    if os.path.exists(out_path):
        for r in json.load(open(out_path)): out[r["id"]] = r
        log(f"loaded checkpoint: {len(out)}")

    with camoufox(headless=True, profile=X_PROFILE) as ctx:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("pageerror", lambda e: None)
        page.set_viewport_size({"width": 1366, "height": 950})
        for label, url, max_rounds in slices:
            log(f"=== slice {label}: {url}")
            try: page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e: log(f"goto fail {e}"); continue
            page.wait_for_timeout(6000)
            if any(k in page.url for k in ["/login", "/i/flow", "/i/jf"]):
                log("WALL — not logged in. Run the one-time login (see SKILL.md)."); sys.exit(2)
            # search pages often show "Something went wrong. Try reloading."
            for attempt in range(6):
                if page.locator('article[data-testid="tweet"]').count() > 0: break
                retry = page.locator('button:has-text("Retry")')
                if retry.count():
                    try: retry.first.click()
                    except Exception: pass
                else:
                    try: page.reload(wait_until="domcontentloaded", timeout=60000)
                    except Exception: pass
                page.wait_for_timeout(8000 + attempt * 4000)
            stale = 0; slice_seen = 0
            for i in range(max_rounds):
                try: rows = page.evaluate(EXTRACT_TL)
                except Exception as e: log(f"extract fail {e}"); break
                gained = 0
                for r in rows:
                    if r["id"] and r["handle"].lower() in hset and r["id"] not in out:
                        out[r["id"]] = r; gained += 1; slice_seen += 1
                stale = stale + 1 if gained == 0 else 0
                if i % 5 == 0 or gained:
                    log(f"  round {i+1}: +{gained}, slice {slice_seen}, total {len(out)}")
                if stale >= 6: log("  stale x6 — end of slice"); break
                page.evaluate("window.scrollBy(0, 2600)")
                page.wait_for_timeout(1700)
            json.dump(list(out.values()), open(out_path, "w"), ensure_ascii=False, indent=1)
            log(f"=== {label} done: slice {slice_seen}, total {len(out)} (checkpointed)")
    log(f"==== tweets DONE: {len(out)} -> {out_path}")

# ---------------------------------------------------------------- subcommand: backfill
def likes_of(m):
    x = re.search(r'(\d+) likes', m); return int(x.group(1)) if x else 0

def cmd_backfill(cfg):
    handles = [h.lstrip("@").lower() for h in cfg["x"]["handles"]]
    if not handles: return
    primary = handles[0]
    tweets = json.load(open(cpath(cfg, "tweets.json")))
    ft_path = cpath(cfg, "fulltext.json")
    done = json.load(open(ft_path)) if os.path.exists(ft_path) else {}
    minlen = cfg["x"]["backfill_min_len"]
    cand = [r for r in tweets if len(r["text"]) >= minlen and r["id"] not in done]
    cand.sort(key=lambda r: likes_of(r["metrics"]), reverse=True)
    log(f"{len(cand)} to fetch, {len(done)} already done")
    if not cand: return
    with camoufox(headless=True, profile=X_PROFILE) as ctx:
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.on("pageerror", lambda e: None)
        page.set_viewport_size({"width": 1366, "height": 950})
        for i, r in enumerate(cand):
            url = f"https://x.com/{primary}/status/{r['id']}"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3500)
                txt = page.evaluate(EXTRACT_FULL, r["id"])
                if txt and len(txt) >= len(r["text"]) - 30:
                    done[r["id"]] = txt
                    log(f"{i+1}/{len(cand)} {r['id']} ok ({len(txt)})")
                else:
                    log(f"{i+1}/{len(cand)} {r['id']} MISS")
            except Exception as e:
                log(f"{i+1}/{len(cand)} {r['id']} ERR {e}")
            if (i + 1) % 10 == 0:
                json.dump(done, open(ft_path, "w"), ensure_ascii=False)
    json.dump(done, open(ft_path, "w"), ensure_ascii=False)
    log(f"==== backfill DONE: {len(done)} fulltexts")

# ---------------------------------------------------------------- subcommand: writing
def curl(url):
    r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                       capture_output=True, text=True)
    return r.stdout

def strip_tags(s):
    s = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', H.unescape(s)).strip()

def excerpt_after_title(body, title, n=400):
    idx = body.find(title)
    seg = body[idx + len(title): idx + len(title) + n] if idx >= 0 else body[:n]
    return clean_excerpt(seg)

def clean_excerpt(s):
    s = re.sub(r'^.{0,120}?\b\d{1,2} [A-Z][a-z]{2,8},? \d{4}\s*', '', s)
    s = re.sub(r'^.{0,120}?\b[A-Z][a-z]{2,8} \d{1,2},? \d{4}\s*', '', s)
    return s.strip()

MONTHS = {m: i+1 for i, m in enumerate(
    ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}

def src_github_pages(src):
    """Jekyll-style index: links like /YYYY/MM/DD/slug/."""
    base = src["url"].rstrip("/")
    root = re.match(r'https?://[^/]+', base).group(0)
    idx = curl(src["url"])
    posts = []
    for path, title in re.findall(r'href="(/\d{4}/[^"]+)"[^>]*>([^<]+)', idx):
        title = H.unescape(title).strip()
        if not title or title.startswith("("): continue
        url = root + path
        date = "-".join(path.strip("/").split("/")[0:3])
        page = strip_tags(curl(url))
        posts.append({"source": src.get("label", root.split("//")[1]),
                      "title": title, "url": url, "date": date,
                      "words": len(page.split()),
                      "excerpt": excerpt_after_title(page, title)})
        log(f"  gh: {title}")
    return posts

def src_bearblog(src):
    base = src["url"]; root = re.match(r'https?://[^/]+', base).group(0)
    idx = curl(base)
    posts = []
    for dt, path, title in re.findall(
            r'datetime="([^"]+)"[\s\S]*?href="(/[^"]+/)"[^>]*>\s*([^<]+?)\s*</a>', idx):
        url = root + path
        page = strip_tags(curl(url))
        title = H.unescape(title).strip()
        posts.append({"source": src.get("label", root.split("//")[1]),
                      "title": title, "url": url, "date": dt[:10],
                      "words": len(page.split()),
                      "excerpt": excerpt_after_title(page, title)})
        log(f"  bear: {title}")
    return posts

def src_rss(src):
    """Universal path: RSS 2.0 <item> or Atom <entry>. Best for company blogs."""
    feed = curl(src["url"])
    posts = []
    items = re.findall(r'<item\b[\s\S]*?</item>', feed) or \
            re.findall(r'<entry\b[\s\S]*?</entry>', feed)
    label = src.get("label", re.match(r'https?://([^/]+)', src["url"]).group(1))
    def tag(block, *names):
        for nm in names:
            m = re.search(rf'<{nm}[^>]*>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</{nm}>', block)
            if m: return m.group(1).strip()
        return ""
    for it in items:
        title = strip_tags(tag(it, "title"))
        link = tag(it, "link") or ""
        if not link:  # Atom uses <link href="...">
            m = re.search(r'<link[^>]*href="([^"]+)"', it); link = m.group(1) if m else ""
        raw_date = tag(it, "pubDate", "published", "updated", "dc:date")
        date = normalize_date(raw_date)
        desc = clean_excerpt(strip_tags(tag(it, "description", "summary", "content")))[:400]
        if title:
            posts.append({"source": label, "title": title, "url": link,
                          "date": date, "words": None, "excerpt": desc})
            log(f"  rss: {title}")
    return posts

def normalize_date(s):
    s = s.strip()
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m: return m.group(0)
    # RFC822: "Wed, 10 Jun 2026 ..."
    m = re.search(r'(\d{1,2}) (\w{3}) (\d{4})', s)
    if m: return f"{m.group(3)}-{MONTHS.get(m.group(2),1):02d}-{int(m.group(1)):02d}"
    return ""

def src_medium(src):
    """Cloudflare-gated — needs Camoufox."""
    handle = src["handle"].lstrip("@")
    with camoufox(headless=True) as browser:
        page = browser.new_page()
        page.on("pageerror", lambda e: None)
        page.goto(f"https://medium.com/@{handle}", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        for _ in range(12):
            page.evaluate("window.scrollBy(0, 2200)"); page.wait_for_timeout(1400)
        cards = page.evaluate(r"""() => {
          const out = [];
          document.querySelectorAll('h2').forEach(h => {
            const a = h.closest('a');
            let root = h; for (let i=0;i<8 && root.parentElement;i++) root = root.parentElement;
            const link = a ? a.getAttribute('href')
              : (root.querySelector('a[href]')||{getAttribute:()=>''}).getAttribute('href');
            const txt = root.innerText || '';
            const dm = txt.match(/[A-Z][a-z]{2} \d{1,2}, \d{4}/);
            const sub = root.querySelector('h3, p');
            out.push({title: h.innerText.trim(), link: link||'',
                      date: dm?dm[0]:'', blurb: sub?(sub.innerText||'').slice(0,300):''});
          });
          return out;
        }""")
    seen = set(); posts = []
    for c in cards:
        t = c["title"]
        if not t or t in seen or "signin" in c["link"] or t.lower() == handle.lower():
            continue
        seen.add(t)
        link = c["link"].split("?")[0]
        url = (f"https://{handle}.medium.com" + link) if link.startswith("/") else link
        dm = re.match(r'(\w{3}) (\d{1,2}), (\d{4})', c["date"] or "")
        date = f"{dm.group(3)}-{MONTHS[dm.group(1)]:02d}-{int(dm.group(2)):02d}" if dm else ""
        posts.append({"source": "medium", "title": t, "url": url,
                      "date": date, "words": None, "excerpt": clean_excerpt(c["blurb"])})
        log(f"  md: {t}")
    return posts

def src_generic(src):
    """Config supplies a link_pattern regex with 2 groups: (href, title)."""
    idx = curl(src["url"]); root = re.match(r'https?://[^/]+', src["url"]).group(0)
    posts = []
    for href, title in re.findall(src["link_pattern"], idx):
        url = href if href.startswith("http") else root + href
        posts.append({"source": src.get("label", root.split("//")[1]),
                      "title": H.unescape(title).strip(), "url": url,
                      "date": src.get("date", ""), "words": None, "excerpt": ""})
        log(f"  generic: {title}")
    return posts

SRC_FN = {"github_pages": src_github_pages, "bearblog": src_bearblog,
          "rss": src_rss, "medium": src_medium, "generic": src_generic}

def cmd_writing(cfg):
    posts = []
    for src in cfg["writing"]:
        fn = SRC_FN.get(src["type"])
        if not fn: log(f"unknown writing type {src['type']}"); continue
        log(f"=== writing source: {src['type']} {src.get('url', src.get('handle',''))}")
        try: posts += fn(src)
        except Exception as e: log(f"source fail {e}")
    json.dump(posts, open(cpath(cfg, "writing.json"), "w"), ensure_ascii=False, indent=1)
    log(f"==== writing DONE: {len(posts)} posts")

# ---------------------------------------------------------------- subcommand: build
def parse_metrics(m):
    out = {}
    for n, k in re.findall(r'(\d+) (replies|reposts|likes|bookmarks|views)', m):
        out[k] = int(n)
    return out

def cmd_build(cfg):
    scraped = datetime.date.today().isoformat()
    tw_path = cpath(cfg, "tweets.json")
    tweets = json.load(open(tw_path)) if os.path.exists(tw_path) else []
    ft_path = cpath(cfg, "fulltext.json")
    fulltext = json.load(open(ft_path)) if os.path.exists(ft_path) else {}
    wr_path = cpath(cfg, "writing.json")
    writing = json.load(open(wr_path)) if os.path.exists(wr_path) else []

    rows = []
    for t in tweets:
        mm = parse_metrics(t["metrics"])
        body = fulltext.get(t["id"], t["text"])
        trunc = t["id"] not in fulltext and len(t["text"]) >= cfg["x"]["backfill_min_len"]
        link = t["link"]
        if link.startswith("/"): link = "https://x.com" + link
        rows.append({"id": t["id"], "dt": t["dt"][:10], "link": link, "text": body,
                     "likes": mm.get("likes", 0), "reposts": mm.get("reposts", 0),
                     "views": mm.get("views", 0), "trunc": trunc})
    rows.sort(key=lambda r: r["likes"], reverse=True)

    wseen = set(); wrows = []
    for w in writing:
        key = (w.get("title") or "").lower()
        if not key or key in wseen: continue
        wseen.add(key)
        w["excerpt"] = clean_excerpt(w.get("excerpt") or "")
        wrows.append(w)
    wrows.sort(key=lambda w: w.get("date") or "0000", reverse=True)

    years = sorted({r["dt"][:4] for r in rows})
    src_labels = sorted({w["source"] for w in wrows})
    about = build_about(cfg, scraped, rows, wrows, src_labels)
    stats = {"years": years, "scraped": scraped}
    data = json.dumps({"tweets": rows, "writing": wrows, "stats": stats},
                      ensure_ascii=False).replace("</", "<\\/")

    page = (TEMPLATE
            .replace("__TITLE__", H.escape(cfg["title"]))
            .replace("__SUBTITLE__", H.escape(cfg["subtitle"]))
            .replace("__KICKER__", H.escape("corpus · " + cfg["name"]).lower())
            .replace("__ABOUT__", about)
            .replace("__NT__", str(len(rows)))
            .replace("__NW__", str(len(wrows)))
            .replace("__SCRAPED__", scraped)
            .replace("__DATA__", data))
    os.makedirs(cfg["out_dir"], exist_ok=True)
    out = os.path.join(cfg["out_dir"], "index.html")
    open(out, "w").write(page)
    log(f"wrote {out} ({len(page)} bytes); {len(rows)} tweets, {len(wrows)} writing, "
        f"{len(fulltext)} fulltexts")

def build_about(cfg, scraped, rows, wrows, src_labels):
    handles = ", ".join("@" + h.lstrip("@") for h in cfg["x"]["handles"]) or "—"
    srcs = "".join(f"<li>{H.escape(s)}</li>" for s in src_labels)
    tweet_line = (f"<li><strong>Tweets</strong>: from {H.escape(handles)} — profile timeline"
                  " + X's <em>Highlights</em> tab (X's own curation of top tweets, which "
                  "supplies the popularity weighting for older years). Engagement counts "
                  "captured per tweet; long posts re-fetched individually for full text.</li>"
                  if rows else "")
    return (f"<p>Scraped {scraped} via Camoufox (stealth Firefox) "
            f"from a logged-in X session plus direct fetches of the writing sources.</p>"
            f"<ul style='font-size:16.5px;line-height:1.7'>{tweet_line}"
            f"<li><strong>Writing sources</strong>:<ul>{srcs}</ul></li>"
            f"<li>Default tweet sort is most-liked. Search-based historical sweeps may be "
            f"unavailable to the scraping account; older coverage then leans on Highlights.</li>"
            f"</ul>")

# ---------------------------------------------------------------- HTML template
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,700;1,6..72,400&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {
  color-scheme: light dark;
  --paper: light-dark(#f6f1e7, #16140f);
  --card: light-dark(#fdfaf3, #1e1b14);
  --ink: light-dark(#221d14, #e8e0cf);
  --muted: light-dark(#857b66, #978d77);
  --line: light-dark(#ddd3c0, #383225);
  --accent: light-dark(#b3431b, #e0683a);
  --accent-ink: light-dark(#7c2d10, #f0916b);
  --gold: light-dark(#8a6d1d, #cdab4a);
  --serif: "Newsreader", Georgia, serif;
  --mono: "JetBrains Mono", ui-monospace, monospace;
  accent-color: var(--accent);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font-family: var(--serif); font-size: 19px; line-height: 1.55; }
.wrap { max-width: 760px; margin: 0 auto; padding: 0 20px 80px; }
header { padding: 56px 0 8px; border-bottom: 3px double var(--line); }
.kicker { font-family: var(--mono); font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: var(--accent); }
h1 { font-size: 46px; font-weight: 700; margin: 6px 0 4px; line-height: 1.05; }
.sub { color: var(--muted); font-style: italic; margin: 0 0 18px; }
nav.tabs { position: sticky; top: 0; z-index: 5; background: var(--paper); display: flex; gap: 4px;
  border-bottom: 1px solid var(--line); padding: 10px 0 0; }
nav.tabs button { font-family: var(--mono); font-size: 13px; letter-spacing: .06em; cursor: pointer;
  background: none; border: none; border-bottom: 3px solid transparent; color: var(--muted); padding: 8px 14px 10px; }
nav.tabs button.on { color: var(--accent-ink); border-bottom-color: var(--accent); }
nav.tabs button:hover { color: var(--ink); }
.controls { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-family: var(--mono); font-size: 12.5px; padding: 16px 0 6px; }
.controls input[type=search] { flex: 1; min-width: 180px; font: inherit; color: var(--ink);
  background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 7px 10px; }
.controls select { font: inherit; color: var(--ink); background: var(--card); border: 1px solid var(--line); border-radius: 4px; padding: 6px 8px; }
.chips { display: flex; flex-wrap: wrap; gap: 5px; padding: 4px 0 10px; font-family: var(--mono); font-size: 11.5px; }
.chips button { cursor: pointer; background: var(--card); color: var(--muted); border: 1px solid var(--line); border-radius: 99px; padding: 3px 10px; font: inherit; }
.chips button.on { background: var(--accent); border-color: var(--accent); color: #fff8ee; }
.count { color: var(--muted); font-family: var(--mono); font-size: 12px; padding: 2px 0 14px; }
article.tw { background: var(--card); border: 1px solid var(--line); border-radius: 6px; padding: 18px 20px 14px; margin: 0 0 14px; }
article.tw.mega { border-left: 4px solid var(--gold); }
.twhead { display: flex; gap: 10px; align-items: baseline; font-family: var(--mono); font-size: 12px; color: var(--muted); margin-bottom: 8px; }
.rank { color: var(--gold); font-weight: 700; }
.twhead a { color: var(--muted); text-decoration: none; margin-left: auto; }
.twhead a:hover { color: var(--accent); }
.twbody { white-space: pre-wrap; overflow-wrap: break-word; font-size: 19px; }
.twbody.clamp { display: -webkit-box; -webkit-line-clamp: 7; -webkit-box-orient: vertical; overflow: hidden; }
.more { font-family: var(--mono); font-size: 12px; color: var(--accent); background: none; border: none; cursor: pointer; padding: 6px 0 0; }
.twfoot { display: flex; gap: 16px; font-family: var(--mono); font-size: 12px; color: var(--muted); border-top: 1px dashed var(--line); margin-top: 12px; padding-top: 9px; }
.likes { color: var(--accent-ink); font-weight: 500; }
.truncnote { color: var(--gold); }
.essay { padding: 18px 2px 16px; border-bottom: 1px solid var(--line); }
.essay h3 { margin: 0 0 4px; font-size: 24px; font-weight: 500; }
.essay h3 a { color: var(--ink); text-decoration: none; }
.essay h3 a:hover { color: var(--accent); }
.emeta { font-family: var(--mono); font-size: 11.5px; color: var(--muted); display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 6px; }
.src { color: var(--accent-ink); }
.excerpt { color: var(--muted); font-size: 16.5px; margin: 0; }
.about { font-size: 16.5px; line-height: 1.7; }
.about a { color: var(--accent-ink); }
footer { margin-top: 56px; border-top: 3px double var(--line); padding-top: 14px; font-family: var(--mono); font-size: 11.5px; color: var(--muted); line-height: 1.7; }
footer a { color: var(--accent-ink); }
@media (max-width: 540px) { h1 { font-size: 34px; } body { font-size: 17px; } .twbody { font-size: 17px; } }
</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">__KICKER__</div>
  <h1>__TITLE__</h1>
  <p class="sub">__SUBTITLE__</p>
</header>
<nav class="tabs" id="tabs"></nav>
<section id="tab-tweets" hidden>
  <div class="controls">
    <input type="search" id="q" placeholder="search tweets…">
    <select id="sort">
      <option value="likes">sort: most liked</option>
      <option value="views">sort: most viewed</option>
      <option value="recent">sort: newest</option>
      <option value="oldest">sort: oldest</option>
    </select>
  </div>
  <div class="chips" id="years"></div>
  <div class="count" id="count"></div>
  <div id="list"></div>
</section>
<section id="tab-writing" hidden>
  <div class="count" id="wcount"></div>
  <div id="wlist"></div>
</section>
<section id="tab-about" hidden>
  <h2 style="font-weight:500">How this was built</h2>
  <div class="about">__ABOUT__</div>
</section>
<footer>
  __NT__ tweets · __NW__ long-form pieces · scraped __SCRAPED__ · built with Camoufox + Claude Code<br>
  All content © its author; this is a personal reading index. Links go to originals.
</footer>
</div>
<script type="application/json" id="data">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const HAS_TW = D.tweets.length > 0;
const fmt = n => n >= 1e6 ? (n/1e6).toFixed(1)+'M' : n >= 1e3 ? (n/1e3).toFixed(n<1e4?1:0)+'K' : ''+n;
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;');

// tabs (tweets tab only if there are tweets)
const tabsEl = document.getElementById('tabs');
const TABS = (HAS_TW ? [['tweets','TWEETS']] : []).concat([['writing','WRITING'],['about','SOURCES']]);
TABS.forEach(([id,label], i) => {
  const b = document.createElement('button');
  b.textContent = label; b.dataset.tab = id;
  if (i === 0) b.classList.add('on');
  b.onclick = () => {
    tabsEl.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b));
    ['tweets','writing','about'].forEach(t => {
      const sec = document.getElementById('tab-'+t); if (sec) sec.hidden = (t !== id);
    });
  };
  tabsEl.appendChild(b);
});
document.getElementById('tab-' + TABS[0][0]).hidden = false;

if (HAS_TW) {
  let yearSel = null;
  const yearsEl = document.getElementById('years');
  const allBtn = document.createElement('button');
  allBtn.textContent = 'all years'; allBtn.classList.add('on');
  allBtn.onclick = () => { yearSel = null; setChips(); render(); };
  yearsEl.appendChild(allBtn);
  D.stats.years.forEach(y => {
    const b = document.createElement('button');
    b.textContent = y; b.dataset.y = y;
    b.onclick = () => { yearSel = (yearSel === y ? null : y); setChips(); render(); };
    yearsEl.appendChild(b);
  });
  function setChips() {
    yearsEl.querySelectorAll('button').forEach(b =>
      b.classList.toggle('on', b.dataset.y ? b.dataset.y === yearSel : yearSel === null));
  }
  const q = document.getElementById('q'), sortSel = document.getElementById('sort');
  q.addEventListener('input', render); sortSel.addEventListener('change', render);
  function render() {
    const term = q.value.trim().toLowerCase();
    let rows = D.tweets.filter(t =>
      (!yearSel || t.dt.startsWith(yearSel)) && (!term || t.text.toLowerCase().includes(term)));
    const s = sortSel.value;
    if (s === 'likes') rows.sort((a,b) => b.likes - a.likes);
    if (s === 'views') rows.sort((a,b) => b.views - a.views);
    if (s === 'recent') rows.sort((a,b) => b.dt.localeCompare(a.dt));
    if (s === 'oldest') rows.sort((a,b) => a.dt.localeCompare(b.dt));
    document.getElementById('count').textContent = rows.length + ' tweets';
    const list = document.getElementById('list');
    list.innerHTML = rows.slice(0, 400).map((t, i) => {
      const rank = s === 'likes' ? '<span class="rank">#' + (i+1) + '</span>' : '';
      const long = t.text.length > 600;
      return '<article class="tw' + (t.likes >= 25000 ? ' mega' : '') + '">'
        + '<div class="twhead">' + rank + '<span>' + t.dt + '</span>'
        + '<a href="' + t.link + '" target="_blank" rel="noopener">on x ↗</a></div>'
        + '<div class="twbody' + (long ? ' clamp' : '') + '">' + esc(t.text) + '</div>'
        + (long ? '<button class="more">⌄ expand</button>' : '')
        + '<div class="twfoot"><span class="likes">♥ ' + fmt(t.likes) + '</span>'
        + '<span>⇄ ' + fmt(t.reposts) + '</span>'
        + (t.views ? '<span>◉ ' + fmt(t.views) + '</span>' : '')
        + (t.trunc ? '<span class="truncnote">truncated — read full on X</span>' : '')
        + '</div></article>';
    }).join('');
    list.querySelectorAll('.more').forEach(b => b.addEventListener('click', () => {
      const body = b.previousElementSibling;
      const open = body.classList.toggle('clamp');
      b.textContent = open ? '⌄ expand' : '⌃ collapse';
    }));
  };
  render();
}

// writing
const wl = document.getElementById('wlist');
document.getElementById('wcount').textContent = D.writing.length + ' pieces, newest first';
wl.innerHTML = D.writing.map(w => {
  const mins = w.words ? Math.max(1, Math.round(w.words / 230)) + ' min' : '';
  return '<div class="essay"><h3><a href="' + w.url + '" target="_blank" rel="noopener">'
    + esc(w.title) + '</a></h3>'
    + '<div class="emeta"><span>' + (w.date || '') + '</span><span class="src">' + esc(w.source) + '</span>'
    + (mins ? '<span>' + mins + '</span>' : '') + '</div>'
    + (w.excerpt ? '<p class="excerpt">' + esc(w.excerpt) + '…</p>' : '') + '</div>';
}).join('');
</script>
</body>
</html>"""

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["x", "backfill", "writing", "build", "all"])
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    cfg = load_config(a.config)
    if a.cmd in ("x", "all"): cmd_x(cfg)
    if a.cmd in ("backfill", "all"): cmd_backfill(cfg)
    if a.cmd in ("writing", "all"): cmd_writing(cfg)
    if a.cmd in ("build", "all"): cmd_build(cfg)

if __name__ == "__main__":
    main()
