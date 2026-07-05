"""
test_api.py
------------
pytest-flask tests for the /health, /predict, and /explain endpoints.
Assumes trained models exist (see test_models.py note).
"""
import os

import pytest

from src.api.app import create_app
from src.utils.config import MODELS_DIR

pytestmark = pytest.mark.skipif(
    not os.path.exists(os.path.join(MODELS_DIR, "diabetes_random_forest.joblib")),
    reason="Trained models not found; run `python -m src.models.compare_models` first.",
)

FULL_PATIENT = {
    "age": 45, "bmi": 28.4, "glucose": 130, "blood_pressure": 80,
    "cholesterol": 210, "family_history": 1, "smoking_status": "Former",
    "pregnancies": 2, "skin_thickness": 25, "insulin": 85,
    "diabetes_pedigree_function": 0.45,
    "sex": 1, "cp": 2, "fbs": 0, "restecg": 1, "thalach": 150, "exang": 0,
    "oldpeak": 1.2, "slope": 1, "ca": 0, "thal": 2,
    "sodium_intake": 3200, "alcohol_units_week": 4,
    "physical_activity_min_week": 90, "stress_score": 6, "resting_heart_rate": 76,
}


@pytest.fixture()
def app():
    flask_app = create_app()
    flask_app.config.update({"TESTING": True})
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_predict_all_diseases(client):
    resp = client.post("/predict", json={"patient": FULL_PATIENT})
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body["results"].keys()) == {"diabetes", "heart", "hypertension"}
    for disease_result in body["results"].values():
        for model_result in disease_result.values():
            assert "risk_probability_pct" in model_result
            assert 0 <= model_result["risk_probability_pct"] <= 100
            assert model_result["prediction"] in ("At Risk", "Not at Risk")


def test_predict_single_disease(client):
    resp = client.post("/predict", json={"patient": FULL_PATIENT, "diseases": ["diabetes"]})
    assert resp.status_code == 200
    body = resp.get_json()
    assert list(body["results"].keys()) == ["diabetes"]


def test_predict_missing_required_fields_returns_error(client):
    resp = client.post("/predict", json={"patient": {"age": 30}, "diseases": ["diabetes"]})
    body = resp.get_json()
    assert "diabetes" in body.get("errors", {})


def test_predict_invalid_payload_returns_422(client):
    resp = client.post("/predict", json={"patient": {"age": "not-a-number"}})
    assert resp.status_code == 422


def test_explain_random_forest(client):
    resp = client.post("/explain/diabetes", json={"patient": FULL_PATIENT})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["disease"] == "diabetes"
    assert body["model_type"] == "random_forest"
    assert "feature_contributions" in body
    assert 0 <= body["predicted_probability_pct"] <= 100


def test_explain_unknown_disease_returns_404(client):
    resp = client.post("/explain/unknown_disease", json={"patient": FULL_PATIENT})
    assert resp.status_code == 404


# ── /report endpoint tests ────────────────────────────────────────────────────

def test_report_returns_pdf_or_html(client):
    """POST /report should return a valid PDF (or HTML fallback) with 200."""
    resp = client.post("/report", json={
        "patient": FULL_PATIENT,
        "diseases": ["diabetes"],
        "model_type": "random_forest",
    })
    assert resp.status_code == 200
    ct = resp.content_type
    assert "pdf" in ct or "html" in ct, f"Unexpected content-type: {ct}"
    assert len(resp.data) > 1000, "Response too small to be a real report"

    if "pdf" in ct:
        assert resp.data[:4] == b"%PDF", "PDF magic bytes missing"
    else:
        assert b"<!DOCTYPE" in resp.data[:100] or b"<html" in resp.data[:100]


def test_report_content_disposition_header(client):
    """Content-Disposition should include a filename starting with 'disease_risk_report'."""
    resp = client.post("/report", json={
        "patient": FULL_PATIENT,
        "diseases": ["diabetes"],
    })
    assert resp.status_code == 200
    disp = resp.headers.get("Content-Disposition", "")
    assert "disease_risk_report" in disp


def test_report_all_diseases(client):
    """Omitting 'diseases' should include all three in the report."""
    resp = client.post("/report", json={"patient": FULL_PATIENT})
    assert resp.status_code == 200
    assert len(resp.data) > 5000


def test_report_invalid_patient_returns_422(client):
    """A missing required field (age) should return 422."""
    resp = client.post("/report", json={"patient": {"bmi": 25.0}})
    assert resp.status_code == 422


def test_report_logs_to_database(client):
    """Every successful /report call should add a row to report_logs."""
    import sqlite3, os
    db_path = os.path.join(
        os.path.dirname(__file__), "..", "prediction_logs.db"
    )
    conn = sqlite3.connect(db_path)
    before = conn.execute("SELECT COUNT(*) FROM report_logs").fetchone()[0]

    client.post("/report", json={"patient": FULL_PATIENT, "diseases": ["heart"]})

    after = conn.execute("SELECT COUNT(*) FROM report_logs").fetchone()[0]
    conn.close()
    assert after == before + 1
