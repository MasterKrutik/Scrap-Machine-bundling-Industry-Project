-- ============================================================
-- Scrap Bundle Making Machine - SQL Queries
-- Demonstrates: JOINs, Nested Queries, GROUP BY, Aggregation,
--               Views, Indexes, MTBF/MTTR Calculations
-- ============================================================

USE scrap_machine_db;

-- ─────────────────────────────────────────────────────────────
-- 1. JOIN: Get all fault logs with machine and employee details
-- ─────────────────────────────────────────────────────────────
SELECT
    f.fault_id,
    m.name AS machine_name,
    m.type AS machine_type,
    m.location,
    CONCAT(e.first_name, ' ', e.last_name) AS reported_by_name,
    f.fault_type,
    f.severity,
    f.timestamp,
    f.resolved
FROM fault_logs f
JOIN machines m ON f.machine_id = m.machine_id
JOIN employees e ON f.reported_by = e.employee_id
ORDER BY f.timestamp DESC;

-- ─────────────────────────────────────────────────────────────
-- 2. JOIN: Maintenance records with machine and technician info
-- ─────────────────────────────────────────────────────────────
SELECT
    ml.maintenance_id,
    m.name AS machine_name,
    CONCAT(e.first_name, ' ', e.last_name) AS technician,
    ml.type AS maintenance_type,
    ml.date,
    ml.duration_hours,
    ml.parts_replaced
FROM maintenance_logs ml
JOIN machines m ON ml.machine_id = m.machine_id
JOIN employees e ON ml.performed_by = e.employee_id
ORDER BY ml.date DESC;

-- ─────────────────────────────────────────────────────────────
-- 3. GROUP BY + Aggregation: Fault count by severity per machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    f.severity,
    COUNT(*) AS fault_count
FROM fault_logs f
JOIN machines m ON f.machine_id = m.machine_id
GROUP BY m.name, f.severity
ORDER BY m.name, FIELD(f.severity, 'High', 'Medium', 'Low');

-- ─────────────────────────────────────────────────────────────
-- 4. GROUP BY + Aggregation: Average sensor readings per machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    ROUND(AVG(sr.temperature), 2) AS avg_temperature,
    ROUND(AVG(sr.vibration), 2) AS avg_vibration,
    ROUND(AVG(sr.pressure), 2) AS avg_pressure,
    ROUND(AVG(sr.motor_current), 2) AS avg_motor_current,
    ROUND(AVG(sr.oil_level), 2) AS avg_oil_level,
    COUNT(*) AS total_readings
FROM sensor_readings sr
JOIN machines m ON sr.machine_id = m.machine_id
GROUP BY m.name;

-- ─────────────────────────────────────────────────────────────
-- 5. Nested Query: Machines with above-average fault count
-- ─────────────────────────────────────────────────────────────
SELECT m.name, m.type, m.location, fault_summary.fault_count
FROM machines m
JOIN (
    SELECT machine_id, COUNT(*) AS fault_count
    FROM fault_logs
    GROUP BY machine_id
) fault_summary ON m.machine_id = fault_summary.machine_id
WHERE fault_summary.fault_count > (
    SELECT AVG(fc)
    FROM (
        SELECT COUNT(*) AS fc
        FROM fault_logs
        GROUP BY machine_id
    ) avg_faults
);

-- ─────────────────────────────────────────────────────────────
-- 6. Nested Query: Employees who reported HIGH severity faults
-- ─────────────────────────────────────────────────────────────
SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    e.role,
    e.department
FROM employees e
WHERE e.employee_id IN (
    SELECT DISTINCT reported_by
    FROM fault_logs
    WHERE severity = 'High'
);

-- ─────────────────────────────────────────────────────────────
-- 7. Aggregation: Total production per machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    SUM(pl.bundles_produced) AS total_bundles,
    ROUND(SUM(pl.raw_material_kg), 2) AS total_raw_material_kg,
    ROUND(SUM(pl.operating_hours), 1) AS total_operating_hours,
    ROUND(AVG(pl.efficiency), 2) AS avg_efficiency
FROM production_logs pl
JOIN machines m ON pl.machine_id = m.machine_id
GROUP BY m.name
ORDER BY total_bundles DESC;

-- ─────────────────────────────────────────────────────────────
-- 8. Aggregation: Monthly production summary
-- ─────────────────────────────────────────────────────────────
SELECT
    DATE_FORMAT(date, '%Y-%m') AS month,
    COUNT(DISTINCT machine_id) AS active_machines,
    SUM(bundles_produced) AS total_bundles,
    ROUND(AVG(efficiency), 2) AS avg_efficiency,
    ROUND(SUM(operating_hours), 1) AS total_hours
FROM production_logs
GROUP BY DATE_FORMAT(date, '%Y-%m')
ORDER BY month;

