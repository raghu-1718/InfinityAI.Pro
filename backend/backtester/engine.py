import vectorbt as vbt
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Add project root to sys.path to import Engine B components
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Note: We simulate the logic of Engine B instead of importing to avoid heavy dependencies and complex intra-package imports in a script context
# However, for a real integration, we'd use the actual classes from engine-b/src/services/

class BacktestEngine:
    def __init__(self, symbol="NIFTY", data_path="data/historical"):
        self.symbol = symbol.upper()
        self.file_path = os.path.join(data_path, f"{self.symbol}.csv")
        
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Historical data not found for {self.symbol} at {self.file_path}")
            
        self.df = pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        print(f"Loaded {len(self.df)} rows for {self.symbol}")

    def run_simple_strategy(self, fast_ma=20, slow_ma=50):
        """
        Run a simple MA crossover strategy as a baseline.
        In reality, this would call Engine B's Signal Generator.
        """
        price = self.df["Close"]
        
        fast_ma_vals = vbt.MA.run(price, fast_ma).ma
        slow_ma_vals = vbt.MA.run(price, slow_ma).ma
        
        entries = fast_ma_vals.vbt.crossed_above(slow_ma_vals)
        exits = fast_ma_vals.vbt.crossed_below(slow_ma_vals)
        
        portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=100000, fees=0.0005)
        
        return portfolio

    def report(self, portfolio):
        print("\n--- Backtest Summary ---")
        print(portfolio.stats())
        
        # Save results
        output_dir = "data/results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Instead of plotting (which might fail in headless), save stats to CSV
        stats = portfolio.stats()
        stats.to_csv(os.path.join(output_dir, f"{self.symbol}_stats.csv"))
        print(f"✅ Stats saved to {output_dir}/{self.symbol}_stats.csv")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="NIFTY")
    args = parser.parse_args()
    
    try:
        engine = BacktestEngine(symbol=args.symbol)
        portfolio = engine.run_simple_strategy()
        engine.report(portfolio)
    except Exception as e:
        print(f"❌ Backtest failed: {e}")
