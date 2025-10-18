// InfinityAI Pro - Complete API Service for All 5 Engines
// Indian Market Focus: NSE/BSE/MCX Only
// ✅ CORRECTED PRODUCTION URLS - Updated 2025-10-16

const ENGINES = {
  ENGINE_A: 'https://infinityai.pro/api/engine-a',
  ENGINE_B: 'https://infinityai.pro/api/engine-b',
  ENGINE_C: 'https://infinityai.pro/api/engine-c',
  ENGINE_D: 'https://infinityai.pro/api/engine-d',
  ENGINE_ULTRA: 'https://infinityai.pro/api/engine-ultra'
};

class ApiService {
  constructor() {
    this.headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    this.timeout = 30000;
  }

  async makeRequest(url, options = {}) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      
      const response = await fetch(url, {
        ...options,
        headers: { ...this.headers, ...options.headers },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status} - ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API Request failed for ${url}:`, error);
      throw error;
    }
  }

  // ENGINE A - Market Data (NSE/BSE/MCX Focus)
  async getMarketData(symbols = []) {
    const indianSymbols = symbols.length > 0 ? symbols : [
      'RELIANCE', 'TCS', 'HDFC', 'INFY', 'HDFCBANK', 'ICICIBANK',
      'SBIN', 'BHARTIARTL', 'ITC', 'LT', 'KOTAKBANK', 'ASIANPAINT'
    ];
    
    return this.makeRequest(`${ENGINES.ENGINE_A}/api/market-data`, {
      method: 'POST',
      body: JSON.stringify({ 
        symbols: indianSymbols,
        exchange: 'NSE',
        country: 'IN'
      })
    });
  }

  async getLiveQuotes(symbols) {
    return this.makeRequest(`${ENGINES.ENGINE_A}/api/live-quotes`, {
      method: 'POST',
      body: JSON.stringify({ 
        symbols, 
        exchanges: ['NSE', 'BSE', 'MCX']
      })
    });
  }

  async getNiftyData() {
    return this.makeRequest(`${ENGINES.ENGINE_A}/api/indices/nifty`);
  }

  async getSensexData() {
    return this.makeRequest(`${ENGINES.ENGINE_A}/api/indices/sensex`);
  }

  // ENGINE B - AI/ML Signals (Indian Market Only)
  async getAISignals() {
    return this.makeRequest(`${ENGINES.ENGINE_B}/api/ai-signals`, {
      method: 'POST',
      body: JSON.stringify({
        market: 'indian',
        exchanges: ['NSE', 'BSE'],
        exclude_global: true
      })
    });
  }

  async getTrendAnalysis(symbol) {
    return this.makeRequest(`${ENGINES.ENGINE_B}/api/trend-analysis`, {
      method: 'POST',
      body: JSON.stringify({ 
        symbol, 
        market: 'NSE',
        timeframe: '1D'
      })
    });
  }

  async getMLPredictions() {
    return this.makeRequest(`${ENGINES.ENGINE_B}/api/ml-predictions`, {
      method: 'POST',
      body: JSON.stringify({
        focus: 'indian_equities',
        exchanges: ['NSE', 'BSE']
      })
    });
  }

  // ENGINE C - Execution & Portfolio (Live Dhan Data)
  async getPortfolio() {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/portfolio`);
  }

  async getHoldings() {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/holdings`);
  }

  async getPnL() {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/pnl`);
  }

  async placeOrder(orderData) {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/place-order`, {
      method: 'POST',
      body: JSON.stringify(orderData)
    });
  }

  async getOrderStatus(orderId) {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/order-status/${orderId}`);
  }

  async getDhanProfile() {
    return this.makeRequest(`${ENGINES.ENGINE_C}/api/profile`);
  }

  // ENGINE D - Chatbot & Commands
  async sendChatMessage(message, userId = 'raghu_chandra_raj') {
    return this.makeRequest(`${ENGINES.ENGINE_D}/api/chat`, {
      method: 'POST',
      body: JSON.stringify({ 
        message, 
        user_id: userId,
        context: 'indian_markets'
      })
    });
  }

  async executeChatCommand(command) {
    const commands = {
      '/portfolio': () => this.sendChatMessage('/portfolio'),
      '/holdings': () => this.sendChatMessage('/holdings'),
      '/pnl': () => this.sendChatMessage('/pnl'),
      '/market': () => this.sendChatMessage('/market NSE'),
      '/signals': () => this.sendChatMessage('/signals indian')
    };
    
    if (commands[command]) {
      return await commands[command]();
    } else {
      return this.sendChatMessage(command);
    }
  }

  async getChatHistory(userId = 'raghu_chandra_raj') {
    return this.makeRequest(`${ENGINES.ENGINE_D}/api/chat/history/${userId}`);
  }

  // ENGINE ULTRA - Aggressive Trading
  async getUltraSignals() {
    return this.makeRequest(`${ENGINES.ENGINE_ULTRA}/api/ultra-signals`, {
      method: 'POST',
      body: JSON.stringify({
        market: 'indian',
        risk_level: 'high',
        exchanges: ['NSE', 'BSE']
      })
    });
  }

  async getAggressiveTrades() {
    return this.makeRequest(`${ENGINES.ENGINE_ULTRA}/api/aggressive-trades`);
  }

  async enableUltraMode(settings = {}) {
    return this.makeRequest(`${ENGINES.ENGINE_ULTRA}/api/enable-ultra`, {
      method: 'POST',
      body: JSON.stringify({
        ...settings,
        market_focus: 'indian_only',
        max_position_size: settings.max_position_size || 100000 // ₹1L default
      })
    });
  }

  async disableUltraMode() {
    return this.makeRequest(`${ENGINES.ENGINE_ULTRA}/api/disable-ultra`, {
      method: 'POST'
    });
  }

  // Combined Dashboard Data
  async getDashboardData() {
    try {
      const [marketData, aiSignals, portfolio, ultraSignals] = await Promise.allSettled([
        this.getMarketData(),
        this.getAISignals(),
        this.getPortfolio(),
        this.getUltraSignals()
      ]);
      
      return {
        market: marketData.status === 'fulfilled' ? marketData.value : null,
        ai_signals: aiSignals.status === 'fulfilled' ? aiSignals.value : null,
        portfolio: portfolio.status === 'fulfilled' ? portfolio.value : null,
        ultra_signals: ultraSignals.status === 'fulfilled' ? ultraSignals.value : null,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw error;
    }
  }

  // Health Check All Engines
  async healthCheck() {
    const healthPromises = Object.entries(ENGINES).map(async ([name, url]) => {
      try {
        const response = await fetch(`${url}/health`, { timeout: 5000 });
        return {
          engine: name,
          status: response.ok ? 'healthy' : 'unhealthy',
          url: url
        };
      } catch (error) {
        return {
          engine: name,
          status: 'error',
          error: error.message,
          url: url
        };
      }
    });
    
    const results = await Promise.allSettled(healthPromises);
    return results.map(result => result.status === 'fulfilled' ? result.value : { status: 'failed' });
  }

  // Format currency to Indian Rupees
  formatINR(amount) {
    if (typeof amount !== 'number') return '₹0.00';
    
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(amount);
  }

  // Format percentage
  formatPercentage(value) {
    if (typeof value !== 'number') return '0.00%';
    return `${value.toFixed(2)}%`;
  }
}

const apiService = new ApiService();
export default apiService;
export { ENGINES, apiService };