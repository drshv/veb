# Бронирование столиков в ресторане

Веб-приложение для бронирования столиков (без меню).  
Архитектура: **тонкий клиент** (HTML + CSS + JS) → **Flask REST API** → **PostgreSQL**.

## Паттерны проектирования

| Паттерн | Где в коде |
|---------|------------|
| **Singleton** | `backend/database/postgres_db.py` — единый доступ к БД |
| **Repository** | `backend/repositories/` — работа с users, tables, bookings |
| **Builder** | `backend/patterns/booking_builder.py` — пошаговое создание брони |
| **Facade** | `backend/patterns/booking_facade.py` — отмена (2 ч + статус + уведомление) |
| **Proxy** | `backend/patterns/auth_proxy.py` — проверка прав (клиент / админ) |

## Роли

- **Администратор** — `role_id = 1` (логин `admin`, пароль `admin123`)
- **Клиент** — `role_id = 2` (регистрация на главной странице)

## Требования

- Python 3.10+
- PostgreSQL 14+ (локально, порт 5432)

## Установка и запуск (Windows)

### 1. PostgreSQL

Создайте базу (через pgAdmin или командную строку):

```sql
CREATE DATABASE restaurant_booking;
```

По умолчанию в `config.py` строка подключения:

```
postgresql://postgres:postgres@localhost:5432/restaurant_booking
```

Измените логин/пароль в переменной окружения `DATABASE_URL` или в `config.py`, если у вас другие.

### 2. Виртуальное окружение

```powershell
cd "путь\к\папке\veb"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Запуск сервера

```powershell
python app.py
```

Откройте в браузере:

- Клиент: http://127.0.0.1:5000/
- Админ: http://127.0.0.1:5000/admin

Таблицы в БД создаются автоматически при первом запуске (`db.create_all()` + `seed.py`).

## Установка (Linux)

```bash
sudo -u postgres createdb restaurant_booking
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## API (кратко)

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register` | Регистрация клиента |
| POST | `/api/auth/login` | Вход |
| GET | `/api/tables` | Схема зала |
| GET | `/api/tables/available?datetime=...&guests=...` | Свободные столики |
| POST | `/api/bookings` | Создать бронь (Builder) |
| GET | `/api/bookings/mine` | Мои брони |
| POST | `/api/bookings/<id>/cancel` | Отмена (Facade, 2+ ч) |
| PUT | `/api/bookings/<id>` | Редактировать |
| GET | `/api/admin/bookings/calendar?date=...` | Брони на дату |
| GET | `/api/admin/occupancy?date=...` | Загрузка по часам |
| POST | `/api/admin/bookings/<id>/review` | Подтвердить/отклонить |
| GET | `/api/admin/export/csv?date=...` | CSV за день |
| CRUD | `/api/admin/tables` | Столики |

## Структура проекта

```
veb/
├── app.py                 # Точка входа Flask
├── config.py
├── requirements.txt
├── README.md
├── backend/
│   ├── models/            # SQLAlchemy: users, roles, tables, bookings, statuses
│   ├── repositories/
│   ├── patterns/          # Builder, Facade, AuthProxy
│   ├── database/          # PostgresDB (Singleton)
│   └── routes/            # REST endpoints
└── static/
    ├── index.html         # Страница клиента
    ├── admin.html         # Админ-панель
    ├── css/
    └── js/
```

## Бизнес-правила

1. **Отмена** — только если до визита осталось **2 и более часов** (`Booking.can_cancel()` + `BookingFacade`).
2. **Свободный столик** — нет активной брони в окне ±2 часа от выбранного времени.
3. **Редактирование** — время и количество гостей (и столик при необходимости).

## Уточнения

- Фронтенд **не содержит** бизнес-логики — только запросы к API.
- **Builder** вызывается на сервере при `POST /api/bookings`; на сайте шаги 1–4 повторяют этот процесс визуально.
- **Proxy** — декораторы `@login_required`, `@admin_required`, `@client_required` в `auth_proxy.py`.
