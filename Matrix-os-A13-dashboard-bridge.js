matrix-os A13 dashboard bridge system
// matrix-OS-A13-dashboard-bridge.js
// Enhances A4 dashboard: session verify + logout + UI updates

(() => {
  const AUTH_VERIFY = "http://127.0.0.1:5080/api/auth/session/verify";
  const AUTH_LOGOUT = "http://127.0.0.1:5080/api/auth/logout";
  const LOGIN_PAGE  = "matrix-OS-A1-login.html";

  function get(key) { return localStorage.getItem(key) || ""; }
  function setText(el, text) { if (el) el.textContent = text; }

  async function verifySessionOrRedirect() {
    const token = get("matrix_token");
    if (!token) {
      alert("Session missing. Redirecting to login.");
      window.location.href = LOGIN_PAGE;
      return false;
    }
    try {
      const res = await fetch(AUTH_VERIFY, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ token })
      });
      const data = await res.json();
      if (!data.ok || !data.valid) {
        alert("Session expired or invalid. Please log in again.");
        localStorage.removeItem("matrix_token");
        window.location.href = LOGIN_PAGE;
        return false;
      }
      return true;
    } catch (e) {
      alert("Unable to verify session. Check that A11 is running.\n" + e);
      return false;
    }
  }

  function updateDashboardText() {
    const user = get("matrix_user") || "Unknown";
    const sec  = get("matrix_security") || "Unknown";

    // Try to locate the existing info panel from A4 and rewrite it
    const info = document.querySelector(".info");
    if (info) {
      info.innerHTML = `
        <p><strong>User:</strong> <span id="mx-user"></span></p>
        <p><strong>Security Level:</strong> <span id="mx-sec"></span></p>
        <p><strong>Status:</strong> <span id="mx-status">Active Session</span></p>
        <p><strong>System Time:</strong> <span id="clock"></span></p>
      `;
      setText(document.getElementById("mx-user"), user);
      setText(document.getElementById("mx-sec"), sec);
    }

    // Live clock (keeps compatibility if #clock already exists)
    function updateClock() {
      const el = document.getElementById("clock");
      if (el) el.textContent = new Date().toLocaleTimeString();
    }
    updateClock();
    setInterval(updateClock, 1000);
  }

  async function handleLogout() {
    const token = get("matrix_token");
    if (!token) { window.location.href = LOGIN_PAGE; return; }
    try {
      const res = await fetch(AUTH_LOGOUT, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ token })
      });
      const data = await res.json();
      // Clear storage regardless to avoid stale sessions
      localStorage.removeItem("matrix_token");
      localStorage.removeItem("matrix_user");
      localStorage.removeItem("matrix_security");
      if (!data.ok) {
        alert("Logout request sent, but server reported: " + (data.error || "Unknown"));
      }
    } catch (e) {
      // Still proceed to login to prevent being stuck
      console.warn("Logout error:", e);
    } finally {
      window.location.href = LOGIN_PAGE;
    }
  }

  function wireLogoutButton() {
    // Use the existing button from A4 if present
    const btns = Array.from(document.getElementsByTagName("button"));
    const logoutBtn = btns.find(b => /logout/i.test(b.textContent || ""));
    if (logoutBtn) {
      logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        handleLogout();
      });
    }
  }

  async function init() {
    const ok = await verifySessionOrRedirect();
    if (!ok) return;
    updateDashboardText();
    wireLogoutButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
