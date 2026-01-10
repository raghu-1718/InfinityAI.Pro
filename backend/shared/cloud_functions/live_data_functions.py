#!/usr/bin/env python3
"""
Real-Time Market Data Ingestion for InfinityAI.Pro
Streams live data from Yahoo Finance and stores in Firestore
"""

import functions_framework
import yfinance as yf
import pandas as pd
from google.cloud import firestore
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List


# Initialize Firestore
db = firestore.Client(project='galvanic-pulsar-482815-h0')

# Symbol mappings for Yahoo Finance
SYMBOL_MAPPINGS = {
    'NIFTY': '^NSEI',
    'BANKNIFTY': '^NSEBANK',
    'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
    'SENSEX': '^BSESN',
    'GOLD': 'GC=F',
    'CRUDEOIL': 'CL=F'
}


def fetch_live_data(symbol: str) -> Dict:
    """Fetch current market data from Yahoo Finance"""
    try:
        yf_symbol = SYMBOL_MAPPINGS.get(symbol, symbol)
        ticker = yf.Ticker(yf_symbol)

        # Get latest data
        hist = ticker.history(period='1d', interval='1m')

        if hist.empty:
            return {'error': f'No data available for {symbol}'}

        latest = hist.iloc[-1]

        # Get additional info
        info = ticker.info

        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': float(latest['Close']),
            'open': float(latest['Open']),
            'high': float(latest['High']),
            'low': float(latest['Low']),
            'volume': int(latest['Volume']),
            'market_cap': info.get('marketCap', 0),
            'change': float(latest['Close'] - latest['Open']),
            'change_percent': float(((latest['Close'] - latest['Open']) / latest['Open']) * 100),
            'previous_close': info.get('previousClose', float(latest['Open'])),
            'day_range': f"{float(latest['Low'])}-{float(latest['High'])}",
            'status': 'live'
        }
    except Exception as e:
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'status': 'error'
        }


def store_in_firestore(data: Dict):
    """Store market data in Firestore"""
    try:
        symbol = data['symbol']
        timestamp = datetime.now()

        # Store in live_prices collection (latest price only)
        live_ref = db.collection('live_prices').document(symbol)
        live_ref.set(data, merge=True)

        # Store in price_history collection (time-series data)
        history_ref = db.collection('price_history').document(symbol).collection('ticks').document(
            timestamp.strftime('%Y%m%d_%H%M%S')
        )
        history_ref.set(data)

        print(f"Stored data for {symbol}: {data['price']}")
    except Exception as e:
        print(f"Error storing data: {e}")


@functions_framework.http
def live_data_ingestion(request):
    """
    Cloud Function to fetch and store live market data
    Triggered via HTTP or Cloud Scheduler
    """
    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        symbols = request_json.get('symbols', list(SYMBOL_MAPPINGS.keys()))

        if isinstance(symbols, str):
            symbols = symbols.split(',')

        results = {}

        for symbol in symbols:
            symbol = symbol.strip().upper()
            data = fetch_live_data(symbol)
            store_in_firestore(data)
            results[symbol] = data

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'symbols_updated': len(results),
            'data': results
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
    Get current live prices from Firestore
    Fast endpoint for dashboard
    """
    try:
        request_json = request.get_json(silent=True) or {}
        request_args = request.args or {}

        symbols = (request_json.get('symbols') or request_args.get('symbols') or
                   ','.join(SYMBOL_MAPPINGS.keys())).split(',')

        results = {}

        for symbol in symbols:
            symbol = symbol.strip().upper()
            doc_ref = db.collection('live_prices').document(symbol)
            doc = doc_ref.get()

            if doc.exists:
                results[symbol] = doc.to_dict()
            else:
                results[symbol] = {
                    'symbol': symbol,
                    'status': 'no_data',
                    'message': 'No live data available'
                }

        return json.dumps({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'prices': results
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }), 500, {'Content-Type': 'application/json'}


@functions_framework.http
def get_price_history(request):
    """
    Get historical price ticks from Firestore
    """
    try:
        request_json = request.get_json(silent=True) or {}
        request_args = request.args or {}

        symbol = (request_json.get('symbol') or request_args.get('symbol') or 'NIFTY').upper()
        limit = int(request_json.get('limit') or request_args.get('limit') or 100)

        # Query price history
        history_ref = db.collection('price_history').document(symbol).collection('ticks')
        query = history_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)

        docs = query.stream()
        history = [doc.to_dict() for doc in docs]

        return json.dumps({
            'status': 'success',
            'symbol': symbol,
            'count': len(history),
            'history': list(reversed(history))  # Oldest first
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return json.dumps({
            'status': 'error',
            'error': str(e)
        }), 500, {'Content-Type': 'application/json'}


if __name__ == '__main__':
    """For local testing"""
    import sys
    from flask import Flask, request as flask_request

    app = Flask(__name__)

    @app.route('/ingest', methods=['POST', 'GET'])
    def ingest():
        return live_data_ingestion(flask_request)

    @app.route('/prices', methods=['GET'])
    def prices():
        return get_live_prices(flask_request)

    @app.route('/history', methods=['GET'])
    def history():
        return get_price_history(flask_request)

    app.run(host='0.0.0.0', port=8080, debug=True)
