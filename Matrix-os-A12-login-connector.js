matrix-os A12 login connector system
// matrix-OS-A12-login-connector.js
// Hooks the A1 login page to A11 auth bridge

(() => {
  const AUTH_URL = "http://127.0.0.1:5080/api/auth/login";
  const DASHBOARD = "matrix-OS-A4-dashboard.html";

  function makeUI() {
    // If the page already has our UI, skip
    if (document.getElementById("mx-login-box")) return;

    // Container
    const box = document.createElement("div");
    box.id = "mx-login-box";
    box.style.cssText = `
      position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%);
      width: 90%; max-width: 420px; padding: 16px 16px 20px;
      background: rgba(0,0,0,.65); border: 1px solid #00fff9; border-radius: 12px;
      box-shadow: 0 0 24px #00fff9; color: #aef; font-family: system-ui, sans-serif; text-align:center;
    `;

    box.innerHTML = `
      <div style="font-weight:700;color:#00fff9;text-shadow:0 0 8px #00fff9;margin-bottom:8px;">
        Matrix Biometric Login
      </div>
      <input id="mx-username" placeholder="Username (e.g., Admin)" style="width:100%;padding:10px;margin:6px 0;border-radius:8px;border:none;text-align:center;" />
      <input id="mx-voice" placeholder="Voiceprint (e.g., 9a8b7c6d5e4f)" style="width:100%;padding:10px;margin:6px 0;border-radius:8px;border:none;text-align:center;" />
      <input id="mx-iris" placeholder="Iris ID (e.g., ZXCY-1122-9900)" style="width:100%;padding:10px;margin:6px 0;border-radius:8px;border:none;text-align:center;" />
      <input id="mx-face" placeholder="Facial Hash (e.g., 6df9b2a31c)" style="width:100%;padding:10px;margin:6px 0;border-radius:8px;border:none;text-align:center;" />
      <button id="mx-login-btn" style="margin-top:10px;padding:10px 18px;font-weight:700;border:none;border-radius:8px;background:#00fff9;color:#000;cursor:pointer;">
        Authenticate
      </button>
      <div id="mx-msg" style="margin-top:10px;min-height:18px;color:#aee;"></div>
    `;

    document.body.appendChild(box);
    document.getElementById("mx-login-btn").addEventListener("click", doLogin);
  }

  async function doLogin() {
    const username = document.getElementById("mx-username").value.trim() || "Admin";
    const voice    = document.getElementById("mx-voice").value.trim();
    const iris     = document.getElementById("mx-iris").value.trim();
    const face     = document.getElementById("mx-face").value.trim();
    const msg      = document.getElementById("mx-msg");

    if (!voice || !iris || !face) {
      msg.textContent = "Please enter voiceprint, iris, and facial hash.";
      return;
    }

    msg.textContent = "Authenticating…";

    try {
      const res = await fetch(AUTH_URL, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ username, voice, iris, face })
      });
      const data = await res.json();
      if (!data.ok) {
        msg.textContent = "❌ " + (data.error || "Login failed");
        return;
      }

      // Save token + session info for later pages
      localStorage.setItem("matrix_token", data.token);
      localStorage.setItem("matrix_user", username);
      localStorage.setItem("matrix_security", data.security || "");

      msg.textContent = "✅ Access granted — redirecting…";
      setTimeout(() => { window.location.href = DASHBOARD; }, 700);
    } catch (e) {
      msg.textContent = "⚠️ Connection error: " + e;
    }
  }

  // Replace old button behavior on A1 (if present)
  function overrideA1Button() {
    const btns = Array.from(document.getElementsByTagName("button"));
    const accessBtn = btns.find(b => /access matrix/i.test(b.textContent || ""));
    if (accessBtn) {
      accessBtn.onclick = (e) => {
        e.preventDefault();
        const msg = document.getElementById("mx-msg");
        if (msg) msg.textContent = "Enter biometrics below, then press Authenticate.";
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      };
    }
  }

  // Init
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => { makeUI(); overrideA1Button(); });
  } else {
    makeUI(); overrideA1Button();
  }
})();
