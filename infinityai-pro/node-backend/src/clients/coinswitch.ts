import axios, { AxiosResponse } from "axios";
import { createHmac } from "crypto";

export interface CoinSwitchOrder {
  symbol: string;
  side: "buy" | "sell";
  quantity: number;
  price?: number;
  type?: "limit" | "market";
  timestamp?: number;
}

export interface CoinSwitchPortfolio {
  asset: string;
  free: string;
  locked: string;
  total: string;
}

export interface CoinSwitchOrderResponse {
  orderId: string;
  symbol: string;
  side: string;
  type: string;
  quantity: string;
  price: string;
  status: string;
  timestamp: number;
}

export class CoinSwitchClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;

  constructor(apiKey: string, apiSecret: string, baseUrl = "https://api-trading.coinswitch.co") {
    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  /**
   * Generate HMAC-SHA256 signature for authentication
   */
  private generateSignature(path: string, params: Record<string, any>): string {
    // Sort parameters by key
    const sortedKeys = Object.keys(params).sort();
    const queryString = sortedKeys
      .map(key => `${key}=${params[key]}`)
      .join("&");

    // Create payload: path?queryString
    const payload = `${path}?${queryString}`;

    // Generate HMAC-SHA256 signature
    return createHmac("sha256", this.apiSecret)
      .update(payload)
      .digest("hex");
  }

  /**
   * Make authenticated request to CoinSwitch API
   */
  private async request(
    method: "GET" | "POST" | "DELETE",
    path: string,
    params: Record<string, any> = {}
  ): Promise<any> {
    // Add timestamp to params
    params.timestamp = Date.now();

    // Generate signature
    const signature = this.generateSignature(path, params);

    // Set headers
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-AUTH-APIKEY": this.apiKey,
      "X-AUTH-SIGNATURE": signature
    };

    const url = `${this.baseUrl}${path}`;

    try {
      let response: AxiosResponse;

      if (method === "GET") {
        response = await axios.get(url, { params, headers });
      } else if (method === "POST") {
        response = await axios.post(url, params, { headers });
      } else if (method === "DELETE") {
        response = await axios.delete(url, { data: params, headers });
      } else {
        throw new Error(`Unsupported HTTP method: ${method}`);
      }

      return response.data;
    } catch (error: any) {
      throw new Error(`CoinSwitch API error: ${error.response?.data?.msg || error.message}`);
    }
  }

  /**
   * Test API connectivity
   */
  async ping(): Promise<any> {
    return this.request("GET", "/trade/api/v2/ping");
  }

  /**
   * Get 24hr ticker statistics
   */
  async getTicker(symbol: string): Promise<any> {
    return this.request("GET", "/trade/api/v2/24hr/ticker", { symbol });
  }

  /**
   * Get all 24hr ticker statistics
   */
  async getAllTickers(): Promise<any[]> {
    return this.request("GET", "/trade/api/v2/24hr/ticker", {});
  }

  /**
   * Create a new order
   */
  async createOrder(order: CoinSwitchOrder): Promise<CoinSwitchOrderResponse> {
    const params: Record<string, any> = {
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
  async cancelOrder(orderId: string): Promise<any> {
    return this.request("DELETE", "/trade/api/v2/order", { order_id: orderId });
  }

  /**
   * Get open orders
   */
  async getOpenOrders(symbol?: string): Promise<CoinSwitchOrderResponse[]> {
    const params: Record<string, any> = {};
    if (symbol) {
      params.symbol = symbol;
    }
    return this.request("GET", "/trade/api/v2/orders", params);
  }

  /**
   * Get order by ID
   */
  async getOrder(orderId: string): Promise<CoinSwitchOrderResponse> {
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
  async getPortfolio(): Promise<CoinSwitchPortfolio[]> {
    const response = await this.request("GET", "/trade/api/v2/user/portfolio", {});
    return response.data || [];
  }

  /**
   * Get account information
   */
  async getAccountInfo(): Promise<any> {
    return this.request("GET", "/trade/api/v2/account", {});
  }

  /**
   * Get trade history
   */
  async getTradeHistory(symbol?: string, limit = 100): Promise<any[]> {
    const params: Record<string, any> = { limit };
    if (symbol) {
      params.symbol = symbol;
    }
    return this.request("GET", "/trade/api/v2/myTrades", params);
  }

  /**
   * Get klines/candlestick data
   */
  async getKlines(symbol: string, interval: string, limit = 100): Promise<any[]> {
    return this.request("GET", "/trade/api/v2/klines", {
      symbol,
      interval,
      limit
    });
  }

  /**
   * Get order book depth
   */
  async getOrderBook(symbol: string, limit = 100): Promise<any> {
    return this.request("GET", "/trade/api/v2/depth", {
      symbol,
      limit
    });
  }

  /**
   * Get recent trades
   */
  async getRecentTrades(symbol: string, limit = 100): Promise<any[]> {
    return this.request("GET", "/trade/api/v2/trades", {
      symbol,
      limit
    });
  }

  /**
   * Test connectivity and authentication
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.ping();
      return true;
    } catch (error) {
      console.error("CoinSwitch connection test failed:", error);
      return false;
    }
  }

  /**
   * Get exchange info
   */
  async getExchangeInfo(): Promise<any> {
    return this.request("GET", "/trade/api/v2/exchangeInfo", {});
  }

  /**
   * Get all supported symbols
   */
  async getSymbols(): Promise<string[]> {
    const exchangeInfo = await this.getExchangeInfo();
    return exchangeInfo.symbols?.map((s: any) => s.symbol) || [];
  }
}