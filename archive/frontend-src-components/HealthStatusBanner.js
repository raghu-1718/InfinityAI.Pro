import React, { useState, useEffect } from 'react';
import './HealthStatusBanner.css';

const HealthStatusBanner = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Engine URLs for fallback checks
  const engineUrls = {
    ENGINE_D: 'https://engine-d-chatbot-prod-573866363639.us-central1.run.app',
    ENGINE_C: 'https://engine-c-execution-prod-573866363639.us-central1.run.app',
    ENGINE_ULTRA: 'https://engine-ultra-aggressive-prod-573866363639.us-central1.run.app'
  };

  // Check individual engine health as fallback
  const checkEngineHealth = async (url, timeout = 3000) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(`${url}/health`, {
        signal: controller.signal,
        mode: 'cors'
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      console.warn(`Engine health check failed for ${url}:`, error.message);
      return false;
    }
  };

  // Get comprehensive health from Engine D
  const fetchComprehensiveHealth = async () => {
    try {
      const response = await fetch(
        `${engineUrls.ENGINE_D}/api/health/simple`,
        { 
          timeout: 5000,
          mode: 'cors'
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        return {
          engines: data.engines,
          summary: data.summary,
          source: 'orchestrator'
        };
      }
      throw new Error('Orchestrator unavailable');
      
    } catch (error) {
      console.warn('Orchestrator health check failed, using fallback:', error.message);
      
      // Fallback: Check working engines individually
      const fallbackHealth = {};
      const workingEngines = ['ENGINE_C', 'ENGINE_D', 'ENGINE_ULTRA'];
      
      for (const engine of workingEngines) {
        const engineKey = engine.replace('ENGINE_', '');
        fallbackHealth[engineKey] = await checkEngineHealth(engineUrls[engine]);
      }
      
      // Assume A and B are down (known issue)
      fallbackHealth.A = false;
      fallbackHealth.B = false;
      
      const healthyCount = Object.values(fallbackHealth).filter(Boolean).length;
      const totalEngines = Object.keys(fallbackHealth).length;
      
      return {
        engines: fallbackHealth,
        summary: {
          healthy_engines: healthyCount,
          total_engines: totalEngines,
          health_percentage: Math.round((healthyCount / totalEngines) * 100),
          overall_status: healthyCount >= 3 ? 'healthy' : healthyCount >= 2 ? 'degraded' : 'critical'
        },
        source: 'fallback'
      };
    }
  };

  // Fetch health data
  const updateHealthStatus = async () => {
    setLoading(true);
    try {
      const health = await fetchComprehensiveHealth();
      setHealthData(health);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch health status:', error);
      // Set minimal fallback data
      setHealthData({
        engines: { A: false, B: false, C: false, D: false, ULTRA: false },
        summary: { healthy_engines: 0, total_engines: 5, health_percentage: 0, overall_status: 'critical' },
        source: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    updateHealthStatus();
    
    // Update every 30 seconds
    const interval = setInterval(updateHealthStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !healthData) {
    return (
      <div className="health-banner loading">
        <div className="health-spinner"></div>
        <span>Checking system health...</span>
      </div>
    );
  }

  if (!healthData) {
    return (
      <div className="health-banner error">
        <span>⚠️ Unable to check system health</span>
      </div>
    );
  }

  const { engines, summary, source } = healthData;
  const { healthy_engines, total_engines, health_percentage, overall_status } = summary;

  const getStatusColor = () => {
    if (health_percentage >= 60) return 'healthy';
    if (health_percentage >= 40) return 'degraded';
    return 'critical';
  };

  const getStatusIcon = () => {
    if (health_percentage >= 60) return '✅';
    if (health_percentage >= 40) return '⚠️';
    return '❌';
  };

  const engineNames = {
    A: 'Market Data',
    B: 'AI/ML Signals',
    C: 'Trading/OAuth',
    D: 'Chatbot',
    ULTRA: 'Ultra Trading'
  };

  return (
    <div className={`health-banner ${getStatusColor()}`}>
      <div className="health-summary">
        <span className="health-icon">{getStatusIcon()}</span>
        <span className="health-text">
          <strong>{healthy_engines}/{total_engines}</strong> engines healthy
          <span className="health-percentage">({health_percentage}%)</span>
        </span>
        <span className={`health-status ${overall_status}`}>
          {overall_status.toUpperCase()}
        </span>
      </div>
      
      <div className="health-details">
        <div className="engine-status">
          {Object.entries(engines).map(([key, healthy]) => (
            <div 
              key={key} 
              className={`engine-indicator ${healthy ? 'healthy' : 'unhealthy'}`}
              title={`Engine ${key} (${engineNames[key]}): ${healthy ? 'Healthy' : 'Unhealthy'}`}
            >
              <span className="engine-name">{key}</span>
              <span className="engine-dot">{healthy ? '●' : '○'}</span>
            </div>
          ))}
        </div>
        
        <div className="health-meta">
          <span className="data-source" title={`Data source: ${source}`}>
            {source === 'orchestrator' ? '🎯' : source === 'fallback' ? '🔄' : '⚠️'}
          </span>
          {lastUpdate && (
            <span className="last-update" title={`Last updated: ${lastUpdate.toLocaleTimeString()}`}>
              {Math.floor((new Date() - lastUpdate) / 1000)}s ago
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default HealthStatusBanner;