"""
7 PM VERIFICATION - Trading System Signal Generation Check
Run this at 7:00 PM to verify system has generated signals
"""
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
        'projectId': 'galvanic-pulsar-482815-h0',
    })

db = firestore.client()

print("=" * 80)
print("7 PM VERIFICATION - TRADING SYSTEM STATUS")
print("=" * 80)
print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p IST')}\n")

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

# Calculate time since activation (5:40 PM)
activation_time = datetime(2026, 1, 14, 17, 40, 0)
current_time = datetime.now()
time_elapsed = current_time - activation_time
minutes_elapsed = int(time_elapsed.total_seconds() / 60)

print(f"System Activated: 5:40 PM IST")
print(f"Time Elapsed: {minutes_elapsed} minutes ({time_elapsed.seconds // 3600}h {(time_elapsed.seconds // 60) % 60}m)")
print("\n" + "=" * 80)

# 1. Check if system still active
print("\n1. SYSTEM STATUS")
print("-" * 80)
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    settings = user_data.get('settings', {})
    
    is_active = user_data.get('tradingActive', False)
    auto_trading = settings.get('autoTrading', False)
    
    print(f"Trading Active: {is_active} {'✓' if is_active else '✗'}")
    print(f"Auto Trading: {auto_trading} {'✓' if auto_trading else '✗'}")
    
    if not is_active or not auto_trading:
        print("\n⚠️ WARNING: System appears to have been stopped!")
        print("   Check if you clicked STOP button")
else:
    print("✗ User document not found")

# 2. Signal Generation Analysis
print("\n2. SIGNAL GENERATION STATUS")
print("-" * 80)

signals_ref = db.collection('users').document(user_id).collection('signals')

# Get all signals since activation
all_signals = list(signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream())

if all_signals:
    print(f"✓ SIGNALS FOUND: {len(all_signals)} total signals\n")
    
    # Categorize signals
    equity_signals = []
    commodity_signals = []
    crude_signals = []
    nifty_signals = []
    recent_signals = []  # Last 1 hour
    
    one_hour_ago = datetime.now(timezone.utc).timestamp() - 3600
    
    for signal in all_signals:
        sig_data = signal.to_dict()
        symbol = sig_data.get('symbol', '').upper()
        sig_time = sig_data.get('timestamp')
        
        # Check if recent (last 1 hour)
        if sig_time:
            try:
                if hasattr(sig_time, 'timestamp'):
                    sig_timestamp = sig_time.timestamp()
                else:
                    sig_timestamp = sig_time
                    
                if sig_timestamp > one_hour_ago:
                    recent_signals.append(sig_data)
            except:
                pass
        
        # Categorize
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
    
    print(f"  Total Signals: {len(all_signals)}")
    print(f"  Recent (Last Hour): {len(recent_signals)}")
    print(f"  Equity Signals: {len(equity_signals)}")
    print(f"  Commodity Signals: {len(commodity_signals)}")
    print(f"  NIFTY Signals: {len(nifty_signals)}")
    print(f"  CRUDE OIL Signals: {len(crude_signals)}")
    
    if recent_signals:
        print(f"\n  RECENT SIGNALS (Last Hour):")
        for i, sig in enumerate(recent_signals[:5], 1):
            print(f"    {i}. {sig.get('symbol', 'N/A')}: {sig.get('action', 'N/A')} "
                  f"(Confidence: {sig.get('confidence', 0):.2f})")
    
    if crude_signals:
        print(f"\n  🎯 CRUDE OIL SIGNALS FOUND:")
        for i, sig in enumerate(crude_signals, 1):
            print(f"    {i}. {sig.get('symbol', 'N/A')}: {sig.get('action', 'N/A')} "
                  f"@ {sig.get('timestamp', 'N/A')}")
            print(f"       Confidence: {sig.get('confidence', 0):.2f}, "
                  f"Price: {sig.get('price', 'N/A')}")
else:
    print("✗ NO SIGNALS GENERATED YET")
    print("\n  Possible reasons:")
    print("  1. Market conditions don't meet entry criteria")
    print("  2. System still building confidence scores")
    print("  3. ML models haven't detected high-probability setups")
    print("  4. Check if system was stopped (see Status above)")

# 3. Trading Activity
print("\n3. TRADING ACTIVITY")
print("-" * 80)

# Positions
positions_ref = db.collection('users').document(user_id).collection('positions')
positions = list(positions_ref.stream())

if positions:
    print(f"✓ POSITIONS: {len(positions)} active")
    for pos in positions:
        pos_data = pos.to_dict()
        print(f"  - {pos_data.get('symbol', 'N/A')}: {pos_data.get('quantity', 0)} "
              f"@ Rs{pos_data.get('entryPrice', 0)}")
else:
    print("✗ No positions")

# Orders
orders_ref = db.collection('users').document(user_id).collection('orders')
orders = list(orders_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())

if orders:
    print(f"\n✓ ORDERS: {len(orders)} recent")
    for order in orders[:5]:
        order_data = order.to_dict()
        print(f"  - {order_data.get('symbol', 'N/A')}: {order_data.get('side', 'N/A')} "
              f"{order_data.get('quantity', 0)} - {order_data.get('status', 'N/A')}")
else:
    print("\n✗ No orders")

# 4. System Health
print("\n4. ENGINE HEALTH")
print("-" * 80)

logs_ref = db.collection('users').document(user_id).collection('tradingLogs')
recent_logs = list(logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream())

if recent_logs:
    print(f"✓ System active - {len(recent_logs)} recent log entries")
    last_log = recent_logs[0].to_dict()
    print(f"  Last activity: {last_log.get('action', 'N/A')} @ {last_log.get('timestamp', 'N/A')}")
else:
    print("⚠️ No recent activity logs")

# 5. Market Status
print("\n5. MCX MARKET STATUS")
print("-" * 80)

current_hour = datetime.now().hour
if 9 <= current_hour < 23:
    print("✓ MCX Market: OPEN")
    close_time = datetime.now().replace(hour=23, minute=30, second=0)
    time_to_close = close_time - datetime.now()
    hours_left = time_to_close.seconds // 3600
    mins_left = (time_to_close.seconds // 60) % 60
    print(f"  Time until close: {hours_left}h {mins_left}m")
else:
    print("✗ MCX Market: CLOSED")

# FINAL VERDICT
print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if all_signals and len(recent_signals) > 0:
    print("✓ SUCCESS: Signal generation is WORKING")
    print(f"  - {len(recent_signals)} signals in last hour")
    if crude_signals:
        print(f"  - {len(crude_signals)} CRUDE OIL signals detected")
    if positions or orders:
        print(f"  - Trading activity confirmed")
elif all_signals and len(recent_signals) == 0:
    print("⚠️ PARTIAL: Signals exist but none in last hour")
    print("  - System may have generated signals earlier")
    print("  - Current market conditions may not be favorable")
else:
    print("✗ NO SIGNALS: System has not generated any signals")
    print("\n  Next steps:")
    print("  1. Verify system is still active (check Status above)")
    print("  2. Check Live Audit Trail in UI for errors")
    print("  3. Market conditions may simply not be favorable")
    print("  4. System is selective - this is normal if no good setups")

print("\n" + "=" * 80)
print(f"Report generated at: {datetime.now().strftime('%I:%M:%S %p IST')}")
print("=" * 80)
