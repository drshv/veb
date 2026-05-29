/**
 * Админ-панель: календарь, график загрузки, столики, история, CSV.
 */
let adminUser = null;
let occupancyChart = null;

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnAdminLogin").addEventListener("click", adminLogin);
  document.getElementById("btnAdminLogout").addEventListener("click", adminLogout);
  document.getElementById("btnLoadCalendar").addEventListener("click", loadCalendar);
  document.getElementById("btnLoadOccupancy").addEventListener("click", loadOccupancy);
  document.getElementById("btnLoadHistory").addEventListener("click", loadHistory);
  document.getElementById("btnExportCsv").addEventListener("click", exportCsv);
  document.getElementById("btnAddTable").addEventListener("click", addTable);

  checkAdminSession();
});

async function checkAdminSession() {
  try {
    const data = await apiRequest("/api/auth/me");
    if (data.user.role_id !== 1) {
      showAdminAuth();
      return;
    }
    adminUser = data.user;
    showAdminApp();
  } catch {
    showAdminAuth();
  }
}

function showAdminAuth() {
  document.getElementById("adminAuth").classList.remove("d-none");
  document.getElementById("adminApp").classList.add("d-none");
}

function showAdminApp() {
  document.getElementById("adminAuth").classList.add("d-none");
  document.getElementById("adminApp").classList.remove("d-none");
  document.getElementById("adminGreeting").textContent = `Админ: ${adminUser.username}`;
  loadCalendar();
  loadOccupancy();
  loadAdminTables();
  loadHistory();
}

async function adminLogin() {
  hideAlert("adminAuthAlert");
  try {
    const data = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("adminUsername").value,
        password: document.getElementById("adminPassword").value,
      }),
    });
    if (data.user.role_id !== 1) {
      showAlert("adminAuthAlert", "Это не учётная запись администратора");
      await apiRequest("/api/auth/logout", { method: "POST" });
      return;
    }
    adminUser = data.user;
    showAdminApp();
  } catch (e) {
    showAlert("adminAuthAlert", e.message);
  }
}

async function adminLogout() {
  await apiRequest("/api/auth/logout", { method: "POST" });
  adminUser = null;
  showAdminAuth();
}

function showUpdatedHint(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = `Обновлено в ${new Date().toLocaleTimeString("ru-RU")}`;
  el.classList.remove("d-none");
}

