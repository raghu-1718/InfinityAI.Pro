/**
 * InfinityAI.Pro - Engine D: AI Chatbot & Trading Assistant
 * Serverless deployment on Vercel with AI Gateway integration
 * Optimized for global edge deployment and AI inference
 */

import { VercelRequest, VercelResponse } from '@vercel/node'
import { OpenAI } from 'openai'
import { Anthropic } from '@anthropic-ai/sdk'
import { Redis } from '@upstash/redis'
import { Kafka } from 'kafkajs'
import { createHash } from 'crypto'
import { nanoid } from 'nanoid'

// Environment configuration
const config = {
  environment: process.env.VERCEL_ENV || 'production',
  region: process.env.VERCEL_REGION || 'global',
  
  // AI Gateway configuration (mock mode if keys not available)
  openai: {
    apiKey: process.env.OPENAI_API_KEY || 'mock-key',
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
    mockMode: !process.env.OPENAI_API_KEY
  },
  
  anthropic: {
    apiKey: process.env.ANTHROPIC_API_KEY || 'mock-key',
    baseURL: process.env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com',
    mockMode: !process.env.ANTHROPIC_API_KEY
  },
  
  // Cross-cloud engine endpoints
  engines: {
    engineA: process.env.AZURE_ENGINE_A_URL || 'https://infinityai-engine-a.azurewebsites.net/api',
    engineB: process.env.GCP_ENGINE_B_URL || 'https://infinityai-engine-b.googleapis.com/api',
    engineC: process.env.AWS_ENGINE_C_URL || 'https://infinityai-engine-c.amazonaws.com/api'
  },
  
  // Database and messaging (optional)
  redis: {
    url: process.env.UPSTASH_REDIS_REST_URL || 'http://localhost:6379',
    token: process.env.UPSTASH_REDIS_REST_TOKEN || '',
    mockMode: !process.env.UPSTASH_REDIS_REST_URL
  },
  
  kafka: {
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(','),
    clientId: 'engine-d-vercel',
    sasl: process.env.KAFKA_SASL_MECHANISM ? {
      mechanism: process.env.KAFKA_SASL_MECHANISM as any,
      username: process.env.KAFKA_SASL_USERNAME!,
      password: process.env.KAFKA_SASL_PASSWORD!
    } : undefined
  },
  
  // Security
  jwtSecret: process.env.JWT_SECRET || 'your-secret-key-change-in-production',
  webhookSecret: process.env.WEBHOOK_SECRET || 'webhook-secret',
  
  // Rate limiting
  rateLimit: {
    maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000'),
  }
}

// Initialize clients (with mock fallbacks)
let openai: any, anthropic: any, redis: any;

if (!config.openai.mockMode) {
  openai = new OpenAI({
    apiKey: config.openai.apiKey,
    baseURL: config.openai.baseURL
  })
} else {
  // Mock OpenAI client
  openai = {
    chat: {
      completions: {
        create: async (params: any) => ({
          id: nanoid(),
          choices: [{
            message: {
              role: 'assistant',
              content: `Mock AI Response: I'm currently in demo mode. This is a simulated response to "${params.messages[params.messages.length - 1]?.content || 'your query'}". In production, I would provide real AI-powered trading insights and analysis.`
            },
            finish_reason: 'stop'
          }],
          usage: { prompt_tokens: 50, completion_tokens: 100, total_tokens: 150 }
        })
      }
    }
  }
}

if (!config.anthropic.mockMode) {
  anthropic = new Anthropic({
    apiKey: config.anthropic.apiKey,
    baseURL: config.anthropic.baseURL
  })
} else {
  // Mock Anthropic client
  anthropic = {
    messages: {
      create: async (params: any) => ({
        id: nanoid(),
        content: [{
          text: `Mock Claude Response: This is a demonstration response from Engine D. In production, I would analyze your query: "${params.messages[params.messages.length - 1]?.content || 'your request'}" and provide detailed trading insights.`
        }],
        usage: { input_tokens: 30, output_tokens: 80 },
        stop_reason: 'end_turn'
      })
    }
  }
}

