"""
Паттерн Proxy — проверка прав доступа перед выполнением операций.
Клиент видит только свои брони, администратор — все.
"""
from functools import wraps

from flask import jsonify, session

from backend.repositories.user_repository import UserRepository


class AuthProxy:
    """Прокси для аутентификации и авторизации."""

    ROLE_ADMIN = 1
    ROLE_CLIENT = 2

    def __init__(self):
        self._user_repo = UserRepository()

    def check_auth(self) -> bool:
        """Пользователь авторизован?"""
        return "user_id" in session

    def get_current_user(self):
        if not self.check_auth():
            return None
        return self._user_repo.find_by_id(session["user_id"])

    def check_role(self, required_role: str) -> bool:
        """
        required_role: 'admin' или 'client'
        """
        user = self.get_current_user()
        if not user or not user.role:
            return False
        if required_role == "admin":
            return user.role_id == self.ROLE_ADMIN
        if required_role == "client":
            return user.role_id == self.ROLE_CLIENT
        return False

    def can_access_booking(self, booking) -> bool:
        """Клиент — только свои брони; админ — любые."""
        user = self.get_current_user()
        if not user:
            return False
        if user.role_id == self.ROLE_ADMIN:
            return True
        return booking.user_id == user.id


# Глобальный экземпляр для декораторов
auth_proxy = AuthProxy()


def login_required(f):
    """Декоратор: требуется вход в систему."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not auth_proxy.check_auth():
            return jsonify({"error": "Требуется авторизация"}), 401
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Декоратор: только администратор (role_id=1)."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not auth_proxy.check_auth():
            return jsonify({"error": "Требуется авторизация"}), 401
        if not auth_proxy.check_role("admin"):
            return jsonify({"error": "Доступ только для администратора"}), 403
        return f(*args, **kwargs)

    return decorated


def client_required(f):
    """Декоратор: только клиент (role_id=2)."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not auth_proxy.check_auth():
            return jsonify({"error": "Требуется авторизация"}), 401
        if not auth_proxy.check_role("client"):
            return jsonify({"error": "Доступ только для клиента"}), 403
        return f(*args, **kwargs)

    return decorated
