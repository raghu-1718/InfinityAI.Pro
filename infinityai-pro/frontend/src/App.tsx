import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './components/Dashboard';
import Trading from './pages/Trading';
import AIModels from './pages/AIModels';
import Risk from './pages/Risk';

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