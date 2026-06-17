#!/usr/bin/env bun
// live-review channel server.
//
// A Claude Code *channel* (MCP server) that serves ANY HTML file with a comment
// widget injected, and pushes each comment into the live Claude session as a
// <channel source="live-review" ...> event. Two-way: Claude calls `reply` to write
// a response back onto the page. Spawned by Claude Code from an MCP config.
//
// Env:
//   TARGET  absolute path to the HTML file under review   (required)
//   PORT    HTTP port for the viewer                       (default 4399)
//   LR_DIR  this skill's directory (for assets)            (default: dir of this file)
//
// Gating: bound to 127.0.0.1; /_lr/comment rejects cross-site browser POSTs
// (Sec-Fetch-Site / Origin) — a comment becomes a prompt in a tool-enabled session.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { readFile, writeFile, mkdir } from "fs/promises";
import { watch } from "fs";
import { join, dirname, basename } from "path";

const TARGET = Bun.env.TARGET || "";
const PORT = Number(Bun.env.PORT ?? 4399);
const LR_DIR = Bun.env.LR_DIR || import.meta.dir;
const ASSETS = join(LR_DIR, "assets");
const SESSION = Bun.env.SESSION || "";  // tmux session name, for the in-page "watch" hint
if (!TARGET) { console.error("live-review: TARGET env (HTML file path) is required"); process.exit(1); }

// Comments live in the skill's own .run/ dir keyed by a hash of the target path —
// never a sidecar file dropped into the directory of the file under review.
const RUN_DIR = join(LR_DIR, ".run");
const keyHash = (s: string) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0; return (h >>> 0).toString(36); };
const STORE = join(RUN_DIR, `${keyHash(TARGET)}.comments.json`);
await mkdir(RUN_DIR, { recursive: true }).catch(() => {});

type Comment = { id: string; anchor: string; section_title: string; quote: string; text: string; at: string; reply?: string; resolved?: boolean };
const comments: Comment[] = [];
let seq = 1;
try { const s = JSON.parse(await readFile(STORE, "utf8")); if (Array.isArray(s)) { comments.push(...s); seq = comments.length + 1; } } catch {}
async function persist(){ try { await writeFile(STORE, JSON.stringify(comments, null, 2)); } catch {} }

const sockets = new Set<any>();
watch(dirname(TARGET), { recursive: false }, (_e, f) => {
  if (!f || f === basename(TARGET)) for (const ws of sockets) { try { ws.send("reload"); } catch {} }
});

const INJECT =
  `\n<link rel="stylesheet" href="/_lr/widget.css">\n<script type="module" src="/_lr/widget.js"></script>\n`;

const mcp = new Server(
  { name: "live-review", version: "1.0.0" },
  {
    capabilities: { experimental: { "claude/channel": {} }, tools: {} },
    instructions:
      `You are the reviewer-facing Claude for the HTML file "${TARGET}". Comments arrive as ` +
      `<channel source="live-review" comment_id="..." section="..." anchor="..."> with the reviewer's ` +
      `note as the body (plus an optional quoted passage). For each: make the requested change by editing ` +
      `${TARGET} directly (the viewer hot-reloads), then call the \`reply\` tool with the comment_id to tell ` +
      `the reviewer what you changed, passing resolved:true once it is fully addressed. If a comment is a ` +
      `question, answer via \`reply\` with resolved:true without editing.`,
  },
);

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "reply",
    description: "Post a reply under a specific comment in the reviewer's browser, and optionally mark it resolved once addressed.",
    inputSchema: { type: "object",
      properties: { comment_id: { type: "string", description: "comment_id from the <channel> tag" },
                    text: { type: "string", description: "your reply to the reviewer" },
                    resolved: { type: "boolean", description: "set true once the comment is fully addressed (edit made or question answered)" } },
      required: ["comment_id", "text"] },
  }],
}));
mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "reply") {
    const { comment_id, text, resolved } = req.params.arguments as { comment_id: string; text: string; resolved?: boolean };
    const c = comments.find(x => x.id === comment_id);
    if (!c) return { content: [{ type: "text", text: `no comment ${comment_id}` }], isError: true };
    c.reply = text; if (resolved) c.resolved = true; await persist();
    return { content: [{ type: "text", text: `reply posted under ${comment_id}${resolved ? " (resolved)" : ""}` }] };
  }
  throw new Error(`unknown tool: ${req.params.name}`);
});

await mcp.connect(new StdioServerTransport());

const server = Bun.serve({
  port: PORT, hostname: "127.0.0.1",
  async fetch(req, srv) {
    const url = new URL(req.url);

    if (url.pathname === "/_lr/ws") { if (srv.upgrade(req)) return; return new Response("ws fail", { status: 400 }); }
    if (url.pathname === "/_lr/widget.js") return new Response(Bun.file(join(ASSETS, "widget.js")), { headers: { "Content-Type": "text/javascript" } });
    if (url.pathname === "/_lr/widget.css") return new Response(Bun.file(join(ASSETS, "widget.css")), { headers: { "Content-Type": "text/css" } });
    if (url.pathname === "/_lr/whoami") return Response.json({ mechanism: "claude-channel", target: basename(TARGET), session: SESSION });
    if (url.pathname === "/_lr/comments") return Response.json(comments);

    if (url.pathname === "/_lr/comment" && req.method === "POST") {
      const site = req.headers.get("sec-fetch-site");
      if (site && site !== "same-origin") return new Response("forbidden", { status: 403 });
      const origin = req.headers.get("origin");
      if (origin) { try { const h = new URL(origin).host; if (h !== `localhost:${PORT}` && h !== `127.0.0.1:${PORT}`) return new Response("forbidden", { status: 403 }); } catch { return new Response("forbidden", { status: 403 }); } }
      const d = await req.json();
      const id = `c${seq++}`;
      const anchorOk = /^[A-Za-z0-9_-]{1,64}$/.test(d.anchor ?? "");
      const c: Comment = { id, anchor: anchorOk ? d.anchor : "?", section_title: String(d.section_title ?? d.anchor ?? "?").slice(0,120),
        quote: d.quote ?? "", text: d.text ?? "", at: d.at ?? new Date().toISOString() };
      comments.push(c); await persist();
      await mcp.notification({ method: "notifications/claude/channel",
        params: { content: (c.quote ? `On the passage "${c.quote}":\n` : "") + c.text, meta: { comment_id: id, section: c.section_title, anchor: c.anchor } } });
      return Response.json({ ok: true, id });
    }

    // the page under review, with the widget injected
    if (url.pathname === "/" || url.pathname === "/index.html") {
      let html = await readFile(TARGET, "utf8");
      html = html.includes("</body>") ? html.replace(/<\/body>/i, INJECT + "</body>") : html + INJECT;
      return new Response(html, { headers: { "Content-Type": "text/html; charset=utf-8" } });
    }
    // sibling assets referenced by the target page
    try { const f = Bun.file(join(dirname(TARGET), url.pathname)); if (await f.exists()) return new Response(f); } catch {}
    return new Response("not found", { status: 404 });
  },
  websocket: { open(ws){ sockets.add(ws); }, close(ws){ sockets.delete(ws); }, message(){} },
});

console.error(`📡 live-review serving ${basename(TARGET)} at http://localhost:${server.port}`);
