"""Бронь столика."""
from datetime import datetime, timedelta

from backend.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=False)
    booking_datetime = db.Column(db.DateTime, nullable=False)
    guests_count = db.Column(db.Integer, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey("statuses.id"), nullable=False)
    comment = db.Column(db.Text)
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="bookings")
    table = db.relationship("Table", back_populates="bookings")
    status = db.relationship("Status", back_populates="bookings")

    def hours_until_visit(self) -> float:
        """Сколько часов осталось до визита (локальное время, как в форме брони)."""
        if not self.booking_datetime:
            return 0.0
        delta = self.booking_datetime - datetime.now()
        return delta.total_seconds() / 3600

    def is_active_status(self) -> bool:
        """Можно ли ещё отменять (не отменена и не отклонена)."""
        if self.cancelled_at:
            return False
        if self.status and self.status.name in ("cancelled", "rejected"):
            return False
        return True

    def can_cancel(self) -> bool:
        """Отмена возможна только за 2+ часа до времени брони (локальное время)."""
        if not self.is_active_status():
            return False
        return self.hours_until_visit() >= 2

    def cancel(self):
        """Пометить бронь как отменённую."""
        from backend.models.status import Status

        cancelled = Status.query.filter_by(name="cancelled").first()
        if cancelled:
            self.status_id = cancelled.id
        self.cancelled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def edit(self, booking_datetime=None, guests_count=None, table_id=None):
        """Редактирование времени, гостей или столика."""
        if booking_datetime is not None:
            self.booking_datetime = booking_datetime
        if guests_count is not None:
            self.guests_count = guests_count
        if table_id is not None:
            self.table_id = table_id
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "table_id": self.table_id,
            "booking_datetime": self.booking_datetime.isoformat()
            if self.booking_datetime
            else None,
            "guests_count": self.guests_count,
            "status_id": self.status_id,
            "status": self.status.name if self.status else None,
            "comment": self.comment,
            "special_requests": self.special_requests,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "can_cancel": self.can_cancel(),
            "hours_until_visit": round(self.hours_until_visit(), 1),
            "is_active": self.is_active_status(),
            "table_number": self.table.number if self.table else None,
            "table_seats": self.table.seats if self.table else None,
            "username": self.user.username if self.user else None,
            "user_phone": self.user.phone if self.user else None,
        }
