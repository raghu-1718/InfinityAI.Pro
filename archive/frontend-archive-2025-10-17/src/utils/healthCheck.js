// Health check utilities for InfinityAI.Pro frontend

const ENGINE_ENDPOINTS = {
  ENGINE_A: 'https://engine-a-market-data-prod-573866363639.us-central1.run.app',
  ENGINE_B: 'https://engine-b-ai-ml-prod-573866363639.us-central1.run.app',
  ENGINE_C: 'https://engine-c-oauth-573866363639.us-central1.run.app',
  ENGINE_D: 'https://engine-d-chatbot-prod-573866363639.us-central1.run.app',
  ENGINE_ULTRA: 'https://engine-ultra-aggressive-prod-573866363639.us-central1.run.app'
};

// Check individual engine health
export const checkEngineHealth = async (url, timeout = 3000) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(`${url}/health`, {
      method: 'GET',
      signal: controller.signal,
      mode: 'cors',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });
    
    clearTimeout(timeoutId);
    return {
      healthy: response.ok,
      status: response.status,
      responseTime: Date.now() - performance.now()
    };
  } catch (error) {
    console.warn(`Engine health check failed for ${url}:`, error.message);
    return {
      healthy: false,
      status: 'error',
      error: error.message,
      responseTime: timeout
    };
  }
};

// Check multiple engines in parallel
export const checkMultipleEngines = async (engineUrls = ENGINE_ENDPOINTS, timeout = 3000) => {
  const healthPromises = Object.entries(engineUrls).map(async ([key, url]) => {
    const result = await checkEngineHealth(url, timeout);
    return [key.replace('ENGINE_', ''), result];
  });
  
  try {
    const results = await Promise.allSettled(healthPromises);
    const healthData = {};
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        const [engineKey, healthInfo] = result.value;
        healthData[engineKey] = healthInfo;
      } else {
        const engineKey = Object.keys(engineUrls)[index].replace('ENGINE_', '');
        healthData[engineKey] = {
          healthy: false,
          status: 'error',
          error: result.reason?.message || 'Unknown error',
          responseTime: timeout
        };
      }
    });
    
    return healthData;
  } catch (error) {
    console.error('Failed to check multiple engines:', error);
    return {};
  }
};

// Get comprehensive health from Engine D orchestrator
export const getComprehensiveHealth = async (timeout = 5000) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(
      `${ENGINE_ENDPOINTS.ENGINE_D}/api/health/comprehensive`,
      {
        signal: controller.signal,
        mode: 'cors',
        headers: {
          'Accept': 'application/json'
        }
      }
    );
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        data,
        source: 'orchestrator'
      };
    }
    
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    
  } catch (error) {
    console.warn('Orchestrator health check failed:', error.message);
    return {
      success: false,
      error: error.message,
      source: 'orchestrator_failed'
    };
  }
};

// Get simple health status for frontend display
export const getSimpleHealth = async (timeout = 5000) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(
      `${ENGINE_ENDPOINTS.ENGINE_D}/api/health/simple`,
      {
        signal: controller.signal,
        mode: 'cors',
        headers: {
          'Accept': 'application/json'
        }
      }
    );
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        engines: data.engines,
        summary: data.summary,
        source: 'orchestrator'
      };
    }
    
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    
  } catch (error) {
    console.warn('Simple health check failed, using fallback:', error.message);
    return await getFallbackHealth();
  }
};

// Fallback health check when orchestrator is unavailable
export const getFallbackHealth = async () => {
  try {
    // Check only the engines we know are working
    const workingEngines = {
      ENGINE_C: ENGINE_ENDPOINTS.ENGINE_C,
      ENGINE_D: ENGINE_ENDPOINTS.ENGINE_D,
      ENGINE_ULTRA: ENGINE_ENDPOINTS.ENGINE_ULTRA
    };
    
    const healthResults = await checkMultipleEngines(workingEngines, 3000);
    
    // Build fallback response
    const engines = {
      A: false, // Known to be down
      B: false, // Known to be down
      C: healthResults.C?.healthy || false,
      D: healthResults.D?.healthy || false,
      ULTRA: healthResults.ULTRA?.healthy || false
    };
    
    const healthyCount = Object.values(engines).filter(Boolean).length;
    const totalEngines = Object.keys(engines).length;
    const healthPercentage = Math.round((healthyCount / totalEngines) * 100);
    
    let overallStatus;
    if (healthPercentage >= 60) overallStatus = 'healthy';
    else if (healthPercentage >= 40) overallStatus = 'degraded';
    else overallStatus = 'critical';
    
    return {
      success: true,
      engines,
      summary: {
        healthy_engines: healthyCount,
        total_engines: totalEngines,
        health_percentage: healthPercentage,
        overall_status: overallStatus
      },
      source: 'fallback'
    };
    
  } catch (error) {
    console.error('Fallback health check failed:', error);
    return {
      success: false,
      engines: { A: false, B: false, C: false, D: false, ULTRA: false },
      summary: {
        healthy_engines: 0,
        total_engines: 5,
        health_percentage: 0,
        overall_status: 'critical'
      },
      source: 'error',
      error: error.message
    };
  }
};

// Utility to format health status for display
export const formatHealthStatus = (healthData) => {
  if (!healthData) return 'Unknown';
  
  const { summary } = healthData;
  if (!summary) return 'No data';
  
  const { healthy_engines, total_engines, health_percentage, overall_status } = summary;
  
  return {
    text: `${healthy_engines}/${total_engines} engines healthy (${health_percentage}%)`,
    status: overall_status,
    color: health_percentage >= 60 ? 'green' : health_percentage >= 40 ? 'orange' : 'red',
    icon: health_percentage >= 60 ? '✅' : health_percentage >= 40 ? '⚠️' : '❌'
  };
};

// Export engine endpoints for use in other components
export { ENGINE_ENDPOINTS };