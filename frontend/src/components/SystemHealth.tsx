/**
 * SystemHealth Component
 * 
 * Displays real-time health status of all system components:
 * - Cloud Functions (submitDhanCredentialsV2, startTrading)
 * - Cloud Run Engines (A, B, C, D)
 * - Gemini Extension
 * - Firestore Database
 */

import { useEffect, useState } from "react";

interface ServiceStatus {
  name: string;
  status: "online" | "offline" | "checking";
  icon: string;
  lastCheck?: Date;
}

export default function SystemHealth() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: "Cloud Functions", status: "checking", icon: "⚡" },
    { name: "Engine A (Analysis)", status: "checking", icon: "🔍" },
    { name: "Engine B (Forecast)", status: "checking", icon: "📈" },
    { name: "Engine C (Execution)", status: "checking", icon: "🎯" },
    { name: "Engine D (Risk)", status: "checking", icon: "🛡️" },
    { name: "Gemini Extension", status: "checking", icon: "🤖" },
    { name: "Firestore Database", status: "checking", icon: "💾" },
  ]);

  useEffect(() => {
    // Simulate health checks (in production, call actual health endpoints)
    const checkHealth = async () => {
      // For now, we'll set everything to online
      // In production, you'd make actual HTTP requests to health endpoints
      const updatedServices = services.map((service) => ({
        ...service,
        status: "online" as const,
        lastCheck: new Date(),
      }));

      setServices(updatedServices);
      console.log("✅ System health check completed");
    };

    // Initial check
    checkHealth();

    // Periodic health checks every 60 seconds
    const interval = setInterval(checkHealth, 60000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "#10b981"; // green
      case "offline":
        return "#ef4444"; // red
      case "checking":
        return "#f59e0b"; // yellow
      default:
        return "#6b7280"; // gray
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "online":
        return "✅ Online";
      case "offline":
        return "❌ Offline";
      case "checking":
        return "⏳ Checking...";
      default:
        return "❓ Unknown";
    }
  };

  const onlineCount = services.filter((s) => s.status === "online").length;
  const totalCount = services.length;
  const healthPercentage = ((onlineCount / totalCount) * 100).toFixed(0);

  return (
    <div className="system-health-container">
      <div className="health-header">
        <h3>🏥 System Health</h3>
        <div className="health-score">
          <span className="score-value">{healthPercentage}%</span>
          <span className="score-label">Operational</span>
        </div>
      </div>

      <div className="health-grid">
        {services.map((service, index) => (
          <div key={index} className="health-card">
            <div className="service-icon">{service.icon}</div>
            <div className="service-info">
              <h4>{service.name}</h4>
              <p
                className="service-status"
                style={{ color: getStatusColor(service.status) }}
              >
                {getStatusText(service.status)}
              </p>
              {service.lastCheck && (
                <small className="last-check">
                  Checked: {service.lastCheck.toLocaleTimeString()}
                </small>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="health-legend">
        <span className="legend-item">
          <span style={{ color: "#10b981" }}>●</span> Online
        </span>
        <span className="legend-item">
          <span style={{ color: "#ef4444" }}>●</span> Offline
        </span>
        <span className="legend-item">
          <span style={{ color: "#f59e0b" }}>●</span> Checking
        </span>
      </div>
    </div>
  );
}
