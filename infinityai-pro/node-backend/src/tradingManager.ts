import { DhanClient, DhanOrderParams } from "./clients/dhan";
import { CoinSwitchClient, CoinSwitchOrder } from "./clients/coinswitch";

export interface TradeOrder {
  broker: "dhan" | "coinswitch";
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price?: number;
  orderType?: "limit" | "market";
  // Dhan-specific fields
  exchangeSegment?: string;
  productType?: string;
  validity?: string;
  // Additional safety fields
  maxSlippage?: number;
  stopLoss?: number;
  takeProfit?: number;
}

export interface RiskLimits {
  maxOrderValue: number;        // Maximum value per order
  maxDailyLoss: number;         // Maximum daily loss
  maxPositionSize: number;      // Maximum position size as % of portfolio
  maxLeverage: number;          // Maximum leverage allowed
  allowedSymbols: string[];     // Whitelist of allowed symbols
  marketHoursOnly: boolean;     // Only allow orders during market hours
}

export interface PortfolioSummary {
  broker: string;
  totalValue: number;
  totalPnl: number;
  totalPnlPercentage: number;
  positions: any[];
  lastUpdated: Date;
}

export class TradingManager {
  private dhanClient?: DhanClient;
  private coinswitchClient?: CoinSwitchClient;
  private riskLimits: RiskLimits;
  private dailyLoss: number = 0;
  private lastResetDate: Date = new Date();

  constructor(env: any) {
    // Initialize clients
    if (env.DHAN_KEY) {
      this.dhanClient = new DhanClient(env.DHAN_KEY);
      if (env.DHAN_ACCESS_TOKEN) {
        this.dhanClient.setAccessToken(env.DHAN_ACCESS_TOKEN);
      }
    }

    if (env.COINSWITCH_KEY && env.COINSWITCH_SECRET) {
      this.coinswitchClient = new CoinSwitchClient(
        env.COINSWITCH_KEY,
        env.COINSWITCH_SECRET
      );
    }

    // Default risk limits (should be configurable)
    this.riskLimits = {
      maxOrderValue: parseFloat(env.MAX_ORDER_VALUE || "100000"), // ₹1 lakh default
      maxDailyLoss: parseFloat(env.MAX_DAILY_LOSS || "50000"),    // ₹50k default
      maxPositionSize: parseFloat(env.MAX_POSITION_SIZE || "0.1"), // 10% of portfolio
      maxLeverage: parseFloat(env.MAX_LEVERAGE || "1"),           // No leverage default
      allowedSymbols: (env.ALLOWED_SYMBOLS || "RELIANCE,TCS,INFY,HDFC,BTCINR,ETHINR").split(","),
      marketHoursOnly: env.MARKET_HOURS_ONLY === "true"
    };
  }

  /**
   * Reset daily loss counter (call this daily)
   */
  resetDailyLoss(): void {
    this.dailyLoss = 0;
    this.lastResetDate = new Date();
  }

  /**
   * Validate order against risk limits
   */
  private validateOrder(order: TradeOrder): void {
    const orderValue = (order.price || 0) * order.quantity;

    // Check order value limit
    if (orderValue > this.riskLimits.maxOrderValue) {
      throw new Error(`Order value ₹${orderValue.toLocaleString()} exceeds maximum allowed ₹${this.riskLimits.maxOrderValue.toLocaleString()}`);
    }

    // Check symbol whitelist
    if (!this.riskLimits.allowedSymbols.includes(order.symbol)) {
      throw new Error(`Symbol ${order.symbol} is not in allowed symbols list`);
    }

    // Check market hours (simplified - only for equity)
    if (this.riskLimits.marketHoursOnly && order.broker === "dhan") {
      const now = new Date();
      const hour = now.getHours();
      const day = now.getDay();

      // Monday to Friday, 9:15 AM to 3:30 PM IST
      if (day === 0 || day === 6) {
        throw new Error("Orders not allowed on weekends");
      }

      if (hour < 9 || (hour === 9 && now.getMinutes() < 15) || hour >= 15) {
        throw new Error("Orders only allowed during market hours (9:15 AM - 3:30 PM IST)");
      }
    }

    // Check daily loss limit (would need to track actual P&L)
    if (this.dailyLoss >= this.riskLimits.maxDailyLoss) {
      throw new Error(`Daily loss limit of ₹${this.riskLimits.maxDailyLoss.toLocaleString()} exceeded`);
    }

    // Validate order parameters
    if (order.quantity <= 0) {
      throw new Error("Order quantity must be positive");
    }

    if (order.price && order.price <= 0) {
      throw new Error("Order price must be positive");
    }

    if (order.side !== "buy" && order.side !== "sell") {
      throw new Error("Order side must be 'buy' or 'sell'");
    }
  }

