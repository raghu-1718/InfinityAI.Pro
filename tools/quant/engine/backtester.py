"""
Master Deterministic Replay & Walk-Forward Backtesting Engine
"""
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from ..core.clock import MarketClock
from ..core.greeks import compute_bs_greeks
from ..core.taxes import calculate_sebi_2026_charges
from ..core.fill_model import ExecutionSimulator, FillConfig, REALISTIC_MODEL
from ..core.strategy_wrapper import StrategyWrapper

class InstitutionalBacktester:
    """
    High-fidelity deterministic backtester for InfinityAI.Pro Directional Option Strategy.
    """
    def __init__(
        self,
        strategy_wrapper: Optional[StrategyWrapper] = None,
        fill_config: FillConfig = REALISTIC_MODEL,
        opening_cooldown_enabled: bool = True
    ):
        self.strategy = strategy_wrapper or StrategyWrapper()
        self.fill_sim = ExecutionSimulator(fill_config)
        self.clock = MarketClock(opening_cooldown_enabled=opening_cooldown_enabled)
        self.fill_config = fill_config

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates RSI, MACD, ATR, ADX, and Bollinger Bands"""
        data = df.copy()
        close = data["close"]
        high = data["high"]
        low = data["low"]

        # 1. RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        data["rsi"] = 100 - (100 / (1 + rs))

        # 2. MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        data["macd"] = ema12 - ema26
        data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
        data["macd_hist"] = data["macd"] - data["macd_signal"]

        # 3. ATR & Volatility
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        data["atr"] = tr.rolling(window=14).mean()

        # 4. ADX (Directional Movement)
        plus_dm = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        plus_di = 100 * (plus_dm.rolling(14).mean() / (data["atr"] + 1e-9))
        minus_di = 100 * (minus_dm.rolling(14).mean() / (data["atr"] + 1e-9))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
        data["adx"] = dx.rolling(14).mean()

        # 5. EMA 20 & EMA 50 Trend
        data["ema20"] = close.ewm(span=20, adjust=False).mean()
        data["ema50"] = close.ewm(span=50, adjust=False).mean()

        return data.dropna()

    def run_backtest(self, df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Executes deterministic event-by-event walk-forward replay.
        """
        data = self._calculate_indicators(df)
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        current_capital = self.strategy.capital
        initial_capital = self.strategy.capital
        active_trade: Optional[Dict[str, Any]] = None

        for idx, row in data.iterrows():
            ts = idx if isinstance(idx, datetime) else pd.to_datetime(idx)
            spot = row["close"]
            rsi = row["rsi"]
            macd_hist = row["macd_hist"]
            adx = row["adx"]
            ema20 = row["ema20"]
            ema50 = row["ema50"]

            equity_curve.append({
                "timestamp": ts,
                "capital": round(current_capital, 2),
                "has_active_trade": active_trade is not None
            })

            # 1. MANAGE ACTIVE TRADE (MTM, Ratchet, SL, Target, EOD)
            if active_trade:
                greeks = compute_bs_greeks(
                    spot=spot,
                    strike=active_trade["strike"],
                    dte_days=max(0.5, 3.0 - (ts - active_trade["entry_time"]).total_seconds() / 86400.0),
                    iv=0.145,
                    option_type=active_trade["option_type"]
                )
                cur_premium = greeks["price"]

                if cur_premium > active_trade["highest_premium"]:
                    active_trade["highest_premium"] = cur_premium

                new_sl, ratchet_action = self.strategy.evaluate_trailing_ratchet(
                    entry_price=active_trade["entry_premium_filled"],
                    current_price=cur_premium,
                    highest_price=active_trade["highest_premium"],
                    current_sl=active_trade["current_sl"]
                )
                active_trade["current_sl"] = new_sl

                hit_target = cur_premium >= active_trade["target_premium"]
                hit_sl = cur_premium <= active_trade["current_sl"]
                hit_eod = self.clock.is_eod_squareoff_due(ts)

                if hit_target or hit_sl or hit_eod:
                    if hit_target:
                        exit_reason = "TARGET_HIT"
                        raw_exit_p = active_trade["target_premium"]
                    elif hit_sl:
                        exit_reason = "STOP_LOSS_HIT"
                        raw_exit_p = active_trade["current_sl"]
                    else:
                        exit_reason = "EOD_SQUAREOFF"
                        raw_exit_p = cur_premium

                    fill_exit_p = self.fill_sim.simulate_exit_fill(raw_exit_p)

                    qty = active_trade["units"]
                    gross_pnl = (fill_exit_p - active_trade["entry_premium_filled"]) * qty
                    charges = calculate_sebi_2026_charges(
                        premium_entry=active_trade["entry_premium_filled"],
                        premium_exit=fill_exit_p,
                        lot_size=active_trade["lot_size"],
                        lots=active_trade["lots"]
                    )
                    net_pnl = gross_pnl - charges["total_charges"]
                    current_capital += net_pnl

                    duration_mins = round((ts - active_trade["entry_time"]).total_seconds() / 60.0, 1)

                    trade_record = {
                        "symbol": symbol,
                        "option_symbol": active_trade["option_symbol"],
                        "entry_time": active_trade["entry_time"].isoformat(),
                        "exit_time": ts.isoformat(),
                        "duration_minutes": duration_mins,
                        "option_type": active_trade["option_type"],
                        "strike": active_trade["strike"],
                        "lots": active_trade["lots"],
                        "units": qty,
                        "entry_premium": active_trade["entry_premium_filled"],
                        "exit_premium": fill_exit_p,
                        "highest_premium": active_trade["highest_premium"],
                        "exit_reason": exit_reason,
                        "gross_pnl": round(gross_pnl, 2),
                        "taxes_and_brokerage": charges["total_charges"],
                        "net_pnl": round(net_pnl, 2),
                        "return_pct": round((fill_exit_p - active_trade["entry_premium_filled"]) / active_trade["entry_premium_filled"], 4),
                        "capital_after": round(current_capital, 2)
                    }
                    trades.append(trade_record)
                    active_trade = None
                continue

            # 2. EVALUATE NEW SIGNAL GENERATION
            if not self.clock.is_entry_allowed(ts):
                continue

            signal_type = None
            if rsi > 52 and macd_hist > 0 and spot > ema20 > ema50 and adx >= self.strategy.adx_threshold:
                signal_type = "BUY_CALL"
            elif rsi < 48 and macd_hist < 0 and spot < ema20 < ema50 and adx >= self.strategy.adx_threshold:
                signal_type = "BUY_PUT"

            if not signal_type:
                continue

            opt_info = self.strategy.resolve_itm1_strike(symbol=symbol, spot=spot, signal_type=signal_type)
            est_premium = opt_info["theoretical_premium"]

            sizing = self.strategy.calculate_lot_size(symbol=symbol, premium=est_premium)
            if not sizing["is_viable"] or sizing["lots"] <= 0:
                continue

            fill_res = self.fill_sim.simulate_entry_fill(est_premium)
            if not fill_res["filled"]:
                continue

            filled_entry_p = fill_res["effective_price"]
            target_p = round(filled_entry_p * 1.15, 2)
            stop_loss_p = round(filled_entry_p * 0.92, 2)

            active_trade = {
                "symbol": symbol,
                "option_symbol": f"{symbol} {int(opt_info['strike'])} {opt_info['option_type']}",
                "entry_time": ts,
                "option_type": opt_info["option_type"],
                "strike": opt_info["strike"],
                "lots": sizing["lots"],
                "units": sizing["units"],
                "lot_size": sizing["lot_size"],
                "entry_premium_raw": est_premium,
                "entry_premium_filled": filled_entry_p,
                "target_premium": target_p,
                "stop_loss_initial": stop_loss_p,
                "current_sl": stop_loss_p,
                "highest_premium": filled_entry_p
            }

        df_trades = pd.DataFrame(trades)
        total_trades = len(df_trades)
        if total_trades > 0:
            wins = df_trades[df_trades["net_pnl"] > 0]
            losses = df_trades[df_trades["net_pnl"] <= 0]
            win_rate = len(wins) / total_trades
            total_net_pnl = df_trades["net_pnl"].sum()
            total_gross_pnl = df_trades["gross_pnl"].sum()
            total_taxes = df_trades["taxes_and_brokerage"].sum()
            gross_win = wins["gross_pnl"].sum() if len(wins) > 0 else 0
            gross_loss = abs(losses["gross_pnl"].sum()) if len(losses) > 0 else 1.0
            profit_factor = gross_win / gross_loss if gross_loss > 0 else 99.0
            avg_duration = df_trades["duration_minutes"].mean()
            max_win = df_trades["net_pnl"].max()
            max_loss = df_trades["net_pnl"].min()
        else:
            win_rate = 0.0
            total_net_pnl = 0.0
            total_gross_pnl = 0.0
            total_taxes = 0.0
            profit_factor = 0.0
            avg_duration = 0.0
            max_win = 0.0
            max_loss = 0.0

        df_equity = pd.DataFrame(equity_curve)
        if len(df_equity) > 0:
            df_equity["peak"] = df_equity["capital"].cummax()
            df_equity["drawdown"] = (df_equity["capital"] - df_equity["peak"]) / df_equity["peak"]
            max_dd = abs(df_equity["drawdown"].min())
        else:
            max_dd = 0.0

        return {
            "symbol": symbol,
            "total_trades": total_trades,
            "wins": len(df_trades[df_trades["net_pnl"] > 0]) if total_trades > 0 else 0,
            "losses": len(df_trades[df_trades["net_pnl"] <= 0]) if total_trades > 0 else 0,
            "win_rate_pct": round(win_rate * 100.0, 2),
            "total_gross_pnl": round(total_gross_pnl, 2),
            "total_taxes": round(total_taxes, 2),
            "total_net_pnl": round(total_net_pnl, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_dd * 100.0, 2),
            "avg_duration_minutes": round(avg_duration, 1),
            "max_win": round(max_win, 2),
            "max_loss": round(max_loss, 2),
            "final_capital": round(current_capital, 2),
            "trades_df": df_trades,
            "equity_df": df_equity
        }
