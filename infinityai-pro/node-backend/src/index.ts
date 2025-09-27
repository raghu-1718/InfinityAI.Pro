import express from "express";
import cors from "cors";
import { createServer } from "http";
import { Server } from "socket.io";
import dotenv from "dotenv";
import { TradingManager } from "./tradingManager";
import { DhanClient } from "./clients/dhan";
import { CoinSwitchClient } from "./clients/coinswitch";
import { createRoutes } from "./routes";
import { createSocketManager } from "./socket";

// Load environment variables
dotenv.config();

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
  const dhanClient = new DhanClient(
    process.env.DHAN_ACCESS_TOKEN!,
    process.env.DHAN_DEMO === "true" ? "https://api.dhan.co" : "https://openapi.dhan.co"
  );

  const coinSwitchClient = new CoinSwitchClient(
    process.env.COINSWITCH_API_KEY!,
    process.env.COINSWITCH_API_SECRET!,
    process.env.COINSWITCH_DEMO === "true" ? "https://api-sandbox.coinswitch.co" : "https://api-trading.coinswitch.co"
  );

  // Initialize trading manager
  const tradingManager = new TradingManager({
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
  const app = express();
  const port = parseInt(process.env.PORT || "3001");

  // Middleware
  app.use(cors({
    origin: process.env.FRONTEND_URL || "http://localhost:3000",
    credentials: true
  }));

  app.use(express.json({ limit: "10mb" }));
  app.use(express.urlencoded({ extended: true }));

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
  const apiRouter = createRoutes(tradingManager);
  app.use("/api", apiRouter);

  // Create HTTP server
  const server = createServer(app);

  // Initialize Socket.IO
  const io = new Server(server, {
    cors: {
      origin: process.env.FRONTEND_URL || "http://localhost:3000",
      methods: ["GET", "POST"],
      credentials: true
    }
  });

  // Initialize socket manager
  const socketManager = createSocketManager(io, tradingManager, process.env.BACKEND_API_KEY!);

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
    } catch (error) {
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