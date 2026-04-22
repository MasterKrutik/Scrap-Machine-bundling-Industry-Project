"""
Database connection helper.
Supports MySQL (production) and SQLite (fallback for demo).
Set USE_SQLITE = True to run without MySQL installed.
"""

import sqlite3
import os

# Toggle: set to False if MySQL is available
USE_SQLITE = True

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scrap_machine.db")

# MySQL config (used when USE_SQLITE = False)
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "password",
    "database": "scrap_machine_db"
}


def get_db():
    """Get a database connection."""
    if USE_SQLITE:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    else:
        import mysql.connector
        return mysql.connector.connect(**MYSQL_CONFIG)


def execute_query(query, params=None, fetch=True):
    """Execute a query and return results."""
    conn = get_db()

    if USE_SQLITE:
        # Convert MySQL-style %s placeholders to ? for SQLite
        if params and "%s" in query:
            query = query.replace("%s", "?")
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            if fetch:
                rows = cursor.fetchall()
                # Convert sqlite3.Row to dict
                return [dict(row) for row in rows]
            else:
                conn.commit()
                return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()
    else:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()


def execute_many(query, data_list):
    """Execute a query with multiple data sets."""
    conn = get_db()
    if USE_SQLITE and "%s" in query:
        query = query.replace("%s", "?")
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data_list)
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def init_sqlite_db():
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS machines (
            machine_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            type            TEXT NOT NULL,
            location        TEXT NOT NULL,
            install_date    TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'Idle'
                            CHECK (status IN ('Running', 'Idle', 'Maintenance', 'Fault')),
            max_capacity_tons REAL NOT NULL CHECK (max_capacity_tons > 0)
        );

        CREATE TABLE IF NOT EXISTS employees (
            employee_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name      TEXT NOT NULL,
            last_name       TEXT NOT NULL,
            role            TEXT NOT NULL,
            department      TEXT NOT NULL,
            shift           TEXT NOT NULL CHECK (shift IN ('Morning', 'Afternoon', 'Night')),
            phone           TEXT NOT NULL,
            hire_date       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            password_hash   TEXT NOT NULL,
            role            TEXT NOT NULL DEFAULT 'User' CHECK (role IN ('Admin', 'User')),
            employee_id     INTEGER NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS sensor_readings (
            reading_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id      INTEGER NOT NULL,
            timestamp       TEXT NOT NULL,
            temperature     REAL NOT NULL CHECK (temperature >= 0),
            vibration       REAL NOT NULL CHECK (vibration >= 0),
            pressure        REAL NOT NULL CHECK (pressure >= 0),
            motor_current   REAL NOT NULL CHECK (motor_current >= 0),
            oil_level       REAL NOT NULL CHECK (oil_level >= 0 AND oil_level <= 100),
            bundle_weight   REAL NOT NULL DEFAULT 0 CHECK (bundle_weight >= 0),
            proximity       INTEGER NOT NULL DEFAULT 0 CHECK (proximity IN (0, 1)),
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );

        CREATE TABLE IF NOT EXISTS production_logs (
            log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id      INTEGER NOT NULL,
            date            TEXT NOT NULL,
            bundles_produced INTEGER NOT NULL CHECK (bundles_produced >= 0),
            raw_material_kg REAL NOT NULL CHECK (raw_material_kg >= 0),
            operating_hours REAL NOT NULL CHECK (operating_hours >= 0 AND operating_hours <= 24),
            efficiency      REAL NOT NULL CHECK (efficiency >= 0 AND efficiency <= 100),
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );

        CREATE TABLE IF NOT EXISTS fault_logs (
            fault_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id      INTEGER NOT NULL,
            reported_by     INTEGER NOT NULL,
            timestamp       TEXT NOT NULL,
            fault_type      TEXT NOT NULL,
            severity        TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
            description     TEXT,
            resolved        INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1)),
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
            FOREIGN KEY (reported_by) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_logs (
            maintenance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id      INTEGER NOT NULL,
            performed_by    INTEGER NOT NULL,
            date            TEXT NOT NULL,
            type            TEXT NOT NULL CHECK (type IN ('Preventive', 'Corrective', 'Predictive', 'Emergency')),
            duration_hours  REAL NOT NULL CHECK (duration_hours > 0),
            description     TEXT,
            parts_replaced  TEXT,
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
            FOREIGN KEY (performed_by) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fault_id        INTEGER,
            machine_id      INTEGER NOT NULL,
            timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
            severity        TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High')),
            message         TEXT NOT NULL,
            acknowledged    INTEGER NOT NULL DEFAULT 0 CHECK (acknowledged IN (0, 1)),
            FOREIGN KEY (fault_id) REFERENCES fault_logs(fault_id),
            FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        );

        CREATE INDEX IF NOT EXISTS idx_sensor_machine_ts ON sensor_readings(machine_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp);
        CREATE INDEX IF NOT EXISTS idx_production_machine_date ON production_logs(machine_id, date);
        CREATE INDEX IF NOT EXISTS idx_fault_machine ON fault_logs(machine_id);
        CREATE INDEX IF NOT EXISTS idx_fault_severity ON fault_logs(severity);
        CREATE INDEX IF NOT EXISTS idx_maintenance_machine ON maintenance_logs(machine_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
        CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ SQLite database initialized")


def seed_sqlite_db():
    """Seed SQLite database from CSV files."""
    import csv

    dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dataset")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def read_csv(filename):
        with open(os.path.join(dataset_dir, filename), "r") as f:
            return list(csv.DictReader(f))

    # Machines
    for r in read_csv("machines.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO machines VALUES (?,?,?,?,?,?,?)",
            (r["machine_id"], r["name"], r["type"], r["location"],
             r["install_date"], r["status"], r["max_capacity_tons"])
        )

    # Employees
    for r in read_csv("employees.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO employees VALUES (?,?,?,?,?,?,?,?)",
            (r["employee_id"], r["first_name"], r["last_name"], r["role"],
             r["department"], r["shift"], r["phone"], r["hire_date"])
        )

    # Users
    for r in read_csv("users.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
            (r["user_id"], r["username"], r["password_hash"], r["role"], r["employee_id"])
        )

    # Production logs
    for r in read_csv("production_logs.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO production_logs VALUES (?,?,?,?,?,?,?)",
            (r["log_id"], r["machine_id"], r["date"], r["bundles_produced"],
             r["raw_material_kg"], r["operating_hours"], r["efficiency"])
        )

    # Fault logs
    for r in read_csv("fault_logs.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO fault_logs VALUES (?,?,?,?,?,?,?,?)",
            (r["fault_id"], r["machine_id"], r["reported_by"], r["timestamp"],
             r["fault_type"], r["severity"], r["description"], r["resolved"])
        )

    # Maintenance logs
    for r in read_csv("maintenance_logs.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO maintenance_logs VALUES (?,?,?,?,?,?,?,?)",
            (r["maintenance_id"], r["machine_id"], r["performed_by"], r["date"],
             r["type"], r["duration_hours"], r["description"], r["parts_replaced"])
        )

    # Alerts
    for r in read_csv("alerts.csv"):
        cursor.execute(
            "INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,?,?)",
            (r["alert_id"], r["fault_id"], r["machine_id"], r["timestamp"],
             r["severity"], r["message"], r["acknowledged"])
        )

    # Sensor readings (bulk)
    rows = read_csv("sensor_readings.csv")
    batch = [(r["reading_id"], r["machine_id"], r["timestamp"], r["temperature"],
              r["vibration"], r["pressure"], r["motor_current"], r["oil_level"],
              r["bundle_weight"], r["proximity"]) for r in rows]
    cursor.executemany(
        "INSERT OR IGNORE INTO sensor_readings VALUES (?,?,?,?,?,?,?,?,?,?)", batch
    )

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ SQLite database seeded with all data")


if __name__ == "__main__":
    if USE_SQLITE:
        init_sqlite_db()
        seed_sqlite_db()
    else:
        print("Set USE_SQLITE = True to initialize SQLite, or use seed_database.py for MySQL")
