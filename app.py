"""
Точка входа: Flask + PostgreSQL.
Запуск: python app.py
"""
import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from backend.database.postgres_db import PostgresDB
from backend.extensions import db
from backend.routes.admin_routes import admin_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.bookings_routes import bookings_bp
from backend.routes.tables_routes import tables_bp
from backend.seed import seed_database
from config import Config


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)

    db.init_app(app)
    PostgresDB().init_app(db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tables_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.route("/admin")
    def admin_page():
        return send_from_directory("static", "admin.html")

    with app.app_context():
        db.create_all()
        seed_database()

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
