"""
dashboard.py
-----------
Dashboard routes for metrics, analytics, and statistics.
"""

from flask import Blueprint, jsonify, request
from ..db_helpers import (
    get_dashboard_metrics,
    get_disease_distribution,
    get_risk_distribution,
    get_recent_predictions,
    search_patients,
)
import random

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/metrics", methods=["GET"])
def get_metrics():
    try:
        data = get_dashboard_metrics()
        # The frontend expects these keys; get_dashboard_metrics returns them all
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/daily-predictions", methods=["GET"])
def get_daily_predictions():
    try:
        # Keep mock data to avoid empty charts when DB is empty
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        data = [{"date": day, "predictions": random.randint(35, 65)} for day in days]
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/disease-distribution", methods=["GET"])
def get_disease_distribution_route():
    try:
        data = get_disease_distribution()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/risk-distribution", methods=["GET"])
def get_risk_distribution_route():
    try:
        data = get_risk_distribution()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/monthly-accuracy", methods=["GET"])
def get_monthly_accuracy():
    try:
        # Mock data – can be replaced with real DB query later
        data = [
            {"month": "Jan", "accuracy": 92.1},
            {"month": "Feb", "accuracy": 93.2},
            {"month": "Mar", "accuracy": 91.8},
            {"month": "Apr", "accuracy": 94.5},
            {"month": "May", "accuracy": 93.9},
            {"month": "Jun", "accuracy": 94.2},
        ]
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/recent-predictions", methods=["GET"])
def get_recent_predictions_route():
    try:
        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        data = get_recent_predictions(limit, offset)
        return jsonify({"success": True, "data": data, "total": len(data)}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/search-patients", methods=["GET"])
def search_patients_route():
    try:
        query = request.args.get("q", "", type=str)
        if not query or len(query) < 2:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Search query must be at least 2 characters",
                    }
                ),
                400,
            )
        data = search_patients(query)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route("/notifications", methods=["GET"])
def get_notifications():
    try:
        # Keep mock notifications
        notifications = [
            {
                "id": 1,
                "title": "New prediction submitted",
                "message": "A new disease prediction has been submitted",
                "time": "5 minutes ago",
                "type": "info",
            },
            {
                "id": 2,
                "title": "Patient record updated",
                "message": "Patient record has been updated successfully",
                "time": "1 hour ago",
                "type": "success",
            },
            {
                "id": 3,
                "title": "Report generated",
                "message": "Prediction report has been generated",
                "time": "2 hours ago",
                "type": "success",
            },
        ]
        return jsonify({"success": True, "data": notifications}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
