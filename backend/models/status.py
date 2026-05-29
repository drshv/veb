"""Статусы брони: pending, confirmed, cancelled, rejected."""
from backend.extensions import db


class Status(db.Model):
    __tablename__ = "statuses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))

    bookings = db.relationship("Booking", back_populates="status")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description}
