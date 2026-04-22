/**
 * ScrapMachine IoT — Email Notification Service
 * Uses Nodemailer to send alert emails when high-severity faults are detected.
 *
 * Architecture:
 *   Flask Backend → HTTP POST → This Node.js Service → SMTP → Email
 *
 * For demo: Uses Ethereal (fake SMTP) so emails can be previewed without
 * real credentials. Switch to Gmail/Outlook config for production.
 */

const express = require("express");
const nodemailer = require("nodemailer");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 5001;

// ─── EMAIL CONFIGURATION ────────────────────────────────────
// Option 1: Ethereal (fake/test SMTP — preview emails at ethereal.email)
// Option 2: Gmail (uncomment and use your credentials)
// Option 3: Any custom SMTP server

require('dotenv').config();

let transporter = null;
let emailConfig = {
  alertRecipients: ["yoyokingguys1143@gmail.com"],
  fromAddress: "yoyokingguys143@gmail.com",
  fromName: "ScrapMachine IoT Alerts",
};

// Initialize transporter with actual Gmail account
async function initTransporter() {
  try {
    transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: 'yoyokingguys143@gmail.com',
        pass: process.env.GMAIL_APP_PASSWORD // Reads from .env file
      }
    });

    // Verify connection configuration
    await transporter.verify();
    
    console.log("📧 Email service initialized with Gmail (yoyokingguys143@gmail.com)");
    return true;
  } catch (err) {
    console.error("❌ Failed to connect to Gmail:");
    console.error("   Did you forget to add your App Password to the .env file?");
    console.error("   Error details:", err.message);

    // Fallback: create a "no-op" transporter that logs instead
    transporter = {
      sendMail: async (options) => {
        console.log("📧 [EMAIL SIMULATION - SETUP REQUIRED] Would send to:", options.to);
        return { messageId: "simulated-" + Date.now() };
      },
    };
    return false;
  }
}

// ─── EMAIL TEMPLATES ─────────────────────────────────────────

