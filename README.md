# 🏭 Data Driven Digital Transformation of IoT Enabled Scrap Bundle Making Machine

A full-stack IoT monitoring system for scrap bundle making machines featuring real-time sensor telemetry, predictive analytics, and a modern **Neo-Brutalist** role-based dashboard.

## 📋 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Styling | Vanilla CSS (Neo-Brutalist Design: High contrast, Space Grotesk/DM Sans) |
| Backend | Flask REST API |
| Database | SQLite (Primary, 10-Table Normalized Schema) / MySQL (Fallback) |
| IoT Sensors | Load Cell (HX711) for weight, Proximity Sensors, Temperature, Vibration, etc. |
| Protocol | MQTT (Mosquitto + paho-mqtt) |
| Analytics | scikit-learn (Logistic Regression, Decision Boundaries, Feature Importance) |
| Auth | JWT (JSON Web Tokens) |

## 📁 Project Structure

```
ScrapMachine_Project/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── models/                 # Database connection & SQLite init (database.py)
│   ├── routes/                 # API route blueprints
│   ├── services/               # Analytics service (ML predictions & plots)
│   ├── mqtt_publisher.py       # MQTT sensor data publisher (Load cell, proximity, etc.)
│   ├── mqtt_subscriber.py      # MQTT subscriber → SQLite/MySQL
│   └── scrap_machine.db        # Auto-generated SQLite Database
├── frontend/
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # Neo-Brutalist UI components
│   │   ├── context/            # Auth context
│   │   └── pages/              # Dashboard pages & charts
│   └── index.html
├── dataset/
│   └── *.csv                   # Datasets (Machine, Operator, Sensor, etc.)
└── README.md
```

## 🚀 Step-by-Step Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Mosquitto MQTT Broker (for local MQTT testing)

---

### Step 1: Initialize Database (SQLite by default)

The project uses a lightweight SQLite database out-of-the-box via the `.env` file (`USE_SQLITE=true`).

```bash
cd backend
pip install -r requirements.txt
python models/database.py
```
*(This initializes and seeds `scrap_machine.db` from the CSV datasets in the `dataset/` directory.)*

> **Note on MySQL**: If you prefer MySQL, set `USE_SQLITE=false` in `backend/.env`, import `schema.sql`, and run `python seed_database.py`.

---

### Step 2: Run MQTT Broker (Optional - for IoT telemetry)

#### Install Mosquitto
- **Windows**: Download from https://mosquitto.org/download/
- **macOS**: `brew install mosquitto`
- **Linux**: `sudo apt install mosquitto mosquitto-clients`

#### Start broker:
```bash
mosquitto -v
```

#### Start Telemetry Simulation:
Terminal 1 - Start Subscriber (listens to Mosquitto and saves to DB):
```bash
cd backend
python mqtt_subscriber.py
```

Terminal 2 - Start Publisher (publishes Load cell/Proximity and other sensor data):
```bash
cd backend
python mqtt_publisher.py
```

---

### Step 3: Run Flask Backend

```bash
cd backend
python app.py
```

API runs at: **http://localhost:5000**
Health check: `GET http://localhost:5000/api/health`

---

### Step 4: Run React Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## 🔐 Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `password` |

*(Check `dataset/users.csv` or the `users` table for other role accounts)*

---

## 📊 Features

### Neo-Brutalist UI Overhaul
- **Aesthetic**: High-contrast vibrant colors (Yellow `#ffe17c`, Charcoal `#171e19`, Sage `#b7c6c2`).
- **Styling**: Distinct 2px solid black borders, hard drop shadows, and engaging micro-interactions (physical press button effects).
- **Typography**: Clean, geometric UI utilizing Space Grotesk and DM Sans.

### Admin Dashboard
- System overview with live KPI stats (bundles produced, scrap received, alerts).
- **Predictive Analytics**: Integrated visual assets showing Decision Boundary graphs and Feature Importance charts for machine failure modeling.
- Real-time Load Cell (HX711) weight monitoring and Proximity Scrap Detection status.
- Machine & Operator CRUD management.
- Fault log management & resolution tracking.

### User Dashboard
- View live sensor readings & dynamic charts.
- Track production logs.
- Report faults & view maintenance activities.

---

## 🗄️ Database Design (Normalized 3NF)

The system utilizes a comprehensive 10-table normalized schema encompassing:
1. `machines`
2. `operators`
3. `users`
4. `sensors`
5. `sensor_data`
6. `production_logs`
7. `maintenance_logs`
8. `alerts`
9. `scrap_materials`
10. `bundles`

---

## 🌐 IoT Architecture

```
Sensors (Load Cell, Proximity, Temp) → mqtt_publisher.py → Mosquitto Broker → mqtt_subscriber.py → SQLite/MySQL → Flask API → React Dashboard
```

---

## 📈 Analytics & Machine Learning

- **Downtime / MTBF / MTTR**: Calculated via `analytics_service.py` based on `maintenance_logs` and `production_logs`.
- **Failure Prediction**: Scikit-Learn Logistic Regression evaluates live sensor features.
- **Visualizations**: Auto-generated Decision Boundary and Feature Importance graphs saved to `frontend/public/assets/` to help interpret model predictions natively within the dashboard.
