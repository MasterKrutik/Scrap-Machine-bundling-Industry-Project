"""
Machine routes - CRUD operations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query
import uuid

machines_bp = Blueprint("machines", __name__)


@machines_bp.route("/api/machines", methods=["GET"])
@jwt_required()
def get_machines():
    machines = execute_query("SELECT * FROM machines ORDER BY Machine_ID")
    return jsonify(machines)


@machines_bp.route("/api/machines/<machine_id>", methods=["GET"])
@jwt_required()
def get_machine(machine_id):
    machines = execute_query("SELECT * FROM machines WHERE Machine_ID = %s", (machine_id,))
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
    required = ["Machine_Name", "Location", "Installation_Date", "Capacity"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    machine_id = data.get("Machine_ID", f"M-{str(uuid.uuid4())[:6].upper()}")

    execute_query(
        """INSERT INTO machines (Machine_ID, Machine_Name, Location, Installation_Date, Status, Capacity)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (machine_id, data["Machine_Name"], data["Location"], data["Installation_Date"],
         data.get("Status", "Idle"), data["Capacity"]),
        fetch=False
    )
    return jsonify({"message": "Machine created", "Machine_ID": machine_id}), 201


@machines_bp.route("/api/machines/<machine_id>", methods=["PUT"])
@jwt_required()
def update_machine(machine_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    fields = []
    values = []
    for key in ["Machine_Name", "Location", "Installation_Date", "Status", "Capacity"]:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    values.append(machine_id)
    execute_query(
        f"UPDATE machines SET {', '.join(fields)} WHERE Machine_ID = %s",
        tuple(values),
        fetch=False
    )
    return jsonify({"message": "Machine updated"})


@machines_bp.route("/api/machines/<machine_id>", methods=["DELETE"])
@jwt_required()
def delete_machine(machine_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    execute_query("DELETE FROM machines WHERE Machine_ID = %s", (machine_id,), fetch=False)
    return jsonify({"message": "Machine deleted"})

