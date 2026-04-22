const API_BASE = "http://localhost:5000/api";

function getHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(endpoint, options = {}) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: getHeaders(),
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// Auth
export const login = (username, password) =>
  request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

// Machines
export const getMachines = () => request("/machines");
export const createMachine = (data) =>
  request("/machines", { method: "POST", body: JSON.stringify(data) });
export const updateMachine = (id, data) =>
  request(`/machines/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteMachine = (id) =>
  request(`/machines/${id}`, { method: "DELETE" });

// Employees
export const getEmployees = () => request("/employees");
export const createEmployee = (data) =>
  request("/employees", { method: "POST", body: JSON.stringify(data) });
export const updateEmployee = (id, data) =>
  request(`/employees/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteEmployee = (id) =>
  request(`/employees/${id}`, { method: "DELETE" });

// Sensors
export const getSensorReadings = (machineId, limit = 100) =>
  request(`/sensors?machine_id=${machineId || ""}&limit=${limit}`);
export const getLatestReadings = () => request("/sensors/latest");
export const getSensorStats = () => request("/sensors/stats");

// Production
export const getProductionLogs = (machineId) =>
  request(`/production${machineId ? `?machine_id=${machineId}` : ""}`);
export const createProductionLog = (data) =>
  request("/production", { method: "POST", body: JSON.stringify(data) });
export const getProductionSummary = () => request("/production/summary");

// Faults
export const getFaults = (machineId, severity) => {
  const params = new URLSearchParams();
  if (machineId) params.append("machine_id", machineId);
  if (severity) params.append("severity", severity);
  return request(`/faults?${params}`);
};
export const createFault = (data) =>
  request("/faults", { method: "POST", body: JSON.stringify(data) });
export const resolveFault = (id) =>
  request(`/faults/${id}/resolve`, { method: "PUT" });

// Maintenance
export const getMaintenanceLogs = (machineId) =>
  request(`/maintenance${machineId ? `?machine_id=${machineId}` : ""}`);
export const createMaintenanceLog = (data) =>
  request("/maintenance", { method: "POST", body: JSON.stringify(data) });

// Alerts
export const getAlerts = (acknowledged) =>
  request(`/alerts${acknowledged !== undefined ? `?acknowledged=${acknowledged}` : ""}`);
export const getActiveAlerts = () => request("/alerts/active");
export const acknowledgeAlert = (id) =>
  request(`/alerts/${id}/acknowledge`, { method: "PUT" });
export const acknowledgeAllAlerts = () =>
  request("/alerts/acknowledge-all", { method: "PUT" });
export const getAlertCount = () => request("/alerts/count");

// Analytics
export const getMTBF = () => request("/analytics/mtbf");
export const getMTTR = () => request("/analytics/mttr");
export const getDowntime = () => request("/analytics/downtime");
export const getFailurePrediction = () => request("/analytics/predict");
export const getDashboardStats = () => request("/analytics/stats");

// Reports
export const sendAssignmentReport = () => request("/reports/send-assignments", { method: "POST" });
