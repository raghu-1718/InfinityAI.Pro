"""Scan crude oil market and check for trades."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'engine-c'))

from dhanhq import dhanhq
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'galvanic-pulsar-482815-h0',
    })

db = firestore.client()

print("=" * 80)
print("CRUDE OIL MARKET SCAN & TRADE ANALYSIS")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

# Get credentials from vault
creds_ref = db.collection('dhan_credentials').document(user_id)
creds_doc = creds_ref.get()

if not creds_doc.exists:
    print("\n[ERROR] No credentials found")
    sys.exit(1)

creds_data = creds_doc.to_dict()
credentials = creds_data.get('credentials', {})
client_id = credentials.get('client_id')
access_token = credentials.get('access_token')

if not client_id or not access_token:
    print("\n[ERROR] Incomplete credentials")
    sys.exit(1)

print(f"\n[OK] Using DhanHQ Client ID: {client_id}")

# Create DhanHQ client
dhan = dhanhq(client_id, access_token)

# Crude Oil security ID
crude_oil_id = "11547"
exchange = "MCX"

print("\n" + "=" * 80)
print("CRUDE OIL LIVE MARKET DATA")
print("=" * 80)

try:
    # Get quote data
    securities = {exchange: [int(crude_oil_id)]}
    quote_response = dhan.quote_data(securities=securities)
    
    if quote_response and 'data' in quote_response:
        data = quote_response['data']
        print(f"\nSymbol: CRUDEOIL")
        print(f"Security ID: {crude_oil_id}")
        print(f"Exchange: {exchange}")
        print(f"\nMarket Data:")
        
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")
    else:
        print(f"\n[WARNING] No quote data returned")
        print(f"Response: {quote_response}")
        
except Exception as e:
    print(f"\n[ERROR] Failed to fetch quote: {e}")

# Check for positions
print("\n" + "=" * 80)
print("CRUDE OIL POSITIONS")
print("=" * 80)

try:
    positions = dhan.get_positions()
    
    crude_positions = []
    if positions and 'data' in positions:
        all_positions = positions['data']
        if all_positions:
            for pos in all_positions:
                # Check if this is a crude oil position
                symbol = pos.get('tradingSymbol', '')
                if 'CRUDE' in symbol.upper():
                    crude_positions.append(pos)
    
    if crude_positions:
        print(f"\n[FOUND] {len(crude_positions)} crude oil position(s):")
        for i, pos in enumerate(crude_positions, 1):
            print(f"\n  Position {i}:")
            print(f"    Symbol: {pos.get('tradingSymbol', 'N/A')}")
            print(f"    Quantity: {pos.get('netQty', 0)}")
            print(f"    Buy Avg: {pos.get('buyAvg', 0)}")
            print(f"    LTP: {pos.get('ltp', 0)}")
            print(f"    P&L: {pos.get('realizedProfit', 0)}")
    else:
        print("\n[NONE] No crude oil positions found")
        
except Exception as e:
    print(f"\n[ERROR] Failed to fetch positions: {e}")

# Check for orders
print("\n" + "=" * 80)
print("CRUDE OIL ORDERS (TODAY)")
print("=" * 80)

try:
    orders = dhan.get_order_list()
    
    crude_orders = []
    if orders and 'data' in orders:
        all_orders = orders['data']
        if all_orders:
            for order in all_orders:
                symbol = order.get('tradingSymbol', '')
                if 'CRUDE' in symbol.upper():
                    crude_orders.append(order)
    
    if crude_orders:
        print(f"\n[FOUND] {len(crude_orders)} crude oil order(s):")
        for i, order in enumerate(crude_orders, 1):
            print(f"\n  Order {i}:")
            print(f"    Symbol: {order.get('tradingSymbol', 'N/A')}")
            print(f"    Type: {order.get('transactionType', 'N/A')}")
            print(f"    Quantity: {order.get('quantity', 0)}")
            print(f"    Price: {order.get('price', 0)}")
            print(f"    Status: {order.get('orderStatus', 'N/A')}")
            print(f"    Time: {order.get('createTime', 'N/A')}")
    else:
        print("\n[NONE] No crude oil orders today")
        
except Exception as e:
    print(f"\n[ERROR] Failed to fetch orders: {e}")

# Check Firestore for signals
print("\n" + "=" * 80)
print("AI TRADING SIGNALS (CRUDE OIL)")
print("=" * 80)

signals_ref = db.collection('users').document(user_id).collection('signals')
signals = list(signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

crude_signals = []
for signal in signals:
    signal_data = signal.to_dict()
    symbol = signal_data.get('symbol', '')
    if 'CRUDE' in symbol.upper():
        crude_signals.append(signal_data)

if crude_signals:
    print(f"\n[FOUND] {len(crude_signals)} crude oil signal(s):")
    for i, sig in enumerate(crude_signals, 1):
        print(f"\n  Signal {i}:")
        print(f"    Symbol: {sig.get('symbol', 'N/A')}")
        print(f"    Action: {sig.get('action', 'N/A')}")
        print(f"    Confidence: {sig.get('confidence', 0)}")
        print(f"    Time: {sig.get('timestamp', 'N/A')}")
else:
    print("\n[NONE] No crude oil signals found in Firestore")

print("\n" + "=" * 80)
print("\nNote: To generate trading signals and execute trades:")
print("1. Click 'Start Trading' in the UI")
print("2. System will scan crude oil along with other commodities")
print("3. Trades will execute automatically when signals are generated")
print("=" * 80)
