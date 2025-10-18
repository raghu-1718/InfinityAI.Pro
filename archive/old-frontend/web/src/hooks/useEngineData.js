import { useState, useEffect, useCallback, useRef } from 'react';

// Engine URLs from environment variables
const ENGINE_URLS = {
  A: process.env.REACT_APP_ENGINE_A_URL,
  B: process.env.REACT_APP_ENGINE_B_URL,
  C: process.env.REACT_APP_ENGINE_C_URL,
  D: process.env.REACT_APP_ENGINE_D_URL,
  ULTRA: process.env.REACT_APP_ENGINE_ULTRA_URL
};

// Custom hook for fetching data from a specific engine
export const useEngineData = (engineType, endpoint = '', refreshInterval = 30000) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = useCallback(async () => {
    const engineUrl = ENGINE_URLS[engineType];
    console.log(`🔍 Engine ${engineType} URL configured:`, engineUrl);
    
    if (!engineUrl) {
      console.warn(`⚠️ Engine ${engineType} URL not configured in environment variables`);
      setError(`Engine ${engineType} URL not configured`);
      setLoading(false);
      return;
    }

    try {
      const url = `${engineUrl}${endpoint}`;
      console.log(`📶 Fetching from Engine ${engineType}: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        cache: 'no-store',
        timeout: 10000
      });

      console.log(`📶 Engine ${engineType} response status:`, response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log(`✅ Engine ${engineType} data received:`, result);
      setData(result);
      setError(null);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error(`❌ Error fetching from Engine ${engineType} (${engineUrl}${endpoint}):`, err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [engineType, endpoint]);

  useEffect(() => {
    // Initial fetch
    fetchData();

    // Set up periodic refresh if interval is provided
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, refreshInterval]);

  const refetch = useCallback(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    lastUpdated,
    refetch,
    isHealthy: !error && data !== null
  };
};

// Hook for Engine A - Market Data
export const useMarketData = (symbol = '', refreshInterval = 5000) => {
  const endpoint = symbol ? `/market/${symbol}` : '/health';
  return useEngineData('A', endpoint, refreshInterval);
};

// Hook for Engine B - AI/ML Intelligence  
export const useAIInsights = (refreshInterval = 15000) => {
  return useEngineData('B', '/api/ai-signals', refreshInterval);
};

// Hook for Engine C - Trade Execution
export const useTradeExecution = (refreshInterval = 10000) => {
  return useEngineData('C', '/status', refreshInterval);
};

// Hook for Engine D - Chatbot
export const useChatbotStatus = (refreshInterval = 30000) => {
  return useEngineData('D', '/health', refreshInterval);
};

// Hook for Engine Ultra - Aggressive Trading
export const useUltraTrading = (refreshInterval = 5000) => {
  return useEngineData('ULTRA', '/signals', refreshInterval);
};

// Hook for all engines health status
export const useSystemHealth = (refreshInterval = 30000) => {
  const [healthStatus, setHealthStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [overallHealth, setOverallHealth] = useState('unknown');

  const checkAllEngines = useCallback(async () => {
    setLoading(true);
    const healthChecks = {};
    let healthyCount = 0;
    const totalEngines = Object.keys(ENGINE_URLS).length;

    for (const [engineType, url] of Object.entries(ENGINE_URLS)) {
      if (!url) continue;
      
      try {
        const response = await fetch(`${url}/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          cache: 'no-store',
          timeout: 5000
        });
        
        if (response.ok) {
          const data = await response.json();
          healthChecks[engineType] = {
            status: 'healthy',
            data: data,
            lastCheck: new Date().toISOString()
          };
          healthyCount++;
        } else {
          healthChecks[engineType] = {
            status: 'error',
            error: `HTTP ${response.status}`,
            lastCheck: new Date().toISOString()
          };
        }
      } catch (error) {
        healthChecks[engineType] = {
          status: 'error',
          error: error.message,
          lastCheck: new Date().toISOString()
        };
      }
    }

    setHealthStatus(healthChecks);
    
    // Determine overall health
    if (healthyCount === totalEngines) {
      setOverallHealth('healthy');
    } else if (healthyCount > 0) {
      setOverallHealth('partial');
    } else {
      setOverallHealth('error');
    }
    
    setLoading(false);
  }, []);

  useEffect(() => {
    checkAllEngines();
    
    const interval = setInterval(checkAllEngines, refreshInterval);
    return () => clearInterval(interval);
  }, [checkAllEngines, refreshInterval]);

  return {
    healthStatus,
    overallHealth,
    loading,
    healthyCount: Object.values(healthStatus).filter(h => h.status === 'healthy').length,
    totalCount: Object.keys(ENGINE_URLS).length,
    refetch: checkAllEngines
  };
};

