"""
Sensor reading routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import execute_query

sensors_bp = Blueprint("sensors", __name__)


@sensors_bp.route("/api/sensors", methods=["GET"])
@jwt_required()
def get_sensor_readings():
    machine_id = request.args.get("machine_id")
    limit = request.args.get("limit", 100, type=int)

    if machine_id:
        readings = execute_query(
            "SELECT * FROM sensor_readings WHERE machine_id = %s ORDER BY timestamp DESC LIMIT %s",
            (machine_id, limit)
        )
    else:
        readings = execute_query(
            "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT %s",
            (limit,)
        )

    # Convert Decimal to float for JSON serialization
    for r in readings:
        for key in ["temperature", "vibration", "pressure", "motor_current", "oil_level", "bundle_weight"]:
            if key in r and r[key] is not None:
                r[key] = float(r[key])

    return jsonify(readings)


@sensors_bp.route("/api/sensors/latest", methods=["GET"])
@jwt_required()
def get_latest_readings():
    """Get latest reading per machine."""
    query = """
        SELECT sr.*
        FROM sensor_readings sr
        INNER JOIN (
            SELECT machine_id, MAX(timestamp) AS max_ts
            FROM sensor_readings
            GROUP BY machine_id
        ) latest ON sr.machine_id = latest.machine_id AND sr.timestamp = latest.max_ts
        ORDER BY sr.machine_id
    """
    readings = execute_query(query)
    for r in readings:
        for key in ["temperature", "vibration", "pressure", "motor_current", "oil_level", "bundle_weight"]:
            if key in r and r[key] is not None:
                r[key] = float(r[key])
    return jsonify(readings)


@sensors_bp.route("/api/sensors/stats", methods=["GET"])
@jwt_required()
def get_sensor_stats():
    """Average sensor values per machine."""
    query = """
        SELECT
            m.machine_id,
            m.name AS machine_name,
            ROUND(AVG(sr.temperature), 2) AS avg_temperature,
            ROUND(AVG(sr.vibration), 2) AS avg_vibration,
            ROUND(AVG(sr.pressure), 2) AS avg_pressure,
            ROUND(AVG(sr.motor_current), 2) AS avg_motor_current,
            ROUND(AVG(sr.oil_level), 2) AS avg_oil_level,
            ROUND(AVG(sr.bundle_weight), 2) AS avg_bundle_weight,
            ROUND(SUM(sr.bundle_weight), 2) AS total_weight,
            SUM(sr.proximity) AS scrap_detections,
            COUNT(*) AS total_readings
        FROM sensor_readings sr
        JOIN machines m ON sr.machine_id = m.machine_id
        GROUP BY m.machine_id, m.name
    """
    stats = execute_query(query)
    for s in stats:
        for key in ["avg_temperature", "avg_vibration", "avg_pressure", "avg_motor_current", "avg_oil_level", "avg_bundle_weight", "total_weight"]:
            if key in s and s[key] is not None:
                s[key] = float(s[key])
    return jsonify(stats)
