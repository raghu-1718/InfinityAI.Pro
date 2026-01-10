#!/usr/bin/env python3
"""
Trading Signal Detection and Notification System
Runs momentum strategies on live data and sends notifications
"""

import functions_framework
import json
from google.cloud import firestore, pubsub_v1
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.momentum_strategies import (
    RSIStrategy, MACDStrategy, BollingerBandsStrategy,
    MultiStrategyEngine, Signal
)

# Initialize clients
db = firestore.Client(project='galvanic-pulsar-482815-h0')
publisher = pubsub_v1.PublisherClient()

TOPIC_PATH = publisher.topic_path('galvanic-pulsar-482815-h0', 'trading-signals')


def get_historical_data_from_firestore(symbol: str, hours: int = 24) -> pd.DataFrame:
    """Fetch recent price history from Firestore"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history_ref = db.collection('price_history').document(symbol).collection('ticks')
        query = history_ref.where('timestamp', '>=', cutoff_time.isoformat()).order_by('timestamp')

        docs = query.stream()
        data = []

        for doc in docs:
            d = doc.to_dict()
            data.append({
                'timestamp': pd.to_datetime(d['timestamp']),
                'open': d['open'],
                'high': d['high'],
                'low': d['low'],
                'close': d['price'],
                'volume': d['volume']
            })

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df

    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return pd.DataFrame()


def detect_signals(symbol: str) -> dict:
    """Run strategies and detect trading signals"""
    try:
        # Get recent data
        df = get_historical_data_from_firestore(symbol, hours=72)  # 3 days of data

        if df.empty or len(df) < 50:
            return {
                'symbol': symbol,
                'status': 'insufficient_data',
                'message': f'Need at least 50 data points, got {len(df)}'
            }

        # Run multi-strategy analysis
        engine = MultiStrategyEngine()
        results = engine.run_all_strategies(df, symbol)

        # Check for active signals in latest data
        active_signals = []
        latest_signals = results.get('latest_signals', {})

        for strategy_name, signal_data in latest_signals.items():
            # Only consider recent signals (within last hour)
            signal_time = pd.to_datetime(signal_data['timestamp'])
            if (datetime.now() - signal_time).total_seconds() < 3600:
                active_signals.append({
                    'strategy': strategy_name,
                    'type': signal_data['signal_type'],
                    'price': signal_data['price'],
                    'confidence': signal_data['confidence'],
                    'timestamp': signal_data['timestamp'],
                    'indicators': signal_data['indicators']
                })

        # Store signal in Firestore
        if active_signals:
            signal_doc = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'signals': active_signals,
                'best_strategy': results.get('best_strategy', {}),
                'status': 'active'
            }

            db.collection('trading_signals').document(f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}").set(signal_doc)

        return {
            'symbol': symbol,
            'status': 'success',
            'active_signals': active_signals,
            'best_strategy': results.get('best_strategy', {}),
            'all_strategies': {k: v for k, v in results.items() if k not in ['latest_signals', 'best_strategy']}
        }

    except Exception as e:
        import traceback
        return {
            'symbol': symbol,
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def send_notification(signal_data: dict):
    """Send signal notification via Pub/Sub"""
    try:
        message_data = json.dumps(signal_data).encode('utf-8')
        future = publisher.publish(TOPIC_PATH, message_data)
        message_id = future.result()
        print(f"Published signal to Pub/Sub: {message_id}")
        return message_id
    except Exception as e:
        print(f"Error publishing to Pub/Sub: {e}")
        return None


@functions_framework.http
def signal_detector(request):
    """
    Cloud Function to detect trading signals
    Runs strategies on live data and generates alerts
    """
    try:
        request_json = request.get_json(silent=True) or {}
        symbols = request_json.get('symbols', ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'SENSEX', 'GOLD', 'CRUDEOIL'])

        if isinstance(symbols, str):
            symbols = symbols.split(',')

        all_results = {}
        notifications_sent = 0

        for symbol in symbols:
            symbol = symbol.strip().upper()
            result = detect_signals(symbol)
            all_results[symbol] = result

            # Send notification if signals detected
            if result.get('active_signals'):
                send_notification(result)
                notifications_sent += 1

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbols_analyzed': len(all_results),
            'signals_detected': notifications_sent,
            'results': all_results
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500, {'Content-Type': 'application/json'}


@functions_framework.cloud_event
def process_signal_notification(cloud_event):
    """
    Process signal notifications from Pub/Sub
    Send emails, webhooks, etc.
    """
    import base64

    try:
        # Decode Pub/Sub message
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        signal_data = json.loads(message_data)

        symbol = signal_data['symbol']
        signals = signal_data['active_signals']

        # Store notification in Firestore
        notification_doc = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'signals': signals,
            'sent_at': datetime.now().isoformat(),
            'channels': ['firestore', 'pubsub'],  # Add more channels (email, slack, etc.)
            'status': 'delivered'
        }

        db.collection('notifications').add(notification_doc)

        print(f"Processed notification for {symbol}: {len(signals)} signals")

        # Here you can add:
        # - Send email via SendGrid
        # - Post to Slack/Discord webhook
        # - Send push notification
        # - Trigger webhook to external system

    except Exception as e:
        print(f"Error processing notification: {e}")


@functions_framework.http
def get_latest_signals(request):
    """
    Get latest trading signals for dashboard
    """
    try:
        request_args = request.args or {}
        limit = int(request_args.get('limit', 10))

        # Query latest signals
        signals_ref = db.collection('trading_signals').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = signals_ref.stream()

        signals = [doc.to_dict() for doc in docs]

        return json.dumps({
            'status': 'success',
            'count': len(signals),
            'signals': signals
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }), 500, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    """For local testing"""
    from flask import Flask, request as flask_request

    app = Flask(__name__)

    @app.route('/detect', methods=['POST', 'GET'])
    def detect():
        return signal_detector(flask_request)

    @app.route('/signals', methods=['GET'])
    def signals():
        return get_latest_signals(flask_request)

    app.run(host='0.0.0.0', port=8081, debug=True)
