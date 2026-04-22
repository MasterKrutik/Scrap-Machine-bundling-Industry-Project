"""
Machine routes - CRUD operations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

machines_bp = Blueprint("machines", __name__)


@machines_bp.route("/api/machines", methods=["GET"])
@jwt_required()
def get_machines():
    machines = execute_query("SELECT * FROM machines ORDER BY machine_id")
    return jsonify(machines)


@machines_bp.route("/api/machines/<int:machine_id>", methods=["GET"])
@jwt_required()
def get_machine(machine_id):
    machines = execute_query("SELECT * FROM machines WHERE machine_id = %s", (machine_id,))
    if not machines:
        return jsonify({"error": "Machine not found"}), 404
    return jsonify(machines[0])


@machines_bp.route("/api/machines", methods=["POST"])
@jwt_required()
def create_machine():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["name", "type", "location", "install_date", "max_capacity_tons"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    machine_id = execute_query(
        """INSERT INTO machines (name, type, location, install_date, status, max_capacity_tons)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (data["name"], data["type"], data["location"], data["install_date"],
         data.get("status", "Idle"), data["max_capacity_tons"]),
        fetch=False
    )
    return jsonify({"message": "Machine created", "machine_id": machine_id}), 201


@machines_bp.route("/api/machines/<int:machine_id>", methods=["PUT"])
@jwt_required()
def update_machine(machine_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    fields = []
    values = []
    for key in ["name", "type", "location", "status", "max_capacity_tons"]:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    values.append(machine_id)
    execute_query(
        f"UPDATE machines SET {', '.join(fields)} WHERE machine_id = %s",
        tuple(values),
        fetch=False
    )
    return jsonify({"message": "Machine updated"})


@machines_bp.route("/api/machines/<int:machine_id>", methods=["DELETE"])
@jwt_required()
def delete_machine(machine_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    execute_query("DELETE FROM machines WHERE machine_id = %s", (machine_id,), fetch=False)
    return jsonify({"message": "Machine deleted"})