// Hook for real-time WebSocket connections
export const useWebSocket = (engineType, path = '/ws') => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const engineUrl = ENGINE_URLS[engineType];
    console.log(`🔌 Attempting WebSocket connection to Engine ${engineType}:`, engineUrl);
    
    if (!engineUrl) {
      console.warn(`⚠️ Engine ${engineType} URL not configured for WebSocket`);
      return;
    }

    try {
      const wsUrl = engineUrl.replace('https://', 'wss://').replace('http://', 'ws://');
      const fullWsUrl = `${wsUrl}${path}`;
      console.log(`🔌 WebSocket URL: ${fullWsUrl}`);
      const ws = new WebSocket(fullWsUrl);

      ws.onopen = () => {
        console.log(`✅ WebSocket connected to Engine ${engineType}`);
        setIsConnected(true);
        setError(null);
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log(`📨 WebSocket message from Engine ${engineType}:`, data);
          setMessages(prev => {
            const newMessage = {
              id: Date.now() + Math.random(),
              timestamp: new Date().toISOString(),
              data: data,
              engine: engineType
            };
            const updated = [...prev.slice(-99), newMessage];
            console.log(`📨 Total WebSocket messages for Engine ${engineType}:`, updated.length);
            return updated;
          });
        } catch (err) {
          console.error(`❌ WebSocket message parse error for Engine ${engineType}:`, err, event.data);
        }
      };

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected from Engine ${engineType}:`, event.code, event.reason);
        setIsConnected(false);
        setSocket(null);
        
        // Auto-reconnect after 5 seconds
        if (event.code !== 1000) { // Not a normal close
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect to Engine ${engineType}...`);
            connect();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error for Engine ${engineType}:`, error);
        setError('WebSocket connection failed');
        setIsConnected(false);
      };

    } catch (err) {
      setError(`Failed to connect to Engine ${engineType}: ${err.message}`);
    }
  }, [engineType, path]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.close(1000, 'User disconnected');
    }
  }, [socket]);

  const sendMessage = useCallback((message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, [socket]);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    messages,
    error,
    sendMessage,
    connect,
    disconnect,
    clearMessages: () => setMessages([])
  };
};

// Hook for portfolio data with real-time updates from Engine C
export const usePortfolioData = () => {
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 0,
    todaysPnL: 0,
    todaysPnLPercent: 0,
    activePositions: 0,
    availableCash: 0,
    cash_balance: 0,
    positions: [],
    user: { name: 'Demo User', client_id: '' },
    loading: true,
    error: null,
    lastUpdated: null
  });

  // Use Engine C for real portfolio data from Dhan API
  const portfolioEngine = useEngineData('C', '/api/portfolio', 15000);
  
  // Add component lifecycle logging
  useEffect(() => {
    console.log('📊 usePortfolioData hook mounted');
    return () => console.log('📊 usePortfolioData hook unmounted');
  }, []);

  useEffect(() => {
    console.log('📈 Portfolio engine data update:', {
      data: portfolioEngine.data,
      loading: portfolioEngine.loading,
      error: portfolioEngine.error,
      timestamp: new Date().toISOString()
    });
    
    if (portfolioEngine.data && !portfolioEngine.loading) {
      // Process real data from Engine C (Dhan API)
      const portfolioResponse = portfolioEngine.data;
      
      if (portfolioResponse.status === 'success' && portfolioResponse.summary) {
        const realUpdate = {
          totalValue: portfolioResponse.summary.portfolio_value || 0,
          todaysPnL: portfolioResponse.summary.total_pnl || 0,
          todaysPnLPercent: portfolioResponse.summary.portfolio_value > 0 ? 
            ((portfolioResponse.summary.total_pnl || 0) / portfolioResponse.summary.portfolio_value * 100) : 0,
          activePositions: portfolioResponse.summary.total_positions || 0,
          availableCash: 0, // Not provided by Dhan API
          cash_balance: 0, // Not provided by Dhan API
          positions: portfolioResponse.data?.positions || [],
          user: portfolioResponse.user || { name: 'Demo User', client_id: '' },
          lastUpdated: portfolioResponse.timestamp || new Date().toISOString(),
          loading: false,
          error: null
        };
        
        console.log('💰 Real portfolio update from Engine C:', realUpdate);
        
        setPortfolioData(prev => ({
          ...prev,
          ...realUpdate
        }));
      } else {
        console.log('⚠️ Portfolio data format unexpected:', portfolioResponse);
        setPortfolioData(prev => ({
          ...prev,
          loading: false,
          error: 'Unexpected data format'
        }));
      }
    } else if (portfolioEngine.error) {
      console.log('❌ Portfolio engine error:', portfolioEngine.error);
      setPortfolioData(prev => ({
        ...prev,
        loading: false,
        error: portfolioEngine.error
      }));
    }
  }, [portfolioEngine.data, portfolioEngine.loading, portfolioEngine.error, portfolioData.totalValue, portfolioData.todaysPnL, portfolioData.todaysPnLPercent, portfolioData.activePositions, portfolioData.availableCash, portfolioData.cash_balance]);

  return {
    ...portfolioData,
    refresh: portfolioEngine.refetch
  };
};

export default {
  useEngineData,
  useMarketData,
  useAIInsights,
  useTradeExecution,
  useChatbotStatus,
  useUltraTrading,
  useSystemHealth,
  useWebSocket,
  usePortfolioData
};