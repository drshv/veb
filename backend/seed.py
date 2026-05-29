"""Начальные данные: роли, статусы, админ, столики."""
from backend.extensions import db
from backend.models.role import Role
from backend.models.status import Status
from backend.models.table import Table
from backend.models.user import User
from backend.patterns.auth_proxy import AuthProxy


def seed_database():
    if Role.query.count() == 0:
        db.session.add_all(
            [
                Role(id=1, name="admin", description="Администратор"),
                Role(id=2, name="client", description="Клиент"),
            ]
        )

    if Status.query.count() == 0:
        db.session.add_all(
            [
                Status(id=1, name="pending", description="Ожидает подтверждения"),
                Status(id=2, name="confirmed", description="Подтверждена"),
                Status(id=3, name="cancelled", description="Отменена"),
                Status(id=4, name="rejected", description="Отклонена"),
            ]
        )

    if User.query.filter_by(username="admin").first() is None:
        admin = User(
            username="admin",
            email="admin@restaurant.local",
            phone="+70000000000",
            role_id=AuthProxy.ROLE_ADMIN,
        )
        admin.register("admin123")
        db.session.add(admin)

    if Table.query.count() == 0:
        tables = [
            Table(number=1, seats=2, description="У окна"),
            Table(number=2, seats=2, description="У окна"),
            Table(number=3, seats=4, description="В центре зала"),
            Table(number=4, seats=4, description="В центре зала"),
            Table(number=5, seats=6, description="Большой стол"),
            Table(number=6, seats=8, description="VIP зона"),
        ]
        db.session.add_all(tables)

    db.session.commit()
