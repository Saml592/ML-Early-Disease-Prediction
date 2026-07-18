"""
routes/report.py
-----------------
POST /report
    Accepts patient data and optionally pre-computed prediction results.
    For each disease it:
      1. (Re-)computes predictions via the three trained models.
      2. Generates a SHAP horizontal bar chart with matplotlib, encodes it
         as base64 PNG, and embeds it directly in the HTML template.
      3. Renders report_template.html via Jinja2 (Flask render_template).
      4. Converts the HTML to a PDF with WeasyPrint and streams it back as
         an attachment so the browser triggers a download.
      5. Logs the request to the `report_logs` database table.

WeasyPrint requires the GTK3 runtime on Windows. If it is not available the
route falls back gracefully to returning the rendered HTML so the user can
still print-to-PDF via the browser (Ctrl+P). See README for GTK3 install
instructions for Windows.
"""

import base64
import io
import os
from datetime import datetime
from typing import Optional

import matplotlib

matplotlib.use("Agg")  # must be set before any pyplot import
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from flask import Blueprint, jsonify, render_template, make_response, request
from pydantic import BaseModel, ValidationError

# WeasyPrint: graceful fallback if not installed / GTK3 missing on Windows
try:
    from weasyprint import CSS, HTML as WeasyHTML  # type: ignore

    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

from src.api.database import log_report
from src.api.schemas import PatientData
from src.api.utils import (
    build_model_input,
    load_background_sample,
    load_model,
    load_selected_features,
    predict_with_model,
)
from src.api.shap_explainer import explain_prediction
from src.utils.config import CONFIDENCE_THRESHOLD, DISEASES
from src.utils.logger import get_logger
from sqlalchemy import desc  # <-- add this
from ..database import get_db, ReportLog

logger = get_logger(__name__)
report_bp = Blueprint("report", __name__)

# ── Constants ────────────────────────────────────────────────────────────────

DISEASE_LABELS = {
    "diabetes": "Diabetes",
    "heart": "Cardiovascular Disease",
    "hypertension": "Hypertension",
}
MODEL_LABELS = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "ann": "Neural Network (ANN)",
}
SHAP_MODEL_TYPES = {"logistic_regression", "random_forest", "ann"}
_CSS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static", "css", "report_style.css"
)


# ── Pydantic request schema ───────────────────────────────────────────────────


class ReportRequest(BaseModel):
    patient: PatientData
    predictions: Optional[dict] = None  # pre-computed /predict response body
    model_type: str = "random_forest"  # which model to use for SHAP charts
    diseases: Optional[list] = None  # subset of diseases; None → all three


# ── SHAP chart generation ─────────────────────────────────────────────────────


