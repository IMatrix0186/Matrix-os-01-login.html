matrix-os A16 user api system file

# matrix-OS-A16-user-api.py
# Matrix Windows - User Profile API (Flask)
# Works with A5 database for get/upsert/update security
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, request, jsonify
import importlib.util
from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()

def load_module(module_name: str, filename: str):
    """Load another Matrix module even if its filename has hyphens."""
    path = APP_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load A5 database helpers
db = load_module("matrix_os_a5_database", "matrix-OS-A5-database.py")

app = Flask(__name__)

def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(message, code=400):
    return jsonify({"ok": False, "error": message}), code

@app.route("/api/user/profile", methods=["GET"])
def get_profile():
    """
    Query params:
      ?username=Admin
    """
    username = (request.args.get("username") or "").strip()
    if not username:
        return err("Missing ?username=")
    try:
        user = db.get_user(username)
        if not user:
            return err("User not found", 404)
        return ok(user=user)
    except Exception as e:
        return err(f"Failed to fetch user: {e}", 500)

@app.route("/api/user/profile", methods=["POST"])
def upsert_profile():
    """
    JSON body:
    {
      "username": "Admin",
      "voiceprint": "9a8b7c6d5e4f",
      "iris": "ZXCY-1122-9900",
      "face_hash": "6df9b2a31c",
      "security_lvl": 3   # optional (default 1)
    }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    voice    = (data.get("voiceprint") or "").strip()
    iris     = (data.get("iris") or "").strip()
    face     = (data.get("face_hash") or "").strip()
    level    = int(data.get("security_lvl") or 1)

    if not (username and voice and iris and face):
        return err("Missing required fields: username, voiceprint, iris, face_hash")

    try:
        db.init_db()
        db.upsert_user(username, voice, iris, face, level)
        return ok(message="Profile upserted", user=db.get_user(username))
    except Exception as e:
        return err(f"Failed to upsert profile: {e}", 500)

@app.route("/api/user/security", methods=["POST"])
def set_security():
    """
    JSON body:
    { "username": "Admin", "security_lvl": 3 }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    level    = data.get("security_lvl")

    if not username:
        return err("Missing username")
    try:
        level = int(level)
    except Exception:
        return err("security_lvl must be an integer")

    try:
        ok_update = db.update_security_level(username, level)
        if not ok_update:
            return err("User not found or level not changed", 404)
        return ok(message="Security level updated", user=db.get_user(username))
    except Exception as e:
        return err(f"Failed to update level: {e}", 500)

# Allow local HTML access
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

if __name__ == "__main__":
    # Run: python matrix-OS-A16-user-api.py
    # Endpoints:
    #   GET  http://127.0.0.1:5060/api/user/profile?username=Admin
    #   POST http://127.0.0.1:5060/api/user/profile
    #   POST http://127.0.0.1:5060/api/user/security
    app.run(host="127.0.0.1", port=5060, debug=True)
