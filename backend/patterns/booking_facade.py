"""
Паттерн Facade — упрощённый интерфейс для отмены брони:
проверка времени (2+ часа) + обновление статуса + «уведомление».
"""
from backend.repositories.booking_repository import BookingRepository


class BookingFacade:
    """Фасад для сложных операций с бронированиями."""

    def __init__(self):
        self._repo = BookingRepository()
        self._notifications = []

    def cancel_booking(self, booking_id: int, user_id: int) -> dict:
        """
        Отмена брони клиентом:
        1) найти бронь
        2) проверить владельца
        3) проверить правило 2 часов
        4) отменить и уведомить
        """
        booking = self._repo.find_by_id(booking_id)
        if not booking:
            return {"success": False, "message": "Бронь не найдена"}

        if booking.user_id != user_id:
            return {"success": False, "message": "Нет доступа к этой брони"}

        if booking.cancelled_at or (
            booking.status and booking.status.name == "cancelled"
        ):
            return {"success": False, "message": "Эта бронь уже отменена"}

        if booking.status and booking.status.name == "rejected":
            return {
                "success": False,
                "message": "Бронь отклонена администратором — отменить нельзя",
            }

        if not booking.can_cancel():
            hours = booking.hours_until_visit()
            if hours < 0:
                return {"success": False, "message": "Время визита уже прошло"}
            return {
                "success": False,
                "message": (
                    f"До визита осталось {hours:.1f} ч. "
                    "Отмена возможна только за 2 и более часа."
                ),
            }

        booking.cancel()
        self._repo.save(booking)

        notification = self._send_notification(
            user_id,
            f"Бронь #{booking_id} отменена на {booking.booking_datetime}",
        )

        return {
            "success": True,
            "message": "Бронь успешно отменена",
            "booking": booking.to_dict(),
            "notification": notification,
        }

    def edit_booking(
        self,
        booking_id: int,
        user_id: int,
        booking_datetime=None,
        guests_count=None,
        table_id=None,
    ) -> dict:
        """Редактирование времени и/или количества гостей."""
        from datetime import datetime

        from backend.repositories.table_repository import TableRepository

        booking = self._repo.find_by_id(booking_id)
        if not booking:
            return {"success": False, "message": "Бронь не найдена"}
        if booking.user_id != user_id:
            return {"success": False, "message": "Нет доступа"}

        if booking_datetime and isinstance(booking_datetime, str):
            booking_datetime = datetime.fromisoformat(
                booking_datetime.replace("Z", "")
            )

        new_dt = booking_datetime or booking.booking_datetime
        new_table_id = table_id or booking.table_id

        table = TableRepository().find_by_id(new_table_id)
        if not table:
            return {"success": False, "message": "Столик не найден"}
        if not table.get_availability(new_dt, exclude_booking_id=booking.id):
            return {"success": False, "message": "Столик занят на выбранное время"}

        booking.edit(booking_datetime, guests_count, table_id)
        self._repo.save(booking)
        return {
            "success": True,
            "message": "Бронь обновлена",
            "booking": booking.to_dict(),
        }

    def get_user_bookings(self, user_id: int):
        bookings = self._repo.find_by_user(user_id)
        return [b.to_dict() for b in bookings]

    def _send_notification(self, user_id: int, text: str) -> dict:
        """Имитация уведомления (в реальном проекте — email/SMS)."""
        note = {"user_id": user_id, "text": text}
        self._notifications.append(note)
        return note
