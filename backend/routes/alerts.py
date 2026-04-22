"""
Alert routes - In-app notification messages.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("/api/alerts", methods=["GET"])
@jwt_required()
def get_alerts():
    acknowledged = request.args.get("acknowledged")

    query = """
        SELECT 
            a.Alert_ID AS alert_id,
            m.Machine_Name AS machine_name,
            m.Location AS location,
            'High' AS severity,
            a.Alert_Type AS message,
            a.Alert_Time AS timestamp,
            CASE WHEN a.Status = 'Resolved' THEN 1 ELSE 0 END AS acknowledged
        FROM alerts a
        JOIN machines m ON a.Machine_ID = m.Machine_ID
    """
    params = None
    if acknowledged is not None:
        if int(acknowledged) == 1:
            query += " WHERE a.Status = 'Resolved'"
        else:
            query += " WHERE a.Status != 'Resolved'"

    query += " ORDER BY a.Alert_Time DESC"
    alerts = execute_query(query, params)
    return jsonify(alerts)


@alerts_bp.route("/api/alerts/active", methods=["GET"])
@jwt_required()
def get_active_alerts():
    """Get unacknowledged alerts (in-app notifications)."""
    alerts = execute_query("""
        SELECT 
            a.Alert_ID AS alert_id,
            m.Machine_Name AS machine_name,
            m.Location AS location,
            'High' AS severity,
            a.Alert_Type AS message,
            a.Alert_Time AS timestamp,
            0 AS acknowledged
        FROM alerts a
        JOIN machines m ON a.Machine_ID = m.Machine_ID
        WHERE a.Status != 'Resolved'
        ORDER BY a.Alert_Time DESC
    """)
    return jsonify(alerts)


@alerts_bp.route("/api/alerts/<alert_id>/acknowledge", methods=["PUT"])
@jwt_required()
def acknowledge_alert(alert_id):
    execute_query(
        "UPDATE alerts SET Status = 'Resolved' WHERE Alert_ID = %s",
        (alert_id,),
        fetch=False
    )
    return jsonify({"message": "Alert acknowledged"})


@alerts_bp.route("/api/alerts/acknowledge-all", methods=["PUT"])
@jwt_required()
def acknowledge_all_alerts():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    execute_query("UPDATE alerts SET Status = 'Resolved' WHERE Status != 'Resolved'", fetch=False)
    return jsonify({"message": "All alerts acknowledged"})


@alerts_bp.route("/api/alerts/count", methods=["GET"])
@jwt_required()
def get_alert_count():
    result = execute_query("SELECT COUNT(*) AS count FROM alerts WHERE Status != 'Resolved'")
    return jsonify({"count": result[0]["count"]})

