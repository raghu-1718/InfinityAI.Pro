/**
 * Dashboard Component
 * 
 * Main application dashboard with tab-based navigation:
 * - Dashboard: System health + Gemini AI insights
 * - Strategies: Trading strategy selection
 * - Settings: Dhan API credentials management
 */

import { useState } from "react";
import { User } from "firebase/auth";
import Navbar from "./Navbar";
import StrategySelector from "./StrategySelector";
import CredentialsForm from "./CredentialsForm";
import GeminiInsights from "./GeminiInsights";
import SystemHealth from "./SystemHealth";

interface DashboardProps {
  user: User;
}

type TabType = "dashboard" | "strategies" | "settings";

export default function Dashboard({ user }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<TabType>("dashboard");

  return (
    <div className="dashboard-container">
      <Navbar user={user} activeTab={activeTab} setTab={setActiveTab} />
      
      <main className="dashboard-content">
        {activeTab === "dashboard" && (
          <div className="dashboard-tab">
            <h2>🏠 System Dashboard</h2>
            <SystemHealth />
            <GeminiInsights userId={user.uid} />
          </div>
        )}

        {activeTab === "strategies" && (
          <div className="strategies-tab">
            <h2>📊 Trading Strategies</h2>
            <StrategySelector user={user} />
          </div>
        )}

        {activeTab === "settings" && (
          <div className="settings-tab">
            <h2>⚙️ Settings</h2>
            <CredentialsForm user={user} />
          </div>
        )}
      </main>
    </div>
  );
}