if (!config.redis.mockMode) {
  redis = new Redis({
    url: config.redis.url,
    token: config.redis.token
  })
} else {
  // Mock Redis client
  const mockStore = new Map()
  redis = {
    get: async (key: string) => mockStore.get(key) || null,
    set: async (key: string, value: string) => mockStore.set(key, value),
    setex: async (key: string, ttl: number, value: string) => mockStore.set(key, value),
    expire: async (key: string, ttl: number) => true,
    del: async (key: string) => mockStore.delete(key),
    lrange: async (key: string, start: number, stop: number) => [],
    lpush: async (key: string, value: string) => 1,
    ltrim: async (key: string, start: number, stop: number) => true,
    zadd: async (key: string, scoreMembers: any) => 1,
    zcard: async (key: string) => 0,
    zremrangebyscore: async (key: string, min: number, max: number) => 0
  }
}

// Rate limiting
class RateLimiter {
  static async isAllowed(key: string, limit: number = 100, window: number = 60000): Promise<boolean> {
    const now = Date.now()
    const windowStart = now - window
    
    try {
      // Clean old entries
      await redis.zremrangebyscore(key, 0, windowStart)
      
      // Count current requests
      const count = await redis.zcard(key)
      
      if (count >= limit) {
        return false
      }
      
      // Add current request
      await redis.zadd(key, { score: now, member: now.toString() })
      await redis.expire(key, Math.ceil(window / 1000))
      
      return true
    } catch (error) {
      console.error('Rate limiting error:', error)
      return true // Allow on error
    }
  }
}

// AI Gateway routing with fallbacks
class AIGateway {
  static async chat(messages: any[], userId: string, options: any = {}): Promise<any> {
    const cacheKey = `chat:${createHash('md5').update(JSON.stringify(messages)).digest('hex')}`
    
    try {
      // Check cache first
      const cached = await redis.get(cacheKey)
      if (cached && !options.skipCache) {
        return JSON.parse(cached)
      }
      
      let response;
      const provider = options.provider || 'openai'
      
      if (provider === 'anthropic') {
        response = await anthropic.messages.create({
          model: 'claude-3-sonnet-20240229',
          max_tokens: options.maxTokens || 1000,
          messages: messages.map(msg => ({
            role: msg.role === 'assistant' ? 'assistant' : 'user',
            content: msg.content
          }))
        })
        
        response = {
          id: nanoid(),
          choices: [{
            message: {
              role: 'assistant',
              content: response.content[0].text
            },
            finish_reason: response.stop_reason
          }],
          usage: {
            prompt_tokens: response.usage?.input_tokens || 0,
            completion_tokens: response.usage?.output_tokens || 0,
            total_tokens: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0)
          }
        }
      } else {
        // Default to OpenAI
        response = await openai.chat.completions.create({
          model: config.openai.model,
          messages,
          max_tokens: options.maxTokens || 1000,
          temperature: options.temperature || 0.7,
          user: userId
        })
      }
      
      // Cache response
      await redis.setex(cacheKey, 3600, JSON.stringify(response)) // 1 hour cache
      
      return response
    } catch (error) {
      console.error(`AI Gateway error (${provider}):`, error)
      
      // Fallback to other provider
      if (provider === 'openai') {
        return this.chat(messages, userId, { ...options, provider: 'anthropic' })
      } else {
        return this.chat(messages, userId, { ...options, provider: 'openai' })
      }
    }
  }
  
  static async generateTradingInsight(marketData: any, userId: string): Promise<any> {
    const prompt = `
    As a professional trading AI assistant, analyze the following market data and provide actionable insights:
    
    Market Data: ${JSON.stringify(marketData, null, 2)}
    
    Please provide:
    1. Current market sentiment analysis
    2. Key support and resistance levels
    3. Trading opportunities (if any)
    4. Risk assessment
    5. Specific recommendations with entry/exit points
    
    Be concise but comprehensive. Focus on actionable insights.
    `
    
    const messages = [
      {
        role: 'system',
        content: 'You are a professional trading AI assistant with expertise in financial markets, technical analysis, and risk management.'
      },
      {
        role: 'user',
        content: prompt
      }
    ]
    
    return this.chat(messages, userId, { maxTokens: 1500, temperature: 0.3 })
  }
}

