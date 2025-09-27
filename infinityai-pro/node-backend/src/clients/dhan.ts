import axios, { AxiosResponse } from "axios";

export interface DhanOrderParams {
  dhanClientId: string;
  transactionType: "BUY" | "SELL";
  exchangeSegment: "NSE_EQ" | "NSE_FO" | "BSE_EQ" | "MCX_COMM";
  productType: "INTRADAY" | "DELIVERY" | "MARGIN" | "CNC";
  orderType: "LIMIT" | "MARKET" | "SL" | "SL-M";
  validity: "DAY" | "IOC";
  securityId: string;
  quantity: number;
  price?: number;
  triggerPrice?: number;
}

export interface DhanPosition {
  securityId: string;
  tradingSymbol: string;
  exchangeSegment: string;
  productType: string;
  netQty: number;
  avgCostPrice: number;
  netValue: number;
  rbiRefRate?: number;
  ltp: number;
  pnl: number;
  pnlPercentage: number;
}

export class DhanClient {
  private apiKey: string;
  private accessToken: string | null = null;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl = "https://openapi.dhan.co") {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  /**
   * Generate access token from request token (OAuth flow)
   */
  async generateAccessToken(requestToken: string): Promise<string> {
    try {
      const response: AxiosResponse = await axios.post(`${this.baseUrl}/public/token`, {
        api_key: this.apiKey,
        request_token: requestToken
      });

      if (response.data.access_token) {
        this.accessToken = response.data.access_token;
        return this.accessToken!;
      } else {
        throw new Error("Failed to generate access token");
      }
    } catch (error: any) {
      throw new Error(`Dhan token generation failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Set access token directly (for testing or manual auth)
   */
  setAccessToken(token: string): void {
    this.accessToken = token;
  }

  private getHeaders(): { [key: string]: string } {
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
  async placeOrder(params: DhanOrderParams): Promise<any> {
    try {
      const response: AxiosResponse = await axios.post(
        `${this.baseUrl}/orders`,
        params,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan order placement failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get order book
   */
  async getOrders(): Promise<any[]> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/orders`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get orders failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get specific order
   */
  async getOrder(orderId: string): Promise<any> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/orders/${orderId}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get order failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Cancel an order
   */
  async cancelOrder(orderId: string): Promise<any> {
    try {
      const response: AxiosResponse = await axios.delete(
        `${this.baseUrl}/orders/${orderId}`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan cancel order failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get positions
   */
  async getPositions(): Promise<DhanPosition[]> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/portfolio/positions`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get positions failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get holdings
   */
  async getHoldings(): Promise<any[]> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/portfolio/holdings`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get holdings failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get market quotes
   */
  async getQuotes(securityIds: string[]): Promise<any> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/marketfeed`,
        {
          headers: this.getHeaders(),
          params: { securityId: securityIds.join(',') }
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get quotes failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get historical data
   */
  async getHistoricalData(securityId: string, exchangeSegment: string,
                         instrument: string, fromDate: string, toDate: string): Promise<any[]> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/charts`,
        {
          headers: this.getHeaders(),
          params: {
            securityId,
            exchangeSegment,
            instrument,
            fromDate,
            toDate
          }
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get historical data failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Get funds/margin
   */
  async getFunds(): Promise<any> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/funds`,
        { headers: this.getHeaders() }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(`Dhan get funds failed: ${error.response?.data?.message || error.message}`);
    }
  }

  /**
   * Test connection
   */
  async ping(): Promise<boolean> {
    try {
      const response: AxiosResponse = await axios.get(
        `${this.baseUrl}/ping`,
        { headers: this.getHeaders() }
      );
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }
}