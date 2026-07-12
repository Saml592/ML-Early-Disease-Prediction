"""
db_helpers.py
-----------
Database helper functions for common queries used in dashboard and analytics.
"""

from src.api.database import SessionLocal, PredictionLog, User, Patient
from sqlalchemy import func, and_
from datetime import datetime, timedelta


def get_dashboard_metrics():
    """Get all dashboard metrics in one call."""
    db = SessionLocal()
    try:
        total_predictions = db.query(func.count(PredictionLog.id)).scalar() or 0
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_patients = db.query(func.count(Patient.id)).scalar() or 0

        # Disease counts
        heart_disease = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.disease == "Heart Disease")
            .scalar()
            or 0
        )

        diabetes = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.disease == "Diabetes")
            .scalar()
            or 0
        )

        hypertension = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.disease == "Hypertension")
            .scalar()
            or 0
        )

        # Average accuracy (mock for now)
        avg_accuracy = 94.2

        return {
            "totalPredictions": total_predictions,
            "totalUsers": total_users,
            "totalPatients": total_patients,
            "heartDisease": heart_disease,
            "diabetes": diabetes,
            "hypertension": hypertension,
            "avgAccuracy": avg_accuracy,
        }
    finally:
        db.close()


def get_disease_distribution():
    """Get distribution of diseases."""
    db = SessionLocal()
    try:
        diseases = (
            db.query(PredictionLog.disease, func.count(PredictionLog.id).label("count"))
            .group_by(PredictionLog.disease)
            .all()
        )

        return [
            {"name": disease, "value": count, "color": get_disease_color(disease)}
            for disease, count in diseases
        ]
    finally:
        db.close()


def get_risk_distribution():
    """Get distribution of risk levels."""
    db = SessionLocal()
    try:
        low_risk = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.risk_probability < 0.33)
            .scalar()
            or 0
        )

        medium_risk = (
            db.query(func.count(PredictionLog.id))
            .filter(
                and_(
                    PredictionLog.risk_probability >= 0.33,
                    PredictionLog.risk_probability <= 0.66,
                )
            )
            .scalar()
            or 0
        )

        high_risk = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.risk_probability > 0.66)
            .scalar()
            or 0
        )

        return [
            {"level": "Low Risk", "count": low_risk, "color": "#10b981"},
            {"level": "Medium Risk", "count": medium_risk, "color": "#f59e0b"},
            {"level": "High Risk", "count": high_risk, "color": "#ef4444"},
        ]
    finally:
        db.close()


