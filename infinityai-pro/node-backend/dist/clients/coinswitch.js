"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CoinSwitchClient = void 0;
const axios_1 = __importDefault(require("axios"));
const crypto_1 = require("crypto");
class CoinSwitchClient {
    constructor(apiKey, apiSecret, baseUrl = "https://api-trading.coinswitch.co") {
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.baseUrl = baseUrl.replace(/\/+$/, "");
    }
    /**
     * Generate HMAC-SHA256 signature for authentication
     */
    generateSignature(path, params) {
        // Sort parameters by key
        const sortedKeys = Object.keys(params).sort();
        const queryString = sortedKeys
            .map(key => `${key}=${params[key]}`)
            .join("&");
        // Create payload: path?queryString
        const payload = `${path}?${queryString}`;
        // Generate HMAC-SHA256 signature
        return (0, crypto_1.createHmac)("sha256", this.apiSecret)
            .update(payload)
            .digest("hex");
    }
    /**
     * Make authenticated request to CoinSwitch API
     */
    async request(method, path, params = {}) {
        var _a, _b;
        // Add timestamp to params
        params.timestamp = Date.now();
        // Generate signature
        const signature = this.generateSignature(path, params);
        // Set headers
        const headers = {
            "Content-Type": "application/json",
            "X-AUTH-APIKEY": this.apiKey,
            "X-AUTH-SIGNATURE": signature
        };
        const url = `${this.baseUrl}${path}`;
        try {
            let response;
            if (method === "GET") {
                response = await axios_1.default.get(url, { params, headers });
            }
            else if (method === "POST") {
                response = await axios_1.default.post(url, params, { headers });
            }
            else if (method === "DELETE") {
                response = await axios_1.default.delete(url, { data: params, headers });
            }
            else {
                throw new Error(`Unsupported HTTP method: ${method}`);
            }
            return response.data;
        }
        catch (error) {
            throw new Error(`CoinSwitch API error: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.msg) || error.message}`);
        }
    }
    /**
     * Test API connectivity
     */
    async ping() {
        return this.request("GET", "/trade/api/v2/ping");
    }
    /**
     * Get 24hr ticker statistics
     */
    async getTicker(symbol) {
        return this.request("GET", "/trade/api/v2/24hr/ticker", { symbol });
    }
    /**
     * Get all 24hr ticker statistics
     */
    async getAllTickers() {
        return this.request("GET", "/trade/api/v2/24hr/ticker", {});
    }
    /**
     * Create a new order
     */
    async createOrder(order) {
        const params = {
            symbol: order.symbol,
            side: order.side,
            quantity: order.quantity,
            type: order.type || "limit"
        };
        if (order.price && order.type !== "market") {
            params.price = order.price;
        }
        return this.request("POST", "/trade/api/v2/order", params);
    }
    /**
     * Cancel an order
     */
    async cancelOrder(orderId) {
        return this.request("DELETE", "/trade/api/v2/order", { order_id: orderId });
    }
    /**
     * Get open orders
     */
    async getOpenOrders(symbol) {
        const params = {};
        if (symbol) {
            params.symbol = symbol;
        }
        return this.request("GET", "/trade/api/v2/orders", params);
    }
    /**
     * Get order by ID
     */
    async getOrder(orderId) {
        const orders = await this.getOpenOrders();
        const order = orders.find(o => o.orderId === orderId);
        if (!order) {
            throw new Error(`Order ${orderId} not found`);
        }
        return order;
    }
    /**
     * Get account portfolio
     */
    async getPortfolio() {
        const response = await this.request("GET", "/trade/api/v2/user/portfolio", {});
        return response.data || [];
    }
    /**
     * Get account information
     */
    async getAccountInfo() {
        return this.request("GET", "/trade/api/v2/account", {});
    }
    /**
     * Get trade history
     */
    async getTradeHistory(symbol, limit = 100) {
        const params = { limit };
        if (symbol) {
            params.symbol = symbol;
        }
        return this.request("GET", "/trade/api/v2/myTrades", params);
    }
    /**
     * Get klines/candlestick data
     */
    async getKlines(symbol, interval, limit = 100) {
        return this.request("GET", "/trade/api/v2/klines", {
            symbol,
            interval,
            limit
        });
    }
    /**
     * Get order book depth
     */
    async getOrderBook(symbol, limit = 100) {
        return this.request("GET", "/trade/api/v2/depth", {
            symbol,
            limit
        });
    }
    /**
     * Get recent trades
     */
    async getRecentTrades(symbol, limit = 100) {
        return this.request("GET", "/trade/api/v2/trades", {
            symbol,
            limit
        });
    }
    /**
     * Test connectivity and authentication
     */
    async testConnection() {
        try {
            await this.ping();
            return true;
        }
        catch (error) {
            console.error("CoinSwitch connection test failed:", error);
            return false;
        }
    }
    /**
     * Get exchange info
     */
    async getExchangeInfo() {
        return this.request("GET", "/trade/api/v2/exchangeInfo", {});
    }
    /**
     * Get all supported symbols
     */
    async getSymbols() {
        var _a;
        const exchangeInfo = await this.getExchangeInfo();
        return ((_a = exchangeInfo.symbols) === null || _a === void 0 ? void 0 : _a.map((s) => s.symbol)) || [];
    }
}
exports.CoinSwitchClient = CoinSwitchClient;
