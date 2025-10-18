import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Topbar from './components/layout/Topbar'
import Dashboard from './pages/Dashboard'
import Engines from './pages/Engines'
import Strategies from './pages/Strategies'
import StrategyExecution from './pages/StrategyExecution'
import Analysis from './pages/Analysis'
import Assistant from './pages/Assistant'
import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <div className="flex h-screen overflow-hidden bg-gray-950">
        <Sidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto bg-gray-950 p-6">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/engines" element={<Engines />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/strategies/execute" element={<StrategyExecution />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  )
}

export default App
