import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { updateAccessToken, fetchPortfolio } from '../store/slices/dhanSlice';
import TokenManager from './TokenManager';
import PortfolioSummary from './PortfolioSummary';
import RiskAssessment from './RiskAssessment';
import MarketOverview from './MarketOverview';
import './Dashboard.css';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { isTokenValid, userInfo, portfolio, loading, error } = useSelector(state => state.dhan);
  const [showTokenManager, setShowTokenManager] = useState(false);

  useEffect(() => {
    // Check if token is valid and fetch portfolio
    if (isTokenValid) {
      dispatch(fetchPortfolio());
    }
  }, [isTokenValid, dispatch]);

  useEffect(() => {
    // Show token manager if no valid token
    if (!isTokenValid) {
      setShowTokenManager(true);
    }
  }, [isTokenValid]);

  const handleTokenUpdate = async (token) => {
    try {
      await dispatch(updateAccessToken(token)).unwrap();
      setShowTokenManager(false);
      // Fetch portfolio after successful token update
      dispatch(fetchPortfolio());
    } catch (error) {
      console.error('Token update failed:', error);
    }
  };

  if (loading) {
    return (
      <div className=\"dashboard-loading\">
        <div className=\"spinner\"></div>
        <p>Loading your trading dashboard...</p>
      </div>
    );
  }

  return (
    <div className=\"dashboard\">
      <div className=\"dashboard-header\">
        <h1>InfinityAI.Pro Trading Dashboard</h1>
        <div className=\"user-info\">
          {userInfo && (
            <>
              <span>Welcome, {userInfo.name}</span>
              <div className=\"token-status\">
                <span className={`status-indicator ${isTokenValid ? 'valid' : 'invalid'}`}>
                  {isTokenValid ? '🟢 Connected' : '🔴 Disconnected'}
                </span>
                <button 
                  className=\"btn-secondary\"
                  onClick={() => setShowTokenManager(true)}
                >
                  Update Token
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {showTokenManager && (
        <TokenManager
          onTokenUpdate={handleTokenUpdate}
          onClose={() => setShowTokenManager(false)}
          isOpen={showTokenManager}
        />
      )}

      {!isTokenValid ? (
        <div className=\"no-token-message\">
          <div className=\"message-card\">
            <h2>🔑 DHAN Access Token Required</h2>
            <p>
              Please update your DHAN access token to start using InfinityAI.Pro trading features.
              Your token expires every 24 hours and needs to be refreshed.
            </p>
            <button 
              className=\"btn-primary\"
              onClick={() => setShowTokenManager(true)}
            >
              Add Access Token
            </button>
          </div>
        </div>
      ) : (
        <div className=\"dashboard-content\">
          <div className=\"dashboard-grid\">
            {/* Portfolio Summary */}
            <div className=\"grid-item portfolio-summary\">
              <PortfolioSummary portfolio={portfolio} />
            </div>

            {/* Market Overview */}
            <div className=\"grid-item market-overview\">
              <MarketOverview />
            </div>

            {/* Risk Assessment */}
            <div className=\"grid-item risk-assessment\">
              <RiskAssessment portfolio={portfolio} />
            </div>

            {/* Recent Activity */}
            <div className=\"grid-item recent-activity\">
              <div className=\"card\">
                <h3>Recent Trading Activity</h3>
                {portfolio?.holdings?.length > 0 ? (
                  <div className=\"activity-list\">
                    {portfolio.holdings.slice(0, 5).map((holding, index) => (
                      <div key={index} className=\"activity-item\">
                        <div className=\"activity-symbol\">{holding.symbol}</div>
                        <div className=\"activity-details\">
                          <span>₹{holding.current_price}</span>
                          <span className={holding.pnl >= 0 ? 'profit' : 'loss'}>
                            {holding.pnl >= 0 ? '+' : ''}₹{holding.pnl.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p>No recent activity</p>
                )}
              </div>
            </div>

            {/* AI Insights */}
            <div className=\"grid-item ai-insights\">
              <div className=\"card\">
                <h3>🤖 AI Market Insights</h3>
                <div className=\"insights-content\">
                  <div className=\"insight-item\">
                    <span className=\"insight-label\">Market Sentiment:</span>
                    <span className=\"insight-value bullish\">Bullish</span>
                  </div>
                  <div className=\"insight-item\">
                    <span className=\"insight-label\">Recommended Action:</span>
                    <span className=\"insight-value\">Hold Positions</span>
                  </div>
                  <div className=\"insight-item\">
                    <span className=\"insight-label\">Risk Level:</span>
                    <span className=\"insight-value medium\">Medium</span>
                  </div>
                </div>
                <button className=\"btn-secondary btn-small\">
                  Get Detailed Analysis
                </button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className=\"grid-item quick-actions\">
              <div className=\"card\">
                <h3>Quick Actions</h3>
                <div className=\"action-buttons\">
                  <button className=\"btn-primary btn-small\">
                    📈 Buy Order
                  </button>
                  <button className=\"btn-secondary btn-small\">
                    📉 Sell Order
                  </button>
                  <button className=\"btn-secondary btn-small\">
                    📊 Market Analysis
                  </button>
                  <button className=\"btn-secondary btn-small\">
                    ⚙️ Auto Trading
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className=\"error-message\">
          <div className=\"error-card\">
            <h4>⚠️ Error</h4>
            <p>{error}</p>
            <button 
              className=\"btn-secondary\"
              onClick={() => dispatch(fetchPortfolio())}
            >
              Retry
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;