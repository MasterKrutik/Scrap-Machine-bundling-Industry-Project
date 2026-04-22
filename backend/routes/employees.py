"""
Employee (Operator) routes - CRUD operations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query
import uuid

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/api/employees", methods=["GET"])
@jwt_required()
def get_employees():
    operators = execute_query("SELECT * FROM operators ORDER BY Operator_ID")
    return jsonify(operators)


@employees_bp.route("/api/employees/<operator_id>", methods=["GET"])
@jwt_required()
def get_employee(operator_id):
    operators = execute_query("SELECT * FROM operators WHERE Operator_ID = %s", (operator_id,))
    if not operators:
        return jsonify({"error": "Operator not found"}), 404
    return jsonify(operators[0])


@employees_bp.route("/api/employees", methods=["POST"])
@jwt_required()
def create_employee():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["Name", "Shift", "Contact", "Experience_Years"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    operator_id = data.get("Operator_ID", f"OP-{str(uuid.uuid4())[:6].upper()}")
    execute_query(
        """INSERT INTO operators (Operator_ID, Name, Shift, Contact, Experience_Years)
           VALUES (%s, %s, %s, %s, %s)""",
        (operator_id, data["Name"], data["Shift"], data["Contact"], data["Experience_Years"]),
        fetch=False
    )
    return jsonify({"message": "Operator created", "Operator_ID": operator_id}), 201


@employees_bp.route("/api/employees/<operator_id>", methods=["PUT"])
@jwt_required()
def update_employee(operator_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    fields = []
    values = []
    for key in ["Name", "Shift", "Contact", "Experience_Years"]:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    values.append(operator_id)
    execute_query(
        f"UPDATE operators SET {', '.join(fields)} WHERE Operator_ID = %s",
        tuple(values),
        fetch=False
    )
    return jsonify({"message": "Operator updated"})


@employees_bp.route("/api/employees/<operator_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(operator_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    execute_query("DELETE FROM operators WHERE Operator_ID = %s", (operator_id,), fetch=False)
    return jsonify({"message": "Operator deleted"})
