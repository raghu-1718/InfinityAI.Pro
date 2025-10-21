/**
 * StrategySelector Component
 * 
 * Allows users to select trading strategy, amount, and risk level
 * Calls the startTrading Cloud Function to initiate trading session
 */

import { useState, FormEvent } from "react";
import { httpsCallable, HttpsCallableResult } from "firebase/functions";
import { functions } from "../firebaseConfig";
import { User } from "firebase/auth";

interface StrategySelectorProps {
  user: User;
}

type StrategyType = "equities" | "options" | "mcx";

interface StartTradingData {
  userId: string;
  strategy: string;
  amount: string;
  risk: string;
}

interface StartTradingResponse {
  message: string;
  sessionId?: string;
  status?: string;
}

export default function StrategySelector({ user }: StrategySelectorProps) {
  const [strategy, setStrategy] = useState<StrategyType>("equities");
  const [amount, setAmount] = useState("");
  const [risk, setRisk] = useState("5");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleStartTrading = async (e: FormEvent) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const startTradingFn = httpsCallable<StartTradingData, StartTradingResponse>(
        functions,
        "startTrading"
      );

      const result: HttpsCallableResult<StartTradingResponse> = await startTradingFn({
        userId: user.uid,
        strategy,
        amount,
        risk,
      });

      setMessage(result.data.message || "Trading session started successfully!");
      console.log("✅ Trading started:", result.data);

      // Clear form after successful submission
      setTimeout(() => {
        setMessage("");
      }, 5000);
    } catch (err: any) {
      console.error("❌ Failed to start trading:", err);
      setError(err.message || "Failed to start trading session. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="strategy-container">
      <div className="strategy-card">
        <h3>Select Your Trading Strategy</h3>
        <p className="description">
          Choose your preferred market segment, investment amount, and risk tolerance.
        </p>

        <form onSubmit={handleStartTrading}>
          <div className="form-group">
            <label htmlFor="strategy">Strategy Type</label>
            <select
              id="strategy"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value as StrategyType)}
              disabled={loading}
            >
              <option value="equities">🏢 Equities (Intraday + Swing)</option>
              <option value="options">📈 Options (NIFTY + BANKNIFTY)</option>
              <option value="mcx">🥇 MCX (Commodities)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="amount">Investment Amount (₹)</label>
            <input
              id="amount"
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="50000"
              min="1000"
              step="1000"
              required
              disabled={loading}
            />
            <small>Minimum: ₹1,000</small>
          </div>

          <div className="form-group">
            <label htmlFor="risk">Risk Level (%)</label>
            <input
              id="risk"
              type="number"
              value={risk}
              onChange={(e) => setRisk(e.target.value)}
              placeholder="5"
              min="1"
              max="20"
              step="0.5"
              required
              disabled={loading}
            />
            <small>Max risk per trade (1-20%)</small>
          </div>

          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Starting..." : "🚀 Start Trading"}
          </button>
        </form>
      </div>

      <div className="strategy-info">
        <h4>📚 Strategy Information</h4>
        <ul>
          <li>
            <strong>Equities:</strong> AI-powered intraday and swing trading on NSE stocks
          </li>
          <li>
            <strong>Options:</strong> Automated options strategies on NIFTY & BANKNIFTY
          </li>
          <li>
            <strong>MCX:</strong> Commodity trading (Gold, Silver, Crude Oil)
          </li>
        </ul>

        <div className="risk-warning">
          ⚠️ <strong>Risk Disclaimer:</strong> Trading involves risk. Past performance
          does not guarantee future results. Only invest what you can afford to lose.
        </div>
      </div>
    </div>
  );
}
