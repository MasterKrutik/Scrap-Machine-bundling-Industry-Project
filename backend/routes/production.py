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

    query = """
        SELECT 
            pl.Production_ID AS log_id,
            m.Machine_Name AS machine_name,
            pl.Start_Time AS date,
            1 AS bundles_produced,
            pl.Total_Output AS raw_material_kg,
            1 AS operating_hours,
            85.0 AS efficiency
        FROM production_logs pl
        JOIN machines m ON pl.Machine_ID = m.Machine_ID
        {where_clause}
        ORDER BY pl.Start_Time DESC LIMIT %s
    """

    if machine_id:
        logs = execute_query(query.format(where_clause="WHERE pl.Machine_ID = %s"), (machine_id, limit))
    else:
        logs = execute_query(query.format(where_clause=""), (limit,))

    for l in logs:
        for key in ["raw_material_kg", "operating_hours", "efficiency"]:
            if key in l and l[key] is not None:
                l[key] = float(l[key])

    return jsonify(logs)


@production_bp.route("/api/production", methods=["POST"])
@jwt_required()
def create_production_log():
    data = request.get_json()
    return jsonify({"error": "Creating production log manually is currently disabled."}), 400


@production_bp.route("/api/production/summary", methods=["GET"])
@jwt_required()
def get_production_summary():
    query = """
        SELECT
            m.Machine_ID AS machine_id,
            m.Machine_Name AS machine_name,
            COUNT(pl.Bundle_ID) AS total_bundles,
            ROUND(SUM(pl.Total_Output), 2) AS total_material,
            COUNT(pl.Bundle_ID) AS total_hours,
            85.0 AS avg_efficiency
        FROM production_logs pl
        JOIN machines m ON pl.Machine_ID = m.Machine_ID
        GROUP BY m.Machine_ID, m.Machine_Name
        ORDER BY total_bundles DESC
    """
    summary = execute_query(query)
    for s in summary:
        for key in ["total_material", "total_hours", "avg_efficiency"]:
            if key in s and s[key] is not None:
                s[key] = float(s[key])
    return jsonify(summary)
