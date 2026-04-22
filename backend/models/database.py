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
            Machine_ID TEXT PRIMARY KEY,
            Machine_Name TEXT,
            Location TEXT,
            Installation_Date TEXT,
            Status TEXT,
            Capacity TEXT
        );

        CREATE TABLE IF NOT EXISTS operators (
            Operator_ID TEXT PRIMARY KEY,
            Name TEXT,
            Shift TEXT,
            Contact TEXT,
            Experience_Years TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            Operator_ID TEXT,
            FOREIGN KEY (Operator_ID) REFERENCES operators(Operator_ID)
        );

        CREATE TABLE IF NOT EXISTS maintenance_logs (
            Maintenance_ID TEXT PRIMARY KEY,
            Machine_ID TEXT,
            Maintenance_Date TEXT,
            Description TEXT,
            Technician_Name TEXT,
            Cost TEXT,
            FOREIGN KEY (Machine_ID) REFERENCES machines(Machine_ID)
        );

        CREATE TABLE IF NOT EXISTS sensors (
            Sensor_ID TEXT PRIMARY KEY,
            Sensor_Type TEXT,
            Unit TEXT,
            Machine_ID TEXT,
            FOREIGN KEY (Machine_ID) REFERENCES machines(Machine_ID)
        );

        CREATE TABLE IF NOT EXISTS sensor_data (
            Data_ID TEXT PRIMARY KEY,
            Sensor_ID TEXT,
            Timestamp TEXT,
            Value REAL,
            FOREIGN KEY (Sensor_ID) REFERENCES sensors(Sensor_ID)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            Alert_ID TEXT PRIMARY KEY,
            Machine_ID TEXT,
            Sensor_ID TEXT,
            Alert_Type TEXT,
            Alert_Time TEXT,
            Status TEXT,
            FOREIGN KEY (Machine_ID) REFERENCES machines(Machine_ID),
            FOREIGN KEY (Sensor_ID) REFERENCES sensors(Sensor_ID)
        );

        CREATE TABLE IF NOT EXISTS scrap_materials (
            Scrap_ID TEXT PRIMARY KEY,
            Scrap_Type TEXT,
            Weight REAL,
            Source TEXT,
            Received_Date TEXT
        );

        CREATE TABLE IF NOT EXISTS bundles (
            Bundle_ID TEXT PRIMARY KEY,
            Machine_ID TEXT,
            Scrap_ID TEXT,
            Bundle_Weight REAL,
            Production_Time TEXT,
            Quality_Status TEXT,
            FOREIGN KEY (Machine_ID) REFERENCES machines(Machine_ID),
            FOREIGN KEY (Scrap_ID) REFERENCES scrap_materials(Scrap_ID)
        );

        CREATE TABLE IF NOT EXISTS production_logs (
            Production_ID TEXT PRIMARY KEY,
            Machine_ID TEXT,
            Operator_ID TEXT,
            Bundle_ID TEXT,
            Start_Time TEXT,
            End_Time TEXT,
            Total_Output REAL,
            FOREIGN KEY (Machine_ID) REFERENCES machines(Machine_ID),
            FOREIGN KEY (Operator_ID) REFERENCES operators(Operator_ID),
            FOREIGN KEY (Bundle_ID) REFERENCES bundles(Bundle_ID)
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ SQLite database initialized")


def seed_sqlite_db():
    """Seed SQLite database from CSV files."""
    import csv
    from werkzeug.security import generate_password_hash

    dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dataset")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    def read_csv(filename):
        with open(os.path.join(dataset_dir, filename), "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    # Machines
    try:
        for r in read_csv("machine table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO machines VALUES (?,?,?,?,?,?)",
                (r.get("Machine_ID"), r.get("Machine_Name"), r.get("Location"), 
                 r.get("Installation_Date"), r.get("Status"), r.get("Capacity"))
            )
    except FileNotFoundError: pass

    # Operators
    try:
        operator_ids = []
        for r in read_csv("Operator table.csv"):
            operator_ids.append(r.get("Operator_ID"))
            cursor.execute(
                "INSERT OR IGNORE INTO operators VALUES (?,?,?,?,?)",
                (r.get("Operator_ID"), r.get("Name"), r.get("Shift"), r.get("Contact"), r.get("Experience_Years"))
            )
        
        # Create a default Admin User linked to the first operator
        if operator_ids:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            if cursor.fetchone()[0] == 0:
                pwd_hash = generate_password_hash("password")
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, Operator_ID) VALUES (?,?,?,?)",
                    ("admin", pwd_hash, "Admin", operator_ids[0])
                )
    except FileNotFoundError: pass

    # Scrap Materials
    try:
        for r in read_csv("Scrap_material table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO scrap_materials VALUES (?,?,?,?,?)",
                (r.get("Scrap_ID"), r.get("Scrap_Type"), r.get("Weight"), r.get("Source"), r.get("Received_Date"))
            )
    except FileNotFoundError: pass

    # Sensors
    try:
        for r in read_csv("Sensor table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO sensors VALUES (?,?,?,?)",
                (r.get("Sensor_ID"), r.get("Sensor_Type"), r.get("Unit"), r.get("Machine_ID"))
            )
    except FileNotFoundError: pass

    # Sensor Data
    try:
        rows = read_csv("Sensordata table.csv")
        batch = [(r.get("Data_ID"), r.get("Sensor_ID"), r.get("Timestamp"), r.get("Value")) for r in rows]
        cursor.executemany("INSERT OR IGNORE INTO sensor_data VALUES (?,?,?,?)", batch)
    except FileNotFoundError: pass

    # Alerts
    try:
        for r in read_csv("Alert table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,?)",
                (r.get("Alert_ID"), r.get("Machine_ID"), r.get("Sensor_ID"), r.get("Alert_Type"), r.get("Alert_Time"), r.get("Status"))
            )
    except FileNotFoundError: pass

    # Bundles
    try:
        for r in read_csv("Bundle table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO bundles VALUES (?,?,?,?,?,?)",
                (r.get("Bundle_ID"), r.get("Machine_ID"), r.get("Scrap_ID"), r.get("Bundle_Weight"), r.get("Production_Time"), r.get("Quality_Status"))
            )
    except FileNotFoundError: pass

    # Production Logs
    try:
        for r in read_csv("Production table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO production_logs VALUES (?,?,?,?,?,?,?)",
                (r.get("Production_ID"), r.get("Machine_ID"), r.get("Operator_ID"), r.get("Bundle_ID"), r.get("Start_Time"), r.get("End_Time"), r.get("Total_Output"))
            )
    except FileNotFoundError: pass

    # Maintenance Logs
    try:
        for r in read_csv("Maintenance table.csv"):
            cursor.execute(
                "INSERT OR IGNORE INTO maintenance_logs VALUES (?,?,?,?,?,?)",
                (r.get("Maintenance_ID"), r.get("Machine_ID"), r.get("Maintenance_Date"), r.get("Description"), r.get("Technician_Name"), r.get("Cost"))
            )
    except FileNotFoundError: pass

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
