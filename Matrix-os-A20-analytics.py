matrix-os A20 analytics system
# matrix-OS-A20-analytics.py
# Matrix Windows – Log Analytics Engine (Flask + SQLite)
# Consumes matrix_os_telemetry.sqlite3 and produces summary analytics
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, jsonify
import sqlite3
from datetime import datetime, timedelta
from contextlib import closing
from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()
DB_PATH = APP_DIR / "matrix_os_telemetry.sqlite3"

app = Flask(__name__)

def db():
    return sqlite3.connect(DB_PATH)

def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def get_rows(q, args=()):
    with closing(db()) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(q, args).fetchall()]

# ---------- Core Analytics ----------
def top_users(limit=5):
    q = """SELECT user, COUNT(*) AS count FROM ai_events
           WHERE user IS NOT NULL AND user!=''
           GROUP BY user ORDER BY count DESC LIMIT ?"""
    return get_rows(q, (limit,))

def top_events(limit=5):
    q = """SELECT event, COUNT(*) AS count FROM ai_events
           GROUP BY event ORDER BY count DESC LIMIT ?"""
    return get_rows(q, (limit,))

def session_summary():
    q = """SELECT action, COUNT(*) AS count FROM session_events
           GROUP BY action ORDER BY count DESC"""
    return get_rows(q)

def failed_logins(limit=10):
    q = """SELECT username, ts, details FROM session_events
           WHERE action='failed' ORDER BY id DESC LIMIT ?"""
    return get_rows(q, (limit,))

def recent_activity(hours=24):
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    q_ai = """SELECT ts,'AI' AS type,user AS actor,event AS info
              FROM ai_events WHERE ts>=?"""
    q_sess = """SELECT ts,'SESSION' AS type,username AS actor,action AS info
                FROM session_events WHERE ts>=?"""
    rows = get_rows(q_ai, (cutoff,)) + get_rows(q_sess, (cutoff,))
    rows.sort(key=lambda r: r["ts"], reverse=True)
    return rows

# ---------- API Endpoints ----------
@app.route("/api/analytics/summary")
def api_summary():
    try:
        data = {
            "top_users": top_users(),
            "top_events": top_events(),
            "session_summary": session_summary(),
            "failed_logins": failed_logins(),
            "recent_24h": recent_activity(24),
        }
        return ok(data)
    except Exception as e:
        return err(str(e), 500)

@app.route("/api/analytics/user/<username>")
def api_user(username):
    try:
        q1 = """SELECT ts,event,details FROM ai_events
                WHERE user=? ORDER BY id DESC LIMIT 50"""
        q2 = """SELECT ts,action,details FROM session_events
                WHERE username=? ORDER BY id DESC LIMIT 50"""
        ai = get_rows(q1, (username,))
        sess = get_rows(q2, (username,))
        return ok({"ai": ai, "sessions": sess})
    except Exception as e:
        return err(str(e), 500)

@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

if __name__ == "__main__":
    # Run: python matrix-OS-A20-analytics.py
    # Examples:
    #   GET http://127.0.0.1:5066/api/analytics/summary
    #   GET http://127.0.0.1:5066/api/analytics/user/Admin
    app.run(host="127.0.0.1", port=5066, debug=True)
