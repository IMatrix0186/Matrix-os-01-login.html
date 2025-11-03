matrix-os A18 telemetrysystems program
# matrix-OS-A18-telemetry.py
# Matrix Windows - Telemetry & Logs (Flask + SQLite)
# Stores AI events and Session history for later viewing
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, request, jsonify
import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import datetime
import importlib.util

APP_DIR = Path(__file__).parent.resolve()
DB_PATH = str(APP_DIR / "matrix_os_telemetry.sqlite3")

app = Flask(__name__)

# ---------- DB Helpers ----------

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with closing(db()) as conn, conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            user TEXT,
            event TEXT NOT NULL,
            details TEXT
        );
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS session_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            username TEXT,
            level TEXT,
            token TEXT,
            action TEXT NOT NULL,   -- created|revoked|verified|failed
            details TEXT
        );
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ai_events_ts ON ai_events(ts);
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_session_events_ts ON session_events(ts);
        """)

def now():
    return datetime.utcnow().isoformat()

# Public helpers (importable from other modules):
def log_ai_event(user: str, event: str, details: str = ""):
    init_db()
    with closing(db()) as conn, conn:
        conn.execute(
            "INSERT INTO ai_events (ts, user, event, details) VALUES (?, ?, ?, ?)",
            (now(), user, event, details),
        )

def log_session_event(username: str, level: str, token: str, action: str, details: str = ""):
    init_db()
    with closing(db()) as conn, conn:
        conn.execute(
            "INSERT INTO session_events (ts, username, level, token, action, details) VALUES (?, ?, ?, ?, ?, ?)",
            (now(), username, level, token, action, details),
        )

# ---------- Optional dynamic loads (if you want to call from here) ----------

def load_module(module_name: str, filename: str):
    """Utility to import another Matrix module by filename (supports hyphens)."""
    path = APP_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# You may uncomment these if you want to call A3/A6 from telemetry server directly:
# sec = load_module("matrix_os_a3_security", "matrix-OS-A3-security.py")
# ai_mod = load_module("matrix_os_a6_ai_engine", "matrix-OS-A6-ai-engine.py")
# MatrixAI = ai_mod.MatrixAI
# AI = MatrixAI()

# ---------- API Helpers ----------

def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(message, code=400):
    return jsonify({"ok": False, "error": message}), code

# ---------- Telemetry API ----------

@app.route("/api/telemetry/ai/add", methods=["POST"])
def api_ai_add():
    """
    JSON:
    { "user":"Admin", "event":"command", "details":"encrypt Hello" }
    """
    init_db()
    data = request.get_json(silent=True) or {}
    user    = (data.get("user") or "").strip()
    event   = (data.get("event") or "").strip()
    details = (data.get("details") or "")
    if not event:
        return err("Missing 'event'")
    log_ai_event(user, event, details)
    return ok(message="AI event recorded")

@app.route("/api/telemetry/ai/logs", methods=["GET"])
def api_ai_logs():
    """
    Optional query params:
      ?user=Admin
      ?limit=100 (default 200)
    """
    init_db()
    user = (request.args.get("user") or "").strip()
    try:
        limit = int(request.args.get("limit") or "200")
    except Exception:
        limit = 200
    q = "SELECT ts, user, event, details FROM ai_events "
    params = []
    if user:
        q += "WHERE user = ? "
        params.append(user)
    q += "ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with closing(db()) as conn:
        rows = conn.execute(q, tuple(params)).fetchall()
        result = [
            {"ts": r[0], "user": r[1], "event": r[2], "details": r[3]}
            for r in rows
        ]
        return ok(events=result, count=len(result))

@app.route("/api/telemetry/session/add", methods=["POST"])
def api_session_add():
    """
    JSON:
    { "username":"Admin", "level":"Developer (Level 3)", "token":"...", "action":"created", "details":"via A11" }
    action ∈ { created, revoked, verified, failed }
    """
    init_db()
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    level    = (data.get("level") or "").strip()
    token    = (data.get("token") or "").strip()
    action   = (data.get("action") or "").strip()
    details  = (data.get("details") or "")
    if not action:
        return err("Missing 'action'")
    log_session_event(username, level, token, action, details)
    return ok(message="Session event recorded")

@app.route("/api/telemetry/session/logs", methods=["GET"])
def api_session_logs():
    """
    Optional query params:
      ?username=Admin
      ?action=created
      ?limit=100 (default 200)
    """
    init_db()
    username = (request.args.get("username") or "").strip()
    action   = (request.args.get("action") or "").strip()
    try:
        limit = int(request.args.get("limit") or "200")
    except Exception:
        limit = 200

    q = "SELECT ts, username, level, token, action, details FROM session_events"
    clauses = []
    params = []
    if username:
        clauses.append("username = ?")
        params.append(username)
    if action:
        clauses.append("action = ?")
        params.append(action)
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with closing(db()) as conn:
        rows = conn.execute(q, tuple(params)).fetchall()
        result = [
            {"ts": r[0], "username": r[1], "level": r[2], "token": r[3], "action": r[4], "details": r[5]}
            for r in rows
        ]
        return ok(events=result, count=len(result))

# ---------- CORS ----------

@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

# ---------- Main ----------

if __name__ == "__main__":
    init_db()
    # Run:
    #   python matrix-OS-A18-telemetry.py
    # Endpoints:
    #   POST http://127.0.0.1:5065/api/telemetry/ai/add
    #   GET  http://127.0.0.1:5065/api/telemetry/ai/logs?user=Admin
    #   POST http://127.0.0.1:5065/api/telemetry/session/add
    #   GET  http://127.0.0.1:5065/api/telemetry/session/logs?action=created
    app.run(host="127.0.0.1", port=5065, debug=True)
