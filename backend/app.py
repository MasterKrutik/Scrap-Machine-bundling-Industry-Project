"""
Flask Application - Scrap Bundle Making Machine IoT System
Main entry point with CORS, JWT, and blueprint registration.
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Route imports
from routes.auth import auth_bp
from routes.machines import machines_bp
from routes.employees import employees_bp
from routes.sensors import sensors_bp
from routes.production import production_bp
from routes.faults import faults_bp
from routes.maintenance import maintenance_bp
from routes.alerts import alerts_bp
from routes.analytics import analytics_bp
from routes.reports import reports_bp


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config["JWT_SECRET_KEY"] = "scrap-machine-iot-secret-key-2024"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(sensors_bp)
    app.register_blueprint(production_bp)
    app.register_blueprint(faults_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "ScrapMachine IoT API"}

    return app


if __name__ == "__main__":
    # Auto-initialize SQLite database if it doesn't exist
    from models.database import USE_SQLITE, DB_PATH, init_sqlite_db, seed_sqlite_db
    import os
    if USE_SQLITE and not os.path.exists(DB_PATH):
        print("First run - initializing SQLite database...")
        init_sqlite_db()
        seed_sqlite_db()

    app = create_app()
    print("ScrapMachine IoT API starting on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
