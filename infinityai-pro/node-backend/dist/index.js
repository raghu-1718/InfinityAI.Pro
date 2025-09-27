"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const http_1 = require("http");
const socket_io_1 = require("socket.io");
const dotenv_1 = __importDefault(require("dotenv"));
const tradingManager_1 = require("./tradingManager");
const dhan_1 = require("./clients/dhan");
const coinswitch_1 = require("./clients/coinswitch");
const routes_1 = require("./routes");
const socket_1 = require("./socket");
// Load environment variables
dotenv_1.default.config();
async function main() {
    // Validate required environment variables
    const requiredEnvVars = [
        "BACKEND_API_KEY",
        "DHAN_CLIENT_ID",
        "DHAN_ACCESS_TOKEN",
        "COINSWITCH_API_KEY",
        "COINSWITCH_API_SECRET"
    ];
    const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);
    if (missingVars.length > 0) {
        console.error("Missing required environment variables:", missingVars);
        process.exit(1);
    }
    // Initialize broker clients
    const dhanClient = new dhan_1.DhanClient(process.env.DHAN_ACCESS_TOKEN, process.env.DHAN_DEMO === "true" ? "https://api.dhan.co" : "https://openapi.dhan.co");
    const coinSwitchClient = new coinswitch_1.CoinSwitchClient(process.env.COINSWITCH_API_KEY, process.env.COINSWITCH_API_SECRET, process.env.COINSWITCH_DEMO === "true" ? "https://api-sandbox.coinswitch.co" : "https://api-trading.coinswitch.co");
    // Initialize trading manager
    const tradingManager = new tradingManager_1.TradingManager({
        dhanClient,
        coinSwitchClient,
        riskLimits: {
            maxOrderValue: parseFloat(process.env.MAX_ORDER_VALUE || "100000"),
            maxDailyLoss: parseFloat(process.env.MAX_DAILY_LOSS || "50000"),
            maxPositionSize: parseFloat(process.env.MAX_POSITION_SIZE || "10000"),
            maxOpenPositions: parseInt(process.env.MAX_OPEN_POSITIONS || "10"),
            allowedBrokers: (process.env.ALLOWED_BROKERS || "dhan,coinswitch").split(",")
        }
    });
    // Initialize Express app
    const app = (0, express_1.default)();
    const port = parseInt(process.env.PORT || "3001");
    // Middleware
    app.use((0, cors_1.default)({
        origin: process.env.FRONTEND_URL || "http://localhost:3000",
        credentials: true
    }));
    app.use(express_1.default.json({ limit: "10mb" }));
    app.use(express_1.default.urlencoded({ extended: true }));
    // Health check (no auth required)
    app.get("/health", (req, res) => {
        res.json({
            status: "healthy",
            timestamp: new Date().toISOString(),
            version: "1.0.0",
            uptime: process.uptime()
        });
    });
    // API routes
    const apiRouter = (0, routes_1.createRoutes)(tradingManager);
    app.use("/api", apiRouter);
    // Create HTTP server
    const server = (0, http_1.createServer)(app);
    // Initialize Socket.IO
    const io = new socket_io_1.Server(server, {
        cors: {
            origin: process.env.FRONTEND_URL || "http://localhost:3000",
            methods: ["GET", "POST"],
            credentials: true
        }
    });
    // Initialize socket manager
    const socketManager = (0, socket_1.createSocketManager)(io, tradingManager, process.env.BACKEND_API_KEY);
    // Start server
    server.listen(port, () => {
        console.log(`🚀 InfinityAI Pro Backend Server running on port ${port}`);
        console.log(`📊 Health check: http://localhost:${port}/health`);
        console.log(`🔗 API endpoints: http://localhost:${port}/api`);
        console.log(`🌐 Socket.IO: ws://localhost:${port}`);
    });
    // Graceful shutdown
    process.on("SIGTERM", async () => {
        console.log("🛑 Received SIGTERM, shutting down gracefully...");
        try {
            // Close all connections
            await tradingManager.emergencyStop();
            io.close();
            server.close();
            console.log("✅ Server shut down successfully");
            process.exit(0);
        }
        catch (error) {
            console.error("❌ Error during shutdown:", error);
            process.exit(1);
        }
    });
    process.on("SIGINT", async () => {
        console.log("🛑 Received SIGINT, shutting down gracefully...");
        process.kill(process.pid, "SIGTERM");
    });
    // Handle uncaught exceptions
    process.on("uncaughtException", (error) => {
        console.error("💥 Uncaught Exception:", error);
        process.exit(1);
    });
    process.on("unhandledRejection", (reason, promise) => {
        console.error("💥 Unhandled Rejection at:", promise, "reason:", reason);
        process.exit(1);
    });
}
// Start the server
main().catch((error) => {
    console.error("💥 Failed to start server:", error);
    process.exit(1);
});
