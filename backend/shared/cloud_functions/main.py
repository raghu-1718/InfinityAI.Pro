#!/usr/bin/env python3
"""
Cloud Functions for InfinityAI.Pro Trading Platform
- Backtesting with optimized MA strategies
- Real-time market data ingestion
- Trading signal detection and notifications
"""

import functions_framework
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from google.cloud import storage, firestore, pubsub_v1
from io import StringIO
import yfinance as yf


class SimpleBacktester:
    """Minimal MA Crossover Backtester - Optimized v2.0"""

    # Optimized MA parameters per symbol (based on 3y historical optimization)
    SYMBOL_CONFIG = {
        'NIFTY': {'ma_short': 15, 'ma_long': 45, 'strategy': 'MA_Crossover'},
        'BANKNIFTY': {'ma_short': 20, 'ma_long': 50, 'strategy': 'MA_Crossover'},
        'FINNIFTY': {'ma_short': 20, 'ma_long': 50, 'strategy': 'MA_Crossover'},
        'SENSEX': {'ma_short': 20, 'ma_long': 50, 'strategy': 'MA_Crossover'},
        'GOLD': {'ma_short': 50, 'ma_long': 200, 'strategy': 'MA_Crossover'},
        'CRUDEOIL': {'ma_short': 15, 'ma_long': 45, 'strategy': 'MA_Crossover'},
        'DEFAULT': {'ma_short': 20, 'ma_long': 50, 'strategy': 'MA_Crossover'}
    }

    def __init__(self):
        self.storage_client = storage.Client(project='galvanic-pulsar-482815-h0')

    def get_symbol_config(self, symbol):
        """Get optimized MA parameters for symbol"""
        return self.SYMBOL_CONFIG.get(symbol.upper(), self.SYMBOL_CONFIG['DEFAULT'])

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
            symbol_name = symbol.strip()
            config = backtester.get_symbol_config(symbol_name)

            df = backtester.load_from_gcs(symbol_name, interval, period)
            result = backtester.backtest(
                df,
                ma_short=config['ma_short'],
                ma_long=config['ma_long']
            )
            result['config'] = config  # Include optimized params in response
            results[symbol_name] = result

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


# ========================================
# Real-Time Market Data Functions
# ========================================

# Initialize Firestore and Pub/Sub clients
db = firestore.Client(project='galvanic-pulsar-482815-h0')
publisher = pubsub_v1.PublisherClient()
TOPIC_PATH = publisher.topic_path('galvanic-pulsar-482815-h0', 'trading-signals')

# Symbol mappings for Yahoo Finance
SYMBOL_MAPPINGS = {
    'NIFTY': '^NSEI',
    'BANKNIFTY': '^NSEBANK',
    'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
    'SENSEX': '^BSESN',
    'GOLD': 'GC=F',
    'CRUDEOIL': 'CL=F'
}


@functions_framework.http
def live_data_ingestion(request):
    """
    Ingest real-time market data from Yahoo Finance and store in Firestore
    Endpoint: /live-data-ingestion
    Triggered by Cloud Scheduler every 5 minutes
    """
    try:
        symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL']
        results = {}

        for symbol in symbols:
            yf_symbol = SYMBOL_MAPPINGS.get(symbol, symbol)
            ticker = yf.Ticker(yf_symbol)

            # Get latest 1-minute data
            hist = ticker.history(period='1d', interval='1m')

            if not hist.empty:
                latest = hist.iloc[-1]

                data = {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'price': float(latest['Close']),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'volume': int(latest['Volume']),
                    'change_percent': float(((latest['Close'] - hist.iloc[0]['Open']) / hist.iloc[0]['Open']) * 100) if len(hist) > 1 else 0.0
                }

                # Store in Firestore (dual write for fast reads and time-series)
                # 1. Latest price (overwrites)
                db.collection('live_prices').document(symbol).set(data)

                # 2. Time-series tick data
                db.collection('price_history').document(symbol).collection('ticks').add(data)

                results[symbol] = 'success'
            else:
                results[symbol] = 'no_data'

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'results': results
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


@functions_framework.http
def get_live_prices(request):
    """
    Get current live prices for all symbols (fast Firestore read)
    Endpoint: /get-live-prices
    """
    try:
        live_prices_ref = db.collection('live_prices')
        docs = live_prices_ref.stream()

        prices = {}
        for doc in docs:
            data = doc.to_dict()
            # Convert timestamp to ISO string
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp'].isoformat()
            prices[doc.id] = data

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'prices': prices
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