def get_recent_predictions(limit=10, offset=0):
    """Get recent predictions."""
    db = SessionLocal()
    try:
        predictions = (
            db.query(PredictionLog)
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [
            {
                "id": f"PRED-{pred.id}",
                "disease": pred.disease,
                "risk": f"{pred.risk_probability * 100:.1f}%",
                "probability": f"{pred.risk_probability * 100:.1f}%",
                "date": pred.created_at.isoformat(),
                "status": "Completed",
                "model": pred.model_used,
            }
            for pred in predictions
        ]
    finally:
        db.close()


def get_daily_predictions(days=7):
    """Get daily prediction counts for the past N days."""
    db = SessionLocal()
    try:
        predictions = (
            db.query(
                func.date(PredictionLog.created_at).label("date"),
                func.count(PredictionLog.id).label("count"),
            )
            .filter(PredictionLog.created_at >= datetime.now() - timedelta(days=days))
            .group_by(func.date(PredictionLog.created_at))
            .order_by("date")
            .all()
        )

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [
            {"date": day_names[i % 7], "predictions": count}
            for i, (date, count) in enumerate(predictions)
        ]
    finally:
        db.close()


def get_model_performance():
    """Get performance metrics for each model."""
    db = SessionLocal()
    try:
        models = (
            db.query(
                PredictionLog.model_used, func.count(PredictionLog.id).label("total")
            )
            .group_by(PredictionLog.model_used)
            .all()
        )

        results = []
        for model_name, total in models:
            high_risk = (
                db.query(func.count(PredictionLog.id))
                .filter(
                    and_(
                        PredictionLog.model_used == model_name,
                        PredictionLog.risk_probability > 0.7,
                    )
                )
                .scalar()
                or 0
            )

            # Mock accuracy metrics
            accuracy = 92.5 + (hash(model_name or "") % 5)

            results.append(
                {
                    "model": model_name,
                    "totalPredictions": total,
                    "highRiskCases": high_risk,
                    "accuracy": round(accuracy, 2),
                    "precision": round(accuracy - 1.5, 2),
                    "recall": round(accuracy - 0.5, 2),
                    "f1Score": round(accuracy - 1.0, 2),
                }
            )

        return results
    finally:
        db.close()


def get_disease_color(disease: str) -> str:
    """Get color for a disease."""
    colors = {
        "Heart Disease": "#ef4444",
        "Diabetes": "#3b82f6",
        "Hypertension": "#f59e0b",
    }
    return colors.get(disease, "#6b7280")


def search_patients(query: str, limit=10):
    """Search patients by name or email."""
    db = SessionLocal()
    try:
        patients = (
            db.query(Patient)
            .filter(
                (Patient.name.ilike(f"%{query}%")) | (Patient.email.ilike(f"%{query}%"))
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "age": p.age,
                "gender": p.gender,
            }
            for p in patients
        ]
    finally:
        db.close()


def get_patient_predictions(patient_id: int, limit=10, offset=0):
    """Get predictions for a specific patient."""
    db = SessionLocal()
    try:
        predictions = (
            db.query(PredictionLog)
            .filter(PredictionLog.user_id == patient_id)
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [
            {
                "id": pred.id,
                "disease": pred.disease,
                "risk": pred.risk_probability,
                "label": pred.prediction_label,
                "model": pred.model_used,
                "date": pred.created_at.isoformat(),
            }
            for pred in predictions
        ]
    finally:
        db.close()


def get_analytics_summary():
    """Get comprehensive analytics summary."""
    db = SessionLocal()
    try:
        total_predictions = db.query(func.count(PredictionLog.id)).scalar() or 0
        total_users = db.query(func.count(User.id)).scalar() or 0

        # Predictions this month
        current_month_start = datetime.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        predictions_this_month = (
            db.query(func.count(PredictionLog.id))
            .filter(PredictionLog.created_at >= current_month_start)
            .scalar()
            or 0
        )

        avg_per_user = total_predictions / total_users if total_users > 0 else 0

        # Disease breakdown
        diseases = (
            db.query(PredictionLog.disease, func.count(PredictionLog.id).label("count"))
            .group_by(PredictionLog.disease)
            .all()
        )

        disease_breakdown = {d: c for d, c in diseases}

        # Model usage
        models = (
            db.query(
                PredictionLog.model_used, func.count(PredictionLog.id).label("count")
            )
            .group_by(PredictionLog.model_used)
            .all()
        )

        model_usage = {m: c for m, c in models}

        return {
            "totalPredictions": total_predictions,
            "totalUsers": total_users,
            "predictionsThisMonth": predictions_this_month,
            "avgPredictionsPerUser": round(avg_per_user, 2),
            "diseaseBreakdown": disease_breakdown,
            "modelUsage": model_usage,
        }
    finally:
        db.close()


def get_predictions_history(limit=20, offset=0, disease=None):
    """Get paginated prediction history with optional disease filter."""
    db = SessionLocal()
    try:
        query = db.query(PredictionLog)
        if disease:
            query = query.filter(PredictionLog.disease == disease)
        total = query.count()
        predictions = (
            query.order_by(PredictionLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        data = [
            {
                "id": p.id,
                "disease": p.disease,
                "risk_probability": p.risk_probability,
                "prediction_label": p.prediction_label,
                "model_used": p.model_used,
                "created_at": p.created_at.isoformat(),
                "endpoint": p.endpoint,
                "user_id": p.user_id,
            }
            for p in predictions
        ]
        return {
            "total": total,
            "data": data,
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()
# ---- Patient Management Helpers ----


def get_patients(limit=20, offset=0, search=None):
    """Get paginated list of patients with optional search."""
    db = SessionLocal()
    try:
        query = db.query(Patient)
        if search:
            query = query.filter(
                (Patient.name.ilike(f"%{search}%"))
                | (Patient.email.ilike(f"%{search}%"))
                | (Patient.phone.ilike(f"%{search}%"))
            )
        total = query.count()
        patients = (
            query.order_by(Patient.created_at.desc()).limit(limit).offset(offset).all()
        )
        return {
            "total": total,
            "data": [
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email,
                    "phone": p.phone,
                    "age": p.age,
                    "gender": p.gender,
                    "medical_history": p.medical_history,
                    "created_at": p.created_at.isoformat(),
                    "updated_at": p.updated_at.isoformat(),
                }
                for p in patients
            ],
        }
    finally:
        db.close()


def create_patient(patient_data):
    """Create a new patient."""
    db = SessionLocal()
    try:
        # Check if email already exists
        existing = (
            db.query(Patient).filter(Patient.email == patient_data.get("email")).first()
        )
        if existing:
            raise ValueError("Email already exists")
        patient = Patient(
            name=patient_data.get("name"),
            email=patient_data.get("email"),
            phone=patient_data.get("phone"),
            age=patient_data.get("age"),
            gender=patient_data.get("gender"),
            medical_history=patient_data.get("medical_history"),
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def update_patient(patient_id, update_data):
    """Update an existing patient."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")
        # Update only fields present
        for key, value in update_data.items():
            if hasattr(patient, key) and value is not None:
                setattr(patient, key, value)
        db.commit()
        db.refresh(patient)
        return patient
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def delete_patient(patient_id):
    """Delete a patient by ID."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient not found")
        db.delete(patient)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
