matrix-os A28 unified header (live indicators+nav)

(()=>{
  // ======== Defaults (override with data-* attrs on the script tag) ========
  const DEF = {
    brand: "MATRIX OS",
    a7:  "http://127.0.0.1:5000",  // /api/health
    a10: "http://127.0.0.1:5070",  // /api/status
    a15: "http://127.0.0.1:5090",  // /api/admin/sessions
    a26: "http://127.0.0.1:5069",  // /api/notify/stream, /api/notify/pull
    refreshMs: 10000
  };

  // ======== Read script tag config ========
  const script = document.currentScript || [...document.scripts].slice(-1)[0];
  const cfg = {
    brand: script?.getAttribute("data-brand") || DEF.brand,
    a7:  script?.getAttribute("data-a7")  || DEF.a7,
    a10: script?.getAttribute("data-a10") || DEF.a10,
    a15: script?.getAttribute("data-a15") || DEF.a15,
    a26: script?.getAttribute("data-a26") || DEF.a26,
    refreshMs: parseInt(script?.getAttribute("data-refresh-ms") || DEF.refreshMs, 10)
  };

  // ======== Mount point ========
  const host = document.createElement("div");
  host.setAttribute("data-matrix-header","");
  const root = host.attachShadow({mode:"open"});
  root.innerHTML = `
    <style>
      :host{ all: initial; }
      .bar{
        position:fixed; top:0; left:0; right:0; z-index:2147483000;
        background: linear-gradient(90deg,#000,#04131c 55%,#001b24);
        border-bottom: 1px solid #00fff9;
        box-shadow: 0 0 20px rgba(0,255,249,.35);
        color:#00fff9; font-family:"Orbitron",system-ui,Arial,sans-serif;
      }
      .row{ display:flex; align-items:center; gap:12px; padding:8px 12px; }
      .brand{ font-weight:900; letter-spacing:1px; text-shadow:0 0 12px #00fff9; }
      .sp{ flex:1 }
      nav{ display:flex; gap:8px; flex-wrap:wrap; }
      a.btn{
        text-decoration:none; color:#001016; background:#00fff9; border-radius:10px;
        padding:6px 10px; font-weight:800; display:inline-flex; align-items:center; gap:6px;
      }
      a.btn:hover{ filter:brightness(1.1); transform:scale(1.02); }
      .pill{
        display:inline-flex; align-items:center; gap:6px;
        border:1px solid #00fff9; border-radius:20px; padding:4px 8px;
        background:rgba(0,0,0,.45); color:#aef; font-size:12px;
      }
      .dot{ width:10px; height:10px; border-radius:50%; background:#aaa; box-shadow:0 0 10px currentColor; }
      .ok { color:#5cffc3; }
      .bad{ color:#ff6b6b; }
      .warn{ color:#FFD166; }
      .badge{
        display:inline-flex; align-items:center; justify-content:center;
        min-width:18px; height:18px; padding:0 6px; border-radius:999px; font-weight:900;
        background:#ff6b6b; color:#001016; box-shadow:0 0 8px rgba(255,107,107,.6);
      }
      .pad{ height:44px; } /* page spacer so content isn't hidden under fixed header */
      .menu{ display:none; }
      @media (max-width:820px){
        nav{ display:none; }
        .menu{ display:inline-flex; }
        .drawer{
          position:fixed; top:44px; right:0; width:90%; max-width:420px; bottom:0;
          background:linear-gradient(180deg,#001b24,#000); border-left:1px solid #00fff9; padding:12px;
          transform:translateX(100%); transition:transform .18s ease-out; box-shadow:0 0 20px rgba(0,255,249,.35);
        }
        .drawer.open{ transform:translateX(0); }
        .drawer h3{ margin:6px 0 8px; color:#aef; }
        .drawer a{ display:block; margin:6px 0; }
      }
    </style>
    <div class="bar">
      <div class="row">
        <button class="menu a btn" title="Menu" style="display:inline-flex;align-items:center;gap:6px;">☰ Menu</button>
        <div class="brand">${cfg.brand}</div>
        <div class="sp"></div>
        <nav>
          <a class="btn" href="matrix-OS-A18-overview.html">Overview</a>
          <a class="btn" href="matrix-OS-A21-dashboard.html">Analytics</a>
          <a class="btn" href="matrix-OS-A19-telemetry.html">Telemetry</a>
          <a class="btn" href="matrix-OS-A23-logistics-console.html">Logistics</a>
          <a class="btn" href="matrix-OS-A25-backup-console.html">Backups</a>
          <a class="btn" href="matrix-OS-A17-sessions.html">Sessions</a>
          <a class="btn" href="matrix-OS-A16-user.html">Users</a>
        </nav>
        <div class="pill" title="A10 unified status">
          <span class="dot" id="uDot"></span><span>STATUS</span>
        </div>
        <div class="pill" title="A7 API health">
          <span class="dot" id="hDot"></span><span>HEALTH</span>
        </div>
        <div class="pill" title="Active sessions (A15)">
          <span>SESS</span><span class="badge" id="sessBadge">0</span>
        </div>
        <div class="pill" title="Notifications (A26)">
          <span>NOTIF</span><span class="badge" id="notifBadge">0</span>
        </div>
      </div>
    </div>
    <div class="pad"></div>

    <!-- Mobile drawer -->
    <div class="drawer" id="drawer">
      <h3>Navigation</h3>
      <a class="btn" href="matrix-OS-A18-overview.html">Overview</a>
      <a class="btn" href="matrix-OS-A21-dashboard.html">Analytics</a>
      <a class="btn" href="matrix-OS-A19-telemetry.html">Telemetry</a>
      <a class="btn" href="matrix-OS-A23-logistics-console.html">Logistics</a>
      <a class="btn" href="matrix-OS-A25-backup-console.html">Backups</a>
      <a class="btn" href="matrix-OS-A17-sessions.html">Sessions</a>
      <a class="btn" href="matrix-OS-A16-user.html">Users</a>
    </div>
  `;

  document.documentElement.appendChild(host);

  // ======== Elements ========
  const uDot = root.getElementById("uDot");
  const hDot = root.getElementById("hDot");
  const sessBadge = root.getElementById("sessBadge");
  const notifBadge = root.getElementById("notifBadge");
  const drawer = root.getElementById("drawer");
  const menuBtn = root.querySelector(".menu");
  menuBtn?.addEventListener("click", ()=>drawer.classList.toggle("open"));

  // ======== Helpers ========
  function setDot(el, state){
    el.classList.remove("ok","bad","warn");
    if(state==="ok") el.classList.add("ok");
    else if(state==="warn") el.classList.add("warn");
    else el.classList.add("bad");
  }
  async function getJSON(u){ const r = await fetch(u); return r.json(); }

  // ======== Live indicators ========
  async function refreshStatus(){
    try{
      const j = await getJSON(`${cfg.a10}/api/status`);
      setDot(uDot, j.ok!==false ? "ok" : "bad");
    }catch{ setDot(uDot,"bad"); }
  }
  async function refreshHealth(){
    try{
      const j = await getJSON(`${cfg.a7}/api/health`);
      setDot(hDot, j.ok!==false ? "ok" : "bad");
    }catch{ setDot(hDot,"bad"); }
  }
  async function refreshSessions(){
    try{
      const j = await getJSON(`${cfg.a15}/api/admin/sessions`);
      const count = j && j.sessions ? Object.keys(j.sessions).length : 0;
      sessBadge.textContent = count;
    }catch{ sessBadge.textContent = "0"; }
  }

  // ======== Notifications: SSE with fallback ========
  let es = null, pollTimer = null, lastId = 0, notifCount = 0;
  function incNotif(n){
    notifCount = (notifCount + 1);
    notifBadge.textContent = String(notifCount);
    if(typeof n?.id === "number") lastId = Math.max(lastId, n.id);
  }
  function startSSE(){
    if(typeof EventSource === "undefined"){ startPolling(); return; }
    try{
      es = new EventSource(`${cfg.a26}/api/notify/stream?since=${encodeURIComponent(lastId)}`);
      es.onmessage = (ev)=>{ try{ const n = JSON.parse(ev.data); incNotif(n); }catch{} };
      es.addEventListener("ping", ()=>{ /* heartbeat */ });
      es.onerror = ()=>{ try{ es.close(); }catch{} es=null; startPolling(); };
    }catch{ startPolling(); }
  }
  function startPolling(){
    stopPolling();
    pollTimer = setInterval(async ()=>{
      try{
        const j = await getJSON(`${cfg.a26}/api/notify/pull?since=${lastId}&limit=50&wait=0`);
        const items = j.notifications || j.data || [];
        for(const n of items){ incNotif(n); }
      }catch{}
    }, 3000);
  }
  function stopPolling(){ if(pollTimer){ clearInterval(pollTimer); pollTimer=null; } }

  // ======== Kickoff ========
  refreshStatus(); refreshHealth(); refreshSessions(); startSSE();
  setInterval(()=>{ refreshStatus(); refreshHealth(); refreshSessions(); }, Math.max(2000, cfg.refreshMs));
})();
