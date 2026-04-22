"""
Analytics routes - MTBF, MTTR, Downtime, Failure Prediction.
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from services.analytics_service import (
    calculate_mtbf,
    calculate_mttr,
    calculate_downtime,
    predict_failure,
    get_dashboard_stats
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/mtbf", methods=["GET"])
@jwt_required()
def mtbf():
    data = calculate_mtbf()
    for d in data:
        for key in ["total_hours", "mtbf"]:
            if key in d and d[key] is not None:
                d[key] = float(d[key])
    return jsonify(data)


@analytics_bp.route("/api/analytics/mttr", methods=["GET"])
@jwt_required()
def mttr():
    data = calculate_mttr()
    for d in data:
        for key in ["total_repair_hours", "mttr"]:
            if key in d and d[key] is not None:
                d[key] = float(d[key])
    return jsonify(data)


@analytics_bp.route("/api/analytics/downtime", methods=["GET"])
@jwt_required()
def downtime():
    data = calculate_downtime()
    for d in data:
        if "downtime_hours" in d and d["downtime_hours"] is not None:
            d["downtime_hours"] = float(d["downtime_hours"])
    return jsonify(data)


@analytics_bp.route("/api/analytics/predict", methods=["GET"])
@jwt_required()
def predict():
    result = predict_failure()
    return jsonify(result)


@analytics_bp.route("/api/analytics/stats", methods=["GET"])
@jwt_required()
def stats():
    data = get_dashboard_stats()
    return jsonify(data)
