"""
Institutional Vectorized Backtesting Engine
Supports transaction costs, SEBI 2026 statutory friction, slippage, and DSR/PSR metrics.
"""
import math
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats

from backend.shared.tax_calculator import calculate_options_roundtrip_charges


class VectorizedBacktester:
    """
    Vectorized backtesting engine modeling execution slippage and SEBI 2026 friction.
    """

    def __init__(
        self,
        initial_capital: float = 500000.0,
        slippage_pct: float = 0.0005,
        include_sebi_taxes: bool = True,
        risk_free_rate: float = 0.065  # RBI Repo Rate ~6.5%
    ):
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.include_sebi_taxes = include_sebi_taxes
        self.risk_free_rate = risk_free_rate

    def run_strategy(self, df: pd.DataFrame, signal_col: str = "signal") -> Dict[str, Any]:
        """
        Execute vectorized simulation on price dataframe with a 'signal' column (1: Long, -1: Short, 0: Cash).
        """
        data = df.copy()
        if "close" not in data.columns:
            raise ValueError("Dataframe must contain 'close' price column.")

        # 1. Price returns
        data["asset_return"] = data["close"].pct_change().fillna(0.0)

        # 2. Strategy returns (lag signal by 1 bar to prevent lookahead bias)
        data["position"] = data[signal_col].shift(1).fillna(0.0)
        data["strategy_gross_return"] = data["position"] * data["asset_return"]

        # 3. Detect trades (position transitions)
        data["trades"] = data["position"].diff().abs().fillna(0.0)
        num_trades = int((data["trades"] > 0).sum())

        # 4. Slippage costs
        data["slippage_cost"] = data["trades"] * self.slippage_pct

        # 5. Statutory taxes deduction
        if self.include_sebi_taxes and num_trades > 0:
            avg_premium = float(data["close"].mean())
            roundtrip = calculate_options_roundtrip_charges(premium=avg_premium, lot_size=65, lots=1)
            tax_rate_per_trade = roundtrip.get("total_charges", 55.40) / self.initial_capital
            data["tax_cost"] = data["trades"] * tax_rate_per_trade
        else:
            data["tax_cost"] = 0.0

        # 6. Net returns and equity curve
        data["net_return"] = data["strategy_gross_return"] - data["slippage_cost"] - data["tax_cost"]
        data["equity_curve"] = (1.0 + data["net_return"]).cumprod() * self.initial_capital

        # 7. Metrics calculation
        return self._compute_performance_metrics(data, num_trades)

    def run_buy_and_hold_benchmark(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute passive Buy-and-Hold benchmark strategy.
        """
        data = df.copy()
        data["signal"] = 1.0  # Constant Long
        return self.run_strategy(data, signal_col="signal")

    def _compute_performance_metrics(self, df: pd.DataFrame, num_trades: int) -> Dict[str, Any]:
        """Compute institutional metrics: Sharpe, DSR, PSR, Drawdown, Win Rate."""
        net_returns = df["net_return"].dropna()
        equity = df["equity_curve"]

        final_equity = float(equity.iloc[-1])
        total_pnl = round(final_equity - self.initial_capital, 2)
        total_return_pct = round((total_pnl / self.initial_capital) * 100.0, 2)

        # Annualized Sharpe Ratio
        mean_ret = net_returns.mean() * 252
        std_ret = net_returns.std() * np.sqrt(252)
        rf = self.risk_free_rate

        if std_ret > 0:
            sharpe = (mean_ret - rf) / std_ret
        else:
            sharpe = 0.0

        # Maximum Drawdown
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        max_drawdown_pct = round(abs(float(drawdown.min())) * 100.0, 2)

        # Skewness & Kurtosis for DSR/PSR
        skew = float(stats.skew(net_returns)) if len(net_returns) > 2 else 0.0
        kurt = float(stats.kurtosis(net_returns, fisher=False)) if len(net_returns) > 3 else 3.0

        # Probabilistic Sharpe Ratio (PSR) against benchmark SR=0
        t_samples = len(net_returns)
        sr_std = math.sqrt(max(0.0001, (1.0 - skew * sharpe + (kurt - 1.0) / 4.0 * (sharpe ** 2)) / max(1, t_samples - 1)))
        psr = stats.norm.cdf(sharpe / sr_std) if sr_std > 0 else 0.5

        # Deflated Sharpe Ratio (adjusting for selection bias / N trials)
        num_trials = 10
        expected_max_sr = math.sqrt(2.0 * math.log(max(2, num_trials)))
        dsr = stats.norm.cdf((sharpe - expected_max_sr * 0.2) / max(0.1, sr_std))

        # Win Rate
        winning_days = (net_returns > 0).sum()
        active_days = (df["position"] != 0).sum()
        win_rate_pct = round((winning_days / max(1, active_days)) * 100.0, 1)

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(final_equity, 2),
            "total_pnl": total_pnl,
            "total_return_pct": total_return_pct,
            "sharpe_ratio": round(float(sharpe), 2),
            "deflated_sharpe_ratio": round(float(dsr), 2),
            "probabilistic_sharpe_ratio": round(float(psr), 3),
            "max_drawdown_pct": max_drawdown_pct,
            "win_rate_pct": win_rate_pct,
            "total_trades": num_trades,
            "annualized_volatility": round(float(std_ret) * 100.0, 2)
        }
