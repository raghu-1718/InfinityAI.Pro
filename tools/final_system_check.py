"""Final complete system status check."""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json

import os

# Initialize Firebase
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "gen-lang-client-0779271931")
    firebase_admin.initialize_app(cred, {
        'projectId': project_id,
    })

db = firestore.client()

print("=" * 80)
print("COMPLETE SYSTEM STATUS - FINAL VERIFICATION")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

# 1. User settings
print("1. USER CONFIGURATION")
print("-" * 80)
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    settings = user_data.get('settings', {})
    
    print(f"Auto Trading (Backend): {settings.get('autoTrading', False)}")
    print(f"Trading Active (Backend): {user_data.get('tradingActive', False)}")
    print(f"Dhan Connected: {user_data.get('dhanConnected', False)}")
    print(f"Risk Level: {settings.get('riskLevel', 'N/A')}")
    print(f"Max Position Size: ₹{settings.get('maxPositionSize', 0)}")
    print(f"Stop Loss: {settings.get('stopLossPercent', 0)}%")

#  2. Recent audit trail
print("\n2. LIVE AUDIT TRAIL (Last 10 entries)")
print("-" * 80)
logs_ref = db.collection('users').document(user_id).collection('tradingLogs')  
recent_logs = list(logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

if recent_logs:
    for i, log in enumerate(recent_logs, 1):
        log_data = log.to_dict()
        action = log_data.get('action', 'N/A')
        status = log_data.get('status', None)
        timestamp = log_data.get('timestamp', 'N/A')
        
        if action == 'TRADING_STARTED':
            print(f"  {i}. SESSION START @ {timestamp}")
            if 'source' in log_data:
                print(f"     Source: {log_data['source']}")
        elif action == 'TRADING_STOPPED':
            print(f"  {i}. SESSION STOP @ {timestamp}")
            if 'reason' in log_data:
                print(f"     Reason: {log_data.get('reason', 'N/A')}")
        else:
            print(f"  {i}. {action} @ {timestamp}")
            if status:
                print(f"     Status: {status}")
else:
    print("  No audit trail entries")

# 3. Signals
print("\n3. TRADING SIGNALS")
print("-" * 80)
signals_ref = db.collection('users').document(user_id).collection('signals')
all_signals = list(signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(20).stream())

if all_signals:
    equity_signals = []
    commodity_signals = []
    crude_signals = []
    nifty_signals = []
    
    for signal in all_signals:
        sig_data = signal.to_dict()
        symbol = sig_data.get('symbol', '').upper()
        
        if 'CRUDE' in symbol:
            crude_signals.append(sig_data)
            commodity_signals.append(sig_data)
        elif 'NIFTY' in symbol:
            nifty_signals.append(sig_data)
            equity_signals.append(sig_data)
        elif any(x in symbol for x in ['GOLD', 'SILVER', 'NATURALGAS']):
            commodity_signals.append(sig_data)
        else:
            equity_signals.append(sig_data)
    
    print(f"Total Signals: {len(all_signals)}")
    print(f"  - Equity Signals: {len(equity_signals)}")
    print(f"  - NIFTY Signals: {len(nifty_signals)}")
    print(f"  - Commodity Signals: {len(commodity_signals)}")
    print(f"  - Crude Oil Signals: {len(crude_signals)}")
    
    if crude_signals:
        print("\n  CRUDE OIL SIGNALS:")
        for sig in crude_signals[:3]:
            print(f"    - {sig.get('symbol')}: {sig.get('action')} @ {sig.get('timestamp')}")
    
    if nifty_signals:
        print("\n  NIFTY SIGNALS:")
        for sig in nifty_signals[:3]:
            print(f"    - {sig.get('symbol')}: {sig.get('action')} @ {sig.get('timestamp')}")
else:
    print("  No signals found")

# 4. Positions 
print("\n4. ACTIVE POSITIONS")
print("-" * 80)
positions_ref = db.collection('users').document(user_id).collection('positions')
positions = list(positions_ref.stream())

if positions:
    print(f"Total Positions: {len(positions)}")
    for pos in positions:
        pos_data = pos.to_dict()
        symbol = pos_data.get('symbol', 'N/A')
        qty = pos_data.get('quantity', 0)
        entry = pos_data.get('entryPrice', 0)
        print(f"  - {symbol}: {qty} @ ₹{entry}")
else:
    print("  No active positions")

# 5. Orders
print("\n5. ORDERS (Recent)")
print("-" * 80)
orders_ref = db.collection('users').document(user_id).collection('orders')
orders = list(orders_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

if orders:
    print(f"Total Recent Orders: {len(orders)}")
    for order in orders:
        order_data = order.to_dict()
        symbol = order_data.get('symbol', 'N/A')
        side = order_data.get('side', 'N/A')
        status = order_data.get('status', 'N/A')
        timestamp = order_data.get('timestamp', 'N/A')
        print(f"  - {symbol}: {side} - {status} @ {timestamp}")
else:
    print("  No recent orders")

print("\n" + "=" * 80)
print("FINAL STATUS SUMMARY")
print("=" * 80)
user_data = user_doc.to_dict() if 'user_doc' in locals() and user_doc and user_doc.exists else {}
settings = user_data.get('settings', {})
print(f"System Active: {user_data.get('tradingActive', False)}")
print(f"Auto-Trading Enabled: {settings.get('autoTrading', False)}")
all_sig = all_signals if 'all_signals' in locals() else []
crude_sig = crude_signals if 'crude_signals' in locals() else []
nifty_sig = nifty_signals if 'nifty_signals' in locals() else []
pos = positions if 'positions' in locals() else []
ord_list = orders if 'orders' in locals() else []

print(f"Signal Generation: {'ACTIVE' if all_sig else 'NONE'}")
print(f"Crude Oil Coverage: {'YES' if crude_sig else 'NO'}")
print(f"NIFTY Coverage: {'YES' if nifty_sig else 'NO'}")
print(f"Active Trading: {'YES' if pos or ord_list else 'NO'}")
print("=" * 80)