// Cross-cloud engine communication
class EngineOrchestrator {
  static async fetchMarketData(symbols: string[]): Promise<any> {
    try {
      const response = await fetch(`${config.engines.engineA}/api/v1/market/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.INTERNAL_API_TOKEN}`,
          'X-Source': 'engine-d-vercel'
        },
        body: JSON.stringify({ symbols, timeframe: '1min', limit: 50 })
      })
      
      if (!response.ok) {
        throw new Error(`Engine A error: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Engine A communication error:', error)
      return { error: 'Market data unavailable', symbols }
    }
  }
  
  static async requestAIAnalysis(data: any): Promise<any> {
    try {
      const response = await fetch(`${config.engines.engineB}/api/v1/analysis/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.INTERNAL_API_TOKEN}`,
          'X-Source': 'engine-d-vercel'
        },
        body: JSON.stringify({
          data,
          analysis_type: 'comprehensive',
          model: 'ensemble'
        })
      })
      
      if (!response.ok) {
        throw new Error(`Engine B error: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Engine B communication error:', error)
      return { error: 'AI analysis unavailable' }
    }
  }
  
  static async getPortfolioStatus(userId: string): Promise<any> {
    try {
      const response = await fetch(`${config.engines.engineC}/api/v1/portfolio/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${process.env.INTERNAL_API_TOKEN}`,
          'X-Source': 'engine-d-vercel',
          'X-User-ID': userId
        }
      })
      
      if (!response.ok) {
        throw new Error(`Engine C error: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Engine C communication error:', error)
      return { error: 'Portfolio data unavailable' }
    }
  }
}

// Message processing and context management
class ConversationManager {
  static async getConversationHistory(userId: string, limit: number = 10): Promise<any[]> {
    try {
      const history = await redis.lrange(`conversation:${userId}`, 0, limit - 1)
      return history.map(h => JSON.parse(h)).reverse()
    } catch (error) {
      console.error('Error fetching conversation history:', error)
      return []
    }
  }
  
  static async addMessage(userId: string, message: any): Promise<void> {
    try {
      const messageWithTimestamp = {
        ...message,
        timestamp: new Date().toISOString(),
        id: nanoid()
      }
      
      await redis.lpush(`conversation:${userId}`, JSON.stringify(messageWithTimestamp))
      await redis.ltrim(`conversation:${userId}`, 0, 49) // Keep last 50 messages
      await redis.expire(`conversation:${userId}`, 86400 * 7) // 7 days
    } catch (error) {
      console.error('Error saving conversation:', error)
    }
  }
  
  static async processUserMessage(userId: string, message: string, context: any = {}): Promise<any> {
    try {
      // Get conversation history
      const history = await this.getConversationHistory(userId, 5)
      
      // Determine intent
      const intent = await this.classifyIntent(message)
      
      let response;
      
      switch (intent.category) {
        case 'market_query':
          response = await this.handleMarketQuery(userId, message, intent, context)
          break
        case 'portfolio_query':
          response = await this.handlePortfolioQuery(userId, message, intent, context)
          break
        case 'trading_request':
          response = await this.handleTradingRequest(userId, message, intent, context)
          break
        case 'general_chat':
          response = await this.handleGeneralChat(userId, message, history, context)
          break
        default:
          response = await this.handleUnknownIntent(userId, message, context)
      }
      
      // Save conversation
      await this.addMessage(userId, { role: 'user', content: message, intent })
      await this.addMessage(userId, { role: 'assistant', content: response.message, type: response.type })
      
      return response
    } catch (error) {
      console.error('Error processing user message:', error)
      return {
        message: "I'm experiencing some technical difficulties. Please try again in a moment.",
        type: 'error',
        error: true
      }
    }
  }
  
  static async classifyIntent(message: string): Promise<any> {
    const marketKeywords = ['price', 'chart', 'stock', 'market', 'ticker', 'quote', 'analysis']
    const portfolioKeywords = ['portfolio', 'holdings', 'positions', 'balance', 'pnl', 'performance']
    const tradingKeywords = ['buy', 'sell', 'order', 'trade', 'invest', 'position', 'stop loss']
    
    const messageLower = message.toLowerCase()
    
    if (marketKeywords.some(keyword => messageLower.includes(keyword))) {
      return { category: 'market_query', confidence: 0.8 }
    } else if (portfolioKeywords.some(keyword => messageLower.includes(keyword))) {
      return { category: 'portfolio_query', confidence: 0.8 }
    } else if (tradingKeywords.some(keyword => messageLower.includes(keyword))) {
      return { category: 'trading_request', confidence: 0.8 }
    } else {
      return { category: 'general_chat', confidence: 0.6 }
    }
  }
  
  static async handleMarketQuery(userId: string, message: string, intent: any, context: any): Promise<any> {
    // Extract symbols from message
    const symbolRegex = /\b[A-Z]{1,5}\b/g
    const symbols = message.match(symbolRegex)?.slice(0, 5) || ['SPY', 'AAPL', 'TSLA']
    
    // Fetch market data
    const marketData = await EngineOrchestrator.fetchMarketData(symbols)
    
    if (marketData.error) {
      return {
        message: `I'm having trouble fetching market data right now. Please try again later.`,
        type: 'error'
      }
    }
    
    // Generate AI insight
    const aiInsight = await AIGateway.generateTradingInsight(marketData, userId)
    
    return {
      message: aiInsight.choices[0].message.content,
      type: 'market_analysis',
      data: {
        symbols,
        marketData,
        timestamp: new Date().toISOString()
      },
      metadata: {
        tokens_used: aiInsight.usage?.total_tokens || 0,
        model: config.openai.model
      }
    }
  }
  
  static async handlePortfolioQuery(userId: string, message: string, intent: any, context: any): Promise<any> {
    const portfolio = await EngineOrchestrator.getPortfolioStatus(userId)
    
    if (portfolio.error) {
      return {
        message: `I couldn't retrieve your portfolio information right now. This might be because you haven't connected your broker account yet, or there's a temporary issue. Would you like me to help you set up your broker connection?`,
        type: 'portfolio_error'
      }
    }
    
    const portfolioSummary = `
Here's your current portfolio summary:

**Total Value:** $${portfolio.total_value?.toLocaleString() || 'N/A'}
**Today's P&L:** ${portfolio.daily_pnl >= 0 ? '+' : ''}$${portfolio.daily_pnl?.toLocaleString() || 'N/A'} (${portfolio.daily_pnl_percent?.toFixed(2) || 'N/A'}%)
**Total P&L:** ${portfolio.total_pnl >= 0 ? '+' : ''}$${portfolio.total_pnl?.toLocaleString() || 'N/A'}

**Top Positions:**
${portfolio.positions?.slice(0, 5).map((pos: any) => 
  `• ${pos.symbol}: ${pos.quantity} shares @ $${pos.current_price} (${pos.pnl >= 0 ? '+' : ''}${pos.pnl_percent?.toFixed(2)}%)`
).join('\n') || 'No positions found'}

Is there anything specific about your portfolio you'd like to know more about?
    `.trim()
    
    return {
      message: portfolioSummary,
      type: 'portfolio_summary',
      data: portfolio
    }
  }
  
  static async handleTradingRequest(userId: string, message: string, intent: any, context: any): Promise<any> {
    const warningMessage = `
⚠️ **Trading Advisory Notice**

I can provide market analysis and educational information, but I cannot execute trades directly. For your security and compliance:

1. **Market Analysis**: I can analyze stocks, provide insights, and suggest potential opportunities
2. **Educational Content**: I can explain trading concepts and strategies  
3. **Portfolio Review**: I can help you understand your current positions

To execute trades, please:
- Use your connected broker's platform
- Review all analysis carefully
- Consider your risk tolerance
- Consult with a financial advisor for significant decisions

Would you like me to analyze any specific stocks or provide market insights instead?
    `.trim()
    
    return {
      message: warningMessage,
      type: 'trading_advisory',
      data: {
        disclaimer: true,
        timestamp: new Date().toISOString()
      }
    }
  }
  
  static async handleGeneralChat(userId: string, message: string, history: any[], context: any): Promise<any> {
    const messages = [
      {
        role: 'system',
        content: `You are InfinityAI Pro's trading assistant. You help users with financial markets, trading, and portfolio management. Be helpful, professional, and accurate. If asked about executing trades, remind users to use their broker platforms for actual trading.`
      },
      ...history.map(h => ({ role: h.role, content: h.content })),
      {
        role: 'user',
        content: message
      }
    ]
    
    const response = await AIGateway.chat(messages, userId, { maxTokens: 800 })
    
    return {
      message: response.choices[0].message.content,
      type: 'general_response',
      metadata: {
        tokens_used: response.usage?.total_tokens || 0
      }
    }
  }
  
  static async handleUnknownIntent(userId: string, message: string, context: any): Promise<any> {
    return {
      message: `I'm here to help with trading, market analysis, and portfolio management. Could you please clarify what you'd like to know about? For example, you can ask me about:

• Stock prices and market analysis
• Portfolio performance and holdings  
• Trading strategies and market insights
• Financial news and market trends

What would you like to explore?`,
      type: 'clarification_request'
    }
  }
}

