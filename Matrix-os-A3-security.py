matrix-os-A3-security clearance system
# matrix-OS-A3-security.py
# Matrix Operating System Security Clearance Module
# Matrix Instruction Manual, ARM Index, Volume 1

import hashlib
import json
import time
from datetime import datetime

# Define user security clearance levels
SECURITY_LEVELS = {
    1: "Basic User",
    2: "Administrator",
    3: "Developer",
    4: "Root Access"
}

# Store active sessions
active_sessions = {}

def generate_security_token(username, level):
    """
    Generate a unique token based on username, security level, and timestamp.
    """
    raw = f"{username}-{level}-{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()

def create_session(username, level):
    """
    Create and store a new active session for a verified user.
    """
    token = generate_security_token(username, level)
    session = {
        "username": username,
        "level": SECURITY_LEVELS.get(level, "Unknown"),
        "token": token,
        "created": datetime.now().isoformat(),
        "status": "Active"
    }
    active_sessions[token] = session
    return session

def verify_session(token):
    """
    Verify if a session token is valid and still active.
    """
    return token in active_sessions and active_sessions[token]["status"] == "Active"

def revoke_session(token):
    """
    Revoke (end) a session if it exists.
    """
    if token in active_sessions:
        active_sessions[token]["status"] = "Revoked"
        return True
    return False

def list_sessions():
    """
    Display all active sessions.
    """
    return json.dumps(active_sessions, indent=4)

# Example test
if __name__ == "__main__":
    user = "Admin"
    level = 3  # Developer level
    session = create_session(user, level)
    print("Session Created ✅")
    print(json.dumps(session, indent=4))
    print("\nAll Active Sessions:")
    print(list_sessions())
