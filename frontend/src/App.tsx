/**
 * InfinityAI.Pro - Main Application Component
 * 
 * Handles authentication state and routing
 * Displays AuthGate for unauthenticated users, Dashboard for authenticated users
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { onAuthStateChanged, User } from "firebase/auth";
import { auth } from "./firebaseConfig";
import { useEffect, useState } from "react";
import AuthGate from "./components/AuthGate";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Subscribe to authentication state changes
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
      
      if (currentUser) {
        console.log("✅ User authenticated:", currentUser.email);
      } else {
        console.log("❌ No user authenticated");
      }
    });

    return () => unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading InfinityAI.Pro...</p>
      </div>
    );
  }

  return (
    <BrowserRouter>
      {!user ? (
        <Routes>
          <Route path="/" element={<AuthGate />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      ) : (
        <Routes>
          <Route path="/" element={<Dashboard user={user} />} />
          <Route path="/auth/dhan/callback" element={<Dashboard user={user} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}
