 FILE 1 — matrix-OS-01-login.html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Matrix Windows - Biometric Login</title>
  <style>
    body {
      background: radial-gradient(circle at center, #0a0a12, #000);
      color: #00fff9;
      font-family: "Orbitron", sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      overflow: hidden;
    }

    h1 {
      font-size: 2rem;
      text-shadow: 0 0 10px #00fff9;
      margin-bottom: 10px;
    }

    .scanner {
      border: 2px solid #00fff9;
      border-radius: 50%;
      width: 200px;
      height: 200px;
      box-shadow: 0 0 40px #00fff9;
      position: relative;
      animation: pulse 3s infinite ease-in-out;
    }

    @keyframes pulse {
      0%, 100% { box-shadow: 0 0 40px #00fff9; }
      50% { box-shadow: 0 0 80px #00fff9; }
    }

    .text {
      margin-top: 20px;
      font-size: 1.1rem;
      opacity: 0.8;
    }

    button {
      margin-top: 40px;
      padding: 10px 30px;
      background: #00fff9;
      color: #000;
      font-weight: bold;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      transition: 0.3s;
    }

    button:hover {
      background: #0ff;
      transform: scale(1.1);
    }
  </style>
</head>
<body>
  <h1>Matrix Windows Biometric Login</h1>
  <div class="scanner"></div>
  <div class="text">Scanning Facial, Voice, and Iris Data...</div>
  <button onclick="startLogin()">Access Matrix</button>

  <script>
    function startLogin() {
      alert("Biometric scan complete. Redirecting to Core System...");
      window.location.href = "matrix-OS-02-core.py";
    }
  </script>
</body>
</html>
# matrix-OS-02-core.py
# Matrix Windows Core Authentication System
# Matrix Instruction Manual, ARM Index, Volume 1

import hashlib
import time
from datetime import datetime

# Simulated stored biometric data for authentication
stored_data = {
    "username": "Admin",
    "voiceprint": "9a8b7c6d5e4f",
    "iris": "ZXCY-1122-9900",
    "face_hash": "6df9b2a31c"
}

def generate_token(username):
    """
    Generate a unique security token based on username and timestamp.
    """
    raw = f"{username}-{datetime.now()}-{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()

def verify_biometrics(input_voice, input_iris, input_face):
    """
    Verify input biometrics against stored data.
    """
    return (
        input_voice == stored_data["voiceprint"] and
        input_iris == stored_data["iris"] and
        input_face == stored_data["face_hash"]
    )

def matrix_login():
    """
    Main Matrix login logic.
    """
    print("=== Matrix Core System Activated ===")
    print("Initializing Biometric Verification...\n")

    voice = input("Enter voiceprint code: ")
    iris = input("Enter iris ID: ")
    face = input("Enter facial hash: ")

    if verify_biometrics(voice, iris, face):
        token = generate_token(stored_data["username"])
        print("\nAccess Granted ✅")
        print(f"User: {stored_data['username']}")
        print(f"Session Token: {token}")
        print(f"Login Time: {datetime.now()}")
    else:
        print("\nAccess Denied ❌ - Biometric mismatch detected")

if __name__ == "__main__":
    matrix_login()