function buildAlertEmailHTML(data) {
  const severityColor =
    data.severity === "High"
      ? "#ef4444"
      : data.severity === "Medium"
      ? "#f59e0b"
      : "#10b981";

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a0e17; color: #f1f5f9; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #1a2235, #111827); border-radius: 12px 12px 0 0; padding: 30px; text-align: center; border-bottom: 3px solid ${severityColor}; }
    .header h1 { margin: 0; font-size: 24px; color: #f1f5f9; }
    .header .icon { font-size: 48px; margin-bottom: 10px; }
    .body { background: #1a2235; padding: 30px; border-radius: 0 0 12px 12px; }
    .severity-badge { display: inline-block; padding: 6px 16px; border-radius: 50px; font-weight: 700; font-size: 14px; color: white; background: ${severityColor}; }
    .detail-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .detail-label { color: #94a3b8; font-size: 14px; }
    .detail-value { color: #f1f5f9; font-weight: 600; font-size: 14px; }
    .description { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px; margin: 20px 0; color: #cbd5e1; font-size: 14px; line-height: 1.6; }
    .footer { text-align: center; padding: 20px; color: #64748b; font-size: 12px; }
    .action-btn { display: inline-block; padding: 12px 30px; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="icon">🚨</div>
      <h1>ScrapMachine IoT Alert</h1>
    </div>
    <div class="body">
      <div style="text-align: center; margin-bottom: 20px;">
        <span class="severity-badge">${data.severity} SEVERITY</span>
      </div>

      <div class="detail-row">
        <span class="detail-label">Machine</span>
        <span class="detail-value">${data.machine_name || "Machine #" + data.machine_id}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Fault Type</span>
        <span class="detail-value">${data.fault_type}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Location</span>
        <span class="detail-value">${data.location || "N/A"}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Reported By</span>
        <span class="detail-value">${data.reported_by_name || "System"}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Time</span>
        <span class="detail-value">${data.timestamp || new Date().toLocaleString()}</span>
      </div>

      <div class="description">
        <strong>Description:</strong><br>
        ${data.description || "No additional details provided."}
      </div>

      <div style="text-align: center;">
        <a href="http://localhost:5173" class="action-btn">Open Dashboard →</a>
      </div>
    </div>
    <div class="footer">
      ScrapMachine IoT Monitoring System — This is an automated alert notification.
    </div>
  </div>
</body>
</html>`;
}

function buildMaintenanceEmailHTML(data) {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #0a0e17; color: #f1f5f9; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #1a2235, #111827); border-radius: 12px 12px 0 0; padding: 30px; text-align: center; border-bottom: 3px solid #10b981; }
    .header h1 { margin: 0; font-size: 24px; color: #f1f5f9; }
    .body { background: #1a2235; padding: 30px; border-radius: 0 0 12px 12px; }
    .detail-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
    .detail-label { color: #94a3b8; font-size: 14px; }
    .detail-value { color: #f1f5f9; font-weight: 600; font-size: 14px; }
    .footer { text-align: center; padding: 20px; color: #64748b; font-size: 12px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div style="font-size: 48px; margin-bottom: 10px;">🔧</div>
      <h1>Maintenance Completed</h1>
    </div>
    <div class="body">
      <div class="detail-row">
        <span class="detail-label">Machine</span>
        <span class="detail-value">${data.machine_name || "Machine #" + data.machine_id}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Type</span>
        <span class="detail-value">${data.type}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Duration</span>
        <span class="detail-value">${data.duration_hours} hours</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Parts Replaced</span>
        <span class="detail-value">${data.parts_replaced || "None"}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Description</span>
        <span class="detail-value">${data.description}</span>
      </div>
    </div>
    <div class="footer">ScrapMachine IoT Monitoring System</div>
  </div>
</body>
</html>`;
}

// ─── API ROUTES ──────────────────────────────────────────────

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok", service: "ScrapMachine Email Service" });
});

// Send alert email (called by Flask when high-severity fault is reported)
app.post("/send-alert", async (req, res) => {
  try {
    const data = req.body;
    console.log(
      `\n📨 Sending alert email for ${data.severity} severity fault on Machine #${data.machine_id}...`
    );

    const html = buildAlertEmailHTML(data);
    const recipients = data.recipients || emailConfig.alertRecipients;

    const info = await transporter.sendMail({
      from: `"${emailConfig.fromName}" <${emailConfig.fromAddress}>`,
      to: recipients.join(", "),
      subject: `🚨 [${data.severity}] ScrapMachine Alert: ${data.fault_type} on Machine #${data.machine_id}`,
      html: html,
    });

    console.log(`   ✅ Email sent: ${info.messageId}`);

    // If using Ethereal, show preview URL
    const previewUrl = nodemailer.getTestMessageUrl(info);
    if (previewUrl) {
      console.log(`   🔗 Preview: ${previewUrl}`);
    }

    res.json({
      success: true,
      messageId: info.messageId,
      previewUrl: previewUrl || null,
    });
  } catch (err) {
    console.error("   ❌ Email send failed:", err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// Send maintenance notification email
app.post("/send-maintenance", async (req, res) => {
  try {
    const data = req.body;
    console.log(
      `\n📨 Sending maintenance notification for Machine #${data.machine_id}...`
    );

    const html = buildMaintenanceEmailHTML(data);
    const recipients = data.recipients || emailConfig.alertRecipients;

    const info = await transporter.sendMail({
      from: `"${emailConfig.fromName}" <${emailConfig.fromAddress}>`,
      to: recipients.join(", "),
      subject: `🔧 Maintenance Completed: ${data.type} on Machine #${data.machine_id}`,
      html: html,
    });

    console.log(`   ✅ Email sent: ${info.messageId}`);
    const previewUrl = nodemailer.getTestMessageUrl(info);
    if (previewUrl) {
      console.log(`   🔗 Preview: ${previewUrl}`);
    }

    res.json({
      success: true,
      messageId: info.messageId,
      previewUrl: previewUrl || null,
    });
  } catch (err) {
    console.error("   ❌ Email send failed:", err.message);
    res.status(500).json({ success: false, error: err.message });
  }
});

// Send custom email
app.post("/send-custom", async (req, res) => {
  try {
    const { to, subject, body } = req.body;

    const info = await transporter.sendMail({
      from: `"${emailConfig.fromName}" <${emailConfig.fromAddress}>`,
      to: to,
      subject: subject,
      html: `<div style="font-family: Arial; padding: 20px; background: #1a2235; color: #f1f5f9; border-radius: 12px;">${body}</div>`,
    });

    const previewUrl = nodemailer.getTestMessageUrl(info);
    res.json({ success: true, messageId: info.messageId, previewUrl });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// ─── START SERVER ────────────────────────────────────────────
async function start() {
  await initTransporter();
  app.listen(PORT, () => {
    console.log(
      `\n🚀 Email service running on http://localhost:${PORT}`
    );
    console.log("   Endpoints:");
    console.log("     POST /send-alert       — Send fault alert email");
    console.log("     POST /send-maintenance — Send maintenance notification");
    console.log("     POST /send-custom      — Send custom email");
    console.log("     GET  /health           — Health check\n");
  });
}

start();
