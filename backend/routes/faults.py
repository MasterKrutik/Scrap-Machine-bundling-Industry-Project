"""
Fault log routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

faults_bp = Blueprint("faults", __name__)


@faults_bp.route("/api/faults", methods=["GET"])
@jwt_required()
def get_faults():
    machine_id = request.args.get("machine_id")
    severity = request.args.get("severity")

    query = """
        SELECT f.*, m.name AS machine_name,
               (e.first_name || ' ' || e.last_name) AS reporter_name
        FROM fault_logs f
        JOIN machines m ON f.machine_id = m.machine_id
        JOIN employees e ON f.reported_by = e.employee_id
    """
    conditions = []
    params = []

    if machine_id:
        conditions.append("f.machine_id = %s")
        params.append(machine_id)
    if severity:
        conditions.append("f.severity = %s")
        params.append(severity)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY f.timestamp DESC"
    faults = execute_query(query, tuple(params) if params else None)
    return jsonify(faults)


@faults_bp.route("/api/faults", methods=["POST"])
@jwt_required()
def create_fault():
    data = request.get_json()
    claims = get_jwt()
    required = ["machine_id", "fault_type", "severity", "description"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if data["severity"] not in ["Low", "Medium", "High"]:
        return jsonify({"error": "Severity must be Low, Medium, or High"}), 400

    reported_by = data.get("reported_by", claims.get("employee_id"))

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fault_id = execute_query(
        """INSERT INTO fault_logs (machine_id, reported_by, timestamp, fault_type, severity, description, resolved)
           VALUES (%s, %s, %s, %s, %s, %s, 0)""",
        (data["machine_id"], reported_by, now, data["fault_type"], data["severity"], data["description"]),
        fetch=False
    )

    # Application-level trigger: auto-insert alert for High severity faults
    # (mirrors the MySQL trigger after_fault_high_severity)
    if data["severity"] == "High":
        alert_msg = f"🚨 CRITICAL ALERT: High severity fault [{data['fault_type']}] detected on Machine #{data['machine_id']} - {data['description']}"
        execute_query(
            """INSERT INTO alerts (fault_id, machine_id, timestamp, severity, message, acknowledged)
               VALUES (%s, %s, %s, %s, %s, 0)""",
            (fault_id, data["machine_id"], now, "High", alert_msg),
            fetch=False
        )

        # Send email notification via Nodemailer service
        _send_alert_email(data, now, claims)

    return jsonify({"message": "Fault reported", "fault_id": fault_id}), 201


def _send_alert_email(data, timestamp, claims):
    """Fire-and-forget email via Nodemailer microservice."""
    import threading
    import requests as http_req

    def _send():
        try:
            # Get machine details
            machines = execute_query(
                "SELECT name, location FROM machines WHERE machine_id = %s",
                (data["machine_id"],)
            )
            machine = machines[0] if machines else {}

            payload = {
                "machine_id": data["machine_id"],
                "machine_name": machine.get("name", f"Machine #{data['machine_id']}"),
                "location": machine.get("location", "Unknown"),
                "fault_type": data["fault_type"],
                "severity": data["severity"],
                "description": data["description"],
                "reported_by_name": claims.get("full_name", "System"),
                "timestamp": timestamp,
            }
            resp = http_req.post("http://localhost:5001/send-alert", json=payload, timeout=10)
            if resp.ok:
                result = resp.json()
                print(f"📧 Alert email sent: {result.get('messageId')}")
                if result.get("previewUrl"):
                    print(f"   Preview: {result['previewUrl']}")
            else:
                print(f"📧 Email service returned {resp.status_code}")
        except Exception as e:
            print(f"📧 Email service unavailable: {e}")

    # Run in background thread so API response isn't delayed
    threading.Thread(target=_send, daemon=True).start()


@faults_bp.route("/api/faults/<int:fault_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_fault(fault_id):
    execute_query(
        "UPDATE fault_logs SET resolved = 1 WHERE fault_id = %s",
        (fault_id,),
        fetch=False
    )
    return jsonify({"message": "Fault resolved"})
