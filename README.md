# 🏭 Data Driven Digital Transformation of IoT Enabled Scrap Bundle Making Machine

A full-stack IoT monitoring system for scrap bundle making machines with real-time sensor data, MQTT communication, predictive analytics, and role-based dashboards.

## 📋 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Styling | Vanilla CSS (Dark Industrial Theme) |
| Backend | Flask REST API |
| Database | MySQL |
| IoT Protocol | MQTT (Mosquitto + paho-mqtt) |
| Analytics | scikit-learn (Logistic Regression) |
| Auth | JWT (JSON Web Tokens) |

## 📁 Project Structure

```
ScrapMachine_Project/
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── schema.sql              # Database schema (3NF)
│   ├── queries.sql             # SQL queries (joins, views, etc.)
│   ├── seed_database.py        # Seed DB from CSV files
│   ├── mqtt_publisher.py       # MQTT sensor data publisher
│   ├── mqtt_subscriber.py      # MQTT subscriber → MySQL
│   ├── routes/                 # API route blueprints
│   ├── models/                 # Database connection
│   └── services/               # Analytics service
├── frontend/
│   ├── src/
│   │   ├── api/                # API client
│   │   ├── components/         # Reusable UI components
│   │   ├── context/            # Auth context
│   │   └── pages/              # Dashboard pages
│   └── index.html
├── dataset/
│   ├── generate_dataset.py     # Generate all CSV files
│   └── *.csv                   # Generated datasets
└── README.md
```

## 🚀 Step-by-Step Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Mosquitto MQTT Broker (for MQTT demo)

---

### Step 1: Generate Dataset

```bash
cd dataset
python generate_dataset.py
```

This creates 8 CSV files:
- `machines.csv` (8 records)
- `employees.csv` (15 records)
- `users.csv` (10 records)
- `sensor_readings.csv` (17,000+ records)
- `production_logs.csv` (500+ records)
- `fault_logs.csv` (60 records)
- `maintenance_logs.csv` (45 records)
- `alerts.csv` (auto-generated from high-severity faults)

---

### Step 2: MySQL Setup

1. Start MySQL server
2. Run the schema:

```bash
mysql -u root -p < backend/schema.sql
```

Or in MySQL client:
```sql
source backend/schema.sql;
```

> **Note**: Update credentials in `backend/models/database.py` and `backend/seed_database.py` if not using `root`/`password`.

---

### Step 3: Seed Database

```bash
cd backend
pip install -r requirements.txt
python seed_database.py
```

---

### Step 4: Run MQTT Broker (Optional - for CNDC demo)

#### Install Mosquitto
- **Windows**: Download from https://mosquitto.org/download/
- **macOS**: `brew install mosquitto`
- **Linux**: `sudo apt install mosquitto mosquitto-clients`

#### Start broker:
```bash
mosquitto -v
```

#### Terminal 1 - Start Subscriber:
```bash
cd backend
python mqtt_subscriber.py
```

#### Terminal 2 - Start Publisher:
```bash
cd backend
python mqtt_publisher.py
```

The publisher reads sensor_readings.csv and publishes via MQTT.
The subscriber consumes messages and inserts into MySQL.

---

### Step 5: Run Flask Backend

```bash
cd backend
python app.py
```

API runs at: **http://localhost:5000**

Health check: `GET http://localhost:5000/api/health`

---

### Step 6: Run React Frontend

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
| Admin | `admin` | `admin123` |
| User | `suresh.singh` | `user123` |

---

## 📊 Features

### Admin Dashboard
- System overview with KPI stats
- Machine CRUD management
- Employee CRUD management
- Sensor data visualization
- Production log tracking
- Fault log management & resolution
- Maintenance records
- **In-app alert notification center**
- Analytics: MTBF, MTTR, Downtime, ML Failure Prediction

### User Dashboard
- View sensor readings & charts
- View production logs
- **Report faults** (High severity auto-triggers alerts)
- **Log maintenance activities**
- View & acknowledge alert messages

---

## 🗄️ Database Design (3NF)

### Normalization
- **1NF**: Atomic values, no repeating groups
- **2NF**: No partial dependencies (single-column PKs)
- **3NF**: No transitive dependencies (employee info in `employees`, not duplicated)

### Trigger
When a fault with `severity = 'High'` is inserted, a trigger automatically creates an alert in the `alerts` table.

---

## 🌐 CNDC - Network Architecture

### Data Flow
```
Sensor → mqtt_publisher.py → Mosquitto Broker → mqtt_subscriber.py → MySQL → Flask API → React Dashboard
```

### Protocol Comparison

| Protocol | Use Case | Selected |
|----------|----------|----------|
| MQTT | Sensor telemetry (lightweight pub/sub) | ✅ |
| HTTP | REST API (request-response) | ✅ |
| UDP | Real-time streams (no guarantee) | ❌ |
| Modbus | Industrial SCADA (complex) | ❌ |

---

## 📈 Analytics

- **MTBF** = Total Operating Hours / Number of Failures
- **MTTR** = Total Repair Hours / Number of Repairs
- **Downtime** = Sum of maintenance duration per machine
- **Failure Prediction** = Logistic Regression on sensor features (temperature, vibration, pressure, motor current, oil level)

---

## 🛠️ API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/login` | POST | ❌ | JWT Login |
| `/api/machines` | GET/POST | ✅ | Machine CRUD |
| `/api/employees` | GET/POST | ✅ | Employee CRUD |
| `/api/sensors` | GET | ✅ | Sensor readings |
| `/api/production` | GET/POST | ✅ | Production logs |
| `/api/faults` | GET/POST | ✅ | Fault reports |
| `/api/maintenance` | GET/POST | ✅ | Maintenance logs |
| `/api/alerts` | GET | ✅ | Alert messages |
| `/api/analytics/*` | GET | ✅ | MTBF/MTTR/Predict |
