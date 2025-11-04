matrix-os A27 notify client
(()=>{
  const DEFAULT_BASE = "http://127.0.0.1:5069"; // A26 default
  const LEVEL_STYLE = {
    info:    {accent:"#8fd3ff"},
    success: {accent:"#7CFFB2"},
    warning: {accent:"#FFD166"},
    error:   {accent:"#FF6B6B"}
  };

  let base = DEFAULT_BASE;
  let es = null;
  let polling = null;
  let lastId = 0;
  let stopped = false;
  let backoff = 1000; // ms (auto reconnection)

  // ---------- UI (Shadow DOM) ----------
  const host = document.createElement("div");
  host.setAttribute("data-matrix-notify","");
  const root = host.attachShadow({mode:"open"});
  root.innerHTML = `
    <style>
      :host{ all: initial; }
      .wrap{ position: fixed; right: 16px; bottom: 16px; z-index: 2147483647; display:flex; flex-direction:column; gap:10px; }
      .toast{
        min-width: 260px; max-width: 420px;
        color: #e6ffff; background: rgba(0,0,0,.75); border: 1px solid #00fff9;
        border-left: 6px solid var(--accent, #00fff9);
        border-radius: 12px; padding: 10px 12px 10px 12px;
        box-shadow: 0 0 18px rgba(0,255,249,.35);
        font-family: "Orbitron", system-ui, Arial, sans-serif; line-height: 1.2;
        animation: slideIn .18s ease-out forwards;
      }
      .title { font-weight: 800; margin-bottom: 4px; text-shadow: 0 0 8px rgba(0,255,249,.6); }
      .meta  { font-size: 11px; opacity: .9; margin-top: 6px; color:#aef; display:flex; gap:8px; flex-wrap:wrap;}
      .msg   { white-space: pre-wrap; word-wrap: break-word; }
      .close { all: unset; cursor: pointer; margin-left: auto; font-weight: 800; }
      @keyframes slideIn{ from{ transform: translateY(8px); opacity: 0 } to{ transform: translateY(0); opacity: 1 } }
      @keyframes fadeOut{ to{ transform: translateY(6px); opacity: 0 } }
    </style>
    <div class="wrap"></div>
  `;
  document.documentElement.appendChild(host);
  const wrap = root.querySelector(".wrap");

  function formatTs(ts){
    try{ return new Date(ts).toLocaleTimeString(); }catch{ return ts || ""; }
  }

  function showToast(n){
    const lvl = (n.level||"info").toLowerCase();
    const accent = (LEVEL_STYLE[lvl]?.accent) || "#00fff9";
    const el = document.createElement("div");
    el.className = "toast";
    el.style.setProperty("--accent", accent);
    el.innerHTML = `
      <div style="display:flex; gap:8px; align-items:center;">
        <div class="title">${lvl.toUpperCase()}</div>
        <button class="close" title="dismiss">×</button>
      </div>
      <div class="msg">${escapeHTML(n.message||"")}</div>
      <div class="meta">
        <span>src: ${escapeHTML(n.source||"A26")}</span>
        ${n.user ? `<span>user: ${escapeHTML(n.user)}</span>` : ""}
        <span>${formatTs(n.ts||"")}</span>
        <span>#${n.id||""}</span>
      </div>
    `;
    el.querySelector(".close").onclick = ()=>dismiss(el);
    wrap.appendChild(el);
    // auto dismiss
    setTimeout(()=>dismiss(el), 6000);
  }

  function dismiss(el){
    if(!el || !el.animate){ if(el?.parentNode) el.parentNode.removeChild(el); return; }
    el.style.animation = "fadeOut .2s ease-in forwards";
    setTimeout(()=>{ el.parentNode && el.parentNode.removeChild(el); }, 210);
  }

  function escapeHTML(s){
    return String(s).replace(/[&<>"']/g, m=>({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[m]));
  }

  // ---------- Data plumbing ----------
  async function startSSE(){
    if(typeof EventSource === "undefined") { startPolling(); return; }
    try{
      const url = `${base}/api/notify/stream?since=${encodeURIComponent(lastId)}`;
      es = new EventSource(url, { withCredentials:false });
      es.onmessage = (ev)=>{
        backoff = 1000; // reset on success
        if(!ev.data) return;
        try{
          const n = JSON.parse(ev.data);
          if(n && typeof n.id === "number"){ lastId = Math.max(lastId, n.id); }
          showToast(n);
        }catch{}
      };
      es.addEventListener("ping", ()=>{ /* heartbeat */ });
      es.onerror = ()=>{
        // Attempt reconnect with backoff
        if(es){ es.close(); es = null; }
        if(stopped) return;
        setTimeout(()=>{ if(!stopped) startSSE(); }, backoff);
        backoff = Math.min(backoff*2, 15000);
      };
    }catch{
      startPolling();
    }
  }

  function stopSSE(){
    if(es){ try{ es.close(); }catch{} es = null; }
  }

  function startPolling(){
    stopPolling();
    polling = setInterval(async ()=>{
      try{
        const r = await fetch(`${base}/api/notify/pull?since=${lastId}&limit=50&wait=0`);
        const j = await r.json();
        if(j && j.ok){
          const items = j.notifications || j.data || [];
          for(const n of items){
            if(typeof n.id === "number"){ lastId = Math.max(lastId, n.id); }
            showToast(n);
          }
        }
      }catch{}
    }, 2500);
  }

  function stopPolling(){
    if(polling){ clearInterval(polling); polling = null; }
  }

  // ---------- Public API ----------
  const MatrixNotify = {
    start(){
      stopped = false;
      stopPolling(); stopSSE();
      startSSE();
    },
    stop(){
      stopped = true;
      stopPolling(); stopSSE();
    },
    setBase(url){
      base = String(url||DEFAULT_BASE).replace(/\/+$/,"");
    },
    async test(){
      try{
        const r = await fetch(`${base}/api/notify/test`, { method:"POST" });
        const j = await r.json();
        return j;
      }catch(e){ return { ok:false, error:String(e) }; }
    },
    get lastId(){ return lastId; }
  };

  // auto-config via script tag attributes
  (function bootstrap(){
    const thisScript = document.currentScript || [...document.scripts].slice(-1)[0];
    const attrBase = thisScript?.getAttribute("data-base");
    const auto = (thisScript?.getAttribute("data-autostart") ?? "true").toLowerCase() !== "false";
    if(attrBase) MatrixNotify.setBase(attrBase);
    if(auto) MatrixNotify.start();
  })();

  // Attach to window
  Object.defineProperty(window, "MatrixNotify", { value: MatrixNotify, writable:false });

})();
