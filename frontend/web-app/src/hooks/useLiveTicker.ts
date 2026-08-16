import { useQuery } from "@tanstack/react-query";
import { engineC } from "@/lib/api";

export interface LiveTickerItem {
  symbol: string;
  securityId: string;
  ltp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  change: number;
  pChange: number;
}

/**
 * Robustly extracts quotes from nested DhanHQ response structures
 */
export function extractDhanQuotes(rawResponse: any, segment: string = "IDX_I"): Record<string, any> {
  if (!rawResponse) return {};
  let current = rawResponse.data || rawResponse;
  
  // Recursively unwrap nested 'data' objects until segment is found
  let depth = 0;
  while (current && current.data && typeof current.data === "object" && !current[segment] && depth < 5) {
    current = current.data;
    depth++;
  }
  
  return current?.[segment] || current || {};
}

export function useLiveIndexTickers() {
  return useQuery({
    queryKey: ["liveIndexTickers"],
    queryFn: async () => {
      // 13: NIFTY 50, 25: BANK NIFTY, 27: FIN NIFTY, 28: MIDCP NIFTY
      const raw = await engineC.getMarketQuotes("13,25,27,28", "IDX_I");
      const quotes = extractDhanQuotes(raw, "IDX_I");

      const mapping: Record<string, string> = {
        "13": "NIFTY 50",
        "25": "BANK NIFTY",
        "27": "FIN NIFTY",
        "28": "MIDCP NIFTY",
      };

      const result: Record<string, LiveTickerItem> = {};
      for (const [id, q] of Object.entries(quotes) as [string, any][]) {
        const sym = mapping[id] || `INDEX_${id}`;
        const ltp = Number(q.last_price || q.ltp || q.ohlc?.close || 0);
        const open = Number(q.ohlc?.open || ltp);
        const high = Number(q.ohlc?.high || ltp);
        const low = Number(q.ohlc?.low || ltp);
        const close = Number(q.ohlc?.close || ltp);
        const change = open > 0 ? ltp - open : 0;
        const pChange = open > 0 ? (change / open) * 100 : 0;

        result[id] = {
          symbol: sym,
          securityId: id,
          ltp,
          open,
          high,
          low,
          close,
          change,
          pChange,
        };
      }
      return result;
    },
    refetchInterval: 5000,
    staleTime: 2500,
  });
}

export function useLiveEquityTickers() {
  return useQuery({
    queryKey: ["liveEquityTickers"],
    queryFn: async () => {
      // 2885: RELIANCE, 11536: TCS, 1333: HDFC BANK
      const raw = await engineC.getMarketQuotes("2885,11536,1333", "NSE_EQ");
      const quotes = extractDhanQuotes(raw, "NSE_EQ");

      const mapping: Record<string, string> = {
        "2885": "RELIANCE",
        "11536": "TCS",
        "1333": "HDFCBANK",
      };

      const result: Record<string, LiveTickerItem> = {};
      for (const [id, q] of Object.entries(quotes) as [string, any][]) {
        const sym = mapping[id] || `EQUITY_${id}`;
        const ltp = Number(q.last_price || q.ltp || q.ohlc?.close || 0);
        const open = Number(q.ohlc?.open || ltp);
        const high = Number(q.ohlc?.high || ltp);
        const low = Number(q.ohlc?.low || ltp);
        const close = Number(q.ohlc?.close || ltp);
        const change = open > 0 ? ltp - open : 0;
        const pChange = open > 0 ? (change / open) * 100 : 0;

        result[id] = {
          symbol: sym,
          securityId: id,
          ltp,
          open,
          high,
          low,
          close,
          change,
          pChange,
        };
      }
      return result;
    },
    refetchInterval: 5000,
    staleTime: 2500,
  });
}