@functions_framework.http
def get_price_history(request):
    """
    Get price history for a specific symbol
    Parameters:
    - symbol: NIFTY, BANKNIFTY, etc.
    - hours: Number of hours (default: 24)
    """
    try:
        request_json = request.get_json(silent=True) or {}
        request_args = request.args or {}

        symbol = request_json.get('symbol') or request_args.get('symbol') or 'NIFTY'
        hours = int(request_json.get('hours') or request_args.get('hours') or 24)

        cutoff_time = datetime.now() - timedelta(hours=hours)

        ticks_ref = db.collection('price_history').document(symbol).collection('ticks')
        query = ticks_ref.where('timestamp', '>=', cutoff_time).order_by('timestamp')

        ticks = []
        for doc in query.stream():
            data = doc.to_dict()
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp'].isoformat()
            ticks.append(data)

        return json.dumps({
            'status': 'success',
            'symbol': symbol,
            'hours': hours,
            'count': len(ticks),
            'data': ticks
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


# ========================================
# Momentum Strategy Functions (Simplified)
# ========================================

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.zeros_like(prices)
    avg_loss = np.zeros_like(prices)

    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])

    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD indicator"""
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series(macd_line).ewm(span=signal, adjust=False).mean().values
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


@functions_framework.http
def detect_momentum_signals(request):
    """
    Detect trading signals using momentum strategies (RSI, MACD)
    Returns active BUY/SELL signals for all symbols
    """
    try:
        symbols = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL']
        all_signals = []

        for symbol in symbols:
            # Get historical data from Firestore
            cutoff_time = datetime.now() - timedelta(hours=72)
            ticks_ref = db.collection('price_history').document(symbol).collection('ticks')
            query = ticks_ref.where('timestamp', '>=', cutoff_time).order_by('timestamp').limit(200)

            ticks = []
            for doc in query.stream():
                d = doc.to_dict()
                ticks.append({
                    'timestamp': d['timestamp'],
                    'price': d['price'],
                    'volume': d['volume']
                })

            if len(ticks) < 50:
                continue  # Not enough data

            prices = np.array([t['price'] for t in ticks])
            latest_price = prices[-1]

            # Calculate RSI
            rsi = calculate_rsi(prices, period=14)
            latest_rsi = rsi[-1]

            # Calculate MACD
            macd_line, signal_line, histogram = calculate_macd(prices)
            latest_macd = macd_line[-1]
            latest_signal = signal_line[-1]
            latest_histogram = histogram[-1]
            prev_histogram = histogram[-2]

            # Signal Detection Logic
            signal_type = 'HOLD'
            confidence = 0.0
            strategy = None

            # RSI Strategy
            if latest_rsi < 30:  # Oversold
                signal_type = 'BUY'
                confidence = (30 - latest_rsi) / 30
                strategy = 'RSI'
            elif latest_rsi > 70:  # Overbought
                signal_type = 'SELL'
                confidence = (latest_rsi - 70) / 30
                strategy = 'RSI'

            # MACD Strategy (overrides if stronger)
            if prev_histogram < 0 and latest_histogram > 0:  # Bullish crossover
                if not strategy or confidence < 0.7:
                    signal_type = 'BUY'
                    confidence = min(abs(latest_histogram) / abs(latest_macd + 1e-10), 0.95)
                    strategy = 'MACD'
            elif prev_histogram > 0 and latest_histogram < 0:  # Bearish crossover
                if not strategy or confidence < 0.7:
                    signal_type = 'SELL'
                    confidence = min(abs(latest_histogram) / abs(latest_macd + 1e-10), 0.95)
                    strategy = 'MACD'

            # Only save active signals (not HOLD)
            if signal_type != 'HOLD' and confidence > 0.3:
                signal_data = {
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'signal_type': signal_type,
                    'strategy': strategy,
                    'confidence': float(confidence),
                    'price': float(latest_price),
                    'indicators': {
                        'rsi': float(latest_rsi),
                        'macd': float(latest_macd),
                        'signal_line': float(latest_signal),
                        'histogram': float(latest_histogram)
                    }
                }

                # Store in Firestore
                db.collection('trading_signals').add(signal_data)

                # Publish to Pub/Sub
                message_data = json.dumps(signal_data, default=str).encode('utf-8')
                publisher.publish(TOPIC_PATH, message_data)

                all_signals.append(signal_data)

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'signals': all_signals,
            'count': len(all_signals)
        }, default=str), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


@functions_framework.http
def get_latest_signals(request):
    """
    Get latest trading signals from Firestore
    Parameters:
    - hours: Number of hours to look back (default: 24)
    - limit: Max number of signals (default: 20)
    """
    try:
        request_json = request.get_json(silent=True) or {}
        request_args = request.args or {}

        hours = int(request_json.get('hours') or request_args.get('hours') or 24)
        limit = int(request_json.get('limit') or request_args.get('limit') or 20)

        cutoff_time = datetime.now() - timedelta(hours=hours)

        signals_ref = db.collection('trading_signals')
        query = signals_ref.where('timestamp', '>=', cutoff_time).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)

        signals = []
        for doc in query.stream():
            data = doc.to_dict()
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp'].isoformat()
            signals.append(data)

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'hours': hours,
            'count': len(signals),
            'signals': signals
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


