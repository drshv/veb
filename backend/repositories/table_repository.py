"""Repository для столиков."""
from datetime import datetime

from backend.database.postgres_db import PostgresDB
from backend.models.table import Table


class TableRepository:
    def __init__(self):
        self._db = PostgresDB()

    def find_all(self, active_only=True):
        q = Table.query
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(Table.number).all()

    def find_by_id(self, table_id: int):
        return Table.query.get(table_id)

    def find_available(self, booking_datetime: datetime, min_seats: int = 1):
        """Свободные столики на указанное время с достаточной вместимостью."""
        tables = self.find_all(active_only=True)
        return [
            t
            for t in tables
            if t.seats >= min_seats and t.get_availability(booking_datetime)
        ]

    def save(self, table: Table):
        self._db.session.add(table)
        self._db.session.commit()
        return table

    def delete(self, table: Table):
        self._db.session.delete(table)
        self._db.session.commit()
