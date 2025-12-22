import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import LedoitWolf

logger = logging.getLogger(__name__)

class RiskManager:
    """ML-based risk assessment and portfolio optimization with advanced metrics"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.covariance_estimator = LedoitWolf()
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 1.0
        }
        logger.info("✅ Risk Manager initialized with advanced metrics")

    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95,
                      method: str = "historical") -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) using multiple methods.
        Methods: historical, parametric, cornish-fisher
        """
        if len(returns) == 0:
            return {"var": 0.0, "method": method}

        returns = np.array(returns)

        if method == "historical":
            var = float(np.percentile(returns, (1 - confidence) * 100))
        elif method == "parametric":
            # Assumes normal distribution
            from scipy.stats import norm
            z_score = norm.ppf(1 - confidence)
            var = float(np.mean(returns) + z_score * np.std(returns))
        elif method == "cornish-fisher":
            # Adjusts for skewness and kurtosis
            from scipy.stats import norm
            z = norm.ppf(1 - confidence)
            s = float(pd.Series(returns).skew())
            k = float(pd.Series(returns).kurtosis())
            cf_z = z + (1/6) * (z**2 - 1) * s + (1/24) * (z**3 - 3*z) * k - (1/36) * (2*z**3 - 5*z) * s**2
            var = float(np.mean(returns) + cf_z * np.std(returns))
        else:
            var = float(np.percentile(returns, (1 - confidence) * 100))

        return {
            "var": round(var, 6),
            "var_pct": round(abs(var) * 100, 4),
            "confidence": confidence,
            "method": method,
            "samples": len(returns)
        }

    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> Dict[str, float]:
        """
        Calculate Conditional Value at Risk (CVaR) / Expected Shortfall.
        CVaR represents the expected loss given that VaR threshold is breached.
        """
        if len(returns) == 0:
            return {"cvar": 0.0, "var": 0.0}

        returns = np.array(returns)
        var_threshold = np.percentile(returns, (1 - confidence) * 100)
        cvar = float(np.mean(returns[returns <= var_threshold]))

        return {
            "cvar": round(cvar, 6),
            "cvar_pct": round(abs(cvar) * 100, 4),
            "var": round(var_threshold, 6),
            "confidence": confidence,
            "tail_observations": int(np.sum(returns <= var_threshold)),
            "samples": len(returns)
        }

    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe Ratio (annualized)"""
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        excess_returns = np.mean(returns) - risk_free_rate / 252
        return float(round(excess_returns / np.std(returns) * np.sqrt(252), 4))

    def calculate_sortino_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.05,
                                 target_return: float = 0.0) -> Dict[str, float]:
        """
        Calculate Sortino Ratio - uses downside deviation instead of total std.
        Better for asymmetric return distributions.
        """
        if len(returns) == 0:
            return {"sortino": 0.0, "downside_deviation": 0.0}

        returns = np.array(returns)
        excess_returns = np.mean(returns) - risk_free_rate / 252

        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            downside_deviation = 0.0001  # Avoid division by zero
        else:
            downside_deviation = float(np.std(downside_returns))

        sortino = float(excess_returns / downside_deviation * np.sqrt(252)) if downside_deviation > 0 else 0.0

        return {
            "sortino_ratio": round(sortino, 4),
            "downside_deviation": round(downside_deviation, 6),
            "annualized_downside_deviation": round(downside_deviation * np.sqrt(252), 6),
            "mean_return": round(float(np.mean(returns)), 6),
            "negative_return_days": len(downside_returns)
        }

    def calculate_kelly_criterion(self, win_rate: float, avg_win: float,
                                   avg_loss: float) -> Dict[str, float]:
        """
        Calculate Kelly Criterion for optimal position sizing.
        Returns the optimal fraction of capital to bet.
        """
        if avg_loss == 0 or avg_win == 0:
            return {"kelly_fraction": 0.0, "half_kelly": 0.0}

        # Kelly = W - [(1-W) / R], where W = win rate, R = win/loss ratio
        win_loss_ratio = abs(avg_win / avg_loss)
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)

        # Cap at reasonable levels
        kelly = max(0, min(kelly, 1.0))

        return {
            "kelly_fraction": round(kelly, 4),
            "kelly_pct": round(kelly * 100, 2),
            "half_kelly": round(kelly / 2, 4),  # More conservative
            "quarter_kelly": round(kelly / 4, 4),  # Very conservative
            "win_rate": round(win_rate, 4),
            "win_loss_ratio": round(win_loss_ratio, 4),
            "recommendation": "half_kelly" if kelly > 0.2 else "quarter_kelly"
        }

    def calculate_portfolio_risk(self, returns_matrix: np.ndarray,
                                  weights: np.ndarray) -> Dict[str, Any]:
        """
        Calculate portfolio risk using Ledoit-Wolf covariance estimation.
        More stable than sample covariance for high-dimensional portfolios.
        """
        if returns_matrix.shape[0] < 2 or returns_matrix.shape[1] < 1:
            return {"portfolio_variance": 0.0, "portfolio_std": 0.0}

        try:
            # Fit Ledoit-Wolf shrinkage estimator
            lw = LedoitWolf()
            lw.fit(returns_matrix)
            cov_matrix = lw.covariance_
            shrinkage = lw.shrinkage_

            # Calculate portfolio variance
            portfolio_variance = float(np.dot(weights.T, np.dot(cov_matrix, weights)))
            portfolio_std = float(np.sqrt(portfolio_variance))

            # Annualize
            annualized_std = portfolio_std * np.sqrt(252)

            return {
                "portfolio_variance": round(portfolio_variance, 8),
                "portfolio_std": round(portfolio_std, 6),
                "annualized_volatility": round(annualized_std, 4),
                "annualized_volatility_pct": round(annualized_std * 100, 2),
                "shrinkage_coefficient": round(shrinkage, 4),
                "covariance_method": "ledoit-wolf",
                "assets_count": returns_matrix.shape[1]
            }
        except Exception as e:
            logger.error(f"Portfolio risk calculation failed: {e}")
            return {"error": str(e), "portfolio_variance": 0.0}

    def calculate_max_drawdown(self, cumulative_returns: np.ndarray) -> Dict[str, float]:
        """Calculate Maximum Drawdown from cumulative returns"""
        if len(cumulative_returns) == 0:
            return {"max_drawdown": 0.0, "max_drawdown_pct": 0.0}

        cumulative_returns = np.array(cumulative_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_dd = float(np.min(drawdown))

        # Find drawdown period
        peak_idx = np.argmax(cumulative_returns[:np.argmin(drawdown) + 1])
        trough_idx = np.argmin(drawdown)

        return {
            "max_drawdown": round(max_dd, 6),
            "max_drawdown_pct": round(abs(max_dd) * 100, 2),
            "peak_index": int(peak_idx),
            "trough_index": int(trough_idx),
            "recovery_needed_pct": round((1 / (1 + max_dd) - 1) * 100, 2) if max_dd > -1 else 0
        }

    def score_risk(self, position_size: float, volatility: float, max_drawdown: float) -> Dict[str, Any]:
        """Score risk for a trade"""
        # Normalize inputs
        size_score = min(position_size / 100000, 1.0)  # Normalize by max position
        vol_score = min(volatility / 0.5, 1.0)  # Normalize by max volatility
        dd_score = min(abs(max_drawdown) / 0.2, 1.0)  # Normalize by max drawdown

        # Weighted risk score
        risk_score = 0.3 * size_score + 0.4 * vol_score + 0.3 * dd_score

        # Determine risk level
        if risk_score < self.risk_thresholds["low"]:
            risk_level = "LOW"
        elif risk_score < self.risk_thresholds["medium"]:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "components": {
                "position_size_risk": round(size_score, 4),
                "volatility_risk": round(vol_score, 4),
                "drawdown_risk": round(dd_score, 4)
            },
            "recommendation": "PROCEED" if risk_score < 0.7 else "REVIEW"
        }

    def optimize_position_size(self, capital: float, risk_per_trade: float,
                                stop_loss_pct: float) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters"""
        risk_amount = capital * risk_per_trade
        position_size = risk_amount / stop_loss_pct if stop_loss_pct > 0 else 0

        return {
            "optimal_position_size": round(position_size, 2),
            "risk_amount": round(risk_amount, 2),
            "max_loss": round(risk_amount, 2),
            "position_pct_of_capital": round((position_size / capital) * 100, 2) if capital > 0 else 0
        }

    def get_comprehensive_metrics(self, returns: np.ndarray,
                                   risk_free_rate: float = 0.05) -> Dict[str, Any]:
        """Get all risk metrics in a single call"""
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)

        var_result = self.calculate_var(returns, 0.95, "historical")
        cvar_result = self.calculate_cvar(returns, 0.95)
        sortino_result = self.calculate_sortino_ratio(returns, risk_free_rate)
        drawdown_result = self.calculate_max_drawdown(cumulative)

        return {
            "sharpe_ratio": self.calculate_sharpe_ratio(returns, risk_free_rate),
            "sortino_ratio": sortino_result["sortino_ratio"],
            "var_95": var_result["var"],
            "cvar_95": cvar_result["cvar"],
            "max_drawdown_pct": drawdown_result["max_drawdown_pct"],
            "annualized_return": round(float(np.mean(returns) * 252), 4),
            "annualized_volatility": round(float(np.std(returns) * np.sqrt(252)), 4),
            "total_return": round(float(cumulative[-1] - 1) if len(cumulative) > 0 else 0, 4),
            "samples": len(returns)
        }
