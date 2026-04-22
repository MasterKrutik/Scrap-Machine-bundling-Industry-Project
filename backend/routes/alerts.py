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
        SELECT a.*, m.name AS machine_name, m.location
        FROM alerts a
        JOIN machines m ON a.machine_id = m.machine_id
    """
    params = None
    if acknowledged is not None:
        query += " WHERE a.acknowledged = %s"
        params = (int(acknowledged),)

    query += " ORDER BY a.timestamp DESC"
    alerts = execute_query(query, params)
    return jsonify(alerts)


@alerts_bp.route("/api/alerts/active", methods=["GET"])
@jwt_required()
def get_active_alerts():
    """Get unacknowledged alerts (in-app notifications)."""
    alerts = execute_query("""
        SELECT a.*, m.name AS machine_name, m.location
        FROM alerts a
        JOIN machines m ON a.machine_id = m.machine_id
        WHERE a.acknowledged = 0
        ORDER BY a.timestamp DESC
    """)
    return jsonify(alerts)


@alerts_bp.route("/api/alerts/<int:alert_id>/acknowledge", methods=["PUT"])
@jwt_required()
def acknowledge_alert(alert_id):
    execute_query(
        "UPDATE alerts SET acknowledged = 1 WHERE alert_id = %s",
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

    execute_query("UPDATE alerts SET acknowledged = 1 WHERE acknowledged = 0", fetch=False)
    return jsonify({"message": "All alerts acknowledged"})


@alerts_bp.route("/api/alerts/count", methods=["GET"])
@jwt_required()
def get_alert_count():
    result = execute_query("SELECT COUNT(*) AS count FROM alerts WHERE acknowledged = 0")
    return jsonify({"count": result[0]["count"]})
