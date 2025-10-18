import React from 'react'
import { Route, Routes, Link, NavLink } from 'react-router-dom'
import Analysis from './pages/Analysis'
import StrategyExecution from './pages/StrategyExecution'
import Assistant from './pages/Assistant'
import Dashboard from './pages/Dashboard'

export default function App() {
  const nav = [
    { to: '/', label: 'Dashboard' },
    { to: '/analysis', label: 'Analysis' },
    { to: '/execute', label: 'Execute' },
    { to: '/assistant', label: 'Assistant' },
  ]
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 bg-gray-900/80 backdrop-blur border-b border-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
          <Link to="/" className="font-semibold">InfinityAI.Pro</Link>
          <nav className="flex gap-4 text-sm">
            {nav.map(n => (
              <NavLink key={n.to} to={n.to} className={({isActive}) => isActive ? 'text-white' : 'text-gray-400 hover:text-gray-200'}>
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/execute" element={<StrategyExecution />} />
          <Route path="/assistant" element={<Assistant />} />
        </Routes>
      </main>
    </div>
  )
}
