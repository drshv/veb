"""Repository для бронирований."""
from datetime import date, datetime

from backend.database.postgres_db import PostgresDB
from backend.models.booking import Booking
from backend.models.status import Status


class BookingRepository:
    def __init__(self):
        self._db = PostgresDB()

    def find_by_id(self, booking_id: int):
        return Booking.query.get(booking_id)

    def find_by_user(self, user_id: int):
        return (
            Booking.query.filter_by(user_id=user_id)
            .order_by(Booking.booking_datetime.desc())
            .all()
        )

    def find_by_date(self, target_date: date):
        """Все брони на конкретную дату."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return (
            Booking.query.filter(
                Booking.booking_datetime >= start,
                Booking.booking_datetime <= end,
            )
            .order_by(Booking.booking_datetime)
            .all()
        )

    def find_today(self):
        return self.find_by_date(date.today())

    def find_by_date_range(self, date_from: date, date_to: date):
        start = datetime.combine(date_from, datetime.min.time())
        end = datetime.combine(date_to, datetime.max.time())
        return (
            Booking.query.filter(
                Booking.booking_datetime >= start,
                Booking.booking_datetime <= end,
            )
            .order_by(Booking.booking_datetime.desc())
            .all()
        )

    def hourly_load(self, target_date: date):
        """Загрузка зала по часам: количество активных броней на каждый час."""
        bookings = self.find_by_date(target_date)
        cancelled = {s.name for s in Status.query.filter(Status.name.in_(("cancelled", "rejected"))).all()}
        hours = {h: 0 for h in range(8, 24)}  # ресторан 8:00–23:00
        for b in bookings:
            if b.status and b.status.name in cancelled:
                continue
            hour = b.booking_datetime.hour
            if hour in hours:
                hours[hour] += 1
        return [{"hour": h, "count": hours[h]} for h in sorted(hours)]

    def save(self, booking: Booking):
        self._db.session.add(booking)
        self._db.session.commit()
        return booking

    def delete(self, booking: Booking):
        self._db.session.delete(booking)
        self._db.session.commit()