  /**
   * Place an order with risk validation
   */
  async placeOrder(order: TradeOrder): Promise<any> {
    // Validate order
    this.validateOrder(order);

    try {
      if (order.broker === "dhan") {
        if (!this.dhanClient) {
          throw new Error("Dhan client not configured");
        }

        const dhanParams: DhanOrderParams = {
          dhanClientId: process.env.DHAN_KEY as string,
          transactionType: order.side.toUpperCase() as "BUY" | "SELL",
          exchangeSegment: (order.exchangeSegment as any) || "NSE_EQ",
          productType: (order.productType as any) || "INTRADAY",
          orderType: (order.orderType?.toUpperCase() as any) || "LIMIT",
          validity: (order.validity as any) || "DAY",
          securityId: order.symbol,
          quantity: order.quantity,
          price: order.price || 0,
          triggerPrice: 0
        };

        const result = await this.dhanClient.placeOrder(dhanParams);
        return { broker: "dhan", order: result };

      } else if (order.broker === "coinswitch") {
        if (!this.coinswitchClient) {
          throw new Error("CoinSwitch client not configured");
        }

        const coinswitchOrder: CoinSwitchOrder = {
          symbol: order.symbol,
          side: order.side,
          quantity: order.quantity,
          price: order.price,
          type: order.orderType
        };

        const result = await this.coinswitchClient.createOrder(coinswitchOrder);
        return { broker: "coinswitch", order: result };

      } else {
        throw new Error(`Unsupported broker: ${order.broker}`);
      }

    } catch (error: any) {
      // Log the error for monitoring
      console.error(`Order placement failed for ${order.broker}:`, error.message);

      // Update daily loss tracking if it's a failed trade
      // This is a simplified version - in production you'd track actual P&L

      throw error;
    }
  }

  /**
   * Cancel an order
   */
  async cancelOrder(broker: "dhan" | "coinswitch", orderId: string): Promise<any> {
    if (broker === "dhan") {
      if (!this.dhanClient) {
        throw new Error("Dhan client not configured");
      }
      return this.dhanClient.cancelOrder(orderId);
    } else if (broker === "coinswitch") {
      if (!this.coinswitchClient) {
        throw new Error("CoinSwitch client not configured");
      }
      return this.coinswitchClient.cancelOrder(orderId);
    } else {
      throw new Error(`Unsupported broker: ${broker}`);
    }
  }

  /**
   * Get orders
   */
  async getOrders(broker: "dhan" | "coinswitch"): Promise<any[]> {
    if (broker === "dhan") {
      if (!this.dhanClient) {
        throw new Error("Dhan client not configured");
      }
      return this.dhanClient.getOrders();
    } else if (broker === "coinswitch") {
      if (!this.coinswitchClient) {
        throw new Error("CoinSwitch client not configured");
      }
      return this.coinswitchClient.getOpenOrders();
    } else {
      throw new Error(`Unsupported broker: ${broker}`);
    }
  }

