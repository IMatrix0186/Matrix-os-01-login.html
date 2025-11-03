matrix-os A11 auth bridge system
# matrix-OS-A11-auth-bridge.py
# Matrix Windows Authentication Bridge (Flask)
# Verifies biometrics (A5), creates sessions (A3), activates AI (A6)
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, request, jsonify
import importlib.util
from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()

def load_module(module_name: str, filename: str):
    """Dynamically load another Matrix module that has hyphens in filename."""
    path = APP_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {filename}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Load the dependent modules
db      = load_module("matrix_os_a5_database",   "matrix-OS-A5-database.py")
sec_mod = load_module("matrix_os_a3_security",   "matrix-OS-A3-security.py")
ai_mod  = load_module("matrix_os_a6_ai_engine",  "matrix-OS-A6-ai-engine.py")
MatrixAI = ai_mod.MatrixAI

app = Flask(__name__)

# One shared AI instance (you can expand to per-token if needed)
AI = MatrixAI()

def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)

def err(message, code=400):
    return jsonify({"ok": False, "error": message}), code

@app.route("/api/auth/login", methods=["POST"])
def login():
    """
    JSON body:
    {
      "username": "Admin",
      "voice": "9a8b7c6d5e4f",
      "iris": "ZXCY-1122-9900",
      "face": "6df9b2a31c",
      "level": 3               # optional requested clearance (default from DB)
    }
    """
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    voice    = (data.get("voice") or "").strip()
    iris     = (data.get("iris") or "").strip()
    face     = (data.get("face") or "").strip()

    if not username or not voice or not iris or not face:
        return err("Missing required fields: username, voice, iris, face")

    # Verify biometrics against A5 database
    if not db.verify_biometrics(username, voice, iris, face):
        return err("Biometric verification failed", 401)

    # Fetch stored user to determine security level
    user = db.get_user(username)
    if not user:
        return err("User not found after verification", 404)

    # Create a security session via A3
    req_level = data.get("level")
    level = int(req_level) if req_level is not None else int(user["security_lvl"])
    session = sec_mod.create_session(username, level)
    token = session["token"]

    # Activate AI session for this user
    AI.activate_session(username)

    return ok(
        message="Login successful",
        token=token,
        security=session["level"],
        session=session
    )

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    """
    JSON body:
    { "token": "<session token from login>" }
    """
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return err("Missing token")

    # Revoke session in A3
    success = sec_mod.revoke_session(token)
    if not success:
        return err("Invalid or already revoked token", 400)

    # Close AI session (simple global; extend to per-token if desired)
    AI.session_active = False
    AI.user = None
    AI.log_event("Session terminated via logout.")

    return ok(message="Logout successful", token=token)

@app.route("/api/auth/session/verify", methods=["POST"])
def verify_session():
    """
    JSON body:
    { "token": "<session token>" }
    """
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return err("Missing token")

    valid = sec_mod.verify_session(token)
    return ok(valid=bool(valid))

# Simple CORS for local HTML pages
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp

if __name__ == "__main__":
    # Run: python matrix-OS-A11-auth-bridge.py
    # Endpoints:
    #   POST http://127.0.0.1:5080/api/auth/login
    #   POST http://127.0.0.1:5080/api/auth/logout
    #   POST http://127.0.0.1:5080/api/auth/session/verify
    app.run(host="127.0.0.1", port=5080, debug=True)
