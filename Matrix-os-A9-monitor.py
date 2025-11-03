matrix-os A9 system monitor
# matrix-OS-A9-monitor.py
# Matrix Windows System Monitor API
# Matrix Instruction Manual, ARM Index, Volume 1

from flask import Flask, jsonify
import psutil
import time
import importlib.util
from pathlib import Path

APP_DIR = Path(__file__).parent.resolve()

def load_module(module_name: str, filename: str):
    """Utility to import another Matrix file dynamically."""
    path = APP_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the database module
db = load_module("matrix_os_a5_database", "matrix-OS-A5-database.py")

app = Flask(__name__)
start_time = time.time()

def get_uptime():
    """Return formatted system uptime."""
    seconds = int(time.time() - start_time)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.route("/api/monitor/health", methods=["GET"])
def health():
    """Return general system health and uptime."""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory().percent
        uptime = get_uptime()
        users = len(db.list_users())
        data = {
            "ok": True,
            "cpu_percent": cpu,
            "memory_percent": memory,
            "uptime": uptime,
            "registered_users": users,
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Run: python matrix-OS-A9-monitor.py
    app.run(host="127.0.0.1", port=5050, debug=True)
