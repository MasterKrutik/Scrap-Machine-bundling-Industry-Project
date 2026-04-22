import { useAuth } from "../context/AuthContext";

export default function Sidebar({ activeTab, setActiveTab, alertCount }) {
  const { user, logout, isAdmin } = useAuth();

  const adminLinks = [
    { id: "overview", icon: "📊", label: "Overview" },
    { id: "machines", icon: "⚙️", label: "Machines" },
    { id: "employees", icon: "👥", label: "Employees" },
    { id: "sensors", icon: "📡", label: "Sensor Data" },
    { id: "production", icon: "📦", label: "Production" },
    { id: "faults", icon: "⚠️", label: "Fault Logs" },
    { id: "maintenance", icon: "🔧", label: "Maintenance" },
    { id: "alerts", icon: "🔔", label: "Alerts", badge: alertCount },
    { id: "analytics", icon: "📈", label: "Analytics" },
  ];

  const userLinks = [
    { id: "overview", icon: "📊", label: "Overview" },
    { id: "sensors", icon: "📡", label: "Sensor Data" },
    { id: "production", icon: "📦", label: "Production" },
    { id: "faults", icon: "⚠️", label: "Report Fault" },
    { id: "maintenance", icon: "🔧", label: "Maintenance" },
    { id: "alerts", icon: "🔔", label: "Alerts", badge: alertCount },
  ];

  const links = isAdmin ? adminLinks : userLinks;

  const initials = user?.full_name
    ? user.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)
    : "U";

  return (
    <nav className="sidebar" id="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">🏭</div>
        <div className="sidebar-title">
          <h2>ScrapMachine</h2>
          <span>IoT Dashboard</span>
        </div>
      </div>

      <div className="sidebar-nav">
        <div className="nav-section">Navigation</div>
        {links.map((link) => (
          <button
            key={link.id}
            className={`nav-item ${activeTab === link.id ? "active" : ""}`}
            onClick={() => setActiveTab(link.id)}
            id={`nav-${link.id}`}
          >
            <div className="nav-item-left">
              <span className="nav-icon">{link.icon}</span>
              <span>{link.label}</span>
            </div>
            {link.badge > 0 && <span className="nav-badge">{link.badge}</span>}
          </button>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="avatar">{initials}</div>
          <div className="user-info">
            <div className="user-name">{user?.full_name || "User"}</div>
            <div className="user-role">{user?.role}</div>
          </div>
          <button className="logout-btn" onClick={logout} title="Logout" id="logout-btn">
            🚪
          </button>
        </div>
      </div>
    </nav>
  );
}