def _shap_bar_chart_b64(
    disease: str,
    model_type: str,
    model_input: pd.DataFrame,
    feature_names: list,
    background_data: pd.DataFrame | None,
) -> tuple[str | None, dict | None]:
    """
    Run SHAP explanation for one disease/model, render a clean horizontal
    bar chart with matplotlib, and return (base64_png_string, explanation_dict).
    Returns (None, None) on any failure so the report can still be generated
    without SHAP when a model file is missing or SHAP computation fails.
    """
    try:
        model = load_model(disease, model_type)
        explanation = explain_prediction(
            model=model,
            model_type=model_type,
            input_data=model_input,
            feature_names=feature_names,
            background_data=background_data,
        )

        contributions = explanation["feature_contributions"]
        # Sort ascending by absolute value so the most important bar is at top
        sorted_items = sorted(
            contributions.items(), key=lambda kv: abs(kv[1]["shap_value"])
        )
        features = [k for k, _ in sorted_items]
        shap_vals = [v["shap_value"] for _, v in sorted_items]
        pct_vals = [v["contribution_pct"] for _, v in sorted_items]
        colors = ["#c62828" if v >= 0 else "#2e7d32" for v in shap_vals]

        fig_h = max(3.0, len(features) * 0.48)
        fig, ax = plt.subplots(figsize=(8.5, fig_h))
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#fafafa")

        bars = ax.barh(
            features,
            shap_vals,
            color=colors,
            edgecolor="white",
            height=0.6,
            linewidth=0.4,
        )

        # Value annotations
        x_range = max(abs(v) for v in shap_vals) or 1.0
        for bar, sv, pct in zip(bars, shap_vals, pct_vals):
            offset = x_range * 0.02
            ha = "left" if sv >= 0 else "right"
            ax.text(
                sv + (offset if sv >= 0 else -offset),
                bar.get_y() + bar.get_height() / 2,
                f"{sv:+.3f}  ({pct:.1f}%)",
                va="center",
                ha=ha,
                fontsize=7.5,
                color="#333333",
            )

        ax.axvline(x=0, color="#555555", linewidth=0.8)
        ax.set_xlabel(
            "SHAP value  (impact on model log-odds / probability)", fontsize=8
        )
        ax.set_title(
            f"{DISEASE_LABELS.get(disease, disease)} — Feature Impact  "
            f"[{MODEL_LABELS.get(model_type, model_type)}]",
            fontsize=9,
            fontweight="bold",
            pad=8,
        )
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="y", labelsize=8)
        ax.tick_params(axis="x", labelsize=7.5)

        red_patch = mpatches.Patch(color="#c62828", label="Increases risk")
        green_patch = mpatches.Patch(color="#2e7d32", label="Decreases risk")
        ax.legend(
            handles=[red_patch, green_patch],
            fontsize=7.5,
            loc="lower right",
            framealpha=0.8,
        )

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return b64, explanation

    except Exception as exc:
        logger.warning(
            f"SHAP chart failed for disease={disease}, model={model_type}: {exc}"
        )
        return None, None


# ── Prediction helpers ────────────────────────────────────────────────────────


def _run_predictions(disease: str, patient_dict: dict) -> dict:
    """Compute predictions for all three model types for one disease."""
    model_input = build_model_input(disease, patient_dict)
    results = {}
    for mt in ("logistic_regression", "random_forest", "ann"):
        try:
            proba = predict_with_model(disease, mt, model_input)
            label = "At Risk" if proba >= CONFIDENCE_THRESHOLD else "Not at Risk"
            results[mt] = {
                "risk_probability_pct": round(proba * 100, 2),
                "prediction": label,
            }
        except Exception as exc:
            logger.warning(f"Prediction failed disease={disease} model={mt}: {exc}")
            results[mt] = {"error": str(exc)}
    return results


def _consensus(model_results: dict) -> str:
    """Majority-vote consensus across the three models."""
    labels = [r["prediction"] for r in model_results.values() if "prediction" in r]
    return "At Risk" if labels.count("At Risk") > len(labels) / 2 else "Not at Risk"


def _max_risk(model_results: dict) -> float:
    probs = [
        r["risk_probability_pct"]
        for r in model_results.values()
        if "risk_probability_pct" in r
    ]
    return max(probs) if probs else 0.0


# ── Report reference ID ───────────────────────────────────────────────────────

_report_counter = 0


def _new_ref() -> str:
    global _report_counter
    _report_counter += 1
    return f"RPT-{datetime.now().strftime('%Y%m%d')}-{_report_counter:04d}"


# ── Route ─────────────────────────────────────────────────────────────────────


