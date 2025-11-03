matrix-os A19 telemetry
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Matrix Windows – Telemetry Viewer</title>
<style>
  body {
    margin:0; padding:20px;
    background:linear-gradient(135deg,#000,#06131a 50%,#001b24);
    color:#00fff9; font-family:"Orbitron",sans-serif;
  }
  h1 { text-align:center; text-shadow:0 0 18px #00fff9; margin-bottom:10px; }
  .grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); }
  .card {
    border:1px solid #00fff9; border-radius:12px;
    background:rgba(0,0,0,.55); box-shadow:0 0 24px #00fff9; padding:16px;
  }
  .title { font-size:1.1rem; text-shadow:0 0 8px #00fff9; margin-bottom:8px; }
  .row { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin:6px 0; }
  label { min-width:100px; }
  input[type="text"], select {
    flex:1; min-width:140px; padding:8px 10px;
    border:none; border-radius:8px; text-align:center;
  }
  button {
    background:#00fff9; color:#000; border:none; border-radius:8px;
    padding:8px 12px; font-weight:700; cursor:pointer;
  }
  button:hover { background:#0ff; transform:scale(1.03); }
  pre {
    white-space:pre-wrap; word-wrap:break-word; color:#aef;
    background:rgba(0,0,0,.35); padding:10px; border-radius:8px;
    border:1px dashed #00fff9; max-height:400px; overflow:auto;
  }
  small { color:#aee; opacity:.85; }
</style>
</head>
<body>
  <h1>Matrix Telemetry Viewer</h1>

  <div class="grid">
    <!-- AI Events -->
    <div class="card">
      <div class="title">AI Event Logs</div>
      <div class="row">
        <label>User:</label>
        <input id="ai_user" type="text" placeholder="Admin or blank for all"/>
      </div>
      <div class="row">
        <label>Limit:</label>
        <input id="ai_limit" type="text" placeholder="200"/>
      </div>
      <div class="row">
        <button onclick="loadAI()">Load</button>
        <button onclick="autoAI()">Auto (5s)</button>
      </div>
      <pre id="ai_box">—</pre>
    </div>

    <!-- Session Events -->
    <div class="card">
      <div class="title">Session Event Logs</div>
      <div class="row">
        <label>User:</label>
        <input id="sess_user" type="text" placeholder="Admin or blank"/>
      </div>
      <div class="row">
        <label>Action:</label>
        <select id="sess_action">
          <option value="">(all)</option>
          <option value="created">created</option>
          <option value="revoked">revoked</option>
          <option value="verified">verified</option>
          <option value="failed">failed</option>
        </select>
      </div>
      <div class="row">
        <label>Limit:</label>
        <input id="sess_limit" type="text" placeholder="200"/>
      </div>
      <div class="row">
        <button onclick="loadSessions()">Load</button>
        <button onclick="autoSessions()">Auto (5s)</button>
      </div>
      <pre id="sess_box">—</pre>
    </div>
  </div>

<script>
const TELE = "http://127.0.0.1:5065";
const AI_LOGS = TELE + "/api/telemetry/ai/logs";
const SESS_LOGS = TELE + "/api/telemetry/session/logs";
let aiTimer=null, sessTimer=null;

function setJSON(id,obj){ document.getElementById(id).textContent=(typeof obj==="string")?obj:JSON.stringify(obj,null,2); }

async function loadAI(){
  const user=(document.getElementById("ai_user").value||"").trim();
  const limit=(document.getElementById("ai_limit").value||"200").trim();
  const url=AI_LOGS+`?user=${encodeURIComponent(user)}&limit=${limit}`;
  try{
    const r=await fetch(url); const j=await r.json();
    if(!j.ok) setJSON("ai_box","Error: "+(j.error||"Unknown"));
    else setJSON("ai_box",j.events||[]);
  }catch(e){ setJSON("ai_box","Connection error: "+e); }
}

async function loadSessions(){
  const user=(document.getElementById("sess_user").value||"").trim();
  const act=(document.getElementById("sess_action").value||"").trim();
  const limit=(document.getElementById("sess_limit").value||"200").trim();
  let url=SESS_LOGS+`?limit=${limit}`;
  if(user) url+=`&username=${encodeURIComponent(user)}`;
  if(act) url+=`&action=${encodeURIComponent(act)}`;
  try{
    const r=await fetch(url); const j=await r.json();
    if(!j.ok) setJSON("sess_box","Error: "+(j.error||"Unknown"));
    else setJSON("sess_box",j.events||[]);
  }catch(e){ setJSON("sess_box","Connection error: "+e); }
}

function autoAI(){
  if(aiTimer){ clearInterval(aiTimer); aiTimer=null; alert("Auto-refresh stopped"); return; }
  loadAI();
  aiTimer=setInterval(loadAI,5000);
  alert("Auto-refresh started (every 5s)");
}
function autoSessions(){
  if(sessTimer){ clearInterval(sessTimer); sessTimer=null; alert("Auto-refresh stopped"); return; }
  loadSessions();
  sessTimer=setInterval(loadSessions,5000);
  alert("Auto-refresh started (every 5s)");
}
</script>

<!-- Protect the page: require Developer Level 3 -->
<script src="matrix-OS-A14-guard.js" data-min-level="3"></script>
</body>
</html>
