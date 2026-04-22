"""
Reports routes.
To send manual/scheduled reports via the Nodemailer email service.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models.database import execute_query
import requests as http_req
import threading

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/api/reports/send-assignments", methods=["POST"])
@jwt_required()
def send_assignment_report():
    claims = get_jwt()
    if claims.get("role") != "Admin":
        return jsonify({"error": "Admin access required"}), 403

    def _send_report():
        try:
            # 1. Fetch data
            machines = execute_query("SELECT Machine_ID as machine_id, Machine_Name as name, 'Unknown' as type, Location as location, Status as status, Capacity as max_capacity_tons FROM machines ORDER BY Machine_ID")
            
            operators = execute_query("SELECT Operator_ID as employee_id, Name as first_name, '' as last_name, 'Operator' as role, '' as department, Shift as shift, Contact as phone FROM operators ORDER BY Operator_ID")

            # Get latest sensor averages per machine (Using new sensors table which is long-format)
            # We must pivot the long format for the report.
            sensor_data = execute_query("""
                SELECT s.Machine_ID as machine_id,
                       ROUND(AVG(CASE WHEN s.Sensor_Type = 'Temperature' THEN sd.Value END), 1) AS avg_temp,
                       ROUND(AVG(CASE WHEN s.Sensor_Type = 'Vibration' THEN sd.Value END), 1) AS avg_vib,
                       ROUND(AVG(CASE WHEN s.Sensor_Type = 'Pressure' THEN sd.Value END), 1) AS avg_press,
                       ROUND(AVG(CASE WHEN s.Sensor_Type = 'Load Cell' THEN sd.Value END), 1) AS avg_weight,
                       SUM(CASE WHEN s.Sensor_Type = 'Proximity' THEN sd.Value ELSE 0 END) AS scrap_detections
                FROM sensor_data sd
                JOIN sensors s ON sd.Sensor_ID = s.Sensor_ID
                GROUP BY s.Machine_ID
            """)
            sensor_stats = {r["machine_id"]: r for r in sensor_data}

            # 2. Build HTML
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
                op_name = f"{op.get('first_name', 'N/A')} {op.get('last_name', '')}".strip()
                if not op_name: op_name = "N/A"
                
                html += f"""
                  <tr style="border-bottom: 1px solid #f1f5f9;">
                    <td style="padding: 12px; font-weight: 600; color: #0f172a;">{m['name']}</td>
                    <td style="padding: 12px; color: #475569;">{m['type']}</td>
                    <td style="padding: 12px;"><span style="background: #eff6ff; color: #2563eb; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 13px;">{m['location']}</span></td>
                    <td style="padding: 12px;"><span style="background: {status_color}22; color: {status_color}; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 13px;">{m['status']}</span></td>
                    <td style="padding: 12px; color: #475569;">{m['max_capacity_tons']} T</td>
                    <td style="padding: 12px; font-weight: 600; color: #0f172a;">{op_name}</td>
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
                    This report was initiated from the Dashboard by <strong>{}</strong><br>
                    <a href="http://localhost:5173" style="color: #2563eb; text-decoration: none;">Open Dashboard →</a>
                  </p>
                </div>
              </div>
            </div>
            """.format(claims.get("full_name", "Admin"))

            # 3. Hand off to Node Email Microservice
            payload = {
                "to": "yoyokingguys1143@gmail.com",
                "subject": "🏭 ScrapMachine IoT — Generated Bay & Operator Report",
                "body": html
            }
            
            resp = http_req.post("http://localhost:5001/send-custom", json=payload, timeout=10)
            if resp.ok:
                print(f"📧 Admin initiated report sent via Nodemailer.")
            else:
                print(f"❌ Failed to reach Nodemailer: {resp.text}")

        except Exception as e:
            print(f"❌ Report email thread failed: {str(e)}")

    # Fire off immediately in background thread so UI doesn't hang
    threading.Thread(target=_send_report, daemon=True).start()

    return jsonify({"message": "Assignment report triggered. It will be delivered to yoyokingguys143@gmail.com shortly."}), 200
