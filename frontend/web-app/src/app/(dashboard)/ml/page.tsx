"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import {
  Brain,
  TrendingUp,
  Activity,
  Zap,
  Target,
  BarChart3,
} from "lucide-react";

const ENGINE_B_URL =
  process.env.NEXT_PUBLIC_ENGINE_B_URL ||
  "https://engine-b-galvanic-pulsar-482815-h0.us-central1.run.app";

const WATCHLIST = [
  "NIFTY",
  "BANKNIFTY",
  "RELIANCE",
  "TCS",
  "INFY",
  "HDFCBANK",
  "ICICIBANK",
];

interface LSTMForecast {
  symbol: string;
  current_price: number;
  predicted_price_30d: number;
  price_change: number;
  price_change_pct: number;
  forecast: Array<{
    date: string;
    predicted_close: number;
  }>;
}

interface DQNAction {
  symbol: string;
  recommended_action: string;
  confidence: number;
  q_values: {
    HOLD: number;
    BUY: number;
    SELL: number;
  };
}

export default function MLDashboard() {
  const [activeSymbol, setActiveSymbol] = useState("NIFTY");
  const [lstmForecast, setLstmForecast] = useState<LSTMForecast | null>(null);
  const [dqnAction, setDqnAction] = useState<DQNAction | null>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Fetch model status on mount
  useEffect(() => {
    fetchModelStatus();
  }, []);

  const fetchModelStatus = async () => {
    try {
      const response = await fetch(
        `${ENGINE_B_URL}/api/v1/models/deep-learning`,
      );
      const data = await response.json();
      setModelStatus(data);
    } catch (error) {
      console.error("Failed to fetch model status:", error);
    }
  };

  const fetchLSTMForecast = async (symbol: string) => {
    setLoading(true);
    try {
      // In production, this would fetch actual recent_data from market data API
      // For now, we'll show that the endpoint is ready
      const response = await fetch(`${ENGINE_B_URL}/api/v1/lstm/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: symbol,
          recent_data: [], // Would be populated with 60 days of OHLCV data
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        setLstmForecast(data);
      }
    } catch (error) {
      console.error("LSTM forecast failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDQNAction = async (symbol: string) => {
    setLoading(true);
    try {
      // In production, current_state would be calculated from portfolio + market features
      const response = await fetch(`${ENGINE_B_URL}/api/v1/dqn/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: symbol,
          current_state: [], // Would be state vector
        }),
      });
      const data = await response.json();
      if (data.status === "success") {
        setDqnAction(data);
      }
    } catch (error) {
      console.error("DQN action failed:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    setActiveSymbol(symbol);
    fetchLSTMForecast(symbol);
    fetchDQNAction(symbol);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Brain className="h-8 w-8 text-blue-500" />
            Deep Learning Models
          </h1>
          <p className="text-muted-foreground">
            LSTM Price Forecasting & DQN Trading Agent
          </p>
        </div>
        <Badge variant="outline" className="text-lg px-4 py-2">
          <Activity className="h-4 w-4 mr-2" />
          AI-Powered
        </Badge>
      </div>

      {/* Model Status Cards */}
      {modelStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                LSTM Models
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {modelStatus.lstm_models?.count || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                60-day lookback, 30-day forecast
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="h-4 w-4" />
                DQN Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {modelStatus.dqn_models?.count || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Reinforcement learning agents
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Zap className="h-4 w-4" />
                Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">ACTIVE</div>
              <p className="text-xs text-muted-foreground mt-1">
                TensorFlow/Keras backend
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Symbol Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Symbol</CardTitle>
          <CardDescription>Choose a symbol for AI analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            {WATCHLIST.map((symbol) => (
              <Button
                key={symbol}
                variant={activeSymbol === symbol ? "default" : "outline"}
                onClick={() => handleSymbolChange(symbol)}
              >
                {symbol}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="lstm" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="lstm">LSTM Forecast</TabsTrigger>
          <TabsTrigger value="dqn">DQN Agent</TabsTrigger>
        </TabsList>

        {/* LSTM Forecast Tab */}
        <TabsContent value="lstm" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                30-Day Price Forecast
              </CardTitle>
              <CardDescription>
                LSTM neural network time-series prediction
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {lstmForecast ? (
                <>
                  {/* Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        Current Price
                      </p>
                      <p className="text-2xl font-bold">
                        ₹{lstmForecast.current_price?.toFixed(2) || 0}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        30-Day Prediction
                      </p>
                      <p className="text-2xl font-bold">
                        ₹{lstmForecast.predicted_price_30d?.toFixed(2) || 0}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        Price Change
                      </p>
                      <p
                        className={`text-2xl font-bold ${lstmForecast.price_change >= 0 ? "text-green-500" : "text-red-500"}`}
                      >
                        ₹{lstmForecast.price_change?.toFixed(2) || 0}
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-muted-foreground">% Change</p>
                      <p
                        className={`text-2xl font-bold ${lstmForecast.price_change_pct >= 0 ? "text-green-500" : "text-red-500"}`}
                      >
                        {lstmForecast.price_change_pct?.toFixed(2) || 0}%
                      </p>
                    </div>
                  </div>

                  {/* Forecast Chart */}
                  {lstmForecast.forecast && (
                    <ResponsiveContainer width="100%" height={400}>
                      <AreaChart data={lstmForecast.forecast}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12 }}
                          angle={-45}
                          textAnchor="end"
                          height={80}
                        />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="predicted_close"
                          stroke="#8884d8"
                          fill="#8884d8"
                          fillOpacity={0.3}
                          name="Predicted Price"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    Select a symbol to view LSTM forecast
                  </p>
                  <Button
                    onClick={() => fetchLSTMForecast(activeSymbol)}
                    className="mt-4"
                  >
                    Generate Forecast
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* DQN Agent Tab */}
        <TabsContent value="dqn" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                DQN Trading Recommendation
              </CardTitle>
              <CardDescription>
                Reinforcement learning agent (Buy/Sell/Hold)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {dqnAction ? (
                <>
                  {/* Recommended Action */}
                  <div className="text-center p-8 border rounded-lg">
                    <p className="text-sm text-muted-foreground mb-2">
                      Recommended Action
                    </p>
                    <div
                      className={`text-5xl font-bold mb-2 ${
                        dqnAction.recommended_action === "BUY"
                          ? "text-green-500"
                          : dqnAction.recommended_action === "SELL"
                            ? "text-red-500"
                            : "text-gray-500"
                      }`}
                    >
                      {dqnAction.recommended_action}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Confidence: {dqnAction.confidence?.toFixed(2) || 0}
                    </p>
                  </div>

                  {/* Q-Values */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium">
                          HOLD Q-Value
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {dqnAction.q_values?.HOLD?.toFixed(4) || 0}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium">
                          BUY Q-Value
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-500">
                          {dqnAction.q_values?.BUY?.toFixed(4) || 0}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium">
                          SELL Q-Value
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-500">
                          {dqnAction.q_values?.SELL?.toFixed(4) || 0}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    Select a symbol to view DQN recommendation
                  </p>
                  <Button
                    onClick={() => fetchDQNAction(activeSymbol)}
                    className="mt-4"
                  >
                    Get Recommendation
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Model Info */}
          <Card>
            <CardHeader>
              <CardTitle>DQN Model Architecture</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between p-2 border-b">
                  <span className="font-medium">State Space:</span>
                  <span className="text-muted-foreground">
                    Position, Balance, Price, Indicators
                  </span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span className="font-medium">Action Space:</span>
                  <span className="text-muted-foreground">
                    HOLD (0), BUY (1), SELL (2)
                  </span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span className="font-medium">Network:</span>
                  <span className="text-muted-foreground">
                    Dense 128 → 64 → 32 → 3
                  </span>
                </div>
                <div className="flex justify-between p-2 border-b">
                  <span className="font-medium">Training:</span>
                  <span className="text-muted-foreground">
                    Experience Replay + Target Network
                  </span>
                </div>
                <div className="flex justify-between p-2">
                  <span className="font-medium">Objective:</span>
                  <span className="text-muted-foreground">
                    Maximize Sharpe Ratio
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Integration Guide */}
      <Card>
        <CardHeader>
          <CardTitle>Model Integration Status</CardTitle>
          <CardDescription>
            Deep learning models are integrated with existing ML ensemble
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-green-50">
                LIVE
              </Badge>
              <span className="text-sm">
                <strong>Existing Ensemble:</strong> XGBoost (40%) + LightGBM
                (30%) + CatBoost (15%) + RF (15%)
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-blue-50">
                NEW
              </Badge>
              <span className="text-sm">
                <strong>LSTM Forecast:</strong> 30-day price prediction
                (regression task)
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-blue-50">
                NEW
              </Badge>
              <span className="text-sm">
                <strong>DQN Agent:</strong> Action optimization (reinforcement
                learning)
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-yellow-50">
                HYBRID
              </Badge>
              <span className="text-sm">
                <strong>Final Signal:</strong> Weighted combination of all
                models
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
