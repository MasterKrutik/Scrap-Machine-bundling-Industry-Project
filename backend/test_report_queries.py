import sqlite3
conn = sqlite3.connect('scrap_machine.db')
print('Testing machines query')
conn.execute("SELECT Machine_ID as machine_id, Machine_Name as name, 'Unknown' as type, Location as location, Status as status, Capacity as max_capacity_tons FROM machines ORDER BY Machine_ID").fetchall()
print('Testing operators query')
conn.execute("SELECT Operator_ID as employee_id, Name as first_name, '' as last_name, 'Operator' as role, '' as department, Shift as shift, Contact as phone FROM operators ORDER BY Operator_ID").fetchall()
print('Testing sensors query')
conn.execute("""
    SELECT Machine_ID as machine_id,
           ROUND(AVG(CASE WHEN Sensor_Type = 'Temperature' THEN Value END), 1) AS avg_temp,
           ROUND(AVG(CASE WHEN Sensor_Type = 'Vibration' THEN Value END), 1) AS avg_vib,
           ROUND(AVG(CASE WHEN Sensor_Type = 'Pressure' THEN Value END), 1) AS avg_press,
           ROUND(AVG(CASE WHEN Sensor_Type = 'Load Cell' THEN Value END), 1) AS avg_weight,
           SUM(CASE WHEN Sensor_Type = 'Proximity' THEN Value ELSE 0 END) AS scrap_detections
    FROM sensors
    GROUP BY Machine_ID
""").fetchall()
print('All queries successful!')
