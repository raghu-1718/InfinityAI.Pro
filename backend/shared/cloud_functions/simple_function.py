#!/usr/bin/env python3
"""
Simple Cloud Function for Backtest Execution
Uses local backtester with Yahoo Finance data from GCS
"""

import functions_framework
import json
import pandas as pd
import numpy as np
from datetime import datetime
from google.cloud import storage
from io import StringIO


class SimpleBacktester:
    """Minimal MA Crossover Backtester"""

    def __init__(self):
        self.storage_client = storage.Client(project='galvanic-pulsar-482815-h0')

    def load_from_gcs(self, symbol, interval='1d', period='1y'):
        """Load CSV from GCS"""
        try:
            bucket = self.storage_client.bucket('infinityai-backtesting-data')
            blob = bucket.blob(f"{symbol}/{symbol}_{interval}_{period}.csv")
            csv_content = blob.download_as_text()

            df = pd.read_csv(StringIO(csv_content))
            df.columns = [c.lower() for c in df.columns]
            df['timestamp'] = pd.to_datetime(df['date'] if 'date' in df.columns else df['timestamp'])
            return df.sort_values('timestamp').reset_index(drop=True)
        except Exception as e:
            return None

    def backtest(self, df, initial_capital=1000000, ma_short=20, ma_long=50):
        """Run MA crossover backtest"""
        if df is None or len(df) < ma_long:
            return {'error': 'Insufficient data'}

        df['ma_short'] = df['close'].rolling(ma_short).mean()
        df['ma_long'] = df['close'].rolling(ma_long).mean()
        df['signal'] = 0
        df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1
        df.loc[df['ma_short'] < df['ma_long'], 'signal'] = -1

        cash = initial_capital
        position = 0
        entry_price = 0
        trades = []

        for i in range(ma_long, len(df)):
            price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]

            # Exit
            if position > 0 and signal == -1:
                pnl = (price - entry_price) * position
                trades.append({'pnl': float(pnl), 'exit_price': float(price)})
                cash += position * price
                position = 0

            # Entry
            elif position == 0 and signal == 1:
                position = int((cash * 0.02) / price)
                entry_price = price
                cash -= position * price

        final_equity = cash + (position * df['close'].iloc[-1] if position > 0 else 0)
        total_pnl = sum(t['pnl'] for t in trades)

        return {
            'trades': len(trades),
            'wins': len([t for t in trades if t['pnl'] > 0]),
            'total_pnl': float(total_pnl),
            'final_equity': float(final_equity),
            'return_pct': float(((final_equity - initial_capital) / initial_capital) * 100)
        }


@functions_framework.http
def main(request):
    """
    Cloud Function HTTP handler

    Parameters:
    - symbols: Comma-separated symbols (default: NIFTY,BANKNIFTY,FINNIFTY)
    - interval: 1d, 1h (default: 1d)
    - period: 6m, 1y, 3y (default: 1y)
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        request_args = request.args or {}

        symbols = (request_json.get('symbols') or request_args.get('symbols') or 'NIFTY,BANKNIFTY,FINNIFTY').split(',')
        interval = request_json.get('interval') or request_args.get('interval') or '1d'
        period = request_json.get('period') or request_args.get('period') or '1y'

        backtester = SimpleBacktester()
        results = {}

        for symbol in symbols:
            df = backtester.load_from_gcs(symbol.strip(), interval, period)
            result = backtester.backtest(df)
            results[symbol.strip()] = result

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'config': {'interval': interval, 'period': period},
            'results': results
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}
