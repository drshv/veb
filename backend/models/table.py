"""Столик в зале ресторана."""
from datetime import datetime, timedelta
from typing import Optional

from backend.extensions import db


class Table(db.Model):
    __tablename__ = "tables"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    seats = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    description = db.Column(db.String(200))

    bookings = db.relationship("Booking", back_populates="table")

    def get_availability(
        self,
        booking_datetime: datetime,
        duration_hours: int = 2,
        exclude_booking_id: Optional[int] = None,
    ) -> bool:
        """
        Проверка: свободен ли столик в указанное время.
        Считаем занятым, если есть активная бронь в окне ±duration_hours.
        exclude_booking_id — при редактировании не учитывать текущую бронь.
        """
        from backend.models.booking import Booking
        from backend.models.status import Status

        if not self.is_active:
            return False

        start = booking_datetime - timedelta(hours=duration_hours)
        end = booking_datetime + timedelta(hours=duration_hours)

        cancelled_names = ("cancelled", "rejected")
        cancelled_ids = [
            s.id for s in Status.query.filter(Status.name.in_(cancelled_names)).all()
        ]

        q = Booking.query.filter(
            Booking.table_id == self.id,
            Booking.booking_datetime >= start,
            Booking.booking_datetime <= end,
        )
        if cancelled_ids:
            q = q.filter(~Booking.status_id.in_(cancelled_ids))
        if exclude_booking_id:
            q = q.filter(Booking.id != exclude_booking_id)

        return q.first() is None

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "seats": self.seats,
            "is_active": self.is_active,
            "description": self.description,
        }
