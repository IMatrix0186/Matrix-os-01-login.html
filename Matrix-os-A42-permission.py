matrix-os A40 permission file
# matrix-OS-A42-permissions.py
# Matrix OS — RBAC (Roles & Permissions) Service
# Provides a simple SQLite-backed role/permission system.
# Endpoints:
#   POST  /api/rbac/role           {name}
#   POST  /api/rbac/perm           {name}
#   POST  /api/rbac/role/grant     {role, perm}
#   POST  /api/rbac/user/assign    {user, role}
#   GET   /api/rbac/user/roles?user=<u>
#   GET   /api/rbac/role/perms?role=<r>
#   GET   /api/rbac/check?user=<u>&perm=<p>
#   GET   /api/rbac/export         → full dump (roles, perms, links)

from flask import Flask, request, jsonify
from pathlib import Path
import sqlite3
from contextlib import closing

APP = Flask(__name__)

APP_DIR = Path(__file__).parent.resolve()
DB_PATH = APP_DIR / "matrix_rbac.sqlite3"

# ---------- DB utils ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows(q, args=()):
    with closing(db()) as conn:
        cur = conn.execute(q, args)
        return [dict(r) for r in cur.fetchall()]

def one(q, args=()):
    with closing(db()) as conn:
        cur = conn.execute(q, args)
        r = cur.fetchone()
        return dict(r) if r else None

def exec_(q, args=()):
    with closing(db()) as conn:
        cur = conn.execute(q, args)
        conn.commit()
        return cur.lastrowid

def ok(**kw): return jsonify({"ok": True, **kw})
def err(msg, code=400): return jsonify({"ok": False, "error": msg}), code

# ---------- Init ----------
def init_db():
    with closing(db()) as conn:
        c = conn.cursor()
        c.executescript("""
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS roles(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS perms(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS role_perms(
          role_id INTEGER NOT NULL,
          perm_id INTEGER NOT NULL,
          UNIQUE(role_id, perm_id),
          FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,
          FOREIGN KEY(perm_id) REFERENCES perms(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS user_roles(
          user TEXT NOT NULL,
          role_id INTEGER NOT NULL,
          UNIQUE(user, role_id),
          FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
        );
        """)
        conn.commit()

        # Seed some sensible defaults
        def ensure_role(name):
            try:
                c.execute("INSERT INTO roles(name) VALUES(?)", (name,))
            except sqlite3.IntegrityError:
                pass

        def ensure_perm(name):
            try:
                c.execute("INSERT INTO perms(name) VALUES(?)", (name,))
            except sqlite3.IntegrityError:
                pass

        for r in ("admin", "developer", "analyst", "viewer"):
            ensure_role(r)
        for p in (
            "system.read", "system.write",
            "users.read", "users.write",
            "telemetry.read", "telemetry.write",
            "analytics.read", "analytics.write",
            "backup.exec", "logistics.exec", "diagnostics.exec"
        ):
            ensure_perm(p)
        conn.commit()

init_db()

# ---------- Helpers ----------
def get_id(table, name):
    r = one(f"SELECT id FROM {table} WHERE name=?", (name,))
    return r["id"] if r else None

def upsert_name(table, name):
    try:
        exec_(f"INSERT INTO {table}(name) VALUES(?)", (name,))
    except sqlite3.IntegrityError:
        pass
    return get_id(table, name)

# ---------- Endpoints ----------
@APP.post("/api/rbac/role")
def create_role():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name: return err("Missing role name")
    rid = upsert_name("roles", name)
    return ok(role={"id": rid, "name": name})

@APP.post("/api/rbac/perm")
def create_perm():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name: return err("Missing permission name")
    pid = upsert_name("perms", name)
    return ok(perm={"id": pid, "name": name})

