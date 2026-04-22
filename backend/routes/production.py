"""
Production log routes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.database import execute_query

production_bp = Blueprint("production", __name__)


@production_bp.route("/api/production", methods=["GET"])
@jwt_required()
def get_production_logs():
    machine_id = request.args.get("machine_id")
    limit = request.args.get("limit", 100, type=int)

    if machine_id:
        logs = execute_query(
            """SELECT pl.*, m.name AS machine_name
               FROM production_logs pl
               JOIN machines m ON pl.machine_id = m.machine_id
               WHERE pl.machine_id = %s
               ORDER BY pl.date DESC LIMIT %s""",
            (machine_id, limit)
        )
    else:
        logs = execute_query(
            """SELECT pl.*, m.name AS machine_name
               FROM production_logs pl
               JOIN machines m ON pl.machine_id = m.machine_id
               ORDER BY pl.date DESC LIMIT %s""",
            (limit,)
        )

    for l in logs:
        for key in ["raw_material_kg", "operating_hours", "efficiency"]:
            if key in l and l[key] is not None:
                l[key] = float(l[key])

    return jsonify(logs)


@production_bp.route("/api/production", methods=["POST"])
@jwt_required()
def create_production_log():
    data = request.get_json()
    required = ["machine_id", "date", "bundles_produced", "raw_material_kg", "operating_hours", "efficiency"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    log_id = execute_query(
        """INSERT INTO production_logs (machine_id, date, bundles_produced, raw_material_kg, operating_hours, efficiency)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (data["machine_id"], data["date"], data["bundles_produced"],
         data["raw_material_kg"], data["operating_hours"], data["efficiency"]),
        fetch=False
    )
    return jsonify({"message": "Production log created", "log_id": log_id}), 201


@production_bp.route("/api/production/summary", methods=["GET"])
@jwt_required()
def get_production_summary():
    query = """
        SELECT
            m.machine_id,
            m.name AS machine_name,
            SUM(pl.bundles_produced) AS total_bundles,
            ROUND(SUM(pl.raw_material_kg), 2) AS total_material,
            ROUND(SUM(pl.operating_hours), 1) AS total_hours,
            ROUND(AVG(pl.efficiency), 2) AS avg_efficiency
        FROM production_logs pl
        JOIN machines m ON pl.machine_id = m.machine_id
        GROUP BY m.machine_id, m.name
        ORDER BY total_bundles DESC
    """
    summary = execute_query(query)
    for s in summary:
        for key in ["total_material", "total_hours", "avg_efficiency"]:
            if key in s and s[key] is not None:
                s[key] = float(s[key])
    return jsonify(summary)
