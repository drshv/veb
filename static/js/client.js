/**
 * Клиентская страница: схема зала, пошаговое бронирование (Builder), мои брони.
 */
let currentUser = null;
let selectedTableId = null;
let hallTables = [];

const bookingDraft = {
  datetime: "",
  table_id: null,
  guests_count: 2,
  guest_name: "",
  phone: "",
  comment: "",
};

document.addEventListener("DOMContentLoaded", () => {
  checkSession();
  document.getElementById("btnLogin").addEventListener("click", doLogin);
  document.getElementById("btnRegister").addEventListener("click", doRegister);
  document.getElementById("btnLogout").addEventListener("click", doLogout);
  document.getElementById("btnFindTables").addEventListener("click", findAvailableTables);
  document.getElementById("btnCreateBooking").addEventListener("click", submitBooking);

  setupStepNav();
});

async function checkSession() {
  try {
    const data = await apiRequest("/api/auth/me");
    currentUser = data.user;
    if (currentUser.role_id === 1) {
      window.location.href = "/admin";
      return;
    }
    showApp();
  } catch {
    showAuth();
  }
}

function showAuth() {
  document.getElementById("authSection").classList.remove("d-none");
  document.getElementById("appSection").classList.add("d-none");
}

function showApp() {
  document.getElementById("authSection").classList.add("d-none");
  document.getElementById("appSection").classList.remove("d-none");
  document.getElementById("userGreeting").textContent =
    `Здравствуйте, ${currentUser.username}!`;
  loadHall();
  loadMyBookings();
}

async function doLogin() {
  hideAlert("authAlert");
  try {
    const data = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("loginUsername").value,
        password: document.getElementById("loginPassword").value,
      }),
    });
    currentUser = data.user;
    if (currentUser.role_id === 1) {
      window.location.href = "/admin";
      return;
    }
    showApp();
  } catch (e) {
    showAlert("authAlert", e.message);
  }
}

async function doRegister() {
  hideAlert("authAlert");
  try {
    const data = await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("regUsername").value,
        password: document.getElementById("regPassword").value,
        email: document.getElementById("regEmail").value,
        phone: document.getElementById("regPhone").value,
      }),
    });
    currentUser = data.user;
    showApp();
  } catch (e) {
    showAlert("authAlert", e.message);
  }
}

async function doLogout() {
  await apiRequest("/api/auth/logout", { method: "POST" });
  currentUser = null;
  showAuth();
}

