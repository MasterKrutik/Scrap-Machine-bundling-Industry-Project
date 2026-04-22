import sqlite3
conn = sqlite3.connect('scrap_machine.db')
print('Testing sensors query')
conn.execute("""
    SELECT s.Machine_ID as machine_id,
           ROUND(AVG(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END), 1) AS avg_temp,
           ROUND(AVG(CASE WHEN s.Sensor_Type = 'Vibration' THEN sd.Value END), 1) AS avg_vib,
           ROUND(AVG(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END), 1) AS avg_press,
           ROUND(AVG(CASE WHEN s.Sensor_Type = 'Load Cell' THEN sd.Value END), 1) AS avg_weight,
           SUM(CASE WHEN s.Sensor_Type = 'Proximity' THEN sd.Value ELSE 0 END) AS scrap_detections
    FROM sensor_data sd
    JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
    GROUP BY s.Machine_ID
""").fetchall()
print('Success!')
