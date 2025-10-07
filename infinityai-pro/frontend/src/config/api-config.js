// InfinityAI.Pro Multi-Cloud API Configuration (No Vercel)
export const API_CONFIG = {
  "api": {
    "base_urls": {
            "primary": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d",
            "engine_a": "https://infinityai-engine-a-573866363639.us-central1.run.app",
            "engine_b": "https://infinityai-engine-b-573866363639.us-central1.run.app",
            "engine_c": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c",
            "engine_d": "http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d"
    },
    "endpoints": {
      "health": "/health",
      "market_data": "/api/market-data",
      "ai_chat": "/api/chat",
      "trading": "/api/trading",
      "websocket": "/ws"
    },
        "fallback_strategy": "aws_primary"
  },
  "deployment": {
    "environment": "production",
        "clouds": ["aws", "gcp"],
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
    
    // Priority order: primary (AWS Engine D) -> engine_d -> engine_c -> engine_a -> engine_b
    const priority = ['primary', 'engine_d', 'engine_c', 'engine_a', 'engine_b'];
    
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