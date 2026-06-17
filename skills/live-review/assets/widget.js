// live-review comment widget — injected by the channel server into the page under review.
// Builds its own UI (panel + composer + toast), makes every text block commentable,
// posts comments to the same-origin channel server, and hot-reloads on file edits.
(() => {
  if (window.__lrLoaded) return; window.__lrLoaded = true;
  const $ = s => document.querySelector(s);
  const esc = s => (s||"").replace(/[&<>"']/g, m => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[m]));
  let activeAnchor = null, activeQuote = "";

  // ---- inject UI ----
  const root = document.createElement("div"); root.id = "lr-root";
  root.innerHTML = `
    <div id="lr-panel">
      <div id="lr-head"><span id="lr-dot"></span><b>live-review</b><span class="lr-tag" id="lr-tag">connecting…</span>
        <button id="lr-toggle" title="collapse">▾</button></div>
      <div class="lr-body" id="lr-list"><div class="lr-empty">No comments yet. Select text, or hover a block and click ＋.</div></div>
      <div id="lr-watch" hidden></div>
    </div>
    <div id="lr-composer">
      <div id="lr-anchor"></div>
      <div id="lr-qrow"><div id="lr-quote"></div><button id="lr-copy" title="Copy selected text">⧉ Copy</button></div>
      <textarea id="lr-text" placeholder="Your comment… (⌘/Ctrl-Enter to send)"></textarea>
      <div id="lr-row"><button id="lr-send">Send comment</button><button id="lr-cancel">Cancel</button></div>
    </div>
    <div id="lr-toast"></div>`;
  document.body.appendChild(root);

  // ---- hot reload ----
  try { const ws = new WebSocket(`ws://${location.host}/_lr/ws`); ws.onmessage = e => { if (e.data === "reload") location.reload(); }; } catch {}

  // ---- whoami ----
  fetch("/_lr/whoami").then(r=>r.json()).then(j=>{
    $("#lr-tag").textContent = j.target || "live";
    $("#lr-dot").classList.add("lr-up");
    if (j.session){ const w=$("#lr-watch"); w.hidden=false;
      w.innerHTML = `▶ watch Claude work · <code>tmux attach -t ${esc(j.session)}</code>`; }
  }).catch(()=> $("#lr-tag").textContent = "offline");

  // ---- content-hash anchors (re-link comments across edits) ----
  const hash = s => { let h=0; for (let i=0;i<s.length;i++) h=(h*31+s.charCodeAt(i))|0; return "b"+(h>>>0).toString(36); };
  const labelFor = el => (el?.textContent||"").replace(/＋\s*$/,"").replace(/\s+/g," ").trim().replace(/^[0-9]{1,2}\s/,"").slice(0,46);
  const fmtWhere = a => { const el = document.querySelector(`[data-lr="${a}"]`); return el ? (labelFor(el)||a) : a; };
  function anchorFor(el){ if(!el.dataset.lr) el.dataset.lr = hash(labelFor(el) || el.tagName+el.className); return el.dataset.lr; }

  const SEL = "h1,h2,h3,h4,h5,p,li,blockquote";
  function wire(){
    document.querySelectorAll(SEL).forEach(el=>{
      if (el.closest("#lr-root")) return;            // never our own UI
      if (!el.textContent.trim()) return;
      el.classList.add("lr-on"); anchorFor(el);
      if (el.querySelector(":scope > .lr-btn")) return;
      const b = document.createElement("button"); b.className="lr-btn"; b.textContent="＋"; b.title="Comment here";
      b.onclick = ev => { ev.stopPropagation(); openComposer(el, "", b.getBoundingClientRect()); };
      el.appendChild(b);
    });
  }
  function resolveBlock(node){
    let el = node?.nodeType===1 ? node : node?.parentElement; if(!el) return null;
    if (el.closest("#lr-root")) return null;
    let b = el.closest(".lr-on") || el.closest("h1,h2,h3,h4,h5,p,li,blockquote,td,th");
    if (b && !b.classList.contains("lr-on")){ b.classList.add("lr-on"); anchorFor(b); }
    return b;
  }

  // ---- selection → open the focused form, keep passage highlighted ----
  function highlightRange(r){ try{ if(window.CSS&&CSS.highlights&&window.Highlight) CSS.highlights.set("lr-sel", new Highlight(r.cloneRange())); }catch{} }
  function clearHighlight(){ try{ window.CSS&&CSS.highlights&&CSS.highlights.delete("lr-sel"); }catch{} }
  function closeComposer(){ $("#lr-composer").classList.remove("lr-show"); clearHighlight(); }

  document.addEventListener("mouseup", e=>{
    if (e.target.closest("#lr-root, .lr-btn")) return;
    setTimeout(()=>{
      const sel = window.getSelection(); const txt = (sel.toString()||"").trim();
      if (txt.length<3 || !sel.rangeCount) return;
      const range = sel.getRangeAt(0);
      const block = resolveBlock(range.startContainer) || resolveBlock(range.commonAncestorContainer);
      if (!block) return;
      highlightRange(range);
      openComposer(block, txt, range.getBoundingClientRect());
    }, 0);
  });
  document.addEventListener("keydown", e=>{ if(e.key==="Escape") closeComposer(); });

  function placeComposer(rect){
    const c=$("#lr-composer"); const cw=c.offsetWidth||312, ch=c.offsetHeight||210, pad=14;
    let left = rect.right + pad;
    if (left+cw > innerWidth-pad) left = rect.left - cw - pad;
    if (left < pad) left = Math.max(pad, Math.min(innerWidth-cw-pad, rect.left));
    let top = rect.top;
    if (top+ch > innerHeight-pad) top = innerHeight-ch-pad;
    if (top < pad) top = pad;
    c.style.left = Math.round(left)+"px"; c.style.top = Math.round(top)+"px";
  }
  function openComposer(block, quote, rect){
    activeAnchor = block.dataset.lr; activeQuote = quote||"";
    $("#lr-anchor").textContent = "▸ " + fmtWhere(activeAnchor);
    $("#lr-quote").textContent = quote ? `“${quote}”` : "";
    $("#lr-qrow").style.display = quote ? "flex" : "none";
    const cp=$("#lr-copy"); cp.classList.remove("lr-done"); cp.textContent="⧉ Copy";
    $("#lr-text").value="";
    $("#lr-composer").classList.add("lr-show");
    placeComposer(rect || block.getBoundingClientRect());
    setTimeout(()=>$("#lr-text").focus(), 30);
  }
  $("#lr-copy").onclick = async () => {
    if (!activeQuote) return;
    try { await navigator.clipboard.writeText(activeQuote); const b=$("#lr-copy"); b.classList.add("lr-done"); b.textContent="✓ Copied"; }
    catch { toast("Copy failed"); }
  };
  $("#lr-cancel").onclick = closeComposer;
  $("#lr-send").onclick = send;
  $("#lr-text").addEventListener("keydown", e=>{ if((e.metaKey||e.ctrlKey)&&e.key==="Enter") send(); });

  async function send(){
    const text = $("#lr-text").value.trim(); if(!text) return;
    const payload = { anchor: activeAnchor, quote: activeQuote, text, section_title: fmtWhere(activeAnchor), at: new Date().toISOString() };
    try { await fetch("/_lr/comment",{ method:"POST", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(payload) });
      toast("Sent — Claude is on it…"); closeComposer(); load(); setTimeout(load, 600);
    } catch { toast("Failed to send"); }
  }
  function toast(m){ const t=$("#lr-toast"); t.textContent=m; t.classList.add("lr-show"); setTimeout(()=>t.classList.remove("lr-show"), 1800); }

  // ---- render (newest first, short muted time) ----
  const timeAgo = at => { const t=Date.parse(at); if(isNaN(t)) return ""; const s=Math.max(0,(Date.now()-t)/1000);
    return s<45?"now":s<3600?Math.round(s/60)+"m":s<86400?Math.round(s/3600)+"h":Math.round(s/86400)+"d"; };
  // re-find a comment's block: by content-hash anchor, else by searching for its quote
  // (so a comment survives the reviewer rewording the block it was hashed from).
  function findAnchorEl(c){
    if (c.anchor){ const el = document.querySelector(`[data-lr="${c.anchor}"]`); if (el) return el; }
    const q = (c.quote||"").replace(/\s+/g," ").trim();
    if (q.length >= 3){
      for (const b of document.querySelectorAll(SEL)){
        if (b.closest("#lr-root")) continue;
        if ((b.textContent||"").replace(/\s+/g," ").includes(q)) return b;
      }
    }
    return null;
  }
  async function load(){
    let list=[]; try { list = await (await fetch("/_lr/comments")).json(); } catch {}
    document.querySelectorAll(".lr-btn.lr-has").forEach(b=>{ b.classList.remove("lr-has","lr-btn-resolved","lr-btn-working"); b.textContent="＋"; });
    const isPending = c => !c.reply && !c.resolved;     // submitted, Claude hasn't responded yet
    list.forEach(c=>{ const el=findAnchorEl(c); const b=el&&el.querySelector(":scope > .lr-btn");
      if(b){ b.classList.add("lr-has"); const p=isPending(c);
        b.textContent = c.resolved ? "✓" : (p ? "…" : "💬");
        b.classList.toggle("lr-btn-resolved", !!c.resolved);
        b.classList.toggle("lr-btn-working", p); }});
    const working = list.filter(isPending).length;
    $("#lr-dot").classList.toggle("lr-busy", working>0);
    const box=$("#lr-list");
    if(!list.length){ box.innerHTML = `<div class="lr-empty">No comments yet. Select text, or hover a block and click ＋.</div>`; return; }
    box.innerHTML = [...list].reverse().map(c=>{
      const moved = !findAnchorEl(c);
      const label = esc(c.section_title || c.anchor || "");
      const pending = isPending(c);
      return `
      <div class="lr-item${c.resolved?' lr-resolved':''}${pending?' lr-working':''}">
        <div class="lr-where" data-cid="${esc(c.id)}">
          <span class="lr-goto">${c.resolved?'✓ ':'▸ '}${label}</span>
          <span class="lr-when">${moved?'<span class="lr-moved">⚠ moved</span> ':''}${timeAgo(c.at)}</span>
        </div>
        ${c.quote?`<div class="lr-quote">“${esc(c.quote)}”</div>`:""}
        <div class="lr-txt">${esc(c.text)}</div>
        ${c.reply?`<div class="lr-reply"><b>Claude${c.resolved?' · resolved':''}</b> ${esc(c.reply)}</div>`:""}
        ${pending?`<div class="lr-pending"><span class="lr-spin"></span>Claude is working on this…</div>`:""}
      </div>`;
    }).join("");
    box.querySelectorAll("[data-cid]").forEach(elr=>elr.onclick=()=>{
      const c=list.find(x=>x.id===elr.dataset.cid); if(!c) return;
      const t=findAnchorEl(c); if(!t){ toast("anchor no longer in the page"); return; }
      t.scrollIntoView({behavior:"smooth",block:"center"}); const o=t.style.outline;
      t.style.outline="2px solid var(--lr-accent)"; setTimeout(()=>t.style.outline=o,1200);
    });
  }

  $("#lr-toggle").onclick = () => $("#lr-panel").classList.toggle("lr-min");

  wire(); load();
  new MutationObserver(()=>wire()).observe(document.body, { childList:true, subtree:true });
  window.addEventListener("focus", load);
  setInterval(load, 4000);
})();
