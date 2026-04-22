import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import StatsCard from "../components/StatsCard";
import DataTable from "../components/DataTable";
import AlertBanner from "../components/AlertBanner";
import { AreaChartComponent, SensorBarChart } from "../components/SensorChart";
import * as api from "../api/api";

export default function UserDashboard({ activeTab, alertCount, setAlertCount }) {
  const { user } = useAuth();
  const [sensors, setSensors] = useState([]);
  const [sensorStats, setSensorStats] = useState([]);
  const [machines, setMachines] = useState([]);
  const [production, setProduction] = useState([]);
  const [faults, setFaults] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(null);
  const [formData, setFormData] = useState({});

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case "overview": {
          const [s, a, m] = await Promise.all([
            api.getDashboardStats(), api.getActiveAlerts(), api.getMachines()
          ]);
          setStats(s); setAlerts(a); setMachines(m);
          setAlertCount(a.length);
          break;
        }
        case "sensors": {
          const [sr, ss] = await Promise.all([api.getSensorReadings(null, 50), api.getSensorStats()]);
          setSensors(sr); setSensorStats(ss);
          break;
        }
        case "production":
          setProduction(await api.getProductionLogs());
          break;
        case "faults": {
          const [f, m] = await Promise.all([api.getFaults(), api.getMachines()]);
          setFaults(f); setMachines(m);
          break;
        }
        case "maintenance": {
          const [ml, m] = await Promise.all([api.getMaintenanceLogs(), api.getMachines()]);
          setMaintenance(ml); setMachines(m);
          break;
        }
        case "alerts": {
          const a = await api.getAlerts();
          setAlerts(a);
          setAlertCount(a.filter(x => !x.acknowledged).length);
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

  const handleSubmitFault = async () => {
    try {
      await api.createFault({ ...formData, reported_by: user.employee_id });
      setShowModal(null); setFormData({}); loadData();
    } catch (err) { alert(err.message); }
  };

  const handleSubmitMaintenance = async () => {
    try {
      await api.createMaintenanceLog({ ...formData, performed_by: user.employee_id });
      setShowModal(null); setFormData({}); loadData();
    } catch (err) { alert(err.message); }
  };

  const severityBadge = (val) => {
    const cls = val === "High" ? "badge-red" : val === "Medium" ? "badge-amber" : "badge-green";
    return <span className={`badge ${cls}`}>{val}</span>;
  };

  if (loading) return <div className="loading-spinner"><div className="spinner"></div> Loading...</div>;

  return (
    <div className="fade-in">
      {/* ── OVERVIEW ── */}
      {activeTab === "overview" && (
        <>
          <div className="page-header">
            <div><h1>Welcome, {user?.full_name}</h1><p className="page-subtitle">User Dashboard — Monitor & Report</p></div>
          </div>

          <AlertBanner alerts={alerts} onAcknowledge={handleAcknowledge} />

          <div className="stats-grid">
            <StatsCard icon="⚙️" label="Total Machines" value={stats.total_machines || 0} color="blue" />
            <StatsCard icon="✅" label="Active" value={stats.active_machines || 0} color="green" />
            <StatsCard icon="⚠️" label="Active Faults" value={stats.unresolved_faults || 0} color="red" />
            <StatsCard icon="🔔" label="Pending Alerts" value={stats.active_alerts || 0} color="amber" />
            <StatsCard icon="📦" label="Total Bundles" value={(stats.total_bundles || 0).toLocaleString()} color="cyan" />
            <StatsCard icon="📈" label="Avg Efficiency" value={`${stats.avg_efficiency || 0}%`} color="green" />
          </div>

          <div className="card">
            <div className="card-header"><h3 className="card-title">Machine Status</h3></div>
            <DataTable
              columns={[
                { key: "Machine_Name", label: "Name" },
                { key: "Location", label: "Location" },
                { key: "Status", label: "Status", render: (v) => {
                  const cls = v === "Running" ? "badge-green" : v === "Fault" ? "badge-red" : v === "Maintenance" ? "badge-amber" : "badge-blue";
                  return <span className={`badge ${cls}`}>{v}</span>;
                }},
              ]}
              data={machines}
            />
          </div>
        </>
      )}

      {/* ── SENSORS ── */}
      {activeTab === "sensors" && (
        <>
          <div className="page-header">
            <div><h1>Sensor Readings</h1><p className="page-subtitle">Live machine telemetry data</p></div>
          </div>
          <div className="content-grid">
            <div className="card">
              <div className="card-header"><h3 className="card-title">🌡️ Avg Temperature</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_temperature }))} dataKey="value" name="Temp (°C)" color="#ef4444" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">📳 Avg Vibration</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_vibration }))} dataKey="value" name="Vibration" color="#f59e0b" />
            </div>
          </div>
          <div className="content-grid" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card">
              <div className="card-header"><h3 className="card-title">⚖️ Avg Bundle Weight (Load Cell HX711)</h3></div>
              <AreaChartComponent data={sensorStats.map(s => ({ name: s.machine_name, value: s.avg_bundle_weight }))} dataKey="value" name="Weight (kg)" color="#8b5cf6" />
            </div>
            <div className="card">
              <div className="card-header"><h3 className="card-title">📡 Scrap Detections (Proximity)</h3></div>
              <SensorBarChart data={sensorStats.map(s => ({ name: s.machine_name, value: s.scrap_detections }))} dataKey="value" name="Detections" color="#06b6d4" />
            </div>
          </div>
          <div className="card" style={{ marginTop: "var(--space-lg)" }}>
            <div className="card-header"><h3 className="card-title">Recent Readings</h3></div>
            <DataTable
              columns={[
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
            <div><h1>Production Logs</h1><p className="page-subtitle">View production records</p></div>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "machine_name", label: "Machine" },
                { key: "date", label: "Date" },
                { key: "bundles_produced", label: "Bundles" },
                { key: "raw_material_kg", label: "Material (kg)" },
                { key: "operating_hours", label: "Hours" },
                { key: "efficiency", label: "Efficiency %", render: (v) => (
                  <span className={`badge ${v > 85 ? "badge-green" : v > 70 ? "badge-amber" : "badge-red"}`}>{v}%</span>
                )},
              ]}
              data={production}
            />
          </div>
        </>
      )}

      {/* ── FAULTS (Report) ── */}
      {activeTab === "faults" && (
        <>
          <div className="page-header">
            <div><h1>Report Fault</h1><p className="page-subtitle">Submit & track fault reports</p></div>
            <button className="btn btn-danger" onClick={() => { setFormData({}); setShowModal("report-fault"); }} id="report-fault-btn">⚠️ Report Fault</button>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "fault_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "fault_type", label: "Type" },
                { key: "severity", label: "Severity", render: severityBadge },
                { key: "timestamp", label: "Time" },
                { key: "resolved", label: "Status", render: (v) => v ? <span className="badge badge-green">Resolved</span> : <span className="badge badge-red">Open</span> },
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
            <div><h1>Maintenance</h1><p className="page-subtitle">Log maintenance activities</p></div>
            <button className="btn btn-success" onClick={() => { setFormData({}); setShowModal("add-maintenance"); }} id="add-maintenance-btn">🔧 Log Maintenance</button>
          </div>
          <div className="card">
            <DataTable
              columns={[
                { key: "maintenance_id", label: "ID" },
                { key: "machine_name", label: "Machine" },
                { key: "technician_name", label: "Technician" },
                { key: "date", label: "Date" },
                { key: "type", label: "Type" },
                { key: "duration_hours", label: "Hours" },
                { key: "parts_replaced", label: "Parts" },
              ]}
              data={maintenance}
            />
          </div>
        </>
      )}



      {/* ── REPORT FAULT MODAL ── */}
      {showModal === "report-fault" && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>⚠️ Report Fault</h2>
            <div className="form-grid">
              <div className="input-group">
                <label>Machine</label>
                <select className="input" onChange={e => setFormData({...formData, machine_id: parseInt(e.target.value)})}>
                  <option value="">Select machine</option>
                  {machines.map(m => <option key={m.Machine_ID} value={m.Machine_ID}>{m.Machine_Name}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label>Fault Type</label>
                <select className="input" onChange={e => setFormData({...formData, fault_type: e.target.value})}>
                  <option value="">Select type</option>
                  <option>Overheating</option><option>Excessive Vibration</option><option>Hydraulic Leak</option>
                  <option>Motor Failure</option><option>Pressure Drop</option><option>Oil Contamination</option>
                  <option>Electrical Short</option><option>Belt Snap</option><option>Bearing Failure</option>
                  <option>Sensor Malfunction</option>
                </select>
              </div>
              <div className="input-group">
                <label>Severity</label>
                <select className="input" onChange={e => setFormData({...formData, severity: e.target.value})}>
                  <option value="">Select severity</option>
                  <option>Low</option><option>Medium</option><option>High</option>
                </select>
              </div>
              <div className="input-group full-width">
                <label>Description</label>
                <textarea className="input" rows="3" placeholder="Describe the fault..." onChange={e => setFormData({...formData, description: e.target.value})}></textarea>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setShowModal(null)}>Cancel</button>
              <button className="btn btn-danger" onClick={handleSubmitFault} id="submit-fault-btn">Submit Fault</button>
            </div>
          </div>
        </div>
      )}

      {/* ── ADD MAINTENANCE MODAL ── */}
      {showModal === "add-maintenance" && (
        <div className="modal-overlay" onClick={() => setShowModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>🔧 Log Maintenance</h2>
            <div className="form-grid">
              <div className="input-group">
                <label>Machine</label>
                <select className="input" onChange={e => setFormData({...formData, machine_id: parseInt(e.target.value)})}>
                  <option value="">Select machine</option>
                  {machines.map(m => <option key={m.Machine_ID} value={m.Machine_ID}>{m.Machine_Name}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label>Type</label>
                <select className="input" onChange={e => setFormData({...formData, type: e.target.value})}>
                  <option value="">Select type</option>
                  <option>Preventive</option><option>Corrective</option><option>Predictive</option><option>Emergency</option>
                </select>
              </div>
              <div className="input-group">
                <label>Duration (Hours)</label>
                <input className="input" type="number" step="0.5" placeholder="2.0" onChange={e => setFormData({...formData, duration_hours: parseFloat(e.target.value)})} />
              </div>
              <div className="input-group">
                <label>Parts Replaced</label>
                <input className="input" placeholder="e.g. Oil Filter" onChange={e => setFormData({...formData, parts_replaced: e.target.value})} />
              </div>
              <div className="input-group full-width">
                <label>Description</label>
                <textarea className="input" rows="3" placeholder="Maintenance details..." onChange={e => setFormData({...formData, description: e.target.value})}></textarea>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-outline" onClick={() => setShowModal(null)}>Cancel</button>
              <button className="btn btn-success" onClick={handleSubmitMaintenance} id="submit-maintenance-btn">Submit</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
