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
