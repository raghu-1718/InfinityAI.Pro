/**
 * AI Agent Integration Components for InfinityAI.Pro
 * Provides UI components for interacting with the Financial Advisor Agent
 */

"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Send,
  Bot,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  XCircle,
  Zap,
} from "lucide-react";

import { getEngineCUrl } from "@/lib/api";

const ENGINE_C_URL = getEngineCUrl();

// Types
interface AgentMessage {
  role: "user" | "agent";
  content: string;
  timestamp: string;
  model?: string;
}

interface TradeSignal {
  action: string;
  confidence: number;
  score: number;
  risk_level: string;
  entry_price?: number;
  stop_loss?: number;
  targets?: number[];
  position_size_pct?: number;
  reasoning: {
    engine_b: string;
    market: string;
    agent: string;
  };
}

interface AgentStatus {
  status: string;
  agent_engine_id: string;
  model: string;
  capabilities: string[];
}

// =========================================================================
// AI Agent Chat Component
// =========================================================================
export function AIAgentChat({ userId }: { userId: string }) {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch agent status on mount
    fetchAgentStatus();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchAgentStatus = async () => {
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/agent/status`);
      const data = await response.json();
      setAgentStatus(data);
    } catch (error) {
      console.error("Failed to fetch agent status:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: AgentMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${ENGINE_C_URL}/api/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          message: input,
          context: {
            risk_profile: "moderate",
          },
        }),
      });

      const data = await response.json();

      if (data.success) {
        const agentMessage: AgentMessage = {
          role: "agent",
          content: data.response,
          timestamp: data.timestamp,
          model: data.model,
        };
        setMessages((prev) => [...prev, agentMessage]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "agent",
            content: `Error: ${data.error || "Failed to get response"}`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: `Connection error: ${error}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <CardTitle>Financial Advisor AI</CardTitle>
          </div>
          {agentStatus && (
            <Badge
              variant={
                agentStatus.status === "operational" ? "default" : "destructive"
              }
            >
              {agentStatus.model || "gemini-2.5-pro"}
            </Badge>
          )}
        </div>
        <CardDescription>
          Ask anything about trading, markets, or investments
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with your Financial Advisor</p>
              <p className="text-sm mt-2">
                Try asking about market outlook, stock analysis, or trading
                strategies
              </p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                  {msg.model && ` • ${msg.model}`}
                </p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg px-4 py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask about markets, stocks, or strategies..."
            disabled={isLoading}
          />
          <Button onClick={sendMessage} disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Real-Time Signal Component
// =========================================================================
export function RealTimeSignal({
  userId,
  symbol,
}: {
  userId: string;
  symbol: string;
}) {
  const [signal, setSignal] = useState<TradeSignal | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSignal = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${ENGINE_C_URL}/api/agent/signal/${userId}/${symbol}?timeframe=intraday`
      );
      const data = await response.json();

      if (data.success) {
        setSignal(data.signal);
      } else {
        setError(data.error || "Failed to get signal");
      }
    } catch (err) {
      setError(`Connection error: ${err}`);
    } finally {
      setIsLoading(false);
    }
  }, [userId, symbol]);

  useEffect(() => {
    fetchSignal();
    // Refresh every 5 minutes
    const interval = setInterval(fetchSignal, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchSignal]);

  const getActionColor = (action: string) => {
    if (action.includes("BUY")) return "text-green-500";
    if (action.includes("SELL")) return "text-red-500";
    return "text-yellow-500";
  };

  const getActionIcon = (action: string) => {
    if (action.includes("BUY")) return <TrendingUp className="h-5 w-5" />;
    if (action.includes("SELL")) return <TrendingDown className="h-5 w-5" />;
    return <AlertTriangle className="h-5 w-5" />;
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            {symbol} Signal
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSignal}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Refresh"
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500 flex items-center gap-2">
            <XCircle className="h-4 w-4" />
            {error}
          </div>
        ) : signal ? (
          <div className="space-y-4">
            {/* Action and Confidence */}
            <div className="flex items-center justify-between">
              <div
                className={`flex items-center gap-2 text-2xl font-bold ${getActionColor(signal.action)}`}
              >
                {getActionIcon(signal.action)}
                {signal.action}
              </div>
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Confidence</div>
                <div className="text-xl font-semibold">
                  {signal.confidence != null ? `${signal.confidence}%` : "N/A"}
                </div>
              </div>
            </div>

            {/* Risk Level */}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Risk Level</span>
              <Badge
                variant={
                  signal.risk_level === "LOW"
                    ? "default"
                    : signal.risk_level === "MEDIUM"
                      ? "secondary"
                      : "destructive"
                }
              >
                {signal.risk_level}
              </Badge>
            </div>

            {/* Entry & Exit */}
            {signal.entry_price && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Entry</span>
                  <div className="font-medium">₹{signal.entry_price}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Stop Loss</span>
                  <div className="font-medium text-red-500">
                    ₹{signal.stop_loss}
                  </div>
                </div>
              </div>
            )}

            {/* Targets */}
            {signal.targets && signal.targets.length > 0 && (
              <div>
                <span className="text-muted-foreground text-sm">Targets</span>
                <div className="flex gap-2 mt-1">
                  {signal.targets.map((target, idx) => (
                    <Badge
                      key={idx}
                      variant="outline"
                      className="text-green-500"
                    >
                      T{idx + 1}: ₹{target}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning */}
            <div className="text-sm border-t pt-3 mt-3">
              <div className="text-muted-foreground mb-2">Signal Sources</div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-muted-foreground">Engine B</div>
                  <div>{signal.reasoning?.engine_b || "N/A"}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Market</div>
                  <div>{signal.reasoning?.market || "N/A"}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">AI Agent</div>
                  <div>{signal.reasoning?.agent || "N/A"}</div>
                </div>
              </div>
            </div>

            {/* Score */}
            <div className="text-xs text-muted-foreground text-right">
              Combined Score: {signal.score}
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
            <p className="text-muted-foreground">Analyzing {symbol}...</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// =========================================================================
// Automated Trading Control Component
// =========================================================================
export function AutomatedTradingControl({ userId }: { userId: string }) {
  /* eslint-disable @typescript-eslint/no-unused-vars */
  const [isEnabled, setIsEnabled] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRun, setLastRun] = useState<any>(null);
  const [watchlist, setWatchlist] = useState([
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
  ]);
  const [config, setConfig] = useState({
    min_confidence: 70,
    max_risk_per_trade: 2,
    max_daily_trades: 10,
    trading_amount: 1000,
  });
  /* eslint-enable @typescript-eslint/no-unused-vars */

  const runAutomatedCycle = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${ENGINE_C_URL}/api/agent/auto-trade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          watchlist,
          config: {
            min_confidence: config.min_confidence / 100,
            max_risk_per_trade: config.max_risk_per_trade / 100,
            max_daily_trades: config.max_daily_trades,
            trading_amount: config.trading_amount,
          },
        }),
      });

      const data = await response.json();
      setLastRun(data);
    } catch (error) {
      console.error("Automated trading error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            AI Automated Trading
          </CardTitle>
          <Badge variant={isEnabled ? "default" : "secondary"}>
            {isEnabled ? "Active" : "Inactive"}
          </Badge>
        </div>
        <CardDescription>
          Let AI analyze and execute trades automatically
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Watchlist */}
        <div>
          <label className="text-sm text-muted-foreground">Watchlist</label>
          <div className="flex flex-wrap gap-2 mt-1">
            {watchlist.map((symbol, idx) => (
              <Badge key={idx} variant="outline">
                {symbol}
              </Badge>
            ))}
          </div>
        </div>

        {/* Config */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-muted-foreground">
              Min Confidence
            </label>
            <div className="font-medium">{config.min_confidence}%</div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">
              Max Risk/Trade
            </label>
            <div className="font-medium">{config.max_risk_per_trade}%</div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">
              Max Daily Trades
            </label>
            <div className="font-medium">{config.max_daily_trades}</div>
          </div>
          <div>
            <label className="text-sm text-muted-foreground">
              Trading Amount
            </label>
            <div className="font-medium">₹{config.trading_amount}</div>
          </div>
        </div>

        {/* Run Button */}
        <Button
          className="w-full"
          onClick={runAutomatedCycle}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Running Analysis...
            </>
          ) : (
            <>
              <Zap className="h-4 w-4 mr-2" />
              Run AI Trading Cycle
            </>
          )}
        </Button>

        {/* Last Run Results */}
        {lastRun && (
          <div className="border rounded-lg p-3 text-sm">
            <div className="font-medium mb-2">Last Run Results</div>
            <div className="grid grid-cols-2 gap-2 text-muted-foreground">
              <div>Symbols Analyzed: {lastRun.symbols_analyzed}</div>
              <div>Signals Generated: {lastRun.signals_generated}</div>
              <div className="text-green-500">
                Trades Executed: {lastRun.trades_executed}
              </div>
              <div className="text-yellow-500">
                Trades Skipped: {lastRun.trades_skipped}
              </div>
            </div>
            {lastRun.errors?.length > 0 && (
              <div className="text-red-500 mt-2">
                Errors: {lastRun.errors.length}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Export all components
export default {
  AIAgentChat,
  RealTimeSignal,
  AutomatedTradingControl,
};
