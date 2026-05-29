"""API: /api/tables — список столиков и свободные на время."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.repositories.table_repository import TableRepository

tables_bp = Blueprint("tables", __name__, url_prefix="/api/tables")
table_repo = TableRepository()


@tables_bp.route("", methods=["GET"])
def list_tables():
    """Схема зала — все активные столики."""
    tables = table_repo.find_all(active_only=False)
    return jsonify({"tables": [t.to_dict() for t in tables]})


@tables_bp.route("/available", methods=["GET"])
def available_tables():
    """Свободные столики на дату/время и число гостей."""
    dt_str = request.args.get("datetime")
    guests = int(request.args.get("guests", 1))

    if not dt_str:
        return jsonify({"error": "Укажите параметр datetime (ISO)"}), 400

    try:
        booking_dt = datetime.fromisoformat(dt_str.replace("Z", ""))
    except ValueError:
        return jsonify({"error": "Некорректный формат datetime"}), 400

    available = table_repo.find_available(booking_dt, min_seats=guests)
    return jsonify({"tables": [t.to_dict() for t in available], "datetime": dt_str})
