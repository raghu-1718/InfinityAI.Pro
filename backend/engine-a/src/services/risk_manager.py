import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import LedoitWolf

from src.safety_limits import MAX_TRADE_CAPITAL, MAX_SESSION_CAPITAL

logger = logging.getLogger(__name__)

class RiskException(Exception):
    pass

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

    def validate_hard_capital_limit(self, order_value: float, current_session_exposure: float = 0.0):
        """
        Hard Guard: Prevents catastrophic exposure.
        Enforced before any API call.
        """
        if order_value > MAX_TRADE_CAPITAL:
            raise RiskException(f"MAX_TRADE_CAPITAL_EXCEEDED: {order_value} > {MAX_TRADE_CAPITAL}")

        if current_session_exposure + order_value > MAX_SESSION_CAPITAL:
            raise RiskException(f"MAX_SESSION_CAPITAL_EXCEEDED: New Exposure {current_session_exposure + order_value} > {MAX_SESSION_CAPITAL}")
        
        return True

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

    def calculate_margin_aware_lot_size(
        self,
        capital: float,
        risk_per_trade: float = 0.10,
        stop_loss_pct: float = 0.11,
        symbol: str = "NIFTY",
        premium: float = 100.0,
        max_lots_cap: int = 10
    ) -> Dict[str, Any]:
        """
        Institutional Margin-Aware Dynamic Lot Sizer for Options Buying.
        Guarantees:
        1. Never exceeds available account capital (prevents Dhan margin rejection).
        2. Fits small capital accounts (e.g. ₹10,000 trades exactly 1 lot safely).
        3. Scales lot count automatically as capital grows.
        """
        sym_u = symbol.upper()
        if "BANKNIFTY" in sym_u:
            lot_size = 30
        elif "FINNIFTY" in sym_u:
            lot_size = 60
        elif "MIDCP" in sym_u:
            lot_size = 120
        elif "SENSEX" in sym_u:
            lot_size = 20
        elif "NIFTY" in sym_u:
            lot_size = 65
        else:
            lot_size = 65

        cost_per_lot = max(1.0, premium * lot_size)
        affordable_lots = int(capital // cost_per_lot)

        # Risk-budgeted lot computation
        risk_amount = capital * max(0.01, min(0.30, risk_per_trade))
        risk_per_lot = cost_per_lot * max(0.05, min(0.50, stop_loss_pct))
        risk_budgeted_lots = max(1, int(risk_amount // risk_per_lot))

        if capital >= cost_per_lot:
            # Capital permits at least 1 lot
            optimal_lots = max(1, min(max_lots_cap, min(affordable_lots, risk_budgeted_lots)))
            is_viable = True
            rejection_reason = None
        else:
            optimal_lots = 0
            is_viable = False
            rejection_reason = f"Insufficient capital (₹{capital:,.2f}) for 1 lot margin (₹{cost_per_lot:,.2f})"

        total_units = optimal_lots * lot_size
        total_margin_required = optimal_lots * cost_per_lot
        max_risk = total_margin_required * stop_loss_pct

        return {
            "symbol": symbol,
            "lot_size": lot_size,
            "optimal_lots": optimal_lots,
            "total_units": total_units,
            "cost_per_lot": round(cost_per_lot, 2),
        "total_margin_required": round(total_margin_required, 2),
            "max_risk_amount": round(max_risk, 2),
            "is_viable": is_viable,
            "rejection_reason": rejection_reason,
            "capital_utilization_pct": round((total_margin_required / capital) * 100, 2) if capital > 0 else 0.0
        }

    def calculate_dynamic_trailing_stop_loss(
        self,
        entry_premium: float,
        highest_observed_premium: float,
        current_premium: float,
        min_stop_loss_pct: float = 0.11,
        min_profit_target_pct: float = 0.15,
        trailing_step_pct: float = 0.05
    ) -> Dict[str, Any]:
        """
        Multi-Tier Dynamic Trailing Stop-Loss & Target Ratchet Engine.
        • Peak Profit >= +8%  -> Lock in Breakeven +1% (Eliminates winning trades reversing to losses)
        • Peak Profit >= +12% -> Lock in +6% guaranteed profit
        • Peak Profit >= +15% -> Lock in +12% guaranteed profit (Allows trade to run to +20%)
        • Peak Profit >= +20% -> Lock in +15% guaranteed profit
        • Peak Profit >= +30% -> Lock in +22% guaranteed profit
        • Peak Profit >= +40% -> Lock in +30% guaranteed profit
        """
        from .dynamic_trailing_profit_lock import DYNAMIC_PROFIT_LOCK
        return DYNAMIC_PROFIT_LOCK.evaluate_trailing_lock(
            entry_premium=entry_premium,
            highest_observed_premium=highest_observed_premium,
            current_premium=current_premium
        )

    def get_comprehensive_metrics(self, returns: np.ndarray,
                                   risk_free_rate: float = 0.05) -> Dict[str, Any]:
        """Get all risk metrics in a single call"""
        returns = np.array(returns)
        cumulative = np.cumprod(1 + returns)

        var_result = self.calculate_var(returns, 0.95, "historical")
        cvar_result = self.calculate_cvar(returns, 0.95)
        sortino_result = self.calculate_sortino_ratio(returns, risk_free_rate)
        drawdown_result = self.calculate_max_drawdown(cumulative)

    def get_optimistic_position_size(self, capital: float, current_price: float, live_volatility: float) -> int:
        """
        Refined VAPS Logic:
        - If vol < target_vol: The market is safe. Scale up (Optimism).
        - If vol > target_vol: The market is risky. Scale down (Caution).
        """
        target_volatility = 0.02  # 2% daily vol target
        max_leverage = 5.0        # SEBI 2025 Intraday limit

        # 1. Calculate Volatility Ratio
        # If live_vol is 1% and target is 2%, scalar is 2.0 (Optimistic)
        vol_scalar = target_volatility / max(live_volatility, 0.005)

        # 2. Apply Risk per trade (e.g., 1% of capital)
        base_risk_amount = capital * 0.01

        # 3. Adjust for Volatility
        if current_price <= 0: return 0
        adjusted_qty = (base_risk_amount * vol_scalar) / current_price

        # 4. Final SEBI Compliance Check (Never exceed 5x leverage)
        max_allowed_qty = (capital * max_leverage) / current_price
        final_qty = min(adjusted_qty, max_allowed_qty)

        return int(final_qty)

    def validate_net_profitability(
        self,
        entry_price: float,
        target_price: float,
        lot_size: int,
        lots: int = 1,
        max_fee_ratio: float = 0.35,
        min_net_profit_margin: float = 0.015
    ) -> Dict[str, Any]:
        """
        Institutional Net Profitability Gate (Anti-Fee Cannibalization).
        Computes exact Indian statutory taxes (STT, GST, Stamp Duty, Exchange Charges, SEBI fees)
        and rejects setups where transactional friction destroys net alpha.
        """
        try:
            try:
                from src.services.tax_calculator import evaluate_net_profitability_gate
            except ImportError:
                try:
                    from shared.tax_calculator import evaluate_net_profitability_gate
                except ImportError:
                    from tax_calculator import evaluate_net_profitability_gate

            return evaluate_net_profitability_gate(
                entry_price=entry_price,
                target_price=target_price,
                lot_size=lot_size,
                lots=lots,
                max_fee_ratio=max_fee_ratio,
                min_net_profit_margin=min_net_profit_margin
            )
        except Exception as e:
            logger.warning(f"Fallback net profitability check: {e}")
            gross = (target_price - entry_price) * (lot_size * lots)
            fees = 50.0  # Safe default estimate
            return {
                "is_viable": (gross - fees) > 0,
                "rejection_reason": None if (gross - fees) > 0 else "Gross profit below fee estimate",
                "gross_profit": round(gross, 2),
                "total_fees": round(fees, 2),
                "net_profit": round(gross - fees, 2),
                "fee_ratio": round(fees / gross, 4) if gross > 0 else 1.0,
                "net_roi": 0.02
            }

