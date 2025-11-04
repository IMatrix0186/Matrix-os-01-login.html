matrix-os A24 backup file
# matrix-OS-A24-backup.py
# Matrix Windows – Backup & Restore Service
# Handles DB snapshots and restore endpoints

from flask import Flask, jsonify, send_file, request
from pathlib import Path
import shutil
import os
import time

APP_DIR = Path(__file__).parent.resolve()
BACKUP_DIR = APP_DIR / "backups"

if not BACKUP_DIR.exists():
    BACKUP_DIR.mkdir(parents=True)

app = Flask(__name__)

# === Helper Functions ===

def timestamp():
    return time.strftime("%Y%m%d-%H%M%S")

def db_backup(source_db, backup_name=None):
    if backup_name is None:
        backup_name = f"{source_db.stem}-{timestamp()}.sqlite3"
    backup_path = BACKUP_DIR / backup_name
    shutil.copy2(source_db, backup_path)
    return backup_path

# === Endpoints ===

@app.route("/api/backup", methods
