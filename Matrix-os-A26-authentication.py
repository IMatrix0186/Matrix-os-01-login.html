matrix-os A26 authentication file
# matrix-OS-A26-notifications.py
# Matrix Windows — Notifications Service (SSE + Pull)
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, request, jsonify, Response
from datetime import datetime
from collections import deque
import json
import threading
import time

app = Flask(__name__)

# ===== Config =====
RING_SIZE = 500            # how many notifications to keep in memory
HEARTBEAT_EVERY = 20       # seconds between SSE heartbeats

# ===== State =====
_notifs = deque(maxlen=RING_SIZE)  # each item: dict with id, ts, level, message, source, user, details
_next_id = 1
_cv = threading.Condition()        # used to wake SSE/pull waiters

def _now_iso():
    return datetime.utcnow().isoformat()

def _next():
    global _next_id
    nid = _next_id
    _next_id += 1
    return nid

def push(level: str, message: str, source: str = "A26", user: str = "", details=None):
    """
    Programmatic helper to push a notification (import from other modules).
    Example:
        from matrix_OS_A26_notifications import push
        push("info", "Backup completed", source="A24", user="Admin")
    """
    if details is None:
        details = {}
    n = {
        "id": _next(),
        "ts": _now_iso(),
        "level": (level or "info").lower(),     # info|success|warning|error
        "message": str(message or ""),
        "source": str(source or "A26"),
        "user": str(user or ""),
        "details": details
    }
    with _cv:
        _notifs.append(n)
        _cv.notify_all()
    return n

# Seed a hello on boot
push("success", "A26 Notifications online", source="A26")

# ===== Helpers =====
def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def _slice_since(since_id: int, limit: int):
    # Return notifications with id > since_id (up to limit)
    items = [n for n in list(_notifs) if n["id"] > since_id]
    if limit > 0:
        items = items[:limit]
    return items

# ===== API: send, pull, stream =====
@app.route("/api/notify/send", methods=["POST"])
def api_send():
    """
    JSON:
    {
      "level": "info|success|warning|error",
      "message": "text",
      "source": "A24",
      "user": "Admin",
      "details": {...}
    }
    """
    data = request.get_json(silent=True) or {}
    level = (data.get("level") or "info")
    message = data.get("message")
    if not message:
        return err("Missing 'message'")
    n = push(level, message, data.get("source") or "A26", data.get("user") or "", data.get("details") or {})
    return ok(notification=n)

@app.route("/api/notify/pull", methods=["GET"])
def api_pull():
    """
    Poll notifications:
      GET /api/notify/pull?since=<id>&limit=50&wait=15
    - since: last seen id (default 0)
    - limit: max items (default 50)
    - wait:  long-poll seconds to wait if none available (default 0 -> no wait)
    """
    try:
        since = int(request.args.get("since", "0"))
    except Exception:
        since = 0
    try:
        limit = int(request.args.get("limit", "50"))
    except Exception:
        limit = 50
    try:
        wait_s = int(request.args.get("wait", "0"))
    except Exception:
        wait_s = 0

    items = _slice_since(since, limit)
    if items or wait_s <= 0:
        last_id = items[-1]["id"] if items else since
        return ok(notifications=items, last_id=last_id)

    # Long-poll wait
    end = time.time() + max(1, min(wait_s, 30))
    with _cv:
        while time.time() < end:
            # Re-check
            items = _slice_since(since, limit)
            if items:
                break
            remaining = end - time.time()
            if remaining <= 0:
                break
            _cv.wait(timeout=remaining)
    last_id = items[-1]["id"] if items else since
    return ok(notifications=items, last_id=last_id)

@app.route("/api/notify/stream", methods=["GET"])
def api_stream():
    """
    Server-Sent Events stream (Content-Type: text/event-stream)
    Optional query params:
      ?since=<id>  start by sending buffered items after <id>
      ?heartbeat=<seconds> override heartbeat interval
    """
    try:
        since = int(request.args.get("since", "0"))
    except Exception:
        since = 0
    try:
        hb = int(request.args.get("heartbeat", str(HEARTBEAT_EVERY)))
    except Exception:
        hb = HEARTBEAT_EVERY

    def gen():
        last_sent = time.time()
        # On connect: flush buffered items after 'since'
        items = _slice_since(since, RING_SIZE)
        for n in items:
            yield f"data: {json.dumps(n)}\n\n"

        # Then wait for new
        last_id = items[-1]["id"] if items else since
        while True:
            # Heartbeat if idle
            if time.time() - last_sent >= hb:
                yield "event: ping\ndata: {}\n\n"
                last_sent = time.time()

            with _cv:
                # Check if new items exist
                fresh = _slice_since(last_id, RING_SIZE)
                if fresh:
                    for n in fresh:
                        yield f"data: {json.dumps(n)}\n\n"
                        last_id = n["id"]
                        last_sent = time.time()
                else:
                    _cv.wait(timeout=1.0)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"   # for nginx proxies
    }
    return Response(gen(), headers=headers)

# ===== Convenience & Test =====
@app.route("/api/notify/test", methods=["POST", "GET"])
def api_test():
    n = push("info", f"Test notification @ { _now_iso() }", source="A26", user="Tester")
    return ok(notification=n)

# ===== CORS =====
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

# ===== Main =====
if __name__ == "__main__":
    # Run:
    #   python matrix-OS-A26-notifications.py
    # Endpoints:
    #   POST http://127.0.0.1:5069/api/notify/send
    #   GET  http://127.0.0.1:5069/api/notify/pull?since=0&limit=50
    #   GET  http://127.0.0.1:5069/api/notify/stream
    #   POST http://127.0.0.1:5069/api/notify/test
    app.run(host="127.0.0.1", port=5069, debug=True)