@report_bp.route("/report", methods=["POST"])
def generate_report():
    """
    POST /report

    Request body (JSON):
        {
          "patient": { ...PatientData fields... },
          "predictions": { ...optional pre-computed /predict results... },
          "model_type": "random_forest",   // SHAP model — default random_forest
          "diseases": ["diabetes", ...]    // optional subset
        }

    Returns:
        200  application/pdf   — downloadable PDF report
        200  text/html         — fallback when WeasyPrint is unavailable
        422  application/json  — validation errors
        500  application/json  — unexpected server errors
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    try:
        validated = ReportRequest(**payload)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "details": exc.errors()}), 422

    patient_dict = validated.patient.model_dump()
    model_type = (
        validated.model_type
        if validated.model_type in SHAP_MODEL_TYPES
        else "random_forest"
    )
    diseases = validated.diseases or DISEASES
    pre_computed = validated.predictions or {}

    report_ref = _new_ref()
    report_date = datetime.now().strftime("%Y-%m-%d  %H:%M")
    status = "success"
    error_msg = None
    fmt = "pdf" if WEASYPRINT_AVAILABLE else "html"

    # ── Build per-disease context ─────────────────────────────────────────────
    disease_results = {}
    for disease in diseases:
        try:
            model_results = pre_computed.get(disease) or _run_predictions(
                disease, patient_dict
            )

            selected_features = load_selected_features(disease)
            try:
                model_input = build_model_input(disease, patient_dict)
                mi_subset = model_input[selected_features]
            except Exception:
                mi_subset = None

            shap_b64 = None
            if mi_subset is not None:
                background_data = None
                if model_type in ("logistic_regression", "ann"):
                    bg = load_background_sample(disease)
                    background_data = bg[selected_features]

                shap_b64, _ = _shap_bar_chart_b64(
                    disease, model_type, mi_subset, selected_features, background_data
                )

            disease_results[disease] = {
                "label": DISEASE_LABELS.get(disease, disease),
                "consensus": _consensus(model_results),
                "max_risk_pct": _max_risk(model_results),
                "model_results": model_results,
                "shap_chart_b64": shap_b64,
            }

        except Exception as exc:
            logger.exception(f"Failed to build report section for disease={disease}")
            disease_results[disease] = {
                "label": DISEASE_LABELS.get(disease, disease),
                "consensus": "Unknown",
                "max_risk_pct": 0.0,
                "model_results": {},
                "shap_chart_b64": None,
                "error": str(exc),
            }

    # ── Render Jinja2 template ────────────────────────────────────────────────
    try:
        html_content = render_template(
            "report_template.html",
            report_ref=report_ref,
            report_date=report_date,
            patient=patient_dict,
            disease_results=disease_results,
            model_labels=MODEL_LABELS,
            weasyprint_ok=WEASYPRINT_AVAILABLE,
        )
    except Exception as exc:
        logger.exception("Template rendering failed")
        log_report(
            report_ref,
            patient_dict.get("age"),
            diseases,
            model_type,
            status="error",
            error_message=str(exc),
            format_returned="none",
        )
        return jsonify({"error": f"Template rendering failed: {exc}"}), 500

    # ── Convert to PDF (or fall back to HTML) ─────────────────────────────────
    if WEASYPRINT_AVAILABLE:
        try:
            css_string = ""
            if os.path.exists(_CSS_PATH):
                with open(_CSS_PATH, "r", encoding="utf-8") as f:
                    css_string = f.read()

            pdf_bytes = WeasyHTML(string=html_content).write_pdf(
                stylesheets=[CSS(string=css_string)] if css_string else []
            )

            response = make_response(pdf_bytes)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = (
                f'attachment; filename="disease_risk_report_{report_ref}.pdf"'
            )
            log_report(
                report_ref,
                patient_dict.get("age"),
                diseases,
                model_type,
                status="success",
                format_returned="pdf",
            )
            return response, 200

        except Exception as exc:
            logger.exception(
                "WeasyPrint PDF conversion failed — returning HTML fallback"
            )
            status = "error"
            error_msg = str(exc)
            fmt = "html"

    # HTML fallback
    response = make_response(html_content)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="disease_risk_report_{report_ref}.html"'
    )
    log_report(
        report_ref,
        patient_dict.get("age"),
        diseases,
        model_type,
        status=status,
        error_message=error_msg,
        format_returned=fmt,
    )
    return response, 200


@report_bp.route("/", methods=["GET"])
def list_reports():
    """
    GET /api/reports
    List all report logs with metadata.
    Query params: limit (default 50), offset (default 0)
    Returns JSON array of report entries.
    """
    try:
        db = get_db()
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)

        reports = (
            db.query(ReportLog)
            .order_by(desc(ReportLog.timestamp))
            .limit(limit)
            .offset(offset)
            .all()
        )

        result = []
        for r in reports:
            result.append(
                {
                    "id": r.id,
                    "report_ref": r.report_ref,
                    "timestamp": r.timestamp.isoformat(),
                    "patient_age": r.patient_age,
                    "diseases_included": r.diseases_included,
                    "model_type": r.model_type_for_shap,
                    "status": r.status,
                    "format": r.format_returned,
                    "error_message": r.error_message,
                }
            )

        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
