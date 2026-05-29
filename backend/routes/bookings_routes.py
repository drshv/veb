"""API: /api/bookings — CRUD, отмена, редактирование."""
from datetime import datetime

from flask import Blueprint, jsonify, request, session

from backend.patterns.auth_proxy import auth_proxy, client_required, login_required
from backend.patterns.booking_builder import BookingBuilder
from backend.patterns.booking_facade import BookingFacade
from backend.repositories.booking_repository import BookingRepository
from backend.repositories.user_repository import UserRepository

bookings_bp = Blueprint("bookings", __name__, url_prefix="/api/bookings")
booking_repo = BookingRepository()
user_repo = UserRepository()
facade = BookingFacade()


@bookings_bp.route("", methods=["GET"])
@client_required
def my_bookings():
    """Свои брони клиента."""
    return jsonify({"bookings": facade.get_user_bookings(session["user_id"])})


@bookings_bp.route("/mine", methods=["GET"])
@client_required
def client_bookings():
    return jsonify({"bookings": facade.get_user_bookings(session["user_id"])})


@bookings_bp.route("", methods=["POST"])
@client_required
def create_booking():
    """
    Создание брони через Builder (все шаги в одном запросе).
    Body: datetime, table_id, guests_count, guest_name, phone, comment
    """
    data = request.get_json() or {}
    user_id = session["user_id"]

    try:
        builder = BookingBuilder(user_id)
        builder.set_datetime(data.get("datetime"))
        builder.set_table(int(data.get("table_id")))
        builder.set_guests(int(data.get("guests_count", 1)))
        builder.set_contacts(
            data.get("guest_name", ""),
            data.get("phone", ""),
        )
        if data.get("comment"):
            builder.set_comment(data["comment"])
        builder.set_status_pending()
        booking = builder.build()
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400

    # Обновить телефон в профиле пользователя
    user = user_repo.find_by_id(user_id)
    if user and data.get("phone"):
        user.phone = data["phone"]
        user_repo.save(user)

    booking_repo.save(booking)
    return jsonify({"message": "Бронь создана", "booking": booking.to_dict()}), 201


@bookings_bp.route("/<int:booking_id>", methods=["GET"])
@login_required
def get_booking(booking_id):
    booking = booking_repo.find_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Не найдено"}), 404
    if not auth_proxy.can_access_booking(booking):
        return jsonify({"error": "Нет доступа"}), 403
    return jsonify({"booking": booking.to_dict()})


@bookings_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@client_required
def cancel_booking(booking_id):
    """Отмена через Facade (правило 2+ часа)."""
    result = facade.cancel_booking(booking_id, session["user_id"])
    status = 200 if result["success"] else 400
    return jsonify(result), status


@bookings_bp.route("/<int:booking_id>", methods=["PUT"])
@client_required
def edit_booking(booking_id):
    data = request.get_json() or {}
    result = facade.edit_booking(
        booking_id,
        session["user_id"],
        booking_datetime=data.get("datetime"),
        guests_count=data.get("guests_count"),
        table_id=data.get("table_id"),
    )
    status = 200 if result["success"] else 400
    return jsonify(result), status


@bookings_bp.route("/<int:booking_id>/confirm", methods=["POST"])
@login_required
def confirm_booking(booking_id):
    """Подтверждение/отклонение — только админ (см. admin_routes)."""
    return jsonify({"error": "Используйте /api/admin/bookings/<id>/review"}), 400
