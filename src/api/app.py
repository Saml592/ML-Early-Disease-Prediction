import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from src.api.database import init_db

# Import only the blueprints that exist and work
from src.api.routes.predict import predict_bp
from src.api.routes.report import report_bp
from src.api.routes.auth import auth_bp
from src.api.routes.dashboard import dashboard_bp
from src.api.routes.patients import patients_bp
from src.api.routes.analytics import analytics_bp

# DO NOT import explain_bp – it's broken/missing
# We'll skip it for now to get the app running.

from src.utils.logger import get_logger

logger = get_logger(__name__)

_HERE = os.path.dirname(__file__)
_TEMPLATE_FOLDER = os.path.join(_HERE, "templates")
_STATIC_FOLDER = os.path.join(_HERE, "static")


def create_app() -> Flask:
    app = Flask(
        __name__, template_folder=_TEMPLATE_FOLDER, static_folder=_STATIC_FOLDER
    )

    # ---------- Database ----------
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set, falling back to SQLite")
        database_url = "sqlite:///local.db"
    else:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ---------- CORS (with fallback) ----------
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "")
    if allowed_origins:
        allowed_origins = [
            origin.strip() for origin in allowed_origins.split(",") if origin.strip()
        ]
    else:
        allowed_origins = [
            "https://ml-early-disease-prediction.vercel.app",
            "http://localhost:3000",
        ]

    CORS(
        app,
        origins=allowed_origins,
        allow_headers=["Content-Type", "Authorization", "Accept"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=True,
        expose_headers=["Content-Disposition", "Content-Type"],
        max_age=3600,
    )

    # FALLBACK – ensures headers are ALWAYS set
    @app.after_request
    def after_request(response):
        origin = request.headers.get("Origin")
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, Accept"
            )
            response.headers["Access-Control-Max-Age"] = "3600"
        return response

    # ---------- Blueprints ----------
    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(analytics_bp)

    # DO NOT register explain_bp – it's missing its dependency
    # If you need it later, fix shap_explainer.py first.

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
        logger.info("Database initialised.")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
