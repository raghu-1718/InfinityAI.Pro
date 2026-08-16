"""Complete verification of trading system status after Start Trading."""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import json

# Initialize Firebase
try:
    app = firebase_admin.get_app()
except ValueError:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'project-841b7f97-5ee3-4fbe-920',
    })

db = firestore.client()

print("=" * 80)
print("COMPLETE TRADING SYSTEM VERIFICATION")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

# Check user document
print("1. USER TRADING STATUS")
print("-" * 80)
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    print(f"Trading Active: {user_data.get('tradingActive', False)}")
    print(f"Auto Trading: {user_data.get('settings', {}).get('autoTrading', False)}")
    print(f"Last Login: {user_data.get('lastLoginAt', 'N/A')}")
else:
    print("User document not found")

# Check trading logs
print("\n2. TRADING LOGS (Recent)")
print("-" * 80)
logs_ref = db.collection('users').document(user_id).collection('tradingLogs')
recent_logs = list(logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream())

if recent_logs:
    print(f"Found {len(recent_logs)} recent log(s):\n")
    for i, log in enumerate(recent_logs, 1):
        log_data = log.to_dict()
        print(f"  Log {i}:")
        print(f"    Action: {log_data.get('action', 'N/A')}")
        print(f"    Status: {log_data.get('status', 'N/A')}")
        print(f"    Time: {log_data.get('timestamp', 'N/A')}")
        print(f"    Message: {log_data.get('message', 'N/A')}")
        print()
else:
    print("No trading logs found")

# Check signals
print("3. TRADING SIGNALS (Recent)")
print("-" * 80)
signals_ref = db.collection('users').document(user_id).collection('signals')
recent_signals = list(signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

if recent_signals:
    print(f"Found {len(recent_signals)} recent signal(s):\n")
    
    equity_signals = []
    commodity_signals = []
    crude_signals = []
    
    for signal in recent_signals:
        sig_data = signal.to_dict()
        symbol = sig_data.get('symbol', '')
        
        if 'CRUDE' in symbol.upper():
            crude_signals.append(sig_data)
            commodity_signals.append(sig_data)
        elif any(x in symbol.upper() for x in ['GOLD', 'SILVER', 'NATURALGAS']):
            commodity_signals.append(sig_data)
        else:
            equity_signals.append(sig_data)
    
    print(f"  Equity Signals: {len(equity_signals)}")
    print(f"  Commodity Signals: {len(commodity_signals)}")
    print(f"  Crude Oil Signals: {len(crude_signals)}")
    
    if crude_signals:
        print("\n  CRUDE OIL SIGNALS DETAIL:")
        for i, sig in enumerate(crude_signals, 1):
            print(f"\n    Signal {i}:")
            print(f"      Symbol: {sig.get('symbol', 'N/A')}")
            print(f"      Action: {sig.get('action', 'N/A')}")
            print(f"      Confidence: {sig.get('confidence', 0)}")
            print(f"      Price: {sig.get('price', 'N/A')}")
            print(f"      Time: {sig.get('timestamp', 'N/A')}")
else:
    print("No signals generated yet")

# Check positions
print("\n4. POSITIONS")
print("-" * 80)
positions_ref = db.collection('users').document(user_id).collection('positions')
positions = list(positions_ref.stream())

if positions:
    print(f"Found {len(positions)} position(s):\n")
    
    crude_positions = []
    for pos in positions:
        pos_data = pos.to_dict()
        symbol = pos_data.get('symbol', '')
        
        if 'CRUDE' in symbol.upper():
            crude_positions.append(pos_data)
        
        print(f"  Symbol: {symbol}")
        print(f"  Quantity: {pos_data.get('quantity', 0)}")
        print(f"  Entry Price: {pos_data.get('entryPrice', 0)}")
        print(f"  Status: {pos_data.get('status', 'N/A')}")
        print()
    
    if crude_positions:
        print(f"\n  CRUDE OIL POSITIONS: {len(crude_positions)}")
else:
    print("No positions found")

# Check orders
print("\n5. ORDERS (Today)")
print("-" * 80)
orders_ref = db.collection('users').document(user_id).collection('orders')
orders = list(orders_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

if orders:
    print(f"Found {len(orders)} recent order(s):\n")
    
    crude_orders = []
    for order in orders:
        order_data = order.to_dict()
        symbol = order_data.get('symbol', '')
        
        if 'CRUDE' in symbol.upper():
            crude_orders.append(order_data)
        
        print(f"  Symbol: {symbol}")
        print(f"  Type: {order_data.get('orderType', 'N/A')}")
        print(f"  Side: {order_data.get('side', 'N/A')}")
        print(f"  Quantity: {order_data.get('quantity', 0)}")
        print(f"  Status: {order_data.get('status', 'N/A')}")
        print(f"  Time: {order_data.get('timestamp', 'N/A')}")
        print()
    
    if crude_orders:
        print(f"\n  CRUDE OIL ORDERS: {len(crude_orders)}")
else:
    print("No orders found")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Trading Started: {'YES' if recent_logs else 'PENDING'}")
print(f"Signals Generated: {'YES' if recent_signals else 'NO'}")
print(f"Crude Oil Signals: {'YES' if recent_signals and any('CRUDE' in s.to_dict().get('symbol', '') for s in recent_signals) else 'NO'}")
print(f"Active Positions: {len(positions) if positions else 0}")
print(f"Orders Placed: {len(orders) if orders else 0}")
print("=" * 80)
