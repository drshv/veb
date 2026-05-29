"""
Паттерн Builder — пошаговое создание брони:
дата/время → столик → контакты → финализация.
"""
from datetime import datetime

from backend.models.booking import Booking
from backend.models.status import Status
from backend.repositories.table_repository import TableRepository


class BookingBuilder:
    """Пошаговый конструктор объекта Booking."""

    def __init__(self, user_id: int):
        self._user_id = user_id
        self._booking = Booking()
        self._booking.user_id = user_id
        self._table_repo = TableRepository()
        self._pending_status_id = None

    def set_datetime(self, booking_datetime: datetime):
        """Шаг 1: дата и время."""
        if isinstance(booking_datetime, str):
            booking_datetime = datetime.fromisoformat(booking_datetime.replace("Z", ""))
        self._booking.booking_datetime = booking_datetime
        return self

    def set_table(self, table_id: int):
        """Шаг 2: выбор столика (с проверкой доступности)."""
        table = self._table_repo.find_by_id(table_id)
        if not table:
            raise ValueError("Столик не найден")
        if not table.is_active:
            raise ValueError("Столик недоступен для бронирования")
        if not self._booking.booking_datetime:
            raise ValueError("Сначала укажите дату и время (set_datetime)")
        if not table.get_availability(self._booking.booking_datetime):
            raise ValueError("Столик занят на выбранное время")
        self._booking.table_id = table_id
        return self

    def set_guests(self, guests_count: int):
        """Количество гостей."""
        if guests_count < 1:
            raise ValueError("Количество гостей должно быть не менее 1")
        self._booking.guests_count = guests_count
        return self

    def set_contacts(self, guest_name: str, phone: str):
        """Шаг 3: контактные данные (имя и телефон)."""
        self._booking.special_requests = f"Имя: {guest_name}"
        # Телефон дублируем в comment для админа
        self._booking.comment = self._booking.comment or ""
        if phone:
            self._booking.comment = (
                f"{self._booking.comment}\nТелефон: {phone}".strip()
            )
        return self

    def set_comment(self, comment: str):
        """Дополнительный комментарий к брони."""
        if comment:
            base = self._booking.comment or ""
            self._booking.comment = f"{base}\n{comment}".strip() if base else comment
        return self

    def set_status_pending(self):
        pending = Status.query.filter_by(name="pending").first()
        if not pending:
            raise ValueError("Статус 'pending' не найден в БД")
        self._booking.status_id = pending.id
        return self

    def build(self) -> Booking:
        """Шаг 4: финализация — проверка обязательных полей."""
        if not self._booking.booking_datetime:
            raise ValueError("Не указана дата и время")
        if not self._booking.table_id:
            raise ValueError("Не выбран столик")
        if not self._booking.guests_count:
            raise ValueError("Не указано количество гостей")
        if not self._booking.status_id:
            self.set_status_pending()
        return self._booking
