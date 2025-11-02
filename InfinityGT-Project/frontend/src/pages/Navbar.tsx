/**
 * Navbar Component
 * 
 * Top navigation bar with tab switching and logout functionality
 */

import { signOut } from "firebase/auth";
import { auth } from "../firebaseConfig";
import { User } from "firebase/auth";

interface NavbarProps {
  user: User;
  activeTab: string;
  setTab: (tab: "dashboard" | "strategies" | "settings") => void;
}

export default function Navbar({ user, activeTab, setTab }: NavbarProps) {
  const handleLogout = async () => {
    try {
      await signOut(auth);
      console.log("✅ Logged out successfully");
    } catch (error) {
      console.error("❌ Logout error:", error);
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <h1>InfinityAI.Pro</h1>
        <span className="version">v3.0</span>
      </div>

      <div className="navbar-links">
        <button
          className={`nav-btn ${activeTab === "dashboard" ? "active" : ""}`}
          onClick={() => setTab("dashboard")}
        >
          🏠 Dashboard
        </button>
        <button
          className={`nav-btn ${activeTab === "strategies" ? "active" : ""}`}
          onClick={() => setTab("strategies")}
        >
          📊 Strategies
        </button>
        <button
          className={`nav-btn ${activeTab === "settings" ? "active" : ""}`}
          onClick={() => setTab("settings")}
        >
          ⚙️ Settings
        </button>
      </div>

      <div className="navbar-user">
        <span className="user-email">{user.email}</span>
        <button className="btn-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}
