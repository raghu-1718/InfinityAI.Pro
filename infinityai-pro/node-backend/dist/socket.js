"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SocketManager = void 0;
exports.createSocketManager = createSocketManager;
class SocketManager {
    constructor(io, tradingManager, apiKey) {
        this.activeSignals = new Map();
        this.io = io;
        this.tradingManager = tradingManager;
        this.apiKey = apiKey;
        this.setupSocketHandlers();
        this.startPeriodicUpdates();
    }
    setupSocketHandlers() {
        this.io.use((socket, next) => {
            const auth = socket.handshake.auth;
            if (!auth || auth.key !== this.apiKey) {
                return next(new Error("Authentication failed"));
            }
            socket.data.userId = auth.userId || "anonymous";
            next();
        });
        this.io.on("connection", (socket) => {
            console.log(`Client connected: ${socket.id} (User: ${socket.data.userId})`);
            // Handle subscription to trade signals
            socket.on("subscribe_signals", () => {
                socket.join("signals");
                console.log(`Client ${socket.id} subscribed to signals`);
                // Send any active signals
                this.activeSignals.forEach(signal => {
                    socket.emit("signal", signal);
                });
            });
            socket.on("unsubscribe_signals", () => {
                socket.leave("signals");
                console.log(`Client ${socket.id} unsubscribed from signals`);
            });
            // Handle manual trade execution
            socket.on("execute_trade", async (signal) => {
                try {
                    console.log(`Manual trade execution requested by ${socket.data.userId}:`, signal);
                    const result = await this.tradingManager.placeOrder(signal);
                    socket.emit("trade_executed", {
                        signal,
                        result,
                        timestamp: new Date()
                    });
                    // Broadcast to all subscribers
                    this.io.to("signals").emit("trade_update", {
                        type: "executed",
                        signal,
                        result,
                        userId: socket.data.userId
                    });
                }
                catch (error) {
                    console.error("Trade execution failed:", error);
                    socket.emit("trade_error", {
                        signal,
                        error: error.message,
                        timestamp: new Date()
                    });
                }
            });
            // Handle auto-trade toggle
            socket.on("set_auto_trade", (enabled) => {
                socket.data.autoTrade = enabled;
                console.log(`Auto-trade ${enabled ? "enabled" : "disabled"} for ${socket.id}`);
                socket.emit("auto_trade_status", {
                    enabled,
                    timestamp: new Date()
                });
            });
            // Handle portfolio requests
            socket.on("get_portfolio", async (broker) => {
                try {
                    const portfolio = await this.tradingManager.getPortfolio(broker);
                    socket.emit("portfolio_data", portfolio);
                }
                catch (error) {
                    socket.emit("portfolio_error", {
                        broker,
                        error: error.message
                    });
                }
            });
            // Handle orders request
            socket.on("get_orders", async (broker) => {
                try {
                    const orders = await this.tradingManager.getOrders(broker);
                    socket.emit("orders_data", { broker, orders });
                }
                catch (error) {
                    socket.emit("orders_error", {
                        broker,
                        error: error.message
                    });
                }
            });
            // Handle emergency stop
            socket.on("emergency_stop", async () => {
                try {
                    console.log(`Emergency stop requested by ${socket.data.userId}`);
                    const results = await this.tradingManager.emergencyStop();
                    socket.emit("emergency_stop_result", {
                        results,
                        timestamp: new Date()
                    });
                    // Broadcast emergency stop to all clients
                    this.io.emit("system_alert", {
                        type: "emergency_stop",
                        message: "Emergency stop activated - all orders cancelled",
                        userId: socket.data.userId,
                        timestamp: new Date()
                    });
                }
                catch (error) {
                    socket.emit("emergency_stop_error", {
                        error: error.message,
                        timestamp: new Date()
                    });
                }
            });
            socket.on("disconnect", () => {
                console.log(`Client disconnected: ${socket.id}`);
            });
        });
    }
    /**
     * Broadcast a trade signal to all subscribed clients
     */
    broadcastSignal(signal) {
        this.activeSignals.set(signal.id, signal);
        this.io.to("signals").emit("signal", signal);
        // Auto-execute for clients with auto-trade enabled
        this.autoExecuteSignal(signal);
    }
    /**
     * Auto-execute signal for clients with auto-trade enabled
     */
    async autoExecuteSignal(signal) {
        const autoTradeSockets = await this.io.fetchSockets();
        for (const socket of autoTradeSockets) {
            if (socket.data.autoTrade && socket.rooms.has("signals")) {
                try {
                    console.log(`Auto-executing trade for ${socket.data.userId}:`, signal);
                    const result = await this.tradingManager.placeOrder(signal);
                    socket.emit("auto_trade_executed", {
                        signal,
                        result,
                        timestamp: new Date()
                    });
                    // Broadcast the execution
                    this.io.to("signals").emit("trade_update", {
                        type: "auto_executed",
                        signal,
                        result,
                        userId: socket.data.userId
                    });
                }
                catch (error) {
                    console.error(`Auto-trade failed for ${socket.data.userId}:`, error);
                    socket.emit("auto_trade_error", {
                        signal,
                        error: error.message,
                        timestamp: new Date()
                    });
                }
            }
        }
    }
    /**
     * Remove expired signals
     */
    cleanupSignals() {
        const now = new Date();
        const expiredIds = [];
        this.activeSignals.forEach((signal, id) => {
            // Remove signals older than 5 minutes
            if (now.getTime() - signal.timestamp.getTime() > 5 * 60 * 1000) {
                expiredIds.push(id);
            }
        });
        expiredIds.forEach(id => this.activeSignals.delete(id));
    }
    /**
     * Start periodic updates (portfolio, market data, etc.)
     */
    startPeriodicUpdates() {
        // Cleanup expired signals every 5 minutes
        setInterval(() => {
            this.cleanupSignals();
        }, 5 * 60 * 1000);
        // Send heartbeat every 30 seconds
        setInterval(() => {
            this.io.emit("heartbeat", {
                timestamp: new Date(),
                activeSignals: this.activeSignals.size,
                connectedClients: this.io.sockets.sockets.size
            });
        }, 30 * 1000);
        // Periodic portfolio updates (every 5 minutes)
        setInterval(async () => {
            try {
                const portfolios = await this.tradingManager.getCombinedPortfolio();
                this.io.to("signals").emit("portfolio_update", {
                    portfolios,
                    timestamp: new Date()
                });
            }
            catch (error) {
                console.error("Failed to send periodic portfolio update:", error);
            }
        }, 5 * 60 * 1000);
    }
    /**
     * Send system alert to all clients
     */
    sendSystemAlert(message, type = "info") {
        this.io.emit("system_alert", {
            type,
            message,
            timestamp: new Date()
        });
    }
    /**
     * Get connection statistics
     */
    getStats() {
        var _a;
        return {
            connectedClients: this.io.sockets.sockets.size,
            activeSignals: this.activeSignals.size,
            subscribedToSignals: ((_a = this.io.sockets.adapter.rooms.get("signals")) === null || _a === void 0 ? void 0 : _a.size) || 0
        };
    }
}
exports.SocketManager = SocketManager;
// Factory function to create socket manager
function createSocketManager(io, tradingManager, apiKey) {
    return new SocketManager(io, tradingManager, apiKey);
}
