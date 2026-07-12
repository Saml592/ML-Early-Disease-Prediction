"""
patients.py
------------
Patient management routes (CRUD) using ORM helpers.
"""

from flask import Blueprint, jsonify, request
from ..db_helpers import get_patients, create_patient, update_patient, delete_patient

patients_bp = Blueprint("patients", __name__, url_prefix="/api/patients")


@patients_bp.route("/", methods=["GET"])
def list_patients():
    try:
        limit = request.args.get("limit", 20, type=int)
        offset = request.args.get("offset", 0, type=int)
        search = request.args.get("search", None)
        result = get_patients(limit=limit, offset=offset, search=search)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@patients_bp.route("/", methods=["POST"])
def add_patient():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        required = ["name", "email"]
        for field in required:
            if not data.get(field):
                return (
                    jsonify(
                        {"success": False, "error": f"Missing required field: {field}"}
                    ),
                    400,
                )
        patient = create_patient(data)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "id": patient.id,
                        "name": patient.name,
                        "email": patient.email,
                        "phone": patient.phone,
                        "age": patient.age,
                        "gender": patient.gender,
                        "medical_history": patient.medical_history,
                    },
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 409
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@patients_bp.route("/<int:patient_id>", methods=["PUT"])
def edit_patient(patient_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400
        patient = update_patient(patient_id, data)
        return (
            jsonify(
                {
                    "success": True,
                    "data": {
                        "id": patient.id,
                        "name": patient.name,
                        "email": patient.email,
                        "phone": patient.phone,
                        "age": patient.age,
                        "gender": patient.gender,
                        "medical_history": patient.medical_history,
                    },
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@patients_bp.route("/<int:patient_id>", methods=["DELETE"])
def remove_patient(patient_id):
    try:
        delete_patient(patient_id)
        return jsonify({"success": True, "message": "Patient deleted"}), 200
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
