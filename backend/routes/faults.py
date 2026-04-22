"""
Fault logs routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

faults_bp = Blueprint("faults", __name__)


@faults_bp.route("/api/faults", methods=["GET"])
@jwt_required()
def get_faults():
    machine_id = request.args.get("machine_id")

    query = """
        SELECT 
            a.Alert_ID AS fault_id,
            m.Machine_Name AS machine_name,
            'System' AS reporter_name,
            a.Alert_Time AS timestamp,
            a.Alert_Type AS fault_type,
            'High' AS severity,
            a.Alert_Type AS description,
            CASE WHEN a.Status = 'Resolved' THEN 1 ELSE 0 END AS resolved
        FROM alerts a
        JOIN machines m ON a.Machine_ID = m.Machine_ID
    """
    params = None
    if machine_id:
        query += " WHERE a.Machine_ID = %s"
        params = (machine_id,)

    query += " ORDER BY a.Alert_Time DESC"
    faults = execute_query(query, params)
    return jsonify(faults)
def _send_alert_email(data, timestamp, claims):
    """Fire-and-forget email via Nodemailer microservice."""
    import threading
    import requests as http_req

    def _send():
        try:
            from models.database import execute_query
            machines = execute_query(
                "SELECT Machine_Name, Location FROM machines WHERE Machine_ID = %s",
                (str(data["machine_id"]),)
            )
            machine = machines[0] if machines else {}

            payload = {
                "to": "yoyokingguys1143@gmail.com",
                "machine_id": data["machine_id"],
                "machine_name": machine.get("Machine_Name", f"Machine #{data['machine_id']}"),
                "location": machine.get("Location", "Unknown"),
                "fault_type": data.get("fault_type", "Maintenance Logged"),
                "severity": data.get("severity", "High"),
                "description": data["description"],
                "reported_by_name": claims.get("full_name", "System"),
                "timestamp": timestamp,
            }
            http_req.post("http://localhost:5001/send-alert", json=payload, timeout=10)
        except Exception as e:
            print("Failed to send alert email:", e)

    threading.Thread(target=_send, daemon=True).start()

@faults_bp.route("/api/faults", methods=["POST"])
@jwt_required()
def report_fault():
    data = request.get_json()
    claims = get_jwt()
    required = ["machine_id", "fault_type", "description"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    from datetime import datetime
    import uuid
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_id = f"AL-{str(uuid.uuid4())[:6].upper()}"

    execute_query(
        """INSERT INTO alerts (Alert_ID, Machine_ID, Sensor_ID, Alert_Type, Alert_Time, Status)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (alert_id, str(data["machine_id"]), None, f"{data['fault_type']} - {data['description']}", now, "Open"),
        fetch=False
    )
    
    _send_alert_email(data, now, claims)
    return jsonify({"message": "Fault reported", "fault_id": alert_id}), 201
@faults_bp.route("/api/faults/<fault_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_fault(fault_id):
    execute_query(
        "UPDATE alerts SET Status = 'Resolved' WHERE Alert_ID = %s",
        (fault_id,),
        fetch=False
    )
    return jsonify({"message": "Fault resolved", "fault_id": fault_id}), 201

