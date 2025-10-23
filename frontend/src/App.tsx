import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { auth } from './firebase'; // Assuming firebase config is in firebase.ts
import { onAuthStateChanged, User } from 'firebase/auth';

import Sidebar from './components/layout/Sidebar';
import Navbar from './pages/Navbar'; // Using the Navbar from the old frontend
import Dashboard from './pages/Dashboard';
import Engines from './pages/Engines';
import StrategySelector from './pages/StrategySelector';
import StrategyExecution from './pages/StrategyExecution';
import Analysis from './pages/Analysis';
import Assistant from './pages/Assistant';
import CredentialsForm from './pages/CredentialsForm';
import SystemHealth from './pages/SystemHealth';
import AuthGate from './pages/AuthGate'; // This is the login page

// A component to protect routes
const ProtectedRoute = ({ user, children }: { user: User | null, children: JSX.Element }) => {
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) {
    // You can add a loading spinner here
    return <div className="flex items-center justify-center h-screen bg-gray-950 text-white">Loading...</div>;
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<AuthGate />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute user={user}>
              <div className="flex h-screen overflow-hidden bg-gray-950">
                <Sidebar />
                <div className="flex flex-col flex-1 overflow-hidden">
                  {user && <Navbar user={user} setTab={() => {}} activeTab="dashboard" />}
                  <main className="flex-1 overflow-y-auto bg-gray-950 p-6">
                    <Routes>
                      <Route path="/dashboard" element={<Dashboard user={user!} />} />
                      <Route path="/engines" element={<Engines />} />
                      <Route path="/strategies" element={<StrategySelector user={user!} />} />
                      <Route path="/strategies/execute" element={<StrategyExecution />} />
                      <Route path="/analysis" element={<Analysis />} />
                      <Route path="/assistant" element={<Assistant />} />
                      <Route path="/settings" element={<CredentialsForm user={user!} />} />
                      <Route path="/system-health" element={<SystemHealth />} />
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
