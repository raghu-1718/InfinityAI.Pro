import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Trading from './pages/Trading';
import AIModels from './pages/AIModels';
import Risk from './pages/Risk';
import Login from './pages/Login';
import Home from './pages/Home';

const App: React.FC = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trading" element={<Trading />} />
          <Route path="/ai-models" element={<AIModels />} />
          <Route path="/risk" element={<Risk />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;