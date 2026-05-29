"""API: /api/auth — регистрация и вход."""
from flask import Blueprint, jsonify, request, session

from backend.models.user import User
from backend.patterns.auth_proxy import AuthProxy
from backend.repositories.user_repository import UserRepository

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
user_repo = UserRepository()
auth = AuthProxy()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = data.get("email")
    phone = data.get("phone")

    if not username or not password:
        return jsonify({"error": "Укажите логин и пароль"}), 400

    if user_repo.find_by_username(username):
        return jsonify({"error": "Пользователь уже существует"}), 400

    user = User(
        username=username,
        email=email,
        phone=phone,
        role_id=AuthProxy.ROLE_CLIENT,
    )
    user.register(password)
    user_repo.save(user)

    session["user_id"] = user.id
    session["role_id"] = user.role_id

    return jsonify({"message": "Регистрация успешна", "user": user.to_dict(include_role=True)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = user_repo.find_by_username(username)
    if not user or not user.login(password):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    session["user_id"] = user.id
    session["role_id"] = user.role_id

    return jsonify({"message": "Вход выполнен", "user": user.to_dict(include_role=True)})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Выход выполнен"})


@auth_bp.route("/me", methods=["GET"])
def me():
    user = auth.get_current_user()
    if not user:
        return jsonify({"error": "Не авторизован"}), 401
    return jsonify({"user": user.to_dict(include_role=True)})
