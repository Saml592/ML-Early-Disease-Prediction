"""
database.py
------------
SQLAlchemy engine/session setup for PostgreSQL, plus ORM models for
PredictionLog, ReportLog, and User authentication.

Connection is configured via the DATABASE_URL environment variable, e.g.:
    postgresql+psycopg2://user:password@localhost:5432/disease_prediction

If DATABASE_URL is not set, a local SQLite file is used instead so the API
remains runnable without a PostgreSQL instance (useful for local dev/tests);
in production, set DATABASE_URL to a real PostgreSQL DSN.
"""

import datetime
import os

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from src.utils.logger import get_logger

logger = get_logger(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///"
    + os.path.join(os.path.dirname(__file__), "..", "..", "prediction_logs.db"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    def set_password(self, password: str):
        """Hash and set the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Patient(Base):
    """Patient model for patient management."""

    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(16), nullable=True)
    medical_history = Column(String(500), nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )


class PredictionLog(Base):
    """One row per /predict (or /explain) API call."""

    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, nullable=True, index=True
    )  # Optional: link to user if authenticated
    timestamp = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    disease = Column(String(32), nullable=False, index=True)
    request_payload = Column(JSON, nullable=False)
    risk_probability = Column(Float, nullable=False)
    prediction_label = Column(String(16), nullable=False)  # "At Risk" / "Not at Risk"
    model_used = Column(String(32), nullable=True)
    endpoint = Column(
        String(32), nullable=False, default="predict"
    )  # "predict" | "explain"
    shaply_values = Column(JSON, nullable=True)  # SHAP explanation values


def init_db():
    \"\"\"Create all tables if they don't already exist.\"\"\"
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized at {DATABASE_URL}")

    db = SessionLocal()
    try:
        if not db.query(User).first():
            logger.info("Seeding default admin user (benny).")
            default_user = User(username="benny", email="benny@example.com")
            default_user.set_password("admin123")
            db.add(default_user)
            db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to seed default user: {exc}")
    finally:
        db.close()


def get_db_session():
    """Yield a SQLAlchemy session; caller is responsible for closing it
    (Flask routes use this via a `with` pattern, see routes/predict.py)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_prediction(
    disease: str,
    request_payload: dict,
    risk_probability: float,
    prediction_label: str,
    model_used: str = None,
    endpoint: str = "predict",
    user_id: int = None,
):
    """Convenience helper: open a session, insert a PredictionLog row, commit, close."""
    db = SessionLocal()
    try:
        entry = PredictionLog(
            user_id=user_id,
            disease=disease,
            request_payload=request_payload,
            risk_probability=risk_probability,
            prediction_label=prediction_label,
            model_used=model_used,
            endpoint=endpoint,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to log prediction to database: {exc}")
    finally:
        db.close()


class ReportLog(Base):
    """One row per /report API call — tracks generation status and metadata."""

    __tablename__ = "report_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    report_ref = Column(String(32), nullable=False, index=True)
    patient_age = Column(Integer, nullable=True)
    diseases_included = Column(String(128), nullable=True)
    model_type_for_shap = Column(String(32), nullable=True)
    status = Column(String(16), nullable=False, default="success")
    error_message = Column(String(512), nullable=True)
    format_returned = Column(String(8), nullable=False, default="pdf")


def log_report(
    report_ref: str,
    patient_age: int,
    diseases_included: list,
    model_type_for_shap: str,
    status: str = "success",
    error_message: str = None,
    format_returned: str = "pdf",
):
    """Insert a ReportLog row — called from routes/report.py."""
    db = SessionLocal()
    try:
        entry = ReportLog(
            report_ref=report_ref,
            patient_age=patient_age,
            diseases_included=",".join(diseases_included),
            model_type_for_shap=model_type_for_shap,
            status=status,
            error_message=error_message,
            format_returned=format_returned,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to log report to database: {exc}")
    finally:
        db.close()


def get_db():
    """
    Return a new database session.

    This is used by routes that were written with a simple `db = get_db()` pattern.
    Note: The session must be closed manually (or use `with` context).
    """
    return SessionLocal()
