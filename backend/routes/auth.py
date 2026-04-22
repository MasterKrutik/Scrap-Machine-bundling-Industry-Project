"""
Auth routes - Login with JWT, role-based (Admin / User).
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import hashlib
from models.database import execute_query

auth_bp = Blueprint("auth", __name__)


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = execute_query(
        "SELECT u.*, (e.first_name || ' ' || e.last_name) AS full_name "
        "FROM users u JOIN employees e ON u.employee_id = e.employee_id "
        "WHERE u.username = %s",
        (username,)
    )

    if not users:
        return jsonify({"error": "Invalid credentials"}), 401

    user = users[0]
    if user["password_hash"] != hash_pw(password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user["user_id"]),
        additional_claims={
            "role": user["role"],
            "username": user["username"],
            "full_name": user["full_name"],
            "employee_id": user["employee_id"]
        }
    )

    return jsonify({
        "token": access_token,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
            "employee_id": user["employee_id"]
        }
    }), 200


@auth_bp.route("/api/auth/me", methods=["GET"])
def get_me():
    from flask_jwt_extended import jwt_required, get_jwt
    @jwt_required()
    def inner():
        claims = get_jwt()
        return jsonify({
            "user_id": claims["sub"],
            "role": claims["role"],
            "username": claims["username"],
            "full_name": claims["full_name"]
        })
    return inner()
