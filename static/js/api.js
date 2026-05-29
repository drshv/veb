/**
 * Общие функции для REST API (тонкий клиент).
 */
const API_BASE = "";

async function apiRequest(path, options = {}) {
  const defaults = {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  };
  const res = await fetch(API_BASE + path, { ...defaults, ...options });
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.message || "Ошибка запроса");
    return data;
  }
  if (!res.ok) throw new Error("Ошибка запроса");
  return res;
}

function showAlert(elId, message, type = "danger") {
  const el = document.getElementById(elId);
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.textContent = message;
  el.classList.remove("d-none");
}

function hideAlert(elId) {
  const el = document.getElementById(elId);
  if (el) el.classList.add("d-none");
}
