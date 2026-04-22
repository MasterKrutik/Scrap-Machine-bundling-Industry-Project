import { useState, useEffect, useCallback } from "react";
import StatsCard from "../components/StatsCard";
import DataTable from "../components/DataTable";
import AlertBanner from "../components/AlertBanner";
import { StatusPieChart, AreaChartComponent, SensorBarChart } from "../components/SensorChart";
import * as api from "../api/api";

export default function AdminDashboard({ activeTab, alertCount, setAlertCount }) {
  const [stats, setStats] = useState({});
  const [machines, setMachines] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [sensorStats, setSensorStats] = useState([]);
  const [production, setProduction] = useState([]);
  const [prodSummary, setProdSummary] = useState([]);
  const [faults, setFaults] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [mtbf, setMtbf] = useState([]);
  const [mttr, setMttr] = useState([]);
  const [downtime, setDowntime] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);
  const [showModal, setShowModal] = useState(null);
  const [formData, setFormData] = useState({});

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case "overview": {
          const [s, m, a] = await Promise.all([
            api.getDashboardStats(), api.getMachines(), api.getActiveAlerts()
          ]);
          setStats(s); setMachines(m); setAlerts(a);
          setAlertCount(a.length);
          break;
        }
        case "machines":
          setMachines(await api.getMachines());
          break;
        case "employees":
          setEmployees(await api.getEmployees());
          break;
        case "sensors": {
          const [sr, ss] = await Promise.all([api.getSensorReadings(null, 50), api.getSensorStats()]);
          setSensors(sr); setSensorStats(ss);
          break;
        }
        case "production": {
          const [p, ps] = await Promise.all([api.getProductionLogs(), api.getProductionSummary()]);
          setProduction(p); setProdSummary(ps);
          break;
        }
        case "faults":
          setFaults(await api.getFaults());
          break;
        case "maintenance":
          setMaintenance(await api.getMaintenanceLogs());
          break;
        case "alerts": {
          const a = await api.getAlerts();
          setAlerts(a);
          setAlertCount(a.filter(x => !x.acknowledged).length);
          break;
        }
        case "analytics": {
          const [mb, mt, dt, pr] = await Promise.all([
            api.getMTBF(), api.getMTTR(), api.getDowntime(), api.getFailurePrediction()
          ]);
          setMtbf(mb); setMttr(mt); setDowntime(dt); setPrediction(pr);
          break;
        }
      }
    } catch (err) { console.error(err); }
    setLoading(false);
  }, [activeTab, setAlertCount]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleAcknowledge = async (alertId) => {
    await api.acknowledgeAlert(alertId);
    loadData();
  };

  const handleDelete = async (type, id) => {
    if (!confirm("Are you sure?")) return;
    if (type === "machine") await api.deleteMachine(id);
    else if (type === "employee") await api.deleteEmployee(id);
    loadData();
  };

  const handleSubmitForm = async () => {
    try {
      if (showModal === "add-machine") await api.createMachine(formData);
      else if (showModal === "add-employee") await api.createEmployee(formData);
      setShowModal(null); setFormData({});
      loadData();
    } catch (err) { alert(err.message); }
  };

  const handleResolve = async (faultId) => {
    await api.resolveFault(faultId);
    loadData();
  };

  const handleSendReport = async () => {
    setSendingReport(true);
    try {
      const res = await api.sendAssignmentReport();
      alert("✅ " + res.message);
    } catch (err) {
      alert("❌ Failed to send report: " + err.message);
    }
    setSendingReport(false);
  };

  if (loading) return <div className="loading-spinner"><div className="spinner"></div> Loading...</div>;

  const severityBadge = (val) => {
    const cls = val === "High" ? "badge-red" : val === "Medium" ? "badge-amber" : "badge-green";
    return <span className={`badge ${cls}`}>{val}</span>;
  };

  const statusBadge = (val) => {
    const cls = val === "Running" ? "badge-green" : val === "Fault" ? "badge-red"
      : val === "Maintenance" ? "badge-amber" : "badge-blue";
    return <span className={`badge ${cls}`}>{val}</span>;
  };

  return (
    <div className="fade-in">
      {/* ── OVERVIEW ── */}
      {activeTab === "overview" && (
        <>
          <div className="page-header">
            <div><h1>Admin Dashboard</h1><p className="page-subtitle">System overview & monitoring</p></div>
            <button 
              className={`btn ${sendingReport ? "btn-outline" : "btn-primary"}`} 
              onClick={handleSendReport} 
              disabled={sendingReport}
            >
              {sendingReport ? "⏳ Sending..." : "📧 Send Report Email"}
            </button>
          </div>

          <AlertBanner alerts={alerts} onAcknowledge={handleAcknowledge} />

          <div className="stats-grid">
            <StatsCard icon="⚙️" label="Total Machines" value={stats.total_machines || 0} color="blue" />
            <StatsCard icon="✅" label="Active Machines" value={stats.active_machines || 0} color="green" />
            <StatsCard icon="👥" label="Employees" value={stats.total_employees || 0} color="purple" />
            <StatsCard icon="⚠️" label="Active Faults" value={stats.unresolved_faults || 0} color="red" />
            <StatsCard icon="🔔" label="Pending Alerts" value={stats.active_alerts || 0} color="amber" />
            <StatsCard icon="📦" label="Total Bundles" value={(stats.total_bundles || 0).toLocaleString()} color="cyan" />
            <StatsCard icon="📈" label="Avg Efficiency" value={`${stats.avg_efficiency || 0}%`} color="green" />
            <StatsCard icon="📡" label="Sensor Readings" value={(stats.total_readings || 0).toLocaleString()} color="blue" />
          </div>

          <div className="content-grid">
            <div className="card">
              <div className="card-header"><h3 className="card-title">Machine Status</h3></div>
              <StatusPieChart data={(() => {
                const counts = {};
                machines.forEach(m => { counts[m.Status] = (counts[m.Status] || 0) + 1; });
                const colorMap = { Running: "#10b981", Idle: "#3b82f6", Maintenance: "#f59e0b", Fault: "#ef4444" };
                return Object.entries(counts).map(([name, value]) => ({ name, value, color: colorMap[name] }));
              })()} />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">Machines Overview</h3></div>
              <DataTable
                columns={[
                  { key: "Machine_Name", label: "Name" },
                  { key: "Location", label: "Location" },
                  { key: "Status", label: "Status", render: statusBadge },
                ]}
                data={machines}
              />
            </div>
          </div>
        </>
      )}

      {/* ── MACHINES ── */}
      {activeTab === "machines" && (
        <>
          <div className="page-header">
            <div><h1>Machines</h1><p className="page-subtitle">Manage scrap bundle making machines</p></div>
            <button className="btn btn-primary" onClick={() => { setFormData({}); setShowModal("add-machine"); }} id="add-machine-btn">+ Add Machine</button>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "Machine_ID", label: "ID" },
                { key: "Machine_Name", label: "Name" },
                { key: "Location", label: "Location" },
                { key: "Installation_Date", label: "Install Date" },
                { key: "Status", label: "Status", render: statusBadge },
                { key: "Capacity", label: "Capacity", render: (v) => `${v}` },
                { key: "Machine_ID", label: "Actions", render: (_, row) => (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete("machine", row.Machine_ID)}>Delete</button>
                )},
              ]}
              data={machines}
            />
          </div>
        </>
      )}

      {/* ── EMPLOYEES ── */}
      {activeTab === "employees" && (
        <>
          <div className="page-header">
            <div><h1>Employees</h1><p className="page-subtitle">Manage workforce</p></div>
            <button className="btn btn-primary" onClick={() => { setFormData({}); setShowModal("add-employee"); }} id="add-employee-btn">+ Add Employee</button>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "Operator_ID", label: "ID" },
                { key: "Name", label: "Name" },
                { key: "Shift", label: "Shift" },
                { key: "Contact", label: "Phone" },
                { key: "Experience_Years", label: "Experience" },
                { key: "Operator_ID", label: "Actions", render: (_, row) => (
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete("employee", row.Operator_ID)}>Delete</button>
                )},
              ]}
              data={employees}
            />
          </div>
        </>
      )}

      {/* ── SENSORS ── */}
      {activeTab === "sensors" && (
        <>
          <div className="page-header">
            <div><h1>Sensor Data</h1><p className="page-subtitle">Real-time machine telemetry</p></div>
          </div>
          <div className="content-grid">
            <div className="card">
              <div className="card-header"><h3 className="card-title">🌡️ Avg Temperature by Machine</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_temperature }))} dataKey="value" name="Temp (°C)" color="#ef4444" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">📳 Avg Vibration by Machine</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_vibration }))} dataKey="value" name="Vibration" color="#f59e0b" />
            </div>
          </div>
          <div className="content-grid" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card">
              <div className="card-header"><h3 className="card-title">⚖️ Avg Bundle Weight by Machine (Load Cell HX711)</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_bundle_weight }))} dataKey="value" name="Weight (kg)" color="#8b5cf6" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">📡 Scrap Detections by Machine (Proximity Sensor)</h3></div>
              <SensorBarChart data={sensorStats.map(s => ({ name: s.machine_name, value: s.scrap_detections }))} dataKey="value" name="Detections" color="#06b6d4" />
            </div>
          </div>
          <div className="card" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card-header"><h3 className="card-title">Recent Readings</h3></div>
            <DataTable
              columns={[
                { key: "reading_id", label: "ID" },
                { key: "machine_id", label: "Machine" },
                { key: "timestamp", label: "Timestamp" },
                { key: "temperature", label: "Temp (°C)" },
                { key: "vibration", label: "Vibration" },
                { key: "pressure", label: "Pressure" },
                { key: "motor_current", label: "Current (A)" },
                { key: "oil_level", label: "Oil (%)" },
                { key: "bundle_weight", label: "Weight (kg)" },
                { key: "proximity", label: "Scrap", render: (v) => v ? <span className="badge badge-green">Detected</span> : <span className="badge badge-blue">None</span> },
              ]}
              data={sensors}
            />
          </div>
        </>
      )}

      {/* ── PRODUCTION ── */}
      {activeTab === "production" && (
        <>
          <div className="page-header">
            <div><h1>Production Logs</h1><p className="page-subtitle">Bundle production tracking</p></div>
          </div>
          <div className="content-grid">
            <div className="card">
              <div className="card-header"><h3 className="card-title">Total Bundles by Machine</h3></div>
              <AreaChartComponent data={prodSummary.map(s => ({ name: s.machine_name, value: s.total_bundles }))} dataKey="value" name="Bundles" color="#10b981" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">Avg Efficiency by Machine</h3></div>
              <AreaChartComponent data={prodSummary.map(s => ({ name: s.machine_name, value: s.avg_efficiency }))} dataKey="value" name="Efficiency %" color="#3b82f6" />
            </div>
          </div>
          <div className="card" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card-header"><h3 className="card-title">Production Records</h3></div>
            <DataTable
              columns={[
                { key: "log_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "date", label: "Date" },
                { key: "bundles_produced", label: "Bundles" },
                { key: "raw_material_kg", label: "Material (kg)" },
                { key: "operating_hours", label: "Hours" },
                { key: "efficiency", label: "Efficiency %", render: (v) => <span className={`badge ${v > 85 ? "badge-green" : v > 70 ? "badge-amber" : "badge-red"}`}>{v}%</span> },
              ]}
              data={production}
            />
          </div>
        </>
      )}

      {/* ── FAULTS ── */}
      {activeTab === "faults" && (
        <>
          <div className="page-header">
            <div><h1>Fault Logs</h1><p className="page-subtitle">Machine fault tracking & resolution</p></div>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "fault_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "reporter_name", label: "Reported By" },
                { key: "timestamp", label: "Time" },
                { key: "fault_type", label: "Type" },
                { key: "severity", label: "Severity", render: severityBadge },
                { key: "resolved", label: "Status", render: (v) => v ? <span className="badge badge-green">Resolved</span> : <span className="badge badge-red">Open</span> },
                { key: "fault_id", label: "Actions", render: (_, row) => !row.resolved && (
                  <button className="btn btn-success btn-sm" onClick={() => handleResolve(row.fault_id)}>Resolve</button>
                )},
              ]}
              data={faults}
            />
          </div>
        </>
      )}

      {/* ── MAINTENANCE ── */}
      {activeTab === "maintenance" && (
        <>
          <div className="page-header">
            <div><h1>Maintenance Logs</h1><p className="page-subtitle">Maintenance history & records</p></div>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "maintenance_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "technician_name", label: "Technician" },
                { key: "date", label: "Date" },
                { key: "type", label: "Type", render: (v) => <span className={`badge ${v === "Emergency" ? "badge-red" : v === "Corrective" ? "badge-amber" : "badge-green"}`}>{v}</span> },
                { key: "duration_hours", label: "Hours" },
                { key: "parts_replaced", label: "Parts" },
              ]}
              data={maintenance}
            />
          </div>
        </>
      )}

      {/* ── ALERTS ── */}
      {activeTab === "alerts" && (
        <>
          <div className="page-header">
            <div><h1>🔔 Alert Messages</h1><p className="page-subtitle">In-app notification center</p></div>
            <button className="btn btn-outline" onClick={async () => { await api.acknowledgeAllAlerts(); loadData(); }} id="ack-all-btn">Acknowledge All</button>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "alert_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "location", label: "Location" },
                { key: "severity", label: "Severity", render: severityBadge },
                { key: "message", label: "Message" },
                { key: "timestamp", label: "Time" },
                { key: "acknowledged", label: "Status", render: (v) => v ? <span className="badge badge-green">Acknowledged</span> : <span className="badge badge-red">Pending</span> },
                { key: "alert_id", label: "Action", render: (_, row) => !row.acknowledged && (
                  <button className="btn btn-primary btn-sm" onClick={() => handleAcknowledge(row.alert_id)}>Ack</button>
                )},
              ]}
              data={alerts}
            />
          </div>
        </>
      )}

      {/* ── ANALYTICS ── */}
      {activeTab === "analytics" && (
        <>
          <div className="page-header">
            <div><h1>Analytics</h1><p className="page-subtitle">MTBF, MTTR, Downtime & Failure Prediction</p></div>
          </div>

          <div className="content-grid">
            <div className="card">
              <div className="card-header"><h3 className="card-title">MTBF (Mean Time Between Failures)</h3></div>
              <AreaChartComponent data={mtbf.map(m => ({ name: m.name, value: m.mtbf || 0 }))} dataKey="value" name="MTBF (hrs)" color="#10b981" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">MTTR (Mean Time To Repair)</h3></div>
              <AreaChartComponent data={mttr.map(m => ({ name: m.name, value: m.mttr || 0 }))} dataKey="value" name="MTTR (hrs)" color="#f59e0b" />
            </div>
          </div>

          <div className="content-grid" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card">
              <div className="card-header"><h3 className="card-title">Downtime per Machine</h3></div>
              <AreaChartComponent data={downtime.map(d => ({ name: d.name, value: d.downtime_hours || 0 }))} dataKey="value" name="Downtime (hrs)" color="#ef4444" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">🤖 Failure Prediction (Logistic Regression)</h3></div>
              {prediction?.predictions ? (
                <>
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
                    Model Accuracy: <span className="badge badge-blue">{prediction.model_accuracy}%</span>
                  </p>
                  <DataTable
                    columns={[
                      { key: "machine_name", label: "Machine" },
                      { key: "failure_probability", label: "Failure Prob %", render: (v) => (
                        <span className={`badge ${v > 60 ? "badge-red" : v > 30 ? "badge-amber" : "badge-green"}`}>{v}%</span>
                      )},
                      { key: "risk_level", label: "Risk", render: severityBadge },
                    ]}
                    data={prediction.predictions}
                  />
                </>
              ) : <p style={{ color: "var(--text-muted)" }}>Loading predictions...</p>}
            </div>
          </div>

          <div className="content-grid" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card">
              <div className="card-header"><h3 className="card-title">MTBF Details</h3></div>
              <DataTable columns={[
                { key: "name", label: "Machine" },
                { key: "total_hours", label: "Total Hours" },
                { key: "total_faults", label: "Faults" },
                { key: "mtbf", label: "MTBF (hrs)" },
              ]} data={mtbf} />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">MTTR Details</h3></div>
              <DataTable columns={[
                { key: "name", label: "Machine" },
                { key: "total_repairs", label: "Repairs" },
                { key: "total_repair_hours", label: "Total Hours" },
                { key: "mttr", label: "MTTR (hrs)" },
              ]} data={mttr} />
            </div>
          </div>
        </>
      )}

      {/* ── MODALS ── */}
      {showModal === "add-machine" && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Add Machine</h2>
            <div className="form-grid">
              <div className="input-group">
                <label>Name</label>
                <input className="input" placeholder="SCM-1009" onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Type</label>
                <select className="input" onChange={e => setFormData({...formData, type: e.target.value})}>
                  <option value="">Select type</option>
                  <option>Hydraulic Press</option>
                  <option>Shearing Machine</option>
                  <option>Baling Press</option>
                  <option>Compactor</option>
                  <option>Guillotine Shear</option>
                </select>
              </div>
              <div className="input-group">
                <label>Location</label>
                <select className="input" onChange={e => setFormData({...formData, location: e.target.value})}>
                  <option value="">Select location</option>
                  <option>Bay-A</option><option>Bay-B</option><option>Bay-C</option><option>Bay-D</option>
                </select>
              </div>
              <div className="input-group">
                <label>Install Date</label>
                <input className="input" type="date" onChange={e => setFormData({...formData, install_date: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Max Capacity (Tons)</label>
                <input className="input" type="number" step="0.1" placeholder="15.0" onChange={e => setFormData({...formData, max_capacity_tons: parseFloat(e.target.value)})} />
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setShowModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmitForm} id="submit-machine-btn">Create Machine</button>
            </div>
          </div>
        </div>
      )}

      {showModal === "add-employee" && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Add Employee</h2>
            <div className="form-grid">
              <div className="input-group">
                <label>First Name</label>
                <input className="input" onChange={e => setFormData({...formData, first_name: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Last Name</label>
                <input className="input" onChange={e => setFormData({...formData, last_name: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Role</label>
                <select className="input" onChange={e => setFormData({...formData, role: e.target.value})}>
                  <option value="">Select</option>
                  <option>Operator</option><option>Technician</option><option>Supervisor</option><option>Engineer</option><option>Quality Inspector</option>
                </select>
              </div>
              <div className="input-group">
                <label>Department</label>
                <select className="input" onChange={e => setFormData({...formData, department: e.target.value})}>
                  <option value="">Select</option>
                  <option>Production</option><option>Maintenance</option><option>Quality</option><option>Operations</option>
                </select>
              </div>
              <div className="input-group">
                <label>Shift</label>
                <select className="input" onChange={e => setFormData({...formData, shift: e.target.value})}>
                  <option value="">Select</option>
                  <option>Morning</option><option>Afternoon</option><option>Night</option>
                </select>
              </div>
              <div className="input-group">
                <label>Phone</label>
                <input className="input" placeholder="9812345678" onChange={e => setFormData({...formData, phone: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Hire Date</label>
                <input className="input" type="date" onChange={e => setFormData({...formData, hire_date: e.target.value})} />
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setShowModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleSubmitForm} id="submit-employee-btn">Create Employee</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
