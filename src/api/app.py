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

# Suppress TensorFlow C++ backend INFO and WARNING messages (e.g. CUDA/TensorRT warnings)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask, jsonify, redirect
from flask_cors import CORS
from src.api.database import init_db

# Import only the blueprints that exist and work
from src.api.routes.predict import predict_bp
from src.api.routes.report import report_bp
from src.api.routes.auth import auth_bp
from src.api.routes.dashboard import dashboard_bp
from src.api.routes.patients import patients_bp
from src.api.routes.analytics import analytics_bp
from src.api.routes.explain import explain_bp

# DO NOT import explain_bp – it's broken/missing
# We'll skip it for now to get the app running.

from src.utils.logger import get_logger

logger = get_logger(__name__)

_HERE = os.path.dirname(__file__)
_TEMPLATE_FOLDER = os.path.join(_HERE, "templates")
_STATIC_FOLDER = os.path.join(_HERE, "static")

ALLOWED_ORIGINS = [
    "https://ml-early-disease-prediction.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_CONFIG = {
    "origins": ALLOWED_ORIGINS,
    "supports_credentials": True,
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Disposition"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=_TEMPLATE_FOLDER,
        static_folder=_STATIC_FOLDER,
    )
    CORS(app, **CORS_CONFIG)

    # Explicit OPTIONS handler — guarantees preflight passes regardless of
    # Flask-CORS version quirks with credentials + specific origins
    @app.after_request
    def apply_cors_headers(response):
        origin = "https://ml-early-disease-prediction.vercel.app"
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
        return response

    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(explain_bp)

    # DO NOT register explain_bp – it's missing its dependency
    # If you need it later, fix shap_explainer.py first.

    # ---- Root redirect — sends browser visitors to the Vercel frontend ----
    @app.route("/", methods=["GET"])
    def root():
        return redirect("https://ml-early-disease-prediction.vercel.app", code=302)

    # ---- Health check ----
    @app.route("/health", methods=["GET"])
    def health():
        from src.utils.config import MODELS_DIR
        diseases = ["diabetes", "heart", "hypertension"]
        suffixes = ["logistic_regression.joblib", "random_forest.joblib",
                    "ann.h5", "scaler.joblib", "encoders.joblib", "selected_features.joblib"]
        missing, found = [], []
        for d in diseases:
            for s in suffixes:
                fname = f"{d}_{s}"
                fpath = os.path.join(MODELS_DIR, fname)
                (found if os.path.exists(fpath) else missing).append(fname)
        status = "ok" if not missing else "degraded"
        return jsonify({
            "status": status,
            "models_dir": MODELS_DIR,
            "models_found": len(found),
            "models_missing": missing,
        }), 200 if status == "ok" else 503

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(exc):
        logger.exception("Unhandled server error")
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        init_db()
        db_url = os.environ.get("DATABASE_URL", "SQLite (local fallback)")
        jwt_set = "SET" if os.environ.get("JWT_SECRET") else "NOT SET (using default — insecure)"
        logger.info("Database initialised.")
        logger.info(f"DB backend  : {db_url[:60]}")
        logger.info(f"JWT_SECRET  : {jwt_set}")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
