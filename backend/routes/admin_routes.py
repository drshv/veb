"""API: /api/admin — панель администратора."""
import io
from datetime import date, datetime

import pandas as pd
from flask import Blueprint, jsonify, request, send_file

from backend.models.status import Status
from backend.models.table import Table
from backend.patterns.auth_proxy import admin_required, auth_proxy
from backend.repositories.booking_repository import BookingRepository
from backend.repositories.table_repository import TableRepository

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
booking_repo = BookingRepository()
table_repo = TableRepository()


@admin_bp.route("/bookings/today", methods=["GET"])
@admin_required
def bookings_today():
    """Все брони на сегодня (для календаря)."""
    bookings = booking_repo.find_today()
    return jsonify(
        {
            "date": date.today().isoformat(),
            "bookings": [b.to_dict() for b in bookings],
        }
    )


@admin_bp.route("/bookings/calendar", methods=["GET"])
@admin_required
def bookings_calendar():
    """Брони на выбранную дату."""
    date_str = request.args.get("date", date.today().isoformat())
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Некорректная дата"}), 400
    bookings = booking_repo.find_by_date(target)
    return jsonify({"date": date_str, "bookings": [b.to_dict() for b in bookings]})


@admin_bp.route("/occupancy", methods=["GET"])
@admin_required
def occupancy():
    """График загрузки зала по часам."""
    date_str = request.args.get("date", date.today().isoformat())
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Некорректная дата"}), 400
    load = booking_repo.hourly_load(target)
    return jsonify({"date": date_str, "hourly_load": load})


@admin_bp.route("/bookings/history", methods=["GET"])
@admin_required
def booking_history():
    """История броней с фильтром по дате."""
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    if not date_from:
        date_from = date.today().isoformat()
    if not date_to:
        date_to = date_from
    try:
        d_from = date.fromisoformat(date_from)
        d_to = date.fromisoformat(date_to)
    except ValueError:
        return jsonify({"error": "Некорректный формат даты"}), 400

    bookings = booking_repo.find_by_date_range(d_from, d_to)
    return jsonify(
        {
            "from": date_from,
            "to": date_to,
            "bookings": [b.to_dict() for b in bookings],
        }
    )


@admin_bp.route("/bookings/<int:booking_id>/review", methods=["POST"])
@admin_required
def review_booking(booking_id):
    """Подтвердить или отклонить бронь с комментарием причины."""
    data = request.get_json() or {}
    action = data.get("action")  # confirm | reject
    reason = data.get("reason", "")

    booking = booking_repo.find_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Бронь не найдена"}), 404

    if action == "confirm":
        status = Status.query.filter_by(name="confirmed").first()
    elif action == "reject":
        status = Status.query.filter_by(name="rejected").first()
    else:
        return jsonify({"error": "action: confirm или reject"}), 400

    if not status:
        return jsonify({"error": "Статус не найден"}), 500

    booking.status_id = status.id
    if reason:
        booking.comment = (booking.comment or "") + f"\n[Админ]: {reason}"
    booking.updated_at = datetime.utcnow()
    booking_repo.save(booking)

    return jsonify({"message": f"Бронь {action}", "booking": booking.to_dict()})


@admin_bp.route("/export/csv", methods=["GET"])
@admin_required
def export_csv():
    """Экспорт броней за день в CSV."""
    date_str = request.args.get("date", date.today().isoformat())
    try:
        target = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Некорректная дата"}), 400

    bookings = booking_repo.find_by_date(target)
    # Плоская таблица с русскими заголовками — нормально открывается в Excel
    rows = []
    for b in bookings:
        rows.append(
            {
                "ID": b.id,
                "Дата и время": b.booking_datetime.strftime("%d.%m.%Y %H:%M")
                if b.booking_datetime
                else "",
                "Стол №": b.table.number if b.table else "",
                "Мест": b.table.seats if b.table else "",
                "Гостей": b.guests_count,
                "Статус": b.status.name if b.status else "",
                "Клиент": b.user.username if b.user else "",
                "Телефон": b.user.phone if b.user else "",
                "Комментарий": (b.comment or "").replace("\n", " ").strip(),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(
            columns=[
                "ID",
                "Дата и время",
                "Стол №",
                "Мест",
                "Гостей",
                "Статус",
                "Клиент",
                "Телефон",
                "Комментарий",
            ]
        )

    buf = io.BytesIO()
    # sep=';' — для русской Windows/Excel; utf-8-sig — кириллица без кракозябр
    df.to_csv(buf, index=False, sep=";", encoding="utf-8-sig")
    buf.seek(0)

    return send_file(
        buf,
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=f"bronirovaniya_{date_str}.csv",
    )


# --- Управление столиками ---

@admin_bp.route("/tables", methods=["GET"])
@admin_required
def admin_list_tables():
    tables = table_repo.find_all(active_only=False)
    return jsonify({"tables": [t.to_dict() for t in tables]})


@admin_bp.route("/tables", methods=["POST"])
@admin_required
def create_table():
    data = request.get_json() or {}
    table = Table(
        number=int(data["number"]),
        seats=int(data["seats"]),
        is_active=data.get("is_active", True),
        description=data.get("description"),
    )
    table_repo.save(table)
    return jsonify({"message": "Столик добавлен", "table": table.to_dict()}), 201


@admin_bp.route("/tables/<int:table_id>", methods=["PUT"])
@admin_required
def update_table(table_id):
    table = table_repo.find_by_id(table_id)
    if not table:
        return jsonify({"error": "Не найден"}), 404
    data = request.get_json() or {}
    if "number" in data:
        table.number = int(data["number"])
    if "seats" in data:
        table.seats = int(data["seats"])
    if "is_active" in data:
        table.is_active = bool(data["is_active"])
    if "description" in data:
        table.description = data["description"]
    table_repo.save(table)
    return jsonify({"message": "Обновлено", "table": table.to_dict()})


@admin_bp.route("/tables/<int:table_id>", methods=["DELETE"])
@admin_required
def delete_table(table_id):
    table = table_repo.find_by_id(table_id)
    if not table:
        return jsonify({"error": "Не найден"}), 404
    table_repo.delete(table)
    return jsonify({"message": "Столик удалён"})
