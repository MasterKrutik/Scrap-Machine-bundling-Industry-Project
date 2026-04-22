"""
Send Machine Assignment & Bay Report email via Nodemailer service.
"""
import sqlite3
import requests

DB_PATH = "C:/Users/Admin/OneDrive/Desktop/ScrapMachine_Project/backend/scrap_machine.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get machines
cursor.execute("SELECT machine_id, name, type, location, status, max_capacity_tons FROM machines ORDER BY machine_id")
machines = [dict(r) for r in cursor.fetchall()]

# Get operators
cursor.execute("SELECT employee_id, first_name, last_name, role, department, shift, phone FROM employees WHERE role = 'Operator' ORDER BY employee_id")
operators = [dict(r) for r in cursor.fetchall()]

# Get latest sensor stats per machine
cursor.execute("""
    SELECT m.machine_id, m.name,
           ROUND(AVG(sr.temperature), 1) AS avg_temp,
           ROUND(AVG(sr.vibration), 1) AS avg_vib,
           ROUND(AVG(sr.pressure), 1) AS avg_press,
           ROUND(AVG(sr.bundle_weight), 1) AS avg_weight,
           SUM(sr.proximity) AS scrap_detections
    FROM sensor_readings sr
    JOIN machines m ON sr.machine_id = m.machine_id
    GROUP BY m.machine_id
""")
sensor_stats = {r["machine_id"]: dict(r) for r in cursor.fetchall()}

conn.close()

# Build HTML email
status_colors = {"Running": "#10b981", "Idle": "#3b82f6", "Maintenance": "#f59e0b", "Fault": "#ef4444"}

html = """
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; background: #f8fafc; padding: 20px;">
  <div style="background: linear-gradient(135deg, #2563eb, #6366f1); color: white; padding: 30px; border-radius: 16px 16px 0 0; text-align: center;">
    <h1 style="margin: 0; font-size: 28px;">🏭 ScrapMachine IoT</h1>
    <p style="margin: 8px 0 0; opacity: 0.9; font-size: 16px;">Machine Assignments & Bay Locations Report</p>
  </div>
  
  <div style="background: white; padding: 30px; border-radius: 0 0 16px 16px; border: 1px solid #e2e8f0;">
    <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📋 Machine-Employee Assignments</h2>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr style="background: #f1f5f9;">
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Machine</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Type</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Bay / Location</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Status</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Capacity</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Assigned Operator</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Shift</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Phone</th>
      </tr>
"""

for i, m in enumerate(machines):
    op = operators[i % len(operators)] if operators else {}
    status_color = status_colors.get(m["status"], "#64748b")
    html += f"""
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 12px; font-weight: 600; color: #0f172a;">{m['name']}</td>
        <td style="padding: 12px; color: #475569;">{m['type']}</td>
        <td style="padding: 12px;"><span style="background: #eff6ff; color: #2563eb; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 13px;">{m['location']}</span></td>
        <td style="padding: 12px;"><span style="background: {status_color}22; color: {status_color}; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 13px;">{m['status']}</span></td>
        <td style="padding: 12px; color: #475569;">{m['max_capacity_tons']} T</td>
        <td style="padding: 12px; font-weight: 600; color: #0f172a;">{op.get('first_name', 'N/A')} {op.get('last_name', '')}</td>
        <td style="padding: 12px; color: #475569;">{op.get('shift', 'N/A')}</td>
        <td style="padding: 12px; color: #475569;">{op.get('phone', 'N/A')}</td>
      </tr>
    """

html += """
    </table>
    
    <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-top: 30px;">📡 Latest Sensor Averages per Machine</h2>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr style="background: #f1f5f9;">
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Machine</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Avg Temp (°C)</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Avg Vibration</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Avg Pressure</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Avg Weight (kg)</th>
        <th style="padding: 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #475569; border-bottom: 2px solid #e2e8f0;">Scrap Detections</th>
      </tr>
"""

for m in machines:
    s = sensor_stats.get(m["machine_id"], {})
    html += f"""
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 12px; font-weight: 600; color: #0f172a;">{m['name']}</td>
        <td style="padding: 12px; color: #ef4444; font-weight: 600;">{s.get('avg_temp', 'N/A')}</td>
        <td style="padding: 12px; color: #f59e0b; font-weight: 600;">{s.get('avg_vib', 'N/A')}</td>
        <td style="padding: 12px; color: #3b82f6; font-weight: 600;">{s.get('avg_press', 'N/A')}</td>
        <td style="padding: 12px; color: #8b5cf6; font-weight: 600;">{s.get('avg_weight', 'N/A')} kg</td>
        <td style="padding: 12px; color: #06b6d4; font-weight: 600;">{s.get('scrap_detections', 'N/A')}</td>
      </tr>
    """

html += """
    </table>
    
    <div style="background: #f1f5f9; padding: 16px; border-radius: 12px; margin-top: 20px; text-align: center;">
      <p style="margin: 0; color: #64748b; font-size: 13px;">
        This report was automatically generated by <strong>ScrapMachine IoT Monitoring System</strong><br>
        <a href="http://localhost:5173" style="color: #2563eb; text-decoration: none;">Open Dashboard →</a>
      </p>
    </div>
  </div>
</div>
"""

# Send via Nodemailer service
payload = {
    "to": "yoyokingguys1143@gmail.com",
    "subject": "🏭 ScrapMachine IoT — Machine Assignments & Bay Locations Report",
    "body": html
}

try:
    resp = requests.post("http://localhost:5001/send-custom", json=payload, timeout=15)
    result = resp.json()
    if result.get("success"):
        print(f"✅ Email sent successfully! MessageId: {result.get('messageId')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
except Exception as e:
    print(f"❌ Could not reach email service: {e}")
