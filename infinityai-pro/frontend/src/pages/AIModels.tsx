import React, { useState, useEffect } from 'react';

interface SimulationResult {
  total_pnl: number;
  trades_executed: number;
  equity: number;
  episode_reward: number;
  epsilon: number;
  win_rate: number;
  sharpe_ratio: number;
}

interface PerformanceData {
  total_return_pct: number;
  final_equity: number;
  total_trades: number;
  avg_reward_per_episode: number;
  best_episode_reward: number;
  worst_episode_reward: number;
  win_rate: number;
  sharpe_ratio: number;
  total_episodes: number;
  final_epsilon: number;
  model_trained: boolean;
}

const AIModels: React.FC = () => {
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const apiUrl = process.env.REACT_APP_API_URL || 'https://infinityai.pro';

  const runSimulation = async (days: number = 1) => {
    setIsSimulating(true);
    setMessage('🤖 Starting AI trading simulation...');

    try {
      const response = await fetch(`${apiUrl}/ai/simulate-day`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days })
      });

      if (response.ok) {
        const result = await response.json();
        setSimulationResult(result);
        setMessage('✅ Simulation completed successfully!');
      } else {
        const error = await response.json();
        setMessage(`❌ Simulation failed: ${error.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Network error: ${error}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const startContinuousSimulation = async (days: number = 30) => {
    setIsSimulating(true);
    setMessage('🚀 Starting continuous AI learning simulation...');

    try {
      const response = await fetch(`${apiUrl}/ai/start-simulation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days })
      });

      if (response.ok) {
        const result = await response.json();
        setPerformance(result);
        setMessage('🎯 Continuous simulation completed! AI has learned from the experience.');
      } else {
        const error = await response.json();
        setMessage(`❌ Continuous simulation failed: ${error.detail}`);
      }
    } catch (error) {
      setMessage(`❌ Network error: ${error}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const getPerformance = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${apiUrl}/ai/performance`);
      if (response.ok) {
        const data = await response.json();
        setPerformance(data);
      } else {
        setMessage('❌ Failed to fetch performance data');
      }
    } catch (error) {
      setMessage(`❌ Network error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    getPerformance();
  }, []);

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>🤖 AI-Powered Trading Simulator</h1>
      <p>Real-time market data fetching, AI-driven trading decisions, and continuous learning optimization.</p>

      {/* Control Panel */}
      <div style={{ background: '#f5f5f5', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>🎮 Simulation Controls</h2>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => runSimulation(1)}
            disabled={isSimulating}
            style={{
              padding: '10px 20px',
              background: isSimulating ? '#ccc' : '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: isSimulating ? 'not-allowed' : 'pointer'
            }}
          >
            {isSimulating ? '🔄 Running...' : '📊 Run Daily Simulation'}
          </button>

          <button
            onClick={() => startContinuousSimulation(7)}
            disabled={isSimulating}
            style={{
              padding: '10px 20px',
              background: isSimulating ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: isSimulating ? 'not-allowed' : 'pointer'
            }}
          >
            {isSimulating ? '🔄 Learning...' : '🧠 AI Learning (7 Days)'}
          </button>

          <button
            onClick={getPerformance}
            disabled={isLoading}
            style={{
              padding: '10px 20px',
              background: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
          >
            {isLoading ? '📊 Loading...' : '📈 Refresh Performance'}
          </button>
        </div>

        {message && (
          <div style={{
            marginTop: '10px',
            padding: '10px',
            background: message.includes('✅') ? '#d4edda' : message.includes('❌') ? '#f8d7da' : '#fff3cd',
            border: `1px solid ${message.includes('✅') ? '#c3e6cb' : message.includes('❌') ? '#f5c6cb' : '#ffeaa7'}`,
            borderRadius: '5px'
          }}>
            {message}
          </div>
        )}
      </div>

      {/* Latest Simulation Results */}
      {simulationResult && (
        <div style={{ background: '#e7f3ff', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h2>📊 Latest Simulation Results</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>💰 P&L</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold', color: simulationResult.total_pnl >= 0 ? '#28a745' : '#dc3545' }}>
                ₹{simulationResult.total_pnl.toFixed(2)}
              </p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>📈 Equity</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>₹{simulationResult.equity.toFixed(2)}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🎯 Trades</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{simulationResult.trades_executed}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🏆 Win Rate</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{(simulationResult.win_rate * 100).toFixed(1)}%</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>📊 Sharpe Ratio</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{simulationResult.sharpe_ratio.toFixed(2)}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🧠 AI Exploration</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{(simulationResult.epsilon * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Performance Summary */}
      {performance && (
        <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
          <h2>📈 AI Learning Performance Summary</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>💹 Total Return</h3>
              <p style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: performance.total_return_pct >= 0 ? '#28a745' : '#dc3545'
              }}>
                {performance.total_return_pct.toFixed(2)}%
              </p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>💰 Final Equity</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>₹{performance.final_equity.toFixed(2)}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🎯 Total Trades</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{performance.total_trades}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🏆 Best Episode</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                {performance.best_episode_reward.toFixed(2)}
              </p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>📊 Win Rate</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{(performance.win_rate * 100).toFixed(1)}%</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>⚡ Sharpe Ratio</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{performance.sharpe_ratio.toFixed(2)}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🧠 Episodes</h3>
              <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{performance.total_episodes}</p>
            </div>
            <div style={{ background: 'white', padding: '15px', borderRadius: '5px' }}>
              <h3>🤖 Model Status</h3>
              <p style={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: performance.model_trained ? '#28a745' : '#ffc107'
              }}>
                {performance.model_trained ? 'Trained' : 'Learning'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* AI Features Explanation */}
      <div style={{ background: '#fff3cd', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2>🧠 How the AI Trading System Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
          <div>
            <h3>📡 Real-Time Data Fetching</h3>
            <p>Continuously fetches live market data from Alpha Vantage API for accurate price information and technical indicators.</p>
          </div>
          <div>
            <h3>🎯 AI Decision Making</h3>
            <p>Uses reinforcement learning to analyze market conditions, technical indicators (RSI, MACD, VWAP), and historical patterns to make trading decisions.</p>
          </div>
          <div>
            <h3>📈 Continuous Learning</h3>
            <p>The AI learns from every trade, improving its strategy over time through experience replay and model updates.</p>
          </div>
          <div>
            <h3>⚡ Risk Management</h3>
            <p>Implements position sizing, stop-loss mechanisms, and portfolio risk controls to protect capital while maximizing returns.</p>
          </div>
          <div>
            <h3>📊 Performance Tracking</h3>
            <p>Monitors win rates, Sharpe ratios, maximum drawdown, and other key metrics to evaluate and improve trading performance.</p>
          </div>
          <div>
            <h3>🔄 Self-Optimization</h3>
            <p>Automatically adjusts exploration vs exploitation balance, retrains models, and evolves trading strategies based on results.</p>
          </div>
        </div>
      </div>

      {/* Technical Details */}
      <div style={{ background: '#e9ecef', padding: '20px', borderRadius: '8px' }}>
        <h2>⚙️ Technical Implementation</h2>
        <ul>
          <li><strong>Algorithms:</strong> Reinforcement Learning (Q-Learning), Random Forest Classification, Technical Analysis</li>
          <li><strong>Data Sources:</strong> Alpha Vantage API (5 API calls/minute, 500/day)</li>
          <li><strong>Features:</strong> 15 technical indicators (MACD, RSI, VWAP, ATR, Bollinger Bands, etc.)</li>
          <li><strong>Risk Controls:</strong> Position sizing (3% per trade), stop-loss (60% of premium), max drawdown limits</li>
          <li><strong>Backtesting:</strong> Historical simulation with realistic slippage and commissions</li>
          <li><strong>Model Persistence:</strong> Automatic saving/loading of trained models</li>
        </ul>
      </div>
    </div>
  );
};

export default AIModels;