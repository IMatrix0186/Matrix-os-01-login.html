matrix-os database system
# matrix-OS-A5-database.py
# Matrix Windows User Database (SQLite)
# Matrix Instruction Manual, ARM Index, Volume 1

import sqlite3
from contextlib import closing
from datetime import datetime

DB_PATH = "matrix_os_users.sqlite3"

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
          username      TEXT PRIMARY KEY,
          voiceprint    TEXT NOT NULL,
          iris          TEXT NOT NULL,
          face_hash     TEXT NOT NULL,
          security_lvl  INTEGER NOT NULL DEFAULT 1,
          created_at    TEXT NOT NULL,
          updated_at    TEXT NOT NULL
        );
        """)

def upsert_user(username, voiceprint, iris, face_hash, security_lvl=1):
    now = datetime.utcnow().isoformat()
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        # insert or update
        conn.execute("""
        INSERT INTO users (username, voiceprint, iris, face_hash, security_lvl, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
          voiceprint=excluded.voiceprint,
          iris=excluded.iris,
          face_hash=excluded.face_hash,
          security_lvl=excluded.security_lvl,
          updated_at=excluded.updated_at;
        """, (username, voiceprint, iris, face_hash, security_lvl, now, now))

def get_user(username):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("""
        SELECT username, voiceprint, iris, face_hash, security_lvl, created_at, updated_at
        FROM users WHERE username=?;
        """, (username,)).fetchone()
        if not row:
            return None
        return {
            "username": row[0],
            "voiceprint": row[1],
            "iris": row[2],
            "face_hash": row[3],
            "security_lvl": row[4],
            "created_at": row[5],
            "updated_at": row[6],
        }

def verify_biometrics(username, input_voice, input_iris, input_face):
    user = get_user(username)
    if not user:
        return False
    return (
        input_voice == user["voiceprint"] and
        input_iris == user["iris"] and
        input_face == user["face_hash"]
    )

def update_security_level(username, new_level):
    now = datetime.utcnow().isoformat()
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        cur = conn.execute("""
        UPDATE users SET security_lvl=?, updated_at=? WHERE username=?;
        """, (new_level, now, username))
        return cur.rowcount == 1

def list_users():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        rows = conn.execute("""
        SELECT username, security_lvl, created_at, updated_at FROM users ORDER BY username;
        """).fetchall()
        return [
            {"username": r[0], "security_lvl": r[1], "created_at": r[2], "updated_at": r[3]}
        for r in rows]

# --- Example seeding & quick test ---
if __name__ == "__main__":
    init_db()
    # Seed Admin (matches earlier examples)
    upsert_user(
        username="Admin",
        voiceprint="9a8b7c6d5e4f",
        iris="ZXCY-1122-9900",
        face_hash="6df9b2a31c",
        security_lvl=3  # Developer
    )
    print("Users:", list_users())
    print("Verify Admin biometrics:", verify_biometrics("Admin", "9a8b7c6d5e4f", "ZXCY-1122-9900", "6df9b2a31c"))
