"""
app.py
------
Flask app factory for the Disease Prediction API. Enables CORS for the
React frontend, registers the /predict, /explain, /report, and /auth blueprints,
and initialises the database tables on startup.

Run locally with:
    python -m src.api.app
or via gunicorn / flask CLI in production.
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS

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

# Absolute paths so Flask finds templates/static regardless of CWD
_HERE = os.path.dirname(__file__)
_TEMPLATE_FOLDER = os.path.join(_HERE, "templates")
_STATIC_FOLDER = os.path.join(_HERE, "static")


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=_TEMPLATE_FOLDER,
        static_folder=_STATIC_FOLDER,
    )

    # -------- CORS configuration (environment-aware) --------
    # Read allowed origins from environment variable, e.g.:
    #   ALLOWED_ORIGINS=https://ml-early-disease-prediction.vercel.app,https://my-preview.vercel.app
    # If not set, fallback to production + local development.
    allowed_env = os.environ.get("ALLOWED_ORIGINS", "")
    if allowed_env:
        allowed_origins = [
            origin.strip() for origin in allowed_env.split(",") if origin.strip()
        ]
    else:
        # Default: production frontend + local React dev server
        allowed_origins = [
            "https://ml-early-disease-prediction.vercel.app",
            "http://localhost:3000",
        ]

    CORS(app, origins=allowed_origins)
    logger.info(f"CORS allowed origins: {allowed_origins}")

    # -------- Register blueprints --------
    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(explain_bp)
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(analytics_bp)

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

    with app.app_context():
        init_db()

    logger.info("Flask app created and database initialised.")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
