"""Конфигурация приложения."""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "restaurant-booking-dev-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:0000@localhost:5432/restaurant_booking",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
