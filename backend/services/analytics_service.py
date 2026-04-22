"""
Analytics Service - MTBF, MTTR, Downtime, and Logistic Regression Failure Prediction.
"""

import numpy as np
from models.database import execute_query

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def calculate_mtbf():
    """Mean Time Between Failures per machine."""
    query = """
        SELECT
            m.machine_id,
            m.name,
            COALESCE(SUM(pl.operating_hours), 0) AS total_hours,
            COALESCE(fc.fault_count, 0) AS total_faults,
            CASE
                WHEN COALESCE(fc.fault_count, 0) > 0
                THEN ROUND(SUM(pl.operating_hours) / fc.fault_count, 2)
                ELSE 0
            END AS mtbf
        FROM machines m
        LEFT JOIN production_logs pl ON m.machine_id = pl.machine_id
        LEFT JOIN (
            SELECT machine_id, COUNT(*) AS fault_count
            FROM fault_logs
            GROUP BY machine_id
        ) fc ON m.machine_id = fc.machine_id
        GROUP BY m.machine_id, m.name, fc.fault_count
        ORDER BY m.machine_id
    """
    return execute_query(query)


def calculate_mttr():
    """Mean Time To Repair per machine."""
    query = """
        SELECT
            m.machine_id,
            m.name,
            COUNT(ml.maintenance_id) AS total_repairs,
            ROUND(COALESCE(SUM(ml.duration_hours), 0), 1) AS total_repair_hours,
            ROUND(COALESCE(AVG(ml.duration_hours), 0), 2) AS mttr
        FROM machines m
        LEFT JOIN maintenance_logs ml ON m.machine_id = ml.machine_id
        GROUP BY m.machine_id, m.name
        ORDER BY m.machine_id
    """
    return execute_query(query)


def calculate_downtime():
    """Total downtime per machine."""
    query = """
        SELECT
            m.machine_id,
            m.name,
            ROUND(COALESCE(SUM(ml.duration_hours), 0), 1) AS downtime_hours,
            COUNT(ml.maintenance_id) AS maintenance_events,
            COALESCE(fc.fault_count, 0) AS fault_events
        FROM machines m
        LEFT JOIN maintenance_logs ml ON m.machine_id = ml.machine_id
        LEFT JOIN (
            SELECT machine_id, COUNT(*) AS fault_count
            FROM fault_logs
            GROUP BY machine_id
        ) fc ON m.machine_id = fc.machine_id
        GROUP BY m.machine_id, m.name, fc.fault_count
        ORDER BY downtime_hours DESC
    """
    return execute_query(query)


def predict_failure():
    """
    Logistic Regression failure probability prediction.
    Uses sensor readings to predict if a machine is likely to fail.
    Features: avg temperature, vibration, pressure, motor_current, oil_level
    Label: 1 if machine had a High severity fault in the same period, else 0
    """
    if not SKLEARN_AVAILABLE:
        return {"error": "scikit-learn not installed"}

    # Get average sensor readings per machine
    sensor_query = """
        SELECT
            sr.machine_id,
            AVG(sr.temperature) AS avg_temp,
            AVG(sr.vibration) AS avg_vib,
            AVG(sr.pressure) AS avg_pressure,
            AVG(sr.motor_current) AS avg_current,
            AVG(sr.oil_level) AS avg_oil
        FROM sensor_readings sr
        GROUP BY sr.machine_id
    """
    sensor_data = execute_query(sensor_query)

    # Get fault labels
    fault_query = """
        SELECT machine_id, COUNT(*) AS high_faults
        FROM fault_logs
        WHERE severity = 'High'
        GROUP BY machine_id
    """
    fault_data = execute_query(fault_query)
    fault_map = {f["machine_id"]: f["high_faults"] for f in fault_data}

    if len(sensor_data) < 2:
        return {"error": "Not enough data for prediction"}

    X = []
    y = []
    machine_ids = []
    for s in sensor_data:
        features = [
            float(s["avg_temp"]),
            float(s["avg_vib"]),
            float(s["avg_pressure"]),
            float(s["avg_current"]),
            float(s["avg_oil"])
        ]
        X.append(features)
        label = 1 if fault_map.get(s["machine_id"], 0) > 2 else 0
        y.append(label)
        machine_ids.append(s["machine_id"])

    X = np.array(X)
    y = np.array(y)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train logistic regression
    model = LogisticRegression(random_state=42)
    model.fit(X_scaled, y)

    # Predict probabilities
    probabilities = model.predict_proba(X_scaled)

    results = []
    for i, mid in enumerate(machine_ids):
        machine_name_query = "SELECT name FROM machines WHERE machine_id = %s"
        machine = execute_query(machine_name_query, (mid,))
        results.append({
            "machine_id": mid,
            "machine_name": machine[0]["name"] if machine else f"Machine-{mid}",
            "failure_probability": round(float(probabilities[i][1]) * 100, 2),
            "risk_level": "High" if probabilities[i][1] > 0.6 else ("Medium" if probabilities[i][1] > 0.3 else "Low")
        })

    results.sort(key=lambda x: x["failure_probability"], reverse=True)

    return {
        "predictions": results,
        "model_accuracy": round(float(model.score(X_scaled, y)) * 100, 2),
        "features_used": ["temperature", "vibration", "pressure", "motor_current", "oil_level"]
    }


def get_dashboard_stats():
    """Get aggregate stats for the dashboard."""
    stats = {}

    # Total machines
    r = execute_query("SELECT COUNT(*) AS count FROM machines")
    stats["total_machines"] = r[0]["count"]

    # Active machines
    r = execute_query("SELECT COUNT(*) AS count FROM machines WHERE Status = 'Running'")
    stats["active_machines"] = r[0]["count"]

    # Total employees
    r = execute_query("SELECT COUNT(*) AS count FROM operators")
    stats["total_employees"] = r[0]["count"]

    # Unresolved faults (alerts where Status = 'Open')
    r = execute_query("SELECT COUNT(*) AS count FROM alerts WHERE Status = 'Open'")
    stats["unresolved_faults"] = r[0]["count"]

    # Active alerts
    r = execute_query("SELECT COUNT(*) AS count FROM alerts WHERE Status = 'Open'")
    stats["active_alerts"] = r[0]["count"]

    # Total production
    r = execute_query("SELECT COALESCE(SUM(Bundles_Produced), 0) AS total FROM production_logs")
    stats["total_bundles"] = r[0]["total"]

    # Avg efficiency
    r = execute_query("SELECT ROUND(COALESCE(AVG(Efficiency), 0), 2) AS avg_eff FROM production_logs")
    stats["avg_efficiency"] = float(r[0]["avg_eff"])

    # Total sensor readings
    r = execute_query("SELECT COUNT(*) AS count FROM sensors")
    stats["total_readings"] = r[0]["count"]

    return stats