-- ─────────────────────────────────────────────────────────────
-- 9. MTBF Calculation (Mean Time Between Failures)
--    MTBF = Total Operating Hours / Number of Failures per machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    ROUND(COALESCE(SUM(pl.operating_hours), 0), 1) AS total_operating_hours,
    COALESCE(fc.fault_count, 0) AS total_faults,
    CASE
        WHEN COALESCE(fc.fault_count, 0) > 0
        THEN ROUND(SUM(pl.operating_hours) / fc.fault_count, 2)
        ELSE NULL
    END AS mtbf_hours
FROM machines m
LEFT JOIN production_logs pl ON m.machine_id = pl.machine_id
LEFT JOIN (
    SELECT machine_id, COUNT(*) AS fault_count
    FROM fault_logs
    GROUP BY machine_id
) fc ON m.machine_id = fc.machine_id
GROUP BY m.machine_id, m.name, fc.fault_count
ORDER BY mtbf_hours;

-- ─────────────────────────────────────────────────────────────
-- 10. MTTR Calculation (Mean Time To Repair)
--     MTTR = Total Maintenance Duration / Number of Repairs per machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    COUNT(ml.maintenance_id) AS total_repairs,
    ROUND(SUM(ml.duration_hours), 1) AS total_repair_hours,
    ROUND(AVG(ml.duration_hours), 2) AS mttr_hours
FROM machines m
LEFT JOIN maintenance_logs ml ON m.machine_id = ml.machine_id
GROUP BY m.machine_id, m.name
ORDER BY mttr_hours DESC;

-- ─────────────────────────────────────────────────────────────
-- 11. Downtime per Machine
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name AS machine_name,
    ROUND(COALESCE(SUM(ml.duration_hours), 0), 1) AS total_downtime_hours,
    COALESCE(COUNT(ml.maintenance_id), 0) AS maintenance_events,
    COALESCE(fc.fault_count, 0) AS fault_events
FROM machines m
LEFT JOIN maintenance_logs ml ON m.machine_id = ml.machine_id
LEFT JOIN (
    SELECT machine_id, COUNT(*) AS fault_count
    FROM fault_logs
    GROUP BY machine_id
) fc ON m.machine_id = fc.machine_id
GROUP BY m.machine_id, m.name, fc.fault_count
ORDER BY total_downtime_hours DESC;

-- ─────────────────────────────────────────────────────────────
-- 12. VIEW: Machine Health Summary
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_machine_health AS
SELECT
    m.machine_id,
    m.name,
    m.type,
    m.status,
    ROUND(AVG(sr.temperature), 2) AS avg_temp,
    ROUND(AVG(sr.vibration), 2) AS avg_vibration,
    ROUND(AVG(sr.pressure), 2) AS avg_pressure,
    COALESCE(fc.fault_count, 0) AS total_faults,
    COALESCE(fc.high_faults, 0) AS high_severity_faults
FROM machines m
LEFT JOIN sensor_readings sr ON m.machine_id = sr.machine_id
LEFT JOIN (
    SELECT
        machine_id,
        COUNT(*) AS fault_count,
        SUM(CASE WHEN severity = 'High' THEN 1 ELSE 0 END) AS high_faults
    FROM fault_logs
    GROUP BY machine_id
) fc ON m.machine_id = fc.machine_id
GROUP BY m.machine_id, m.name, m.type, m.status, fc.fault_count, fc.high_faults;

-- ─────────────────────────────────────────────────────────────
-- 13. VIEW: Unacknowledged Alerts
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_active_alerts AS
SELECT
    a.alert_id,
    a.severity,
    a.message,
    a.timestamp,
    m.name AS machine_name,
    m.location
FROM alerts a
JOIN machines m ON a.machine_id = m.machine_id
WHERE a.acknowledged = 0
ORDER BY a.timestamp DESC;

-- ─────────────────────────────────────────────────────────────
-- 14. VIEW: Daily Production Dashboard
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW v_daily_production AS
SELECT
    pl.date,
    m.name AS machine_name,
    pl.bundles_produced,
    pl.operating_hours,
    pl.efficiency,
    pl.raw_material_kg
FROM production_logs pl
JOIN machines m ON pl.machine_id = m.machine_id
ORDER BY pl.date DESC, m.name;

-- ─────────────────────────────────────────────────────────────
-- 15. Complex: Top-performing machines by efficiency with fault ratio
-- ─────────────────────────────────────────────────────────────
SELECT
    m.name,
    ROUND(AVG(pl.efficiency), 2) AS avg_efficiency,
    COALESCE(fc.fault_count, 0) AS faults,
    ROUND(COALESCE(fc.fault_count, 0) * 100.0 /
          NULLIF(COUNT(pl.log_id), 0), 2) AS fault_to_production_ratio
FROM machines m
LEFT JOIN production_logs pl ON m.machine_id = pl.machine_id
LEFT JOIN (
    SELECT machine_id, COUNT(*) AS fault_count
    FROM fault_logs
    GROUP BY machine_id
) fc ON m.machine_id = fc.machine_id
GROUP BY m.machine_id, m.name, fc.fault_count
ORDER BY avg_efficiency DESC;
