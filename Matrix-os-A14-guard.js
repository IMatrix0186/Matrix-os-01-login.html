matrix-os A14 guard system
// matrix-OS-A14-guard.js
// Drop-in guard for any protected HTML page

(() => {
  const AUTH_VERIFY_URL = "http://127.0.0.1:5080/api/auth/session/verify";
  const LOGIN_PAGE = "matrix-OS-A1-login.html";

  // Read attributes from the <script> tag if provided
  const me = document.currentScript || (function() {
    const scripts = document.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  })();
  const minLevelAttr = me?.dataset?.minLevel || ""; // e.g., data-min-level="3"
  const minLevel = parseInt(minLevelAttr, 10) || 0;

  function getLS(k){ return localStorage.getItem(k) || ""; }

  // Parse "Developer (Level 3)" -> 3
  function parseLevel(text) {
    if (!text) return 0;
    const m = String(text).match(/level\s*(\d+)/i);
    return m ? parseInt(m[1], 10) : 0;
  }

  async function verifyToken(token) {
    const res = await fetch(AUTH_VERIFY_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token })
    });
    const data = await res.json();
    return !!(data && data.ok && data.valid);
  }

  async function guard() {
    const token = getLS("matrix_token");
    if (!token) {
      window.location.href = LOGIN_PAGE;
      return;
    }

    try {
      const ok = await verifyToken(token);
      if (!ok) {
        localStorage.removeItem("matrix_token");
        window.location.href = LOGIN_PAGE;
        return;
      }

      if (minLevel > 0) {
        const storedSec = getLS("matrix_security"); // e.g., "Developer (Level 3)"
        const userLevel = parseLevel(storedSec);
        if (userLevel < minLevel) {
          alert("Insufficient clearance. Redirecting to login.");
          window.location.href = LOGIN_PAGE;
          return;
        }
      }
      // Passed guard — do nothing, page stays loaded
    } catch (e) {
      console.warn("Guard verify error:", e);
      window.location.href = LOGIN_PAGE;
    }
  }

  // Expose manual API if needed
  window.MatrixGuard = { guard };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", guard);
  } else {
    guard();
  }
})();
