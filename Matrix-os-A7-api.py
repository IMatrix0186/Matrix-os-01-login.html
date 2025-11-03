matrix-os A7 api system
# matrix-OS-A7-api.py
# Matrix Windows API Bridge (Flask)
# Exposes endpoints for AI Engine + Database
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, request, jsonify
import importlib.util
from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()

def load_module(module_name: str, filename: str):
    """Dynamically load a module from a file with hyphens in the name."""
    path = APP_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load A5 (database) and A6 (AI Engine) even though filenames contain hyphens
db = load_module("matrix_os_a5_database", "matrix-OS-A5-database.py")
ai_mod = load_module("matrix_os_a6_ai_engine", "matrix-OS-A6-ai-engine.py")
MatrixAI = ai_mod.MatrixAI

app = Flask(__name__)

# Single, simple AI instance (you can expand to per-session later)
AI = MatrixAI()

# --- Helpers ---

def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(message, code=400):
    return jsonify({"ok": False, "error": message}), code

# --- Routes ---

@app.route("/api/health", methods=["GET"])
def health():
    return ok(status="healthy")

@app.route("/api/users", methods=["GET"])
def list_users():
    try:
        users = db.list_users()
        return ok(users=users)
    except Exception as e:
        return err(f"Failed to list users: {e}")

@app.route("/api/ai/activate", methods=["POST"])
def ai_activate():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "Admin")
    try:
        AI.activate_session(username)
        return ok(message=f"AI session activated for {username}")
    except Exception as e:
        return err(f"Activation failed: {e}")

@app.route("/api/ai/command", methods=["POST"])
def ai_command():
    data = request.get_json(silent=True) or {}
    cmd = data.get("command", "").strip()
    if not cmd:
        return err("Missing 'command' in JSON payload.")
    try:
        response = AI.process_command(cmd)
        return ok(response=response)
    except Exception as e:
        return err(f"Command failed: {e}")

@app.route("/api/ai/log", methods=["GET"])
def ai_log():
    try:
        log = AI.show_log()
        return ok(log=log)
    except Exception as e:
        return err(f"Failed to fetch log: {e}")

# --- Simple CORS so a local HTML page can call the API in the browser ---

@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

if __name__ == "__main__":
    # Run: python matrix-OS-A7-api.py
    # Default: http://127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