async function loadCalendar() {
  const dateStr = document.getElementById("calendarDate").value || todayStr();
  const list = document.getElementById("calendarBookings");
  list.innerHTML = "Загрузка...";
  try {
    const data = await apiRequest(`/api/admin/bookings/calendar?date=${dateStr}`);
    // В календаре показываем только заявки, которые требуют решения (pending).
    // Подтверждённые/отклонённые смотрим в "Истории броней".
    const pending = (data.bookings || []).filter((b) => b.status === "pending");

    if (!pending.length) {
      list.innerHTML = "<p class='text-muted'>Нет заявок (pending) на эту дату.</p>";
      return;
    }
    list.innerHTML = "";
    pending.forEach((b) => {
      const item = document.createElement("div");
      item.className = "list-group-item";
      const dt = new Date(b.booking_datetime).toLocaleString("ru-RU");
      item.innerHTML = `
        <div class="d-flex justify-content-between flex-wrap gap-2">
          <div>
            <strong>${dt}</strong> — стол №${b.table_number}, ${b.guests_count} гостей<br>
            <small>${b.username} | ${b.status}</small>
          </div>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-success btn-confirm" data-id="${b.id}">✓</button>
            <button class="btn btn-danger btn-reject" data-id="${b.id}">✗</button>
          </div>
        </div>`;
      list.appendChild(item);
      item.querySelector(".btn-confirm").addEventListener("click", () => review(b.id, "confirm"));
      item.querySelector(".btn-reject").addEventListener("click", () => review(b.id, "reject"));
    });
    showUpdatedHint("calendarHint");
  } catch (e) {
    list.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

async function review(id, action) {
  const reason = prompt(action === "reject" ? "Причина отклонения:" : "Комментарий (необязательно):") || "";
  try {
    await apiRequest(`/api/admin/bookings/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ action, reason }),
    });
    loadCalendar();
    loadOccupancy();
  } catch (e) {
    alert(e.message);
  }
}

async function loadOccupancy() {
  const dateStr = document.getElementById("occupancyDate").value || todayStr();
  try {
    const data = await apiRequest(`/api/admin/occupancy?date=${dateStr}`);
    const labels = data.hourly_load.map((x) => `${x.hour}:00`);
    const counts = data.hourly_load.map((x) => x.count);
    const ctx = document.getElementById("occupancyChart");
    if (occupancyChart) occupancyChart.destroy();
    occupancyChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Броней", data: counts, backgroundColor: "#0d6efd" }],
      },
      options: { scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
    });
    showUpdatedHint("occupancyHint");
  } catch (e) {
    console.error(e);
  }
}

async function loadHistory() {
  const from = document.getElementById("historyFrom").value;
  const to = document.getElementById("historyTo").value || from;
  const el = document.getElementById("historyList");
  el.innerHTML = "Загрузка...";
  try {
    const data = await apiRequest(`/api/admin/bookings/history?from=${from}&to=${to}`);
    if (!data.bookings.length) {
      el.innerHTML = "<p class='text-muted'>Нет записей.</p>";
      return;
    }
    el.innerHTML = "<table class='table table-sm'><thead><tr><th>Дата</th><th>Стол</th><th>Гости</th><th>Статус</th><th>Клиент</th></tr></thead><tbody></tbody></table>";
    const tbody = el.querySelector("tbody");
    data.bookings.forEach((b) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${new Date(b.booking_datetime).toLocaleString("ru-RU")}</td>
        <td>№${b.table_number}</td>
        <td>${b.guests_count}</td>
        <td>${b.status}</td>
        <td>${b.username}</td>`;
      tbody.appendChild(tr);
    });
    showUpdatedHint("historyHint");
  } catch (e) {
    el.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

function exportCsv() {
  const dateStr = document.getElementById("exportDate").value || todayStr();
  window.location.href = `/api/admin/export/csv?date=${dateStr}`;
}

async function loadAdminTables() {
  const el = document.getElementById("tablesAdminList");
  el.innerHTML = "Загрузка...";
  try {
    const data = await apiRequest("/api/admin/tables");
    el.innerHTML = "";
    data.tables.forEach((t) => {
      const row = document.createElement("div");
      row.className = "d-flex justify-content-between align-items-center border rounded p-2 mb-2";
      row.innerHTML = `
        <span>№${t.number} — ${t.seats} мест ${t.is_active ? "" : "(неактивен)"}</span>
        <div>
          <button class="btn btn-sm btn-outline-primary btn-edit-table">Изменить</button>
          <button class="btn btn-sm btn-outline-danger btn-del-table">Удалить</button>
        </div>`;
      el.appendChild(row);
      row.querySelector(".btn-edit-table").addEventListener("click", () => editTable(t));
      row.querySelector(".btn-del-table").addEventListener("click", () => deleteTable(t.id));
    });
  } catch (e) {
    el.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

async function addTable() {
  const number = document.getElementById("newTableNumber").value;
  const seats = document.getElementById("newTableSeats").value;
  try {
    await apiRequest("/api/admin/tables", {
      method: "POST",
      body: JSON.stringify({ number: parseInt(number, 10), seats: parseInt(seats, 10) }),
    });
    loadAdminTables();
  } catch (e) {
    alert(e.message);
  }
}

async function editTable(t) {
  const seats = prompt("Новая вместимость:", t.seats);
  if (!seats) return;
  try {
    await apiRequest(`/api/admin/tables/${t.id}`, {
      method: "PUT",
      body: JSON.stringify({ seats: parseInt(seats, 10) }),
    });
    loadAdminTables();
  } catch (e) {
    alert(e.message);
  }
}

async function deleteTable(id) {
  if (!confirm("Удалить столик?")) return;
  try {
    await apiRequest(`/api/admin/tables/${id}`, { method: "DELETE" });
    loadAdminTables();
  } catch (e) {
    alert(e.message);
  }
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}
