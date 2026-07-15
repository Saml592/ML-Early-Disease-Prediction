"""
app.py
------
Flask app factory for the Disease Prediction API.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from src.api.database import init_db
from src.api.routes.explain import explain_bp
from src.api.routes.predict import predict_bp
from src.api.routes.report import report_bp
from src.api.routes.auth import auth_bp
from src.api.routes.dashboard import dashboard_bp
from src.api.routes.patients import patients_bp
from src.api.routes.analytics import analytics_bp
from src.utils.logger import get_logger

logger = get_logger(__name__)

_HERE = os.path.dirname(__file__)
_TEMPLATE_FOLDER = os.path.join(_HERE, "templates")
_STATIC_FOLDER = os.path.join(_HERE, "static")

db = SQLAlchemy()


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=_TEMPLATE_FOLDER,
        static_folder=_STATIC_FOLDER,
    )

    # ---------- Database configuration ----------
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, falling back to SQLite")
        database_url = "sqlite:///local.db"
    else:
        # Render provides postgres:// but SQLAlchemy expects postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Create tables (if needed) – this is optional if init_db() handles it
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified via SQLAlchemy.")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    # ---------- CORS ----------
    allowed_env = os.environ.get("ALLOWED_ORIGINS", "")
    if allowed_env:
        allowed_origins = [
            origin.strip() for origin in allowed_env.split(",") if origin.strip()
        ]
    else:
        allowed_origins = [
            "https://ml-early-disease-prediction.vercel.app",
            "http://localhost:3000",
        ]
    CORS(app, origins=allowed_origins)
    logger.info(f"CORS allowed origins: {allowed_origins}")

    # ---------- Blueprints ----------
    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(explain_bp)
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(auth_bp)  # only once
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(analytics_bp)

    # ---------- Routes ----------
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(exc):
        logger.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    # Call your existing init_db() if it does additional setup
    with app.app_context():
        try:
            init_db()
            logger.info("Database initialized via init_db().")
        except Exception as e:
            logger.error(f"init_db() failed: {e}")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
