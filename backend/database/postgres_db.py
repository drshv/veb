"""
Singleton для доступа к БД через SQLAlchemy.
Все репозитории используют один экземпляр PostgresDB.
"""


class PostgresDB:
    """Паттерн Singleton — единое подключение к PostgreSQL."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = None
        return cls._instance

    def init_app(self, db):
        """Привязка к Flask-SQLAlchemy после создания приложения."""
        self._db = db

    @property
    def db(self):
        if self._db is None:
            raise RuntimeError("PostgresDB не инициализирован. Вызовите init_app(db).")
        return self._db

    @property
    def session(self):
        return self.db.session

    def execute_query(self, query, params=None):
        """Выполнение сырого SQL (при необходимости)."""
        return self.session.execute(query, params or {})

    def close(self):
        """Закрытие сессии."""
        self.session.remove()
