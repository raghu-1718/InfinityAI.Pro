import yfinance as yf
import pandas as pd
import os
import argparse
from datetime import datetime, timedelta

def ingest_data(symbols, period="1y", interval="1d", output_dir="data/historical"):
    """
    Ingest historical data from yfinance and save to CSV.
    """
    # Ensure output directory starts from workspace root if not absolute
    if not os.path.isabs(output_dir):
        # Assuming this script ends up in tools/, and we want data/historical at root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Map Indian indices to yfinance symbols if needed
    mapping = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN"
    }

    for symbol in symbols:
        yf_symbol = mapping.get(symbol.upper(), symbol)
        # Append .NS for NSE stocks if not present and not an index
        if not yf_symbol.startswith("^") and not yf_symbol.endswith(".NS") and not yf_symbol.endswith(".BO"):
            yf_symbol = f"{yf_symbol}.NS"

        print(f"Fetching data for {symbol} (yfinance: {yf_symbol})...")
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"⚠️ No data found for {yf_symbol}")
                continue

            file_path = os.path.join(output_dir, f"{symbol.upper()}.csv")
            df.to_csv(file_path)
            print(f"✅ Saved {len(df)} rows to {file_path}")

        except Exception as e:
            print(f"❌ Error fetching {yf_symbol}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InfinityAI.Pro Historical Data Ingester")
    parser.add_argument("--symbols", nargs="+", default=["NIFTY", "BANKNIFTY", "HDFCBANK", "RELIANCE"], help="Symbols to ingest")
    parser.add_argument("--period", default="1y", help="Period (e.g., 1y, 2y, 5y, max)")
    parser.add_argument("--interval", default="1d", help="Interval (1d, 1h, 15m, etc.)")
    parser.add_argument("--output", default="data/historical", help="Output directory")

    args = parser.parse_args()
    ingest_data(args.symbols, args.period, args.interval, args.output)
