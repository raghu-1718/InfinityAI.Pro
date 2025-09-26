import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login.tsx';
import Dashboard from './components/Dashboard.tsx';
import Trading from './pages/Trading.tsx';
import AIModels from './pages/AIModels.tsx';
import Risk from './pages/Risk.tsx';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trading" element={<Trading />} />
        <Route path="/ai-models" element={<AIModels />} />
        <Route path="/risk" element={<Risk />} />
      </Routes>
    </Router>
  );
}

export default App;