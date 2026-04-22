"""
Employee routes - CRUD operations.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/api/employees", methods=["GET"])
@jwt_required()
def get_employees():
    employees = execute_query("SELECT * FROM employees ORDER BY employee_id")
    return jsonify(employees)


@employees_bp.route("/api/employees/<int:employee_id>", methods=["GET"])
@jwt_required()
def get_employee(employee_id):
    employees = execute_query("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
    if not employees:
        return jsonify({"error": "Employee not found"}), 404
    return jsonify(employees[0])


@employees_bp.route("/api/employees", methods=["POST"])
@jwt_required()
def create_employee():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    required = ["first_name", "last_name", "role", "department", "shift", "phone", "hire_date"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    emp_id = execute_query(
        """INSERT INTO employees (first_name, last_name, role, department, shift, phone, hire_date)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (data["first_name"], data["last_name"], data["role"], data["department"],
         data["shift"], data["phone"], data["hire_date"]),
        fetch=False
    )
    return jsonify({"message": "Employee created", "employee_id": emp_id}), 201


@employees_bp.route("/api/employees/<int:employee_id>", methods=["PUT"])
@jwt_required()
def update_employee(employee_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    data = request.get_json()
    fields = []
    values = []
    for key in ["first_name", "last_name", "role", "department", "shift", "phone"]:
        if key in data:
            fields.append(f"{key} = %s")
            values.append(data[key])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    values.append(employee_id)
    execute_query(
        f"UPDATE employees SET {', '.join(fields)} WHERE employee_id = %s",
        tuple(values),
        fetch=False
    )
    return jsonify({"message": "Employee updated"})


@employees_bp.route("/api/employees/<int:employee_id>", methods=["DELETE"])
@jwt_required()
def delete_employee(employee_id):
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    execute_query("DELETE FROM employees WHERE employee_id = %s", (employee_id,), fetch=False)
    return jsonify({"message": "Employee deleted"})
