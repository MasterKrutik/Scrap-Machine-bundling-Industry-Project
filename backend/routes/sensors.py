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

    query = """
        SELECT 
            sd.Timestamp AS reading_id,
            s.Machine_ID AS machine_id,
            sd.Timestamp AS timestamp,
            MAX(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END) AS temperature,
            MAX(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END) AS pressure,
            MAX(CASE WHEN s.Sensor_Type = 'Weight' THEN sd.Value END) AS bundle_weight,
            0 AS vibration,
            0 AS motor_current,
            0 AS oil_level,
            0 AS proximity
        FROM sensor_data sd
        JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
        {where_clause}
        GROUP BY s.Machine_ID, sd.Timestamp
        ORDER BY sd.Timestamp DESC
        LIMIT %s
    """
    
    if machine_id:
        readings = execute_query(query.format(where_clause="WHERE s.Machine_ID = %s"), (machine_id, limit))
    else:
        readings = execute_query(query.format(where_clause=""), (limit,))

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
        SELECT 
            sd.Timestamp AS reading_id,
            s.Machine_ID AS machine_id,
            sd.Timestamp AS timestamp,
            MAX(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END) AS temperature,
            MAX(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END) AS pressure,
            MAX(CASE WHEN s.Sensor_Type = 'Weight' THEN sd.Value END) AS bundle_weight,
            0 AS vibration,
            0 AS motor_current,
            0 AS oil_level,
            0 AS proximity
        FROM sensor_data sd
        JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
        JOIN (
            SELECT s2.Machine_ID, MAX(sd2.Timestamp) AS max_ts
            FROM sensor_data sd2
            JOIN sensors s2 ON sd2.Sensor_ID = s2.Sensor_ID
            GROUP BY s2.Machine_ID
        ) latest ON s.Machine_ID = latest.Machine_ID AND sd.Timestamp = latest.max_ts
        GROUP BY s.Machine_ID, sd.Timestamp
        ORDER BY s.Machine_ID
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
        WITH Pivoted AS (
            SELECT 
                s.Machine_ID,
                MAX(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END) AS temperature,
                MAX(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END) AS pressure,
                MAX(CASE WHEN s.Sensor_Type = 'Weight' THEN sd.Value END) AS bundle_weight
            FROM sensor_data sd
            JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
            GROUP BY s.Machine_ID, sd.Timestamp
        )
        SELECT
            p.Machine_ID AS machine_id,
            m.Machine_Name AS machine_name,
            ROUND(AVG(p.temperature), 2) AS avg_temperature,
            0 AS avg_vibration,
            ROUND(AVG(p.pressure), 2) AS avg_pressure,
            0 AS avg_motor_current,
            0 AS avg_oil_level,
            ROUND(AVG(p.bundle_weight), 2) AS avg_bundle_weight,
            ROUND(SUM(p.bundle_weight), 2) AS total_weight,
            0 AS scrap_detections,
            COUNT(*) AS total_readings
        FROM Pivoted p
        JOIN machines m ON p.Machine_ID = m.Machine_ID
        GROUP BY p.Machine_ID, m.Machine_Name
    """
    stats = execute_query(query)
    for s in stats:
        for key in ["avg_temperature", "avg_vibration", "avg_pressure", "avg_motor_current", "avg_oil_level", "avg_bundle_weight", "total_weight"]:
            if key in s and s[key] is not None:
                s[key] = float(s[key])
    return jsonify(stats)
