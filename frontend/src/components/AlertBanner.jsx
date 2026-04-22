export default function AlertBanner({ alerts, onAcknowledge }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="alerts-panel">
      {alerts.slice(0, 5).map((alert) => (
        <div className="alert-item" key={alert.alert_id}>
          <span className="alert-icon">🚨</span>
          <div className="alert-content">
            <div className="alert-message">{alert.message}</div>
            <div className="alert-meta">
              {alert.machine_name} • {alert.location} • {new Date(alert.timestamp).toLocaleString()}
            </div>
          </div>
          <button
            className="alert-dismiss"
            onClick={() => onAcknowledge(alert.alert_id)}
            id={`ack-alert-${alert.alert_id}`}
          >
            Acknowledge
          </button>
        </div>
      ))}
    </div>
  );
}
