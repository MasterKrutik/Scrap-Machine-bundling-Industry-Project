"""
Auth routes - Login with JWT, role-based (Admin / User).
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from models.database import execute_query

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = execute_query(
        "SELECT u.*, o.Name AS full_name "
        "FROM users u LEFT JOIN operators o ON u.Operator_ID = o.Operator_ID "
        "WHERE u.username = %s",
        (username,)
    )

    if not users:
        return jsonify({"error": "Invalid credentials"}), 401

    user = users[0]
    
    # Backward compatibility: check if it's werkzeug hash (scrypt/pbkdf2) or sha256
    import hashlib
    is_valid = False
    if user["password_hash"].startswith("scrypt:") or user["password_hash"].startswith("pbkdf2:"):
        is_valid = check_password_hash(user["password_hash"], password)
    else:
        is_valid = user["password_hash"] == hashlib.sha256(password.encode()).hexdigest()

    if not is_valid:
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user["user_id"]),
        additional_claims={
            "role": user["role"],
            "username": user["username"],
            "full_name": user["full_name"] or "Admin",
            "employee_id": user["Operator_ID"]
        }
    )

    return jsonify({
        "token": access_token,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"] or "Admin",
            "employee_id": user["Operator_ID"]
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

