"""Пользователь системы (клиент или администратор)."""
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from backend.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    role = db.relationship("Role", back_populates="users")
    bookings = db.relationship("Booking", back_populates="user")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def register(self, password: str):
        """Регистрация — установка пароля."""
        self.set_password(password)

    def login(self, password: str) -> bool:
        """Проверка пароля при входе."""
        return self.check_password(password)

    def to_dict(self, include_role=False):
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role_id": self.role_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_role and self.role:
            data["role"] = self.role.name
        return data
