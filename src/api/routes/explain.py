"""
routes/explain.py
------------------
POST /explain/<disease>
    Body: { "patient": {...PatientData fields...}, "model_type": "random_forest" (optional) }

Returns SHAP values and per-feature contribution percentages for the given
patient input, plus the SHAP base value and final predicted probability.
Defaults to explaining the Random Forest model (TreeExplainer is exact and
fast); pass "model_type": "logistic_regression" or "ann" to explain those
instead.
"""
# from src.explainability.shap_explainer import explain_prediction

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from src.api.database import log_prediction
from src.api.schemas import ExplainRequest
from src.api.utils import build_model_input, load_background_sample, load_model
from src.explainability.shap_explainer import explain_prediction
from src.utils.config import CONFIDENCE_THRESHOLD, DISEASES
from src.utils.logger import get_logger

logger = get_logger(__name__)

explain_bp = Blueprint("explain", __name__)

VALID_MODEL_TYPES = {"logistic_regression", "random_forest", "ann"}
DEFAULT_MODEL_TYPE = "random_forest"


@explain_bp.route("/explain/<disease>", methods=["POST"])
def explain(disease: str):
    if disease not in DISEASES:
        return (
            jsonify(
                {"error": f"Unknown disease '{disease}'. Expected one of {DISEASES}"}
            ),
            404,
        )

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    model_type = payload.get("model_type", DEFAULT_MODEL_TYPE)
    if model_type not in VALID_MODEL_TYPES:
        return (
            jsonify(
                {
                    "error": f"Invalid model_type '{model_type}'. Expected one of {sorted(VALID_MODEL_TYPES)}"
                }
            ),
            422,
        )

    try:
        validated = ExplainRequest(patient=payload.get("patient", {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 422

    patient_dict = validated.patient.model_dump()

    try:
        model_input = build_model_input(disease, patient_dict)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422

    model = load_model(disease, model_type)
    feature_names = model_input.columns.tolist()

    background_data = None
    if model_type in ("logistic_regression", "ann"):
        background_data = load_background_sample(disease)[feature_names]

    try:
        explanation = explain_prediction(
            model=model,
            model_type=model_type,
            input_data=model_input,
            feature_names=feature_names,
            background_data=background_data,
        )
    except Exception as exc:
        logger.exception(
            f"SHAP explanation failed for disease={disease}, model={model_type}"
        )
        return jsonify({"error": f"Explanation failed: {exc}"}), 500

    label = (
        "At Risk"
        if explanation["predicted_probability"] >= CONFIDENCE_THRESHOLD
        else "Not at Risk"
    )

    # Sort feature contributions by absolute SHAP magnitude, descending,
    # for convenient front-end rendering (e.g. a sorted horizontal bar chart).
    sorted_contributions = dict(
        sorted(
            explanation["feature_contributions"].items(),
            key=lambda item: abs(item[1]["shap_value"]),
            reverse=True,
        )
    )

    log_prediction(
        disease=disease,
        request_payload=patient_dict,
        risk_probability=explanation["predicted_probability"],
        prediction_label=label,
        model_used=model_type,
        endpoint="explain",
    )

    return (
        jsonify(
            {
                "disease": disease,
                "model_type": model_type,
                "base_value": explanation["base_value"],
                "predicted_probability_pct": round(
                    explanation["predicted_probability"] * 100, 2
                ),
                "prediction": label,
                "feature_contributions": sorted_contributions,
            }
        ),
        200,
    )
