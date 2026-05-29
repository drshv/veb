"""Repository для пользователей."""
from backend.database.postgres_db import PostgresDB
from backend.models.user import User


class UserRepository:
    def __init__(self):
        self._db = PostgresDB()

    def find_by_id(self, user_id: int):
        return User.query.get(user_id)

    def find_by_username(self, username: str):
        return User.query.filter_by(username=username).first()

    def save(self, user: User):
        self._db.session.add(user)
        self._db.session.commit()
        return user
