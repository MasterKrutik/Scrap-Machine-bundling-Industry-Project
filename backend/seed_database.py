"""
Seed the MySQL database with data from CSV files.
Run this after creating the schema with schema.sql.
"""

import csv
import os
import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "amit2059",
    "database": "ScrapBundle"
}

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def read_csv(filename):
    filepath = os.path.join(DATASET_DIR, filename)
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)


def seed_machines(cursor):
    rows = read_csv("machines.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO machines (machine_id, name, type, location, install_date, status, max_capacity_tons)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (r["machine_id"], r["name"], r["type"], r["location"],
              r["install_date"], r["status"], r["max_capacity_tons"]))
    print(f"  ✓ Seeded {len(rows)} machines")


def seed_employees(cursor):
    rows = read_csv("employees.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO employees (employee_id, first_name, last_name, role, department, shift, phone, hire_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (r["employee_id"], r["first_name"], r["last_name"], r["role"],
              r["department"], r["shift"], r["phone"], r["hire_date"]))
    print(f"  ✓ Seeded {len(rows)} employees")


def seed_users(cursor):
    rows = read_csv("users.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO users (user_id, username, password_hash, role, employee_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (r["user_id"], r["username"], r["password_hash"], r["role"], r["employee_id"]))
    print(f"  ✓ Seeded {len(rows)} users")


def seed_sensor_readings(cursor):
    rows = read_csv("sensor_readings.csv")
    batch = []
    for r in rows:
        batch.append((r["reading_id"], r["machine_id"], r["timestamp"],
                       r["temperature"], r["vibration"], r["pressure"],
                       r["motor_current"], r["oil_level"]))
        if len(batch) >= 1000:
            cursor.executemany("""
                INSERT IGNORE INTO sensor_readings
                (reading_id, machine_id, timestamp, temperature, vibration, pressure, motor_current, oil_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, batch)
            batch = []
    if batch:
        cursor.executemany("""
            INSERT IGNORE INTO sensor_readings
            (reading_id, machine_id, timestamp, temperature, vibration, pressure, motor_current, oil_level)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, batch)
    print(f"  ✓ Seeded {len(rows)} sensor readings")


def seed_production_logs(cursor):
    rows = read_csv("production_logs.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO production_logs (log_id, machine_id, date, bundles_produced, raw_material_kg, operating_hours, efficiency)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (r["log_id"], r["machine_id"], r["date"], r["bundles_produced"],
              r["raw_material_kg"], r["operating_hours"], r["efficiency"]))
    print(f"  ✓ Seeded {len(rows)} production logs")


def seed_fault_logs(cursor):
    rows = read_csv("fault_logs.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO fault_logs (fault_id, machine_id, reported_by, timestamp, fault_type, severity, description, resolved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (r["fault_id"], r["machine_id"], r["reported_by"], r["timestamp"],
              r["fault_type"], r["severity"], r["description"], r["resolved"]))
    print(f"  ✓ Seeded {len(rows)} fault logs")


def seed_maintenance_logs(cursor):
    rows = read_csv("maintenance_logs.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO maintenance_logs
            (maintenance_id, machine_id, performed_by, date, type, duration_hours, description, parts_replaced)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (r["maintenance_id"], r["machine_id"], r["performed_by"], r["date"],
              r["type"], r["duration_hours"], r["description"], r["parts_replaced"]))
    print(f"  ✓ Seeded {len(rows)} maintenance logs")


def seed_alerts(cursor):
    rows = read_csv("alerts.csv")
    for r in rows:
        cursor.execute("""
            INSERT IGNORE INTO alerts (alert_id, fault_id, machine_id, timestamp, severity, message, acknowledged)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (r["alert_id"], r["fault_id"], r["machine_id"], r["timestamp"],
              r["severity"], r["message"], r["acknowledged"]))
    print(f"  ✓ Seeded {len(rows)} alerts")


def main():
    print("🔄 Connecting to MySQL...")
    conn = get_connection()
    cursor = conn.cursor()

    # Disable FK checks for bulk insert
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    print("📊 Seeding database...")
    seed_machines(cursor)
    seed_employees(cursor)
    seed_users(cursor)
    seed_production_logs(cursor)
    seed_fault_logs(cursor)
    seed_maintenance_logs(cursor)
    seed_alerts(cursor)
    seed_sensor_readings(cursor)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Database seeded successfully!")


if __name__ == "__main__":
    main()
