"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.BTCOptionsTrader = void 0;
const axios_1 = __importDefault(require("axios"));
// Mock CoinSwitch client for BTC options
class CoinSwitchBTCClient {
    constructor(apiKey, apiSecret) {
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.baseUrl = "https://api.coinswitch.co"; // BTC options endpoint
    }
    async placeBTCSpreadOrder(spread) {
        // Mock implementation - replace with actual CoinSwitch BTC options API
        console.log("Placing BTC spread order:", spread);
        // Simulate API call
        return {
            orderId: `btc_${Date.now()}`,
            status: "placed",
            spread
        };
    }
    async closeBTCSpreadOrder(orderId) {
        // Mock implementation
        console.log("Closing BTC spread order:", orderId);
        return {
            orderId,
            status: "closed",
            pnl: Math.random() * 1000 - 500 // Random P&L for demo
        };
    }
    async getBTCPrice() {
        // Get current BTC price from CoinSwitch
        try {
            const response = await axios_1.default.get(`${this.baseUrl}/trade/api/v2/24hr/ticker`, {
                params: { symbol: "BTCINR" }
            });
            return response.data.lastPrice;
        }
        catch (error) {
            console.error("Failed to get BTC price:", error);
            return 4500000; // Fallback price
        }
    }
}
class BTCOptionsTrader {
    constructor(config) {
        this.activePositions = new Map();
        this.coinSwitchClient = new CoinSwitchBTCClient(config.coinSwitchApiKey, config.coinSwitchApiSecret);
        this.capital = config.capital;
        this.maxRiskPercent = config.maxRiskPercent;
        this.targetProfitPercent = config.targetProfitPercent;
    }
    /**
     * Execute BTC options spread trade based on AI signal
     */
    async executeSpreadTrade(signal) {
        // Validate signal confidence
        if (signal.confidence < 0.7) {
            console.log(`Signal confidence ${signal.confidence} too low, skipping trade`);
            return null;
        }
        // Check if we already have an active position
        if (this.activePositions.size > 0) {
            console.log("Active position exists, skipping new trade");
            return null;
        }
        // Calculate position sizing
        const maxRiskAmount = this.capital * this.maxRiskPercent;
        const targetProfitAmount = this.capital * this.targetProfitPercent;
        // Determine spread type and strikes
        const spreadType = signal.direction === "bull" ? "bull_call_spread" : "bear_put_spread";
        const buyStrike = signal.btcPrice; // ATM strike
        const strikeDistance = signal.btcPrice * 0.05; // 5% OTM
        const sellStrike = signal.direction === "bull"
            ? Math.round(signal.btcPrice + strikeDistance)
            : Math.round(signal.btcPrice - strikeDistance);
        // Calculate premium (max loss)
        const premium = maxRiskAmount;
        // Calculate max profit potential
        const maxProfit = (Math.abs(sellStrike - buyStrike) * 0.1) - premium; // Conservative estimate
        // Create position record
        const position = {
            id: `btc_${spreadType}_${Date.now()}`,
            type: spreadType,
            buyStrike,
            sellStrike,
            premium,
            maxLoss: premium,
            maxProfit,
            expiry: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 1 week expiry
            status: "active",
            entryPrice: signal.btcPrice,
            createdAt: new Date()
        };
        try {
            // Execute the spread order via CoinSwitch
            const orderResult = await this.placeSpreadOrder(position);
            if (orderResult) {
                this.activePositions.set(position.id, position);
                console.log(`BTC ${spreadType} position opened:`, position);
                return position;
            }
            return null;
        }
        catch (error) {
            console.error("Failed to execute BTC spread trade:", error);
            return null;
        }
    }
    /**
     * Place spread order on CoinSwitch
     */
    async placeSpreadOrder(position) {
        try {
            // This would integrate with CoinSwitch BTC options API
            // For now, simulate the order placement
            console.log(`Placing ${position.type} order:`, {
                symbol: "BTCINR",
                buyStrike: position.buyStrike,
                sellStrike: position.sellStrike,
                premium: position.premium
            });
            // Simulate API call to CoinSwitch
            // const response = await this.coinSwitchClient.placeBTCOptionsOrder({
            //   type: position.type,
            //   buyStrike: position.buyStrike,
            //   sellStrike: position.sellStrike,
            //   premium: position.premium,
            //   expiry: position.expiry
            // });
            // For demonstration, assume order placement succeeds
            return true;
        }
        catch (error) {
            console.error("CoinSwitch order placement failed:", error);
            return false;
        }
    }
    async monitorPositions(currentBTCPrice) {
        // Get current BTC price if not provided
        if (!currentBTCPrice) {
            currentBTCPrice = await this.coinSwitchClient.getBTCPrice();
        }
        // Use forEach instead of for...of to avoid iteration issues
        this.activePositions.forEach((position, id) => {
            if (position.status !== "active")
                return;
            // Calculate current P&L
            const priceMove = currentBTCPrice - position.entryPrice;
            const priceMovePercent = Math.abs(priceMove) / position.entryPrice;
            // Check stop-loss (5-8% loss threshold)
            if (this.shouldCloseForLoss(position, priceMove, priceMovePercent)) {
                this.closePosition(id, "stop_loss");
                return;
            }
            // Check profit target (10-15% gain)
            if (this.shouldCloseForProfit(position, priceMove, priceMovePercent)) {
                this.closePosition(id, "profit_target");
                return;
            }
            // Check expiry
            if (new Date() >= position.expiry) {
                this.closePosition(id, "expired");
                return;
            }
            // Update position value
            position.currentValue = this.calculatePositionValue(position, currentBTCPrice);
            position.pnl = position.currentValue - position.premium;
        });
    }
    /**
     * Check if position should be closed due to losses
     */
    shouldCloseForLoss(position, priceMove, priceMovePercent) {
        const lossThreshold = this.maxRiskPercent;
        if (position.type === "bull_call_spread") {
            // Close if BTC drops more than loss threshold
            return priceMove < 0 && priceMovePercent >= lossThreshold;
        }
        else {
            // Close if BTC rises more than loss threshold
            return priceMove > 0 && priceMovePercent >= lossThreshold;
        }
    }
    /**
     * Check if position should be closed for profit
     */
    shouldCloseForProfit(position, priceMove, priceMovePercent) {
        const profitThreshold = this.targetProfitPercent;
        if (position.type === "bull_call_spread") {
            // Close if BTC rises enough for profit target
            return priceMove > 0 && priceMovePercent >= profitThreshold;
        }
        else {
            // Close if BTC drops enough for profit target
            return priceMove < 0 && priceMovePercent >= profitThreshold;
        }
    }
    /**
     * Calculate current position value
     */
    calculatePositionValue(position, currentBTCPrice) {
        // Simplified calculation - in reality would depend on option pricing model
        const timeToExpiry = (position.expiry.getTime() - Date.now()) / (1000 * 60 * 60 * 24); // days
        const timeDecay = Math.max(0, timeToExpiry / 7); // normalize to 1 week
        if (position.type === "bull_call_spread") {
            if (currentBTCPrice <= position.buyStrike) {
                return 0; // Worthless
            }
            else if (currentBTCPrice >= position.sellStrike) {
                return position.maxProfit;
            }
            else {
                // Linear interpolation
                const range = position.sellStrike - position.buyStrike;
                const progress = currentBTCPrice - position.buyStrike;
                return (progress / range) * position.maxProfit * timeDecay;
            }
        }
        else {
            if (currentBTCPrice >= position.buyStrike) {
                return 0; // Worthless
            }
            else if (currentBTCPrice <= position.sellStrike) {
                return position.maxProfit;
            }
            else {
                // Linear interpolation
                const range = position.buyStrike - position.sellStrike;
                const progress = position.buyStrike - currentBTCPrice;
                return (progress / range) * position.maxProfit * timeDecay;
            }
        }
    }
    /**
     * Close a position
     */
    async closePosition(positionId, reason) {
        var _a;
        const position = this.activePositions.get(positionId);
        if (!position)
            return;
        try {
            // Close the spread position via CoinSwitch
            console.log(`Closing position ${positionId} for reason: ${reason}`);
            // Simulate closing order
            // const closeResult = await this.coinSwitchClient.closeBTCOptionsPosition(positionId);
            position.status = "closed";
            position.closedAt = new Date();
            // Calculate final P&L
            if (position.currentValue !== undefined) {
                position.pnl = position.currentValue - position.premium;
            }
            console.log(`Position ${positionId} closed. P&L: ₹${(_a = position.pnl) === null || _a === void 0 ? void 0 : _a.toFixed(2)}`);
            this.activePositions.delete(positionId);
        }
        catch (error) {
            console.error(`Failed to close position ${positionId}:`, error);
        }
    }
    /**
     * Get all positions
     */
    getPositions() {
        return Array.from(this.activePositions.values());
    }
    /**
     * Get trading statistics
     */
    getStats() {
        const positions = this.getPositions();
        const totalTrades = positions.length;
        const winningTrades = positions.filter(p => (p.pnl || 0) > 0).length;
        const losingTrades = positions.filter(p => (p.pnl || 0) < 0).length;
        const totalPnL = positions.reduce((sum, p) => sum + (p.pnl || 0), 0);
        const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;
        return {
            totalTrades,
            winningTrades,
            losingTrades,
            winRate: winRate.toFixed(1) + "%",
            totalPnL: totalPnL.toFixed(2),
            activePositions: positions.filter(p => p.status === "active").length,
            capital: this.capital,
            maxRiskPercent: (this.maxRiskPercent * 100) + "%",
            targetProfitPercent: (this.targetProfitPercent * 100) + "%"
        };
    }
    /**
     * Emergency stop - close all positions
     */
    async emergencyStop() {
        console.log("BTC Options Trader: Emergency stop activated");
        const positionIds = Array.from(this.activePositions.keys());
        for (const id of positionIds) {
            await this.closePosition(id, "stop_loss");
        }
    }
}
exports.BTCOptionsTrader = BTCOptionsTrader;