  /**
   * Get portfolio summary
   */
  async getPortfolio(broker: "dhan" | "coinswitch"): Promise<PortfolioSummary> {
    if (broker === "dhan") {
      if (!this.dhanClient) {
        throw new Error("Dhan client not configured");
      }

      const positions = await this.dhanClient.getPositions();
      const holdings = await this.dhanClient.getHoldings();

      // Calculate totals
      let totalValue = 0;
      let totalPnl = 0;

      const allPositions = [...positions, ...holdings];
      allPositions.forEach(pos => {
        totalValue += pos.netValue || (pos.ltp * pos.netQty);
        totalPnl += pos.pnl || 0;
      });

      return {
        broker: "dhan",
        totalValue,
        totalPnl,
        totalPnlPercentage: totalValue > 0 ? (totalPnl / totalValue) * 100 : 0,
        positions: allPositions,
        lastUpdated: new Date()
      };

    } else if (broker === "coinswitch") {
      if (!this.coinswitchClient) {
        throw new Error("CoinSwitch client not configured");
      }

      const portfolio = await this.coinswitchClient.getPortfolio();

      // For crypto, we need to get current prices to calculate values
      // This is simplified - in production you'd cache prices
      let totalValue = 0;
      portfolio.forEach(asset => {
        const free = parseFloat(asset.free);
        const locked = parseFloat(asset.locked);
        // Simplified: assume 1:1 value for demo
        totalValue += free + locked;
      });

      return {
        broker: "coinswitch",
        totalValue,
        totalPnl: 0, // CoinSwitch doesn't provide P&L directly
        totalPnlPercentage: 0,
        positions: portfolio,
        lastUpdated: new Date()
      };

    } else {
      throw new Error(`Unsupported broker: ${broker}`);
    }
  }

  /**
   * Get combined portfolio from all brokers
   */
  async getCombinedPortfolio(): Promise<PortfolioSummary[]> {
    const portfolios: PortfolioSummary[] = [];

    if (this.dhanClient) {
      try {
        portfolios.push(await this.getPortfolio("dhan"));
      } catch (error) {
        console.error("Failed to get Dhan portfolio:", error);
      }
    }

    if (this.coinswitchClient) {
      try {
        portfolios.push(await this.getPortfolio("coinswitch"));
      } catch (error) {
        console.error("Failed to get CoinSwitch portfolio:", error);
      }
    }

    return portfolios;
  }

  /**
   * Get market quotes
   */
  async getQuotes(broker: "dhan" | "coinswitch", symbols: string[]): Promise<any> {
    if (broker === "dhan") {
      if (!this.dhanClient) {
        throw new Error("Dhan client not configured");
      }
      return this.dhanClient.getQuotes(symbols);
    } else if (broker === "coinswitch") {
      if (!this.coinswitchClient) {
        throw new Error("CoinSwitch client not configured");
      }

      const quotes: any = {};
      for (const symbol of symbols) {
        quotes[symbol] = await this.coinswitchClient.getTicker(symbol);
      }
      return quotes;
    } else {
      throw new Error(`Unsupported broker: ${broker}`);
    }
  }

  /**
   * Test broker connections
   */
  async testConnections(): Promise<{ [key: string]: boolean }> {
    const results: { [key: string]: boolean } = {};

    if (this.dhanClient) {
      try {
        results.dhan = await this.dhanClient.ping();
      } catch (error) {
        results.dhan = false;
      }
    }

    if (this.coinswitchClient) {
      try {
        results.coinswitch = await this.coinswitchClient.testConnection();
      } catch (error) {
        results.coinswitch = false;
      }
    }

    return results;
  }

  /**
   * Update risk limits
   */
  updateRiskLimits(limits: Partial<RiskLimits>): void {
    this.riskLimits = { ...this.riskLimits, ...limits };
  }

  /**
   * Get current risk limits
   */
  getRiskLimits(): RiskLimits {
    return { ...this.riskLimits };
  }

  /**
   * Emergency stop - cancel all open orders
   */
  async emergencyStop(): Promise<any[]> {
    const results: any[] = [];

    // Cancel Dhan orders
    if (this.dhanClient) {
      try {
        const orders = await this.dhanClient.getOrders();
        for (const order of orders) {
          if (order.orderStatus === "PENDING") {
            await this.dhanClient.cancelOrder(order.orderId);
            results.push({ broker: "dhan", orderId: order.orderId, status: "cancelled" });
          }
        }
      } catch (error) {
        results.push({ broker: "dhan", error: (error as Error).message });
      }
    }

    // Cancel CoinSwitch orders
    if (this.coinswitchClient) {
      try {
        const orders = await this.coinswitchClient.getOpenOrders();
        for (const order of orders) {
          await this.coinswitchClient.cancelOrder(order.orderId);
          results.push({ broker: "coinswitch", orderId: order.orderId, status: "cancelled" });
        }
      } catch (error) {
        results.push({ broker: "coinswitch", error: (error as Error).message });
      }
    }

    return results;
  }
}