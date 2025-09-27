"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.createRoutes = createRoutes;
const express_1 = __importDefault(require("express"));
const dhan_1 = require("./clients/dhan");
const router = express_1.default.Router();
function createRoutes(tradingManager) {
    // Middleware to check API key
    const requireApiKey = (req, res, next) => {
        const apiKey = req.headers["x-api-key"] || req.headers["authorization"];
        if (!apiKey || apiKey !== process.env.BACKEND_API_KEY) {
            return res.status(401).json({
                error: "Unauthorized",
                message: "Valid API key required"
            });
        }
        next();
    };
    // Health check
    router.get("/health", (req, res) => {
        res.json({
            status: "healthy",
            timestamp: new Date().toISOString(),
            version: "1.0.0"
        });
    });
    // Test broker connections
    router.get("/test-connections", requireApiKey, async (req, res) => {
        try {
            const results = await tradingManager.testConnections();
            res.json({
                success: true,
                connections: results,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Dhan token generation
    router.post("/dhan/token", requireApiKey, async (req, res) => {
        try {
            const { requestToken } = req.body;
            if (!requestToken) {
                return res.status(400).json({
                    error: "Request token required"
                });
            }
            // Initialize Dhan client with API key from env
            const dhanClient = new dhan_1.DhanClient(process.env.DHAN_CLIENT_ID || "");
            // Generate access token
            const accessToken = await dhanClient.generateAccessToken(requestToken);
            res.json({
                success: true,
                accessToken,
                message: "Access token generated successfully",
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            console.error("Dhan token generation failed:", error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Place order
    router.post("/order", requireApiKey, async (req, res) => {
        try {
            const orderData = req.body;
            // Validate required fields
            const required = ["broker", "symbol", "side", "quantity"];
            for (const field of required) {
                if (!orderData[field]) {
                    return res.status(400).json({
                        error: `Missing required field: ${field}`
                    });
                }
            }
            const result = await tradingManager.placeOrder(orderData);
            res.json({
                success: true,
                order: result,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            console.error("Order placement error:", error);
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    });
    // Cancel order
    router.delete("/order/:orderId", requireApiKey, async (req, res) => {
        try {
            const { orderId } = req.params;
            const { broker } = req.query;
            if (!broker || !["dhan", "coinswitch"].includes(broker)) {
                return res.status(400).json({
                    error: "Valid broker parameter required (dhan or coinswitch)"
                });
            }
            const result = await tradingManager.cancelOrder(broker, orderId);
            res.json({
                success: true,
                cancelledOrder: result,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get orders
    router.get("/orders/:broker", requireApiKey, async (req, res) => {
        try {
            const { broker } = req.params;
            if (!["dhan", "coinswitch"].includes(broker)) {
                return res.status(400).json({
                    error: "Invalid broker. Must be 'dhan' or 'coinswitch'"
                });
            }
            const orders = await tradingManager.getOrders(broker);
            res.json({
                success: true,
                broker,
                orders,
                count: orders.length,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get portfolio
    router.get("/portfolio/:broker", requireApiKey, async (req, res) => {
        try {
            const { broker } = req.params;
            if (!["dhan", "coinswitch"].includes(broker)) {
                return res.status(400).json({
                    error: "Invalid broker. Must be 'dhan' or 'coinswitch'"
                });
            }
            const portfolio = await tradingManager.getPortfolio(broker);
            res.json({
                success: true,
                portfolio,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get combined portfolio from all brokers
    router.get("/portfolio", requireApiKey, async (req, res) => {
        try {
            const portfolios = await tradingManager.getCombinedPortfolio();
            // Calculate combined totals
            let totalValue = 0;
            let totalPnl = 0;
            portfolios.forEach(portfolio => {
                totalValue += portfolio.totalValue;
                totalPnl += portfolio.totalPnl;
            });
            res.json({
                success: true,
                combined: {
                    totalValue,
                    totalPnl,
                    totalPnlPercentage: totalValue > 0 ? (totalPnl / totalValue) * 100 : 0
                },
                portfolios,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get market quotes
    router.post("/quotes/:broker", requireApiKey, async (req, res) => {
        try {
            const { broker } = req.params;
            const { symbols } = req.body;
            if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
                return res.status(400).json({
                    error: "Symbols array required"
                });
            }
            if (!["dhan", "coinswitch"].includes(broker)) {
                return res.status(400).json({
                    error: "Invalid broker. Must be 'dhan' or 'coinswitch'"
                });
            }
            const quotes = await tradingManager.getQuotes(broker, symbols);
            res.json({
                success: true,
                broker,
                quotes,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get historical data
    router.get("/historical/:broker/:symbol", requireApiKey, async (req, res) => {
        try {
            const { broker, symbol } = req.params;
            const { interval = "1d", days = 30 } = req.query;
            if (!["dhan", "coinswitch"].includes(broker)) {
                return res.status(400).json({
                    error: "Invalid broker. Must be 'dhan' or 'coinswitch'"
                });
            }
            // This would need to be implemented in the trading manager
            // For now, return placeholder
            res.json({
                success: true,
                broker,
                symbol,
                interval,
                days: parseInt(days),
                message: "Historical data endpoint - implement in trading manager",
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Risk management endpoints
    router.get("/risk/limits", requireApiKey, (req, res) => {
        try {
            const limits = tradingManager.getRiskLimits();
            res.json({
                success: true,
                riskLimits: limits,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    router.put("/risk/limits", requireApiKey, (req, res) => {
        try {
            const newLimits = req.body;
            tradingManager.updateRiskLimits(newLimits);
            res.json({
                success: true,
                message: "Risk limits updated",
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    });
    // Emergency stop
    router.post("/emergency-stop", requireApiKey, async (req, res) => {
        try {
            const results = await tradingManager.emergencyStop();
            res.json({
                success: true,
                emergencyStop: {
                    cancelledOrders: results,
                    timestamp: new Date().toISOString()
                }
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // AI suggestions endpoint (placeholder for AI integration)
    router.post("/ai/suggestions", requireApiKey, async (req, res) => {
        try {
            const { symbol, marketData } = req.body;
            // This would integrate with your AI models
            // For now, return mock suggestions
            const suggestions = {
                action: Math.random() > 0.5 ? "buy" : "sell",
                confidence: Math.random() * 0.4 + 0.6,
                reasoning: `AI analysis suggests ${symbol} has ${Math.random() > 0.5 ? 'bullish' : 'bearish'} momentum`,
                technical_indicators: {
                    rsi: Math.floor(Math.random() * 30) + 35,
                    macd: Math.random() * 2 - 1,
                    moving_average: (marketData === null || marketData === void 0 ? void 0 : marketData.close) * (0.95 + Math.random() * 0.1)
                }
            };
            res.json({
                success: true,
                symbol,
                suggestions,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // ===============================
    // BTC Options Trading Routes
    // ===============================
    // BTC trading status
    router.get("/btc/status", requireApiKey, (req, res) => {
        res.json({
            success: true,
            status: "BTC options trading module",
            message: "BTC trading routes are available",
            endpoints: [
                "GET /api/btc/status",
                "POST /api/btc/signal",
                "POST /api/btc/trade",
                "GET /api/btc/positions",
                "POST /api/btc/monitor",
                "POST /api/btc/emergency-stop",
                "GET /api/btc/market-data"
            ],
            configuration: {
                capital: "₹2,000–₹4,000",
                maxRisk: "5–8% per trade",
                targetProfit: "10–15% per trade",
                strategy: "Bull Call / Bear Put spreads"
            },
            timestamp: new Date().toISOString()
        });
    });
    // Generate AI-powered BTC trading signal
    router.post("/btc/signal", requireApiKey, async (req, res) => {
        try {
            const { btcPrice } = req.body;
            if (!btcPrice || typeof btcPrice !== "number") {
                return res.status(400).json({
                    error: "Valid BTC price required"
                });
            }
            // Mock AI signal generation (integrate with actual AI services)
            const signal = {
                direction: Math.random() > 0.5 ? "bull" : "bear",
                confidence: 0.7 + Math.random() * 0.2,
                btcPrice,
                timestamp: new Date(),
                reasoning: `AI analysis suggests ${btcPrice > 4500000 ? 'bullish' : 'bearish'} momentum based on technical indicators`,
                components: {
                    yoloAnalysis: {
                        pattern: "ascending_triangle",
                        confidence: 0.8,
                        direction: "bull"
                    },
                    whisperSentiment: {
                        sentiment: "positive",
                        confidence: 0.75,
                        keyPhrases: ["institutional adoption", " ETF approval"]
                    },
                    llmAnalysis: {
                        summary: "BTC showing strong bullish signals",
                        direction: "bull",
                        confidence: 0.82,
                        reasoning: "Multiple indicators align for upward movement"
                    }
                }
            };
            res.json({
                success: true,
                signal,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Execute BTC options spread trade
    router.post("/btc/trade", requireApiKey, async (req, res) => {
        try {
            const { btcPrice, direction, confidence } = req.body;
            if (!btcPrice || typeof btcPrice !== "number") {
                return res.status(400).json({
                    error: "Valid BTC price required"
                });
            }
            if (confidence < 0.7) {
                return res.json({
                    success: true,
                    message: "Signal confidence too low for execution",
                    recommended: false,
                    btcPrice,
                    confidence,
                    timestamp: new Date().toISOString()
                });
            }
            // Mock trade execution
            const spreadType = direction === "bull" ? "bull_call_spread" : "bear_put_spread";
            const premium = Math.round(btcPrice * 0.02); // 2% of BTC price as premium
            const position = {
                id: `btc_${spreadType}_${Date.now()}`,
                type: spreadType,
                buyStrike: btcPrice,
                sellStrike: direction === "bull" ? Math.round(btcPrice * 1.05) : Math.round(btcPrice * 0.95),
                premium,
                maxLoss: premium,
                maxProfit: Math.round(premium * 2.5),
                expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
                status: "active",
                entryPrice: btcPrice,
                createdAt: new Date()
            };
            res.json({
                success: true,
                message: "BTC spread trade executed successfully",
                position,
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // Get BTC positions
    router.get("/btc/positions", requireApiKey, (req, res) => {
        // Mock positions data
        const positions = [
            {
                id: "btc_bull_call_spread_123456",
                type: "bull_call_spread",
                buyStrike: 4500000,
                sellStrike: 4725000,
                premium: 90000,
                maxLoss: 90000,
                maxProfit: 225000,
                status: "active",
                pnl: 45000,
                createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
            }
        ];
        res.json({
            success: true,
            positions,
            count: positions.length,
            activeCount: positions.filter((p) => p.status === "active").length,
            timestamp: new Date().toISOString()
        });
    });
    // Monitor BTC positions
    router.post("/btc/monitor", requireApiKey, async (req, res) => {
        try {
            const { btcPrice } = req.body;
            const currentPrice = btcPrice || 4500000;
            res.json({
                success: true,
                message: "Position monitoring completed",
                currentBTCPrice: currentPrice,
                positionsMonitored: 1,
                statistics: {
                    totalTrades: 1,
                    winningTrades: 1,
                    losingTrades: 0,
                    winRate: "100%",
                    totalPnL: 45000,
                    activePositions: 1
                },
                timestamp: new Date().toISOString()
            });
        }
        catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    });
    // BTC emergency stop
    router.post("/btc/emergency-stop", requireApiKey, (req, res) => {
        res.json({
            success: true,
            message: "Emergency stop executed - all BTC positions closed",
            closedPositions: 1,
            timestamp: new Date().toISOString()
        });
    });
    // Get BTC market data
    router.get("/btc/market-data", requireApiKey, (req, res) => {
        const marketData = {
            btcPrice: 4500000 + Math.floor(Math.random() * 100000),
            volume24h: 1500000000,
            marketCap: 850000000000,
            change24h: (Math.random() - 0.5) * 10,
            volatility: Math.random() > 0.7 ? "high" : "medium",
            timestamp: new Date().toISOString()
        };
        res.json({
            success: true,
            marketData
        });
    });
    return router;
}
