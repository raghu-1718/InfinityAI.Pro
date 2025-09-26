# backtester.py
import os, math, random, pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.config import CONFIG
from typing import Callable, Dict, Any

random.seed(CONFIG.RANDOM_SEED)
np.random.seed(CONFIG.RANDOM_SEED)

# Candle CSV format expectation:
# datetime,open,high,low,close,volume  (datetime ISO or %Y-%m-%d %H:%M:%S)

class Backtester:
    def __init__(self, symbol:str, data_path:str, initial_capital:float=CONFIG.CAPITAL):
        self.symbol = symbol
        self.df = pd.read_csv(os.path.join(data_path, f"{symbol}.csv"), parse_dates=["datetime"]).sort_values("datetime").reset_index(drop=True)
        self.capital = initial_capital
        self.equity_curve = []
        self.positions = []
        self.commission = CONFIG.COMMISSION_PER_TRADE
        self.slippage = CONFIG.SLIPPAGE_PTS

    def simulate_option_premium(self, row:pd.Series) -> float:
        # Simple heuristic: option ATM premium proportional to volatility & price
        price = row["close"]
        # simplistic implied vol proxy: rolling std of returns
        vol = self.df["close"].pct_change().rolling(50).std().loc[row.name]
        if np.isnan(vol): vol = 0.01
        premium = max(5.0, (price * vol * 10))  # tune multiplier
        return float(premium)

    def run(self, strategy_fn: Callable[[pd.DataFrame, int], Dict[str,Any]], verbose=True):
        balance = self.capital
        open_trades = []
        for i, row in self.df.iterrows():
            # let strategy decide at index i (use past window inside strategy)
            decision = strategy_fn(self.df, i)
            # decision example: {"action":"BUY_OPT","contracts":1,"premium":premium,"sl":sl,"tp":tp}
            if decision:
                action = decision.get("action")
                if action == "BUY_OPT":
                    cost = decision["premium"] * decision["contracts"]
                    cost += self.commission
                    # slippage: reduce fill favorably/unfavorably
                    cost += self.slippage * decision["contracts"]
                    if cost <= balance * 0.3:  # position cap rule
                        balance -= cost
                        open_trades.append({"entry_index": i, "contracts": decision["contracts"], "entry_premium": decision["premium"], "sl":decision["sl"], "tp":decision["tp"], "status":"OPEN"})
                        if verbose:
                            print(f"[{row['datetime']}] Bought {decision['contracts']} opt at {decision['premium']:.2f}, cost {cost:.2f} bal {balance:.2f}")
            # Evaluate open trades (naive: check if sl/tp hit using candle low/high)
            to_close = []
            for t in open_trades:
                if t["status"]!="OPEN": continue
                # for simplicity check current candle high/low to see if target hit
                if row["low"] <= t["sl"]:
                    # hit SL -> loss
                    pnl = - (t["entry_premium"] - t["sl"]) * t["contracts"]
                    balance += 0  # premium already paid; realize loss separately
                    t["status"]="CLOSED"
                    t["exit_index"]=i
                    t["pnl"]=pnl
                    to_close.append(t)
                    if verbose: print(f"[{row['datetime']}] SL hit for trade entered at {t['entry_index']} pnl {pnl:.2f}")
                elif row["high"] >= t["tp"]:
                    pnl = (t["tp"] - t["entry_premium"]) * t["contracts"]
                    balance += t["entry_premium"]*t["contracts"] + pnl  # assume we get back cost + pnl
                    t["status"]="CLOSED"
                    t["exit_index"]=i
                    t["pnl"]=pnl
                    to_close.append(t)
                    if verbose: print(f"[{row['datetime']}] TP hit for trade entered at {t['entry_index']} pnl {pnl:.2f}")
            # remove closed trades
            for c in to_close:
                open_trades.remove(c)
            # Track equity snapshot (balance + unrealized placeholders)
            unrealized = sum([(row["close"] - t["entry_premium"]) * t["contracts"] for t in open_trades])
            self.equity_curve.append(balance + unrealized)
        self.capital = balance + sum([(t.get("pnl",0)) for t in (open_trades+[] )])
        return self.summary()

    def summary(self):
        s = {
            "final_capital": self.capital,
            "equity_curve_len": len(self.equity_curve)
        }
        return s

# Example strategy function for backtester (simple MACD+RSI rule)
def example_strategy(df:pd.DataFrame, idx:int):
    if idx < 60: return None
    window = df.iloc[max(0, idx-50):idx]
    close = window["close"]
    ema12 = close.ewm(span=12).mean().iloc[-1]
    ema26 = close.ewm(span=26).mean().iloc[-1]
    macd = ema12 - ema26
    rsi = (100 - (100/(1 + ((close.diff().clip(lower=0).rolling(14).mean().iloc[-1])/( -close.diff().clip(upper=0).abs().rolling(14).mean().iloc[-1] + 1e-9)))))
    # get premium using current row approximate
    row = df.iloc[idx]
    price = row["close"]
    # compute simple premium
    premium = max(10.0, price * 0.0005)
    if macd > 0 and rsi > 45 and premium > 30:
        sl = premium * 0.4
        tp = premium * 1.5
        return {"action":"BUY_OPT","contracts":1,"premium":premium,"sl":sl,"tp":tp}
    return None

if __name__ == "__main__":
    # example usage (ensure you have data/backtest_5m/NIFTY.csv)
    symbol = "NIFTY"
    path = CONFIG.BACKTEST_DATA_PATH
    bt = Backtester(symbol, path)
    report = bt.run(example_strategy, verbose=False)
    print("Backtest finished:", report)