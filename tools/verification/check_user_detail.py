"""Check the specific Firebase user document with all details."""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
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
print("DETAILED USER CHECK - Firebase UID: znyNtT2lW3MKHqFrVA6E0A2Iv3N2")
print("=" * 80)

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    print(f"\nFull User Document:")
    print(json.dumps(user_data, indent=2, default=str))
    
    # Check subcollections
    print(f"\n\nChecking subcollections...\n")
    
    # Positions
    print("=" * 40)
    print("POSITIONS:")
    positions_ref = db.collection('users').document(user_id).collection('positions')
    positions = list(positions_ref.stream())
    if positions:
        print(f"Found {len(positions)} positions:")
        for pos in positions:
            print(f"\n  Position ID: {pos.id}")
            print(f"  {json.dumps(pos.to_dict(), indent=4, default=str)}")
    else:
        print("  No positions found")
    
    # Orders
    print("\n" + "=" * 40)
    print("ORDERS:")
    orders_ref = db.collection('users').document(user_id).collection('orders')
    orders = list(orders_ref.stream())
    if orders:
        print(f"Found {len(orders)} orders:")
        for order in orders:
            print(f"\n  Order ID: {order.id}")
            print(f"  {json.dumps(order.to_dict(), indent=4, default=str)}")
    else:
        print("  No orders found")
    
    # Trading Logs
    print("\n" + "=" * 40)
    print("TRADING LOGS:")
    logs_ref = db.collection('users').document(user_id).collection('tradingLogs')
    logs = list(logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())
    if logs:
        print(f"Found {len(logs)} trading logs:")
        for log in logs:
            print(f"\n  Log ID: {log.id}")
            print(f"  {json.dumps(log.to_dict(), indent=4, default=str)}")
    else:
        print("  No trading logs found")
    
    # Signals
    print("\n" + "=" * 40)
    print("SIGNALS:")
    signals_ref = db.collection('users').document(user_id).collection('signals')
    signals = list(signals_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).stream())
    if signals:
        print(f"Found {len(signals)} signals:")
        for signal in signals:
            print(f"\n  Signal ID: {signal.id}")
            print(f"  {json.dumps(signal.to_dict(), indent=4, default=str)}")
    else:
        print("  No signals found")
else:
    print(f"ERROR: User document not found")

print("\n" + "=" * 80)
