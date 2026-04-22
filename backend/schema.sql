-- ============================================================
-- Scrap Bundle Making Machine - Database Schema
-- Normalized to 3NF
-- ============================================================

-- 3NF NORMALIZATION EXPLANATION:
-- ─────────────────────────────
-- 1NF: All columns contain atomic (indivisible) values. No repeating
--      groups or arrays. Each row is uniquely identified by a primary key.
--
-- 2NF: No partial dependencies. Every non-key attribute depends on the
--      ENTIRE primary key. Since we use single-column surrogate keys,
--      2NF is automatically satisfied.
--
-- 3NF: No transitive dependencies. Non-key attributes depend ONLY on
--      the primary key, not on other non-key attributes.
--      Examples:
--        - Employee name/role is stored in `employees`, not duplicated
--          in `users` or `maintenance_logs`.
--        - Machine name/type is stored in `machines`, not repeated in
--          `sensor_readings` or `fault_logs`.
--        - Alert details reference `fault_id` instead of duplicating
--          fault information.
-- ============================================================

CREATE DATABASE IF NOT EXISTS scrap_machine_db;
USE scrap_machine_db;

-- ─── 1. Machines ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS machines (
    machine_id      INT             PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(50)     NOT NULL UNIQUE,
    type            VARCHAR(50)     NOT NULL,
    location        VARCHAR(50)     NOT NULL,
    install_date    DATE            NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'Idle'
                                    CHECK (status IN ('Running', 'Idle', 'Maintenance', 'Fault')),
    max_capacity_tons DECIMAL(6,1)  NOT NULL CHECK (max_capacity_tons > 0)
);

-- ─── 2. Employees ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id     INT             PRIMARY KEY AUTO_INCREMENT,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    role            VARCHAR(30)     NOT NULL,
    department      VARCHAR(30)     NOT NULL,
    shift           VARCHAR(15)     NOT NULL
                                    CHECK (shift IN ('Morning', 'Afternoon', 'Night')),
    phone           VARCHAR(15)     NOT NULL,
    hire_date       DATE            NOT NULL
);

-- ─── 3. Users (Login Accounts) ────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         INT             PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(20)     NOT NULL DEFAULT 'User'
                                    CHECK (role IN ('Admin', 'User')),
    employee_id     INT             NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ─── 4. Sensor Readings ──────────────────────────────────
CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id      INT             PRIMARY KEY AUTO_INCREMENT,
    machine_id      INT             NOT NULL,
    timestamp       DATETIME        NOT NULL,
    temperature     DECIMAL(6,2)    NOT NULL CHECK (temperature >= 0),
    vibration       DECIMAL(6,2)    NOT NULL CHECK (vibration >= 0),
    pressure        DECIMAL(7,2)    NOT NULL CHECK (pressure >= 0),
    motor_current   DECIMAL(6,2)    NOT NULL CHECK (motor_current >= 0),
    oil_level       DECIMAL(5,2)    NOT NULL CHECK (oil_level >= 0 AND oil_level <= 100),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── 5. Production Logs ──────────────────────────────────
CREATE TABLE IF NOT EXISTS production_logs (
    log_id          INT             PRIMARY KEY AUTO_INCREMENT,
    machine_id      INT             NOT NULL,
    date            DATE            NOT NULL,
    bundles_produced INT            NOT NULL CHECK (bundles_produced >= 0),
    raw_material_kg DECIMAL(8,2)    NOT NULL CHECK (raw_material_kg >= 0),
    operating_hours DECIMAL(4,1)    NOT NULL CHECK (operating_hours >= 0 AND operating_hours <= 24),
    efficiency      DECIMAL(5,2)    NOT NULL CHECK (efficiency >= 0 AND efficiency <= 100),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── 6. Fault Logs ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS fault_logs (
    fault_id        INT             PRIMARY KEY AUTO_INCREMENT,
    machine_id      INT             NOT NULL,
    reported_by     INT             NOT NULL,
    timestamp       DATETIME        NOT NULL,
    fault_type      VARCHAR(50)     NOT NULL,
    severity        VARCHAR(10)     NOT NULL
                                    CHECK (severity IN ('Low', 'Medium', 'High')),
    description     TEXT,
    resolved        TINYINT(1)      NOT NULL DEFAULT 0
                                    CHECK (resolved IN (0, 1)),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (reported_by) REFERENCES employees(employee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ─── 7. Maintenance Logs ─────────────────────────────────
CREATE TABLE IF NOT EXISTS maintenance_logs (
    maintenance_id  INT             PRIMARY KEY AUTO_INCREMENT,
    machine_id      INT             NOT NULL,
    performed_by    INT             NOT NULL,
    date            DATE            NOT NULL,
    type            VARCHAR(20)     NOT NULL
                                    CHECK (type IN ('Preventive', 'Corrective', 'Predictive', 'Emergency')),
    duration_hours  DECIMAL(4,1)    NOT NULL CHECK (duration_hours > 0),
    description     TEXT,
    parts_replaced  VARCHAR(100),
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES employees(employee_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ─── 8. Alerts ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    alert_id        INT             PRIMARY KEY AUTO_INCREMENT,
    fault_id        INT,
    machine_id      INT             NOT NULL,
    timestamp       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity        VARCHAR(10)     NOT NULL
                                    CHECK (severity IN ('Low', 'Medium', 'High')),
    message         TEXT            NOT NULL,
    acknowledged    TINYINT(1)      NOT NULL DEFAULT 0
                                    CHECK (acknowledged IN (0, 1)),
    FOREIGN KEY (fault_id) REFERENCES fault_logs(fault_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ─── INDEXES ─────────────────────────────────────────────
CREATE INDEX idx_sensor_machine_ts ON sensor_readings(machine_id, timestamp);
CREATE INDEX idx_sensor_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_production_machine_date ON production_logs(machine_id, date);
CREATE INDEX idx_fault_machine ON fault_logs(machine_id);
CREATE INDEX idx_fault_severity ON fault_logs(severity);
CREATE INDEX idx_maintenance_machine ON maintenance_logs(machine_id);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp);

-- ─── TRIGGER: Auto-insert alert on High severity fault ──
DELIMITER //
CREATE TRIGGER after_fault_high_severity
AFTER INSERT ON fault_logs
FOR EACH ROW
BEGIN
    IF NEW.severity = 'High' THEN
        INSERT INTO alerts (fault_id, machine_id, timestamp, severity, message, acknowledged)
        VALUES (
            NEW.fault_id,
            NEW.machine_id,
            NOW(),
            'High',
            CONCAT('🚨 CRITICAL ALERT: High severity fault [', NEW.fault_type,
                   '] detected on Machine #', NEW.machine_id, ' - ', NEW.description),
            0
        );
    END IF;
END //
DELIMITER ;
