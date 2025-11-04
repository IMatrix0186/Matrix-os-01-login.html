matrix-os A43 rbac/guard file
(()=>{
// Matrix OS — A43 RBAC Guard (front-end)
// Works with A42 (matrix-OS-A42-permissions.py)

const DEF_BASE = "http://127.0.0.1:5072"; // A42 default port
let BASE = DEF_BASE;
let CURRENT_USER = "Admin";                // change at runtime via setUser()
let observing = false, mo = null;

const State = {
  roles: new Set(),      // role names for CURRENT_USER
  perms: new Set(),      // effective permissions
  loaded: false,
  lastLoad: 0
};

// ---------- Styling for locked elements ----------
const style = document.createElement("style");
style.textContent = `
  [data-rbac-locked],
  .rbac-locked{
    opacity: .45 !important;
    filter: grayscale(0.35);
    pointer-events: none !important;
    cursor: not-allowed !important;
  }
`;
document.head.appendChild(style);

// ---------- Helpers ----------
async function getJSON(url){
  const r = await fetch(url);
  if(!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

function parseList(val){
  if(!val) return [];
  if(Array.isArray(val)) return val;
  return String(val).split(/[,\s]+/).map(s=>s.trim()).filter(Boolean);
}

function meetsAny(haveSet, required){
  return required.some(x=>haveSet.has(x));
}
function meetsAll(haveSet, required){
  return required.every(x=>haveSet.has(x));
}

// ---------- Load roles and permissions for CURRENT_USER ----------
async function loadProfile(){
  const now = Date.now();
  if (State.loaded && (now - State.lastLoad) < 10_000) return; // 10s cache

  State.roles.clear();
  State.perms.clear();

  // 1) roles for user
  const rolesResp = await getJSON(`${BASE}/api/rbac/user/roles?user=${encodeURIComponent(CURRENT_USER)}`);
  if(rolesResp?.ok){
    (rolesResp.roles||[]).forEach(r=>State.roles.add(String(r)));
  }

  // 2) union all permissions granted to those roles
  const roleList = Array.from(State.roles);
  for(const role of roleList){
    try{
      const rp = await getJSON(`${BASE}/api/rbac/role/perms?role=${encodeURIComponent(role)}`);
      if(rp?.ok){
        (rp.perms||[]).forEach(p=>State.perms.add(String(p)));
      }
    }catch{ /* ignore bad role */ }
  }

  State.loaded = true;
  State.lastLoad = Date.now();
}

// ---------- Element guarding ----------
function checkElement(el){
  // Attributes:
  //   data-perm="analytics.read"
  //   data-perms-any="telemetry.read, analytics.read"
  //   data-perms-all="system.write analytics.write"
  //   data-role="admin"
  //   data-roles-any="developer, analyst"
  //   data-rbac-mode="hide|disable"   (optional; default = disable)
  //   data-rbac-invert="true"         (optional; invert result)
  const needPerm      = el.getAttribute("data-perm");
  const needPermsAny  = el.getAttribute("data-perms-any");
  const needPermsAll  = el.getAttribute("data-perms-all");
  const needRole      = el.getAttribute("data-role");
  const needRolesAny  = el.getAttribute("data-roles-any");
  const mode          = (el.getAttribute("data-rbac-mode")||"disable").toLowerCase();
  const invert        = (el.getAttribute("data-rbac-invert")||"false").toLowerCase() === "true";

  let ok = true;

  if(needPerm){
    ok = ok && State.perms.has(needPerm);
  }
  if(needPermsAny){
    ok = ok && meetsAny(State.perms, parseList(needPermsAny));
  }
  if(needPermsAll){
    ok = ok && meetsAll(State.perms, parseList(needPermsAll));
  }
  if(needRole){
    ok = ok && State.roles.has(needRole);
  }
  if(needRolesAny){
    ok = ok && meetsAny(State.roles, parseList(needRolesAny));
  }

  if(invert) ok = !ok;

  // Apply
  if(ok){
    el.classList.remove("rbac-locked");
    el.removeAttribute("data-rbac-locked");
    if(mode==="hide") el.style.display = "";
    el.removeAttribute("aria-disabled");
  }else{
    if(mode==="hide"){
      el.style.display = "none";
    }else{
      el.style.display = "";
      el.classList.add("rbac-locked");
      el.setAttribute("data-rbac-locked", "true");
      el.setAttribute("aria-disabled","true");
    }
    // Dispatch an event so apps can react if needed
    try{
      el.dispatchEvent(new CustomEvent("rbac:denied", { bubbles:true, detail:{ user: CURRENT_USER }}));
    }catch{}
  }
}

function guard(root=document){
  const all = root.querySelectorAll("[data-perm], [data-perms-any], [data-perms-all], [data-role], [data-roles-any]");
  all.forEach(checkElement);
}

// ---------- Observer ----------
function startObserver(){
  if(observing) return;
  mo = new MutationObserver((muts)=>{
    for(const m of muts){
      if(m.type==="childList"){
        m.addedNodes.forEach(node=>{
          if(node.nodeType===1){
            const el = node;
            if(el.matches?.("[data-perm], [data-perms-any], [data-perms-all], [data-role], [data-roles-any]")){
              checkElement(el);
            }
            const inner = el.querySelectorAll?.("[data-perm], [data-perms-any], [data-perms-all], [data-role], [data-roles-any]");
            inner && inner.forEach(checkElement);
          }
        });
      }else if(m.type==="attributes"){
        if(m.target && m.target.nodeType===1){
          const el = m.target;
          if(["data-perm","data-perms-any","data-perms-all","data-role","data-roles-any","data-rbac-mode","data-rbac-invert"].includes(m.attributeName)){
            checkElement(el);
          }
        }
      }
    }
  });
  mo.observe(document.documentElement, { childList:true, subtree:true, attributes:true, attributeFilter:[
    "data-perm","data-perms-any","data-perms-all","data-role","data-roles-any","data-rbac-mode","data-rbac-invert"
  ]});
  observing = true;
}
function stopObserver(){
  if(mo){ mo.disconnect(); mo=null; }
  observing = false;
}

// ---------- Public API ----------
const MatrixRBAC = {
  async refresh(){
    await loadProfile();
    guard(document);
  },
  async setUser(name){
    CURRENT_USER = String(name||"").trim() || "Admin";
    State.loaded = false;
    await MatrixRBAC.refresh();
  },
  setBase(url){
    BASE = String(url||DEF_BASE).replace(/\/+$/,"");
    State.loaded = false;
  },
  allowed(perm){
    return State.perms.has(String(perm));
  },
  guard,         // guard(root?)
  observe(){ startObserver(); },
  stop(){ stopObserver(); },
  get user(){ return CURRENT_USER; },
  get roles(){ return Array.from(State.roles); },
  get perms(){ return Array.from(State.perms); }
};

// Auto bootstrap via script tag attributes
(function bootstrap(){
  const s = document.currentScript || [...document.scripts].slice(-1)[0];
  const base = s?.getAttribute("data-base");
  const user = s?.getAttribute("data-user");
  const autostart = (s?.getAttribute("data-autostart") ?? "true").toLowerCase() !== "false";
  if(base) MatrixRBAC.setBase(base);
  if(user) MatrixRBAC.setUser(user);
  MatrixRBAC.refresh().then(()=>{ if(autostart) startObserver(); });
})();

Object.defineProperty(window, "MatrixRBAC", { value: MatrixRBAC, writable:false });
})();
