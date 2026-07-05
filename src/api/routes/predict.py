"""
routes/predict.py
------------------
POST /predict
    Body: { "patient": {...PatientData fields...}, "diseases": ["diabetes", ...] (optional) }

For each requested disease, runs all three trained models (Logistic
Regression, Random Forest, ANN) and returns each one's risk probability
(0-100%) plus a binary "At Risk"/"Not at Risk" label using a 0.5
confidence threshold. Every individual model prediction is logged to the
`prediction_logs` table.
"""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from src.api.database import log_prediction
from src.api.schemas import PredictionRequest
from src.api.utils import build_model_input, predict_with_model
from src.utils.config import CONFIDENCE_THRESHOLD, DISEASES
from src.utils.logger import get_logger

logger = get_logger(__name__)

predict_bp = Blueprint("predict", __name__)

MODEL_TYPES = ["logistic_regression", "random_forest", "ann"]


@predict_bp.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    try:
        validated = PredictionRequest(**payload)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 422

    diseases_to_run = validated.diseases or DISEASES
    patient_dict = validated.patient.model_dump()

    results = {}
    errors = {}

    for disease in diseases_to_run:
        try:
            model_input = build_model_input(disease, patient_dict)
        except ValueError as exc:
            errors[disease] = str(exc)
            continue

        disease_result = {}
        for model_type in MODEL_TYPES:
            try:
                proba = predict_with_model(disease, model_type, model_input)
            except Exception as exc:
                logger.exception(
                    f"Prediction failed for disease={disease}, model={model_type}"
                )
                disease_result[model_type] = {"error": str(exc)}
                continue

            label = "At Risk" if proba >= CONFIDENCE_THRESHOLD else "Not at Risk"
            disease_result[model_type] = {
                "risk_probability_pct": round(proba * 100, 2),
                "prediction": label,
                "confidence_threshold": CONFIDENCE_THRESHOLD,
            }

            log_prediction(
                disease=disease,
                request_payload=patient_dict,
                risk_probability=proba,
                prediction_label=label,
                model_used=model_type,
                endpoint="predict",
            )

        results[disease] = disease_result

    response = {"results": results}
    if errors:
        response["errors"] = errors

    status_code = 200 if results else 422
    return jsonify(response), status_code
