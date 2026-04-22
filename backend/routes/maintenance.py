"""
Maintenance log routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query
import uuid

maintenance_bp = Blueprint("maintenance", __name__)


@maintenance_bp.route("/api/maintenance", methods=["GET"])
@jwt_required()
def get_maintenance_logs():
    machine_id = request.args.get("machine_id")

    query = """
        SELECT 
            ml.Maintenance_ID AS maintenance_id,
            m.Machine_Name AS machine_name,
            ml.Technician_Name AS technician_name,
            ml.Maintenance_Date AS date,
            'Corrective' AS type,
            1.0 AS duration_hours,
            ml.Description AS description,
            'None' AS parts_replaced,
            ml.Cost AS cost
        FROM maintenance_logs ml
        JOIN machines m ON ml.Machine_ID = m.Machine_ID
    """
    params = None
    if machine_id:
        query += " WHERE ml.Machine_ID = %s"
        params = (machine_id,)

    query += " ORDER BY ml.Maintenance_Date DESC"
    logs = execute_query(query, params)
    return jsonify(logs)


def _send_maintenance_email(data, timestamp, claims):
    import threading
    import requests as http_req

    def _send():
        try:
            from models.database import execute_query
            machines = execute_query(
                "SELECT Machine_Name FROM machines WHERE Machine_ID = %s",
                (str(data["machine_id"]),)
            )
            machine_name = machines[0]["Machine_Name"] if machines else f"Machine #{data['machine_id']}"

            payload = {
                "to": "yoyokingguys143@gmail.com",
                "machine_id": data["machine_id"],
                "machine_name": machine_name,
                "type": data["type"],
                "duration_hours": data["duration_hours"],
                "parts_replaced": data.get("parts_replaced", "None"),
                "description": data["description"],
                "timestamp": timestamp,
            }
            http_req.post("http://localhost:5001/send-maintenance", json=payload, timeout=10)
        except Exception as e:
            print("Failed to send maintenance email:", e)

    threading.Thread(target=_send, daemon=True).start()

@maintenance_bp.route("/api/maintenance", methods=["POST"])
@jwt_required()
def create_maintenance_log():
    data = request.get_json()
    claims = get_jwt()
    required = ["machine_id", "description"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    technician_name = claims.get("full_name", "Unknown Technician")

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    log_id = data.get("maintenance_id", f"MT-{str(uuid.uuid4())[:6].upper()}")

    execute_query(
        """INSERT INTO maintenance_logs
           (Maintenance_ID, Machine_ID, Maintenance_Date, Description, Technician_Name, Cost)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (log_id, str(data["machine_id"]), today, data["description"], technician_name, 0.0),
        fetch=False
    )
    
    _send_maintenance_email(data, today, claims)
    return jsonify({"message": "Maintenance log created", "maintenance_id": log_id}), 201
