/**
 * Ably Publisher Utility for Cloud Functions
 * Handles publishing real-time data to Ably channels
 */

import * as admin from "firebase-admin";
import axios from "axios";

const ABLY_API_BASE_URL = "https://rest.ably.io";
const ABLY_API_KEY = process.env.ABLY_API_KEY || "";

interface AblyMessage {
  name?: string;
  data: any;
  clientId?: string;
}

/**
 * Publish message to Ably channel using REST API
 */
export async function publishToAblyChannel(
  channelName: string,
  message: AblyMessage,
): Promise<void> {
  if (!ABLY_API_KEY) {
    throw new Error("ABLY_API_KEY environment variable is not set");
  }

  try {
    const encodedChannel = encodeURIComponent(channelName);
    const url = `${ABLY_API_BASE_URL}/channels/${encodedChannel}/messages`;

    const auth = Buffer.from(`:${ABLY_API_KEY}`).toString("base64");

    await axios.post(url, message, {
      headers: {
        Authorization: `Basic ${auth}`,
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error(`Failed to publish to Ably channel ${channelName}:`, error);
    throw error;
  }
}

/**
 * Publish market quote data
 */
export async function publishMarketQuote(data: {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
}): Promise<void> {
  await publishToAblyChannel("infinityai:live-quotes", {
    name: "quote-update",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });
}

/**
 * Publish trading signal
 */
export async function publishTradingSignal(data: {
  engineId: string;
  symbol: string;
  action: "BUY" | "SELL" | "HOLD";
  confidence: number;
  reason: string;
}): Promise<void> {
  // Publish to general channel
  await publishToAblyChannel("infinityai:trading-signals", {
    name: "signal",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });

  // Also publish to engine-specific channel
  await publishToAblyChannel(`infinityai:engine:${data.engineId}`, {
    name: "signal",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });
}

/**
 * Publish trade execution
 */
export async function publishTradeExecution(data: {
  tradeId: string;
  symbol: string;
  quantity: number;
  price: number;
  type: "BUY" | "SELL";
  status: "PENDING" | "EXECUTED" | "FAILED";
}): Promise<void> {
  await publishToAblyChannel("infinityai:trade-execution", {
    name: "trade-update",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });
}

/**
 * Publish portfolio update
 */
export async function publishPortfolioUpdate(
  userId: string,
  data: {
    totalValue: number;
    buyingPower: number;
    positions: Array<{
      symbol: string;
      quantity: number;
      avgPrice: number;
      currentPrice: number;
    }>;
  },
): Promise<void> {
  // Publish to user-specific channel
  await publishToAblyChannel(`infinityai:portfolio:${userId}`, {
    name: "portfolio-update",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });

  // Also publish to general channel
  await publishToAblyChannel("infinityai:portfolio-update", {
    name: "portfolio-update",
    data: {
      userId,
      ...data,
      timestamp: Date.now(),
    },
  });
}

/**
 * Publish system status
 */
export async function publishSystemStatus(data: {
  isOnline: boolean;
  engines: {
    [key: string]: {
      status: "operational" | "degraded" | "down";
      lastHeartbeat: number;
    };
  };
  latency: number;
}): Promise<void> {
  await publishToAblyChannel("infinityai:system-status", {
    name: "status-update",
    data: {
      ...data,
      timestamp: Date.now(),
    },
  });
}

/**
 * Publish user notification
 */
export async function publishNotification(
  userId: string,
  notification: {
    type: "info" | "warning" | "error" | "success";
    title: string;
    message: string;
  },
): Promise<void> {
  await publishToAblyChannel("infinityai:user-notifications", {
    name: "notification",
    data: {
      userId,
      ...notification,
      id: `${userId}-${Date.now()}`,
      timestamp: Date.now(),
    },
  });
}