// Main API handler
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-User-ID')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  try {
    const startTime = Date.now()
    const userId = req.headers['x-user-id'] as string || 'anonymous'
    const clientIP = req.headers['x-forwarded-for'] as string || req.connection?.remoteAddress || 'unknown'
    
    // Rate limiting
    const rateLimitKey = `rate_limit:${userId}:${clientIP}`
    const isAllowed = await RateLimiter.isAllowed(
      rateLimitKey,
      config.rateLimit.maxRequests,
      config.rateLimit.windowMs
    )
    
    if (!isAllowed) {
      return res.status(429).json({
        error: 'Rate limit exceeded',
        message: 'Too many requests. Please wait before trying again.',
        retry_after: Math.ceil(config.rateLimit.windowMs / 1000)
      })
    }
    
    // Health check endpoint
    if (req.method === 'GET' && req.url === '/health') {
      return res.status(200).json({
        status: 'healthy',
        service: 'Engine D - AI Chatbot',
        timestamp: new Date().toISOString(),
        version: '1.0.0',
        region: config.region,
        environment: config.environment
      })
    }
    
    // Chat endpoint
    if (req.method === 'POST' && (req.url === '/' || req.url?.startsWith('/chat'))) {
      const { message, context = {}, options = {} } = req.body
      
      if (!message) {
        return res.status(400).json({
          error: 'Missing message',
          message: 'Please provide a message to process'
        })
      }
      
      // Process the message
      const response = await ConversationManager.processUserMessage(userId, message, {
        ...context,
        clientIP,
        timestamp: new Date().toISOString(),
        region: config.region
      })
      
      const processingTime = Date.now() - startTime
      
      return res.status(200).json({
        ...response,
        metadata: {
          ...response.metadata,
          processing_time_ms: processingTime,
          user_id: userId,
          timestamp: new Date().toISOString(),
          engine: 'engine-d',
          cloud: 'vercel'
        }
      })
    }
    
    // Market analysis endpoint
    if (req.method === 'POST' && req.url?.startsWith('/analysis')) {
      const { symbols = [], analysis_type = 'basic' } = req.body
      
      if (!symbols.length) {
        return res.status(400).json({
          error: 'Missing symbols',
          message: 'Please provide symbols to analyze'
        })
      }
      
      const marketData = await EngineOrchestrator.fetchMarketData(symbols)
      const aiAnalysis = await AIGateway.generateTradingInsight(marketData, userId)
      
      return res.status(200).json({
        analysis: aiAnalysis.choices[0].message.content,
        market_data: marketData,
        symbols,
        timestamp: new Date().toISOString(),
        metadata: {
          processing_time_ms: Date.now() - startTime,
          tokens_used: aiAnalysis.usage?.total_tokens || 0
        }
      })
    }
    
    // Portfolio endpoint
    if (req.method === 'GET' && req.url?.startsWith('/portfolio')) {
      const portfolio = await EngineOrchestrator.getPortfolioStatus(userId)
      
      return res.status(200).json({
        portfolio,
        timestamp: new Date().toISOString(),
        metadata: {
          processing_time_ms: Date.now() - startTime,
          user_id: userId
        }
      })
    }
    
    // Default 404
    return res.status(404).json({
      error: 'Endpoint not found',
      message: 'Available endpoints: /health, /chat, /analysis, /portfolio',
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Engine D error:', error)
    
    return res.status(500).json({
      error: 'Internal server error',
      message: 'An unexpected error occurred while processing your request',
      timestamp: new Date().toISOString(),
      request_id: nanoid()
    })
  }
}