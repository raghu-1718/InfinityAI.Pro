"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DhanClient = void 0;
const axios_1 = __importDefault(require("axios"));
class DhanClient {
    constructor(apiKey, baseUrl = "https://openapi.dhan.co") {
        this.accessToken = null;
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replace(/\/+$/, "");
    }
    /**
     * Generate access token from request token (OAuth flow)
     */
    async generateAccessToken(requestToken) {
        var _a, _b;
        try {
            const response = await axios_1.default.post(`${this.baseUrl}/public/token`, {
                api_key: this.apiKey,
                request_token: requestToken
            });
            if (response.data.access_token) {
                this.accessToken = response.data.access_token;
                return this.accessToken;
            }
            else {
                throw new Error("Failed to generate access token");
            }
        }
        catch (error) {
            throw new Error(`Dhan token generation failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Set access token directly (for testing or manual auth)
     */
    setAccessToken(token) {
        this.accessToken = token;
    }
    getHeaders() {
        if (!this.accessToken) {
            throw new Error("Dhan access token not set. Call generateAccessToken() or setAccessToken() first.");
        }
        return {
            "Authorization": `Bearer ${this.accessToken}`,
            "Content-Type": "application/json"
        };
    }
    /**
     * Place an order
     */
    async placeOrder(params) {
        var _a, _b;
        try {
            const response = await axios_1.default.post(`${this.baseUrl}/orders`, params, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan order placement failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get order book
     */
    async getOrders() {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/orders`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get orders failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get specific order
     */
    async getOrder(orderId) {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/orders/${orderId}`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get order failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Cancel an order
     */
    async cancelOrder(orderId) {
        var _a, _b;
        try {
            const response = await axios_1.default.delete(`${this.baseUrl}/orders/${orderId}`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan cancel order failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get positions
     */
    async getPositions() {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/portfolio/positions`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get positions failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get holdings
     */
    async getHoldings() {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/portfolio/holdings`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get holdings failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get market quotes
     */
    async getQuotes(securityIds) {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/marketfeed`, {
                headers: this.getHeaders(),
                params: { securityId: securityIds.join(',') }
            });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get quotes failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get historical data
     */
    async getHistoricalData(securityId, exchangeSegment, instrument, fromDate, toDate) {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/charts`, {
                headers: this.getHeaders(),
                params: {
                    securityId,
                    exchangeSegment,
                    instrument,
                    fromDate,
                    toDate
                }
            });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get historical data failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Get funds/margin
     */
    async getFunds() {
        var _a, _b;
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/funds`, { headers: this.getHeaders() });
            return response.data;
        }
        catch (error) {
            throw new Error(`Dhan get funds failed: ${((_b = (_a = error.response) === null || _a === void 0 ? void 0 : _a.data) === null || _b === void 0 ? void 0 : _b.message) || error.message}`);
        }
    }
    /**
     * Test connection
     */
    async ping() {
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/ping`, { headers: this.getHeaders() });
            return response.status === 200;
        }
        catch (error) {
            return false;
        }
    }
}
exports.DhanClient = DhanClient;
