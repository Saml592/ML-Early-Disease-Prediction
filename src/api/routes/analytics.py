"""
analytics.py
-----------
Analytics routes for system statistics and reports.
"""

from flask import Blueprint, jsonify, request
from ..db_helpers import (
    get_analytics_summary,
    get_model_performance,
    get_risk_distribution,
    get_daily_predictions,
)

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/summary", methods=["GET"])
def get_summary():
    try:
        data = get_analytics_summary()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/predictions-by-date", methods=["GET"])
def get_predictions_by_date():
    try:
        days = request.args.get("days", 30, type=int)
        data = get_daily_predictions(days)
        # Format as expected by frontend (date + count)
        formatted = [
            {"date": item["date"], "count": item["predictions"]} for item in data
        ]
        return jsonify({"success": True, "data": formatted}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/model-performance", methods=["GET"])
def get_model_performance_route():
    try:
        data = get_model_performance()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/risk-distribution", methods=["GET"])
def get_risk_distribution_route():
    try:
        data = get_risk_distribution()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/age-group-analysis", methods=["GET"])
def get_age_group_analysis():
    try:
        # Keep mock data – you can later replace with real DB query
        age_groups = [
            {"group": "18-30", "predictions": 245, "avgRisk": 0.35},
            {"group": "31-45", "predictions": 387, "avgRisk": 0.52},
            {"group": "46-60", "predictions": 512, "avgRisk": 0.68},
            {"group": "60+", "predictions": 298, "avgRisk": 0.75},
        ]
        return jsonify({"success": True, "data": age_groups}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@analytics_bp.route("/export", methods=["GET"])
def export_analytics():
    try:
        export_format = request.args.get("format", "csv", type=str)
        # Mock export data (you can replace with real data from DB)
        predictions = [
            {
                "id": 1,
                "disease": "Heart Disease",
                "risk_probability": 0.753,
                "prediction_label": "At Risk",
                "model_used": "Random Forest",
                "created_at": "2024-07-10T13:00:00",
            }
        ]
        if export_format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(
                output, fieldnames=predictions[0].keys() if predictions else []
            )
            writer.writeheader()
            writer.writerows(predictions)
            return (
                output.getvalue(),
                200,
                {
                    "Content-Type": "text/csv",
                    "Content-Disposition": "attachment; filename=analytics.csv",
                },
            )
        else:
            return jsonify({"success": True, "data": predictions}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