async function loadHall() {
  const grid = document.getElementById("hallGrid");
  grid.innerHTML = "<p class='text-muted'>Загрузка...</p>";
  try {
    const data = await apiRequest("/api/tables");
    hallTables = data.tables;
    grid.innerHTML = "";
    hallTables.forEach((t) => {
      const card = document.createElement("div");
      card.className = `table-card ${t.is_active ? "" : "unavailable"}`;
      card.innerHTML = `
        <strong>Стол №${t.number}</strong><br>
        <small>${t.seats} мест</small><br>
        <small class="text-muted">${t.description || ""}</small>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    grid.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

function setupStepNav() {
  document.querySelectorAll("[data-next]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = parseInt(btn.dataset.next, 10);
      const current = next - 1;
      if (current === 2 && !bookingDraft.table_id) {
        showAlert("bookingAlert", "Сначала выберите столик");
        return;
      }
      if (next === 4) goStep(4);
      else goStep(next);
    });
  });
  document.querySelectorAll("[data-prev]").forEach((btn) => {
    btn.addEventListener("click", () => goStep(parseInt(btn.dataset.prev, 10)));
  });
}

function goStep(n) {
  document.querySelectorAll(".booking-steps .step").forEach((s) => {
    s.classList.toggle("active", parseInt(s.dataset.step, 10) === n);
  });
  document.querySelectorAll(".step-indicator span").forEach((sp) => {
    const sn = parseInt(sp.dataset.step, 10);
    sp.classList.remove("active", "done");
    if (sn < n) sp.classList.add("done");
    if (sn === n) sp.classList.add("active");
  });
}

async function findAvailableTables() {
  const dt = document.getElementById("bookingDatetime").value;
  const guests = document.getElementById("bookingGuests").value;
  if (!dt) {
    showAlert("bookingAlert", "Выберите дату и время");
    return;
  }
  hideAlert("bookingAlert");
  bookingDraft.datetime = dt;
  bookingDraft.guests_count = parseInt(guests, 10);

  try {
    const data = await apiRequest(
      `/api/tables/available?datetime=${encodeURIComponent(dt)}&guests=${guests}`
    );
    const list = document.getElementById("availableTables");
    list.innerHTML = "";
    if (!data.tables.length) {
      list.innerHTML = "<p>Нет свободных столиков на это время.</p>";
      return;
    }
    data.tables.forEach((t) => {
      const card = document.createElement("div");
      card.className = "table-card";
      card.dataset.id = t.id;
      card.innerHTML = `<strong>№${t.number}</strong> — ${t.seats} мест`;
      card.addEventListener("click", () => {
        document
          .querySelectorAll("#availableTables .table-card")
          .forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        selectedTableId = t.id;
        bookingDraft.table_id = t.id;
      });
      list.appendChild(card);
    });
    goStep(2);
  } catch (e) {
    showAlert("bookingAlert", e.message);
  }
}

async function submitBooking() {
  hideAlert("bookingAlert");
  bookingDraft.guest_name = document.getElementById("guestName").value;
  bookingDraft.phone = document.getElementById("guestPhone").value;
  bookingDraft.comment = document.getElementById("guestComment").value;

  if (!bookingDraft.table_id) {
    showAlert("bookingAlert", "Выберите столик на шаге 2");
    return;
  }

  try {
    await apiRequest("/api/bookings", {
      method: "POST",
      body: JSON.stringify({
        datetime: bookingDraft.datetime,
        table_id: bookingDraft.table_id,
        guests_count: bookingDraft.guests_count,
        guest_name: bookingDraft.guest_name,
        phone: bookingDraft.phone,
        comment: bookingDraft.comment,
      }),
    });
    showAlert("bookingAlert", "Бронь создана! Ожидайте подтверждения.", "success");
    loadMyBookings();
    goStep(1);
  } catch (e) {
    showAlert("bookingAlert", e.message);
  }
}

async function loadMyBookings() {
  const container = document.getElementById("myBookingsList");
  if (!currentUser) return;
  container.innerHTML = "Загрузка...";
  try {
    const data = await apiRequest("/api/bookings/mine");
    if (!data.bookings.length) {
      container.innerHTML = "<p class='text-muted'>У вас пока нет броней.</p>";
      return;
    }
    container.innerHTML = "";
    const statusRu = {
      pending: "Ожидает подтверждения",
      confirmed: "Подтверждена",
      cancelled: "Отменена",
      rejected: "Отклонена",
    };

    data.bookings.forEach((b) => {
      const card = document.createElement("div");
      card.className = "card mb-2";
      const dt = new Date(b.booking_datetime).toLocaleString("ru-RU");
      const statusText = statusRu[b.status] || b.status;
      const isCancelled = b.status === "cancelled" || b.cancelled_at;
      const isRejected = b.status === "rejected";
      const showCancel = b.can_cancel && !isCancelled && !isRejected;
      const showEdit = !isCancelled && !isRejected;

      let hint = "";
      if (isCancelled) {
        hint = '<small class="text-success d-block">Бронь отменена</small>';
      } else if (isRejected) {
        hint = '<small class="text-danger d-block">Отклонена администратором</small>';
      } else if (!b.can_cancel && b.hours_until_visit !== undefined) {
        if (b.hours_until_visit < 0) {
          hint = '<small class="text-muted d-block">Время визита уже прошло</small>';
        } else {
          hint = `<small class="text-muted d-block">До визита ${b.hours_until_visit} ч — отмена только за 2+ ч</small>`;
        }
      }

      card.innerHTML = `
        <div class="card-body">
          <h6>Стол №${b.table_number} — ${dt}</h6>
          <p class="mb-1">Гостей: ${b.guests_count} | Статус: <span class="badge bg-secondary">${statusText}</span></p>
          <p class="small text-muted">${b.comment || ""}</p>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary btn-edit" data-id="${b.id}"
              ${showEdit ? "" : "disabled"}>Изменить</button>
            <button class="btn btn-outline-danger btn-cancel" data-id="${b.id}"
              ${showCancel ? "" : "disabled"}>Отменить</button>
          </div>
          ${hint}
        </div>`;
      container.appendChild(card);

      if (showCancel) {
        card.querySelector(".btn-cancel").addEventListener("click", () => cancelBooking(b.id));
      }
      if (showEdit) {
        card.querySelector(".btn-edit").addEventListener("click", () => openEditModal(b));
      }
    });
  } catch (e) {
    container.innerHTML = `<p class="text-danger">${e.message}</p>`;
  }
}

async function cancelBooking(id) {
  if (!confirm("Отменить бронь?")) return;
  try {
    const data = await apiRequest(`/api/bookings/${id}/cancel`, { method: "POST" });
    alert(data.message || "Бронь отменена");
    loadMyBookings();
  } catch (e) {
    alert(e.message || "Не удалось отменить бронь");
  }
}

function openEditModal(b) {
  const newDt = prompt("Новая дата и время (YYYY-MM-DDTHH:MM):", b.booking_datetime.slice(0, 16));
  if (!newDt) return;
  const guests = prompt("Количество гостей:", b.guests_count);
  if (!guests) return;
  apiRequest(`/api/bookings/${b.id}`, {
    method: "PUT",
    body: JSON.stringify({ datetime: newDt, guests_count: parseInt(guests, 10) }),
  })
    .then((data) => {
      alert(data.message);
      loadMyBookings();
    })
    .catch((e) => alert(e.message));
}
