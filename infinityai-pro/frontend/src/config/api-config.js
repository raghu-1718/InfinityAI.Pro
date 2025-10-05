// InfinityAI.Pro Multi-Cloud API Configuration (No Vercel)
export const API_CONFIG = {
  "api": {
    "base_urls": {
      "primary": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
      "engine_a": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
      "engine_a_alt": "https://infinityai-engine-a--0000006.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
      "engine_b": "https://engine-b-service-infinityai.run.app",
      "engine_c": "https://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8002", 
      "engine_d": "https://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8000"
    },
    "endpoints": {
      "health": "/health",
      "market_data": "/api/market-data",
      "ai_chat": "/api/chat",
      "trading": "/api/trading",
      "websocket": "/ws"
    },
    "fallback_strategy": "azure_primary"
  },
  "deployment": {
    "environment": "production",
    "clouds": ["azure", "aws", "gcp"],
    "eliminated": ["vercel"],
    "last_updated": "2025-10-05T14:50:00Z"
  }
};

export const getApiUrl = (service = 'primary') => {
    return API_CONFIG.api.base_urls[service] || API_CONFIG.api.base_urls.primary;
};

export const getEndpoint = (endpoint) => {
    return API_CONFIG.api.endpoints[endpoint] || '';
};

export const buildApiUrl = (service = 'primary', endpoint = '') => {
    const baseUrl = getApiUrl(service);
    const endpointPath = getEndpoint(endpoint);
    return `${baseUrl}${endpointPath}`;
};

// Helper function to test all endpoints
export const testAllEndpoints = async () => {
    const results = {};
    
    for (const [service, url] of Object.entries(API_CONFIG.api.base_urls)) {
        try {
            const response = await fetch(`${url}/health`, { 
                method: 'GET',
                timeout: 10000 
            });
            results[service] = {
                status: response.status,
                healthy: response.ok,
                url: url
            };
        } catch (error) {
            results[service] = {
                status: 'error',
                healthy: false,
                error: error.message,
                url: url
            };
        }
    }
    
    return results;
};

// Multi-cloud failover logic
export const getHealthyEndpoint = async () => {
    const testResults = await testAllEndpoints();
    
    // Priority order: primary (Azure) -> engine_a_alt -> others
    const priority = ['primary', 'engine_a_alt', 'engine_a', 'engine_b', 'engine_c', 'engine_d'];
    
    for (const service of priority) {
        if (testResults[service]?.healthy) {
            return {
                service,
                url: API_CONFIG.api.base_urls[service],
                status: 'healthy'
            };
        }
    }
    
    return {
        service: 'primary',
        url: API_CONFIG.api.base_urls.primary,
        status: 'fallback'
    };
};