@APP.post("/api/rbac/role/grant")
def role_grant():
    data = request.get_json(silent=True) or {}
    role = (data.get("role") or "").strip()
    perm = (data.get("perm") or "").strip()
    if not role or not perm: return err("Need {role, perm}")
    rid = get_id("roles", role); pid = get_id("perms", perm)
    if rid is None: return err(f"Unknown role '{role}'", 404)
    if pid is None: return err(f"Unknown permission '{perm}'", 404)
    try:
        exec_("INSERT INTO role_perms(role_id, perm_id) VALUES(?,?)", (rid, pid))
    except sqlite3.IntegrityError:
        pass
    return ok(message=f"Granted {perm} to {role}")

@APP.post("/api/rbac/user/assign")
def user_assign():
    data = request.get_json(silent=True) or {}
    user = (data.get("user") or "").strip()
    role = (data.get("role") or "").strip()
    if not user or not role: return err("Need {user, role}")
    rid = get_id("roles", role)
    if rid is None: return err(f"Unknown role '{role}'", 404)
    try:
        exec_("INSERT INTO user_roles(user, role_id) VALUES(?,?)", (user, rid))
    except sqlite3.IntegrityError:
        pass
    return ok(message=f"Assigned role {role} to {user}")

@APP.get("/api/rbac/user/roles")
def user_roles():
    user = (request.args.get("user") or "").strip()
    if not user: return err("Missing user")
    rs = rows("""
        SELECT r.name FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user=? ORDER BY r.name
    """, (user,))
    return ok(roles=[r["name"] for r in rs])

@APP.get("/api/rbac/role/perms")
def role_perms():
    role = (request.args.get("role") or "").strip()
    if not role: return err("Missing role")
    rid = get_id("roles", role)
    if rid is None: return err(f"Unknown role '{role}'", 404)
    ps = rows("""
        SELECT p.name FROM role_perms rp
        JOIN perms p ON p.id = rp.perm_id
        WHERE rp.role_id=? ORDER BY p.name
    """, (rid,))
    return ok(perms=[p["name"] for p in ps])

@APP.get("/api/rbac/check")
def check_access():
    user = (request.args.get("user") or "").strip()
    perm = (request.args.get("perm") or "").strip()
    if not user or not perm: return err("Need user & perm")
    rs = rows("""
        SELECT 1 FROM user_roles ur
        JOIN role_perms rp ON rp.role_id = ur.role_id
        JOIN perms p ON p.id = rp.perm_id
        WHERE ur.user=? AND p.name=? LIMIT 1
    """, (user, perm))
    return ok(allowed=bool(rs))

@APP.get("/api/rbac/export")
def export_all():
    return ok(
        roles=rows("SELECT * FROM roles ORDER BY name"),
        perms=rows("SELECT * FROM perms ORDER BY name"),
        role_perms=rows("""
            SELECT r.name AS role, p.name AS perm
            FROM role_perms rp
            JOIN roles r ON r.id = rp.role_id
            JOIN perms p ON p.id = rp.perm_id
            ORDER BY r.name, p.name
        """),
        user_roles=rows("""
            SELECT ur.user, r.name AS role
            FROM user_roles ur
            JOIN roles r ON r.id = ur.role_id
            ORDER BY ur.user, r.name
        """)
    )

# ---------- CORS ----------
@APP.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

if __name__ == "__main__":
    # Run:
    #   python matrix-OS-A42-permissions.py
    # Quick try:
    #   curl -X POST localhost:5072/api/rbac/role -H "Content-Type: application/json" -d '{"name":"operator"}'
    #   curl -X POST localhost:5072/api/rbac/perm -H "Content-Type: application/json" -d '{"name":"analytics.read"}'
    #   curl -X POST localhost:5072/api/rbac/role/grant -H "Content-Type: application/json" -d '{"role":"operator","perm":"analytics.read"}'
    #   curl -X POST localhost:5072/api/rbac/user/assign -H "Content-Type: application/json" -d '{"user":"Admin","role":"operator"}'
    #   curl "localhost:5072/api/rbac/check?user=Admin&perm=analytics.read"
    APP.run(host="127.0.0.1", port=5072, debug=True)
