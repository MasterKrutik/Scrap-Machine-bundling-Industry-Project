"""
Maintenance log routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.route("/api/maintenance", methods=["GET"])
@jwt_required()
def get_maintenance_logs():
    machine_id = request.args.get("machine_id")

    query = """
        SELECT ml.*, m.name AS machine_name,
               (e.first_name || ' ' || e.last_name) AS technician_name
        FROM maintenance_logs ml
        JOIN machines m ON ml.machine_id = m.machine_id
        JOIN employees e ON ml.performed_by = e.employee_id
    """
    params = None
    if machine_id:
        query += " WHERE ml.machine_id = %s"
        params = (machine_id,)

    query += " ORDER BY ml.date DESC"
    logs = execute_query(query, params)

    for l in logs:
        if "duration_hours" in l and l["duration_hours"] is not None:
            l["duration_hours"] = float(l["duration_hours"])

    return jsonify(logs)


@maintenance_bp.route("/api/maintenance", methods=["POST"])
@jwt_required()
def create_maintenance_log():
    data = request.get_json()
    claims = get_jwt()
    required = ["machine_id", "type", "duration_hours", "description"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    performed_by = data.get("performed_by", claims.get("employee_id"))

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    log_id = execute_query(
        """INSERT INTO maintenance_logs
           (machine_id, performed_by, date, type, duration_hours, description, parts_replaced)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (data["machine_id"], performed_by, today, data["type"],
         data["duration_hours"], data["description"],
         data.get("parts_replaced", "None")),
        fetch=False
    )
    return jsonify({"message": "Maintenance log created", "maintenance_id": log_id}), 201
