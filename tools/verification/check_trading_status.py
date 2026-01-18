"""Quick script to check trading status in Firestore."""
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
print("TRADING STATUS CHECK - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 80)

# Check user document
user_id = "B79BqvTlaTZltC8uGO3jLxJBBt93"
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if user_doc.exists:
    user_data = user_doc.to_dict()
    print(f"\nUSER CREDENTIALS STATUS:")
    print(f"   User ID: {user_id}")
    
    if 'dhanCredentials' in user_data:
        dhan_creds = user_data['dhanCredentials']
        print(f"   [OK] DhanHQ Credentials Present (Legacy Format)")
        print(f"   Client ID: {dhan_creds.get('clientId', 'N/A')}")
        print(f"   Last Updated: {dhan_creds.get('lastUpdated', 'N/A')}")
        if 'encryptedAccessToken' in dhan_creds:
            print(f"   [OK] Encrypted Access Token: Present ({len(dhan_creds['encryptedAccessToken'])} chars)")
    elif 'dhanClientId' in user_data:
        print(f"   [OK] DhanHQ Credentials Present (New Format)")
        print(f"   Client ID: {user_data.get('dhanClientId', 'N/A')}")
        print(f"   Status: {user_data.get('dhanConnected', False)}")
        print(f"   Mode: {user_data.get('tradingMode', 'live')}")
    else:
        print(f"   [MISSING] No DhanHQ credentials found")
    
    if 'tradingEnabled' in user_data:
        print(f"\nTRADING STATE:")
        print(f"   Trading Enabled: {user_data.get('tradingEnabled', False)}")
        print(f"   Last Trading Action: {user_data.get('lastTradingAction', 'N/A')}")
else:
    print(f"[ERROR] User document not found for {user_id}")

# Check for positions
print(f"\nPOSITIONS:")
positions_ref = db.collection('users').document(user_id).collection('positions')
positions = list(positions_ref.limit(10).stream())
if positions:
    print(f"   Found {len(positions)} positions:")
    for pos in positions:
        pos_data = pos.to_dict()
        print(f"   - {pos.id}: {json.dumps(pos_data, indent=6)}")
else:
    print("   [EMPTY] No positions found")

# Check for orders
print(f"\nORDERS:")
orders_ref = db.collection('users').document(user_id).collection('orders')
orders = list(orders_ref.limit(10).stream())
if orders:
    print(f"   Found {len(orders)} orders:")
    for order in orders:
        order_data = order.to_dict()
        print(f"   - {order.id}: {json.dumps(order_data, indent=6)}")
else:
    print("   [EMPTY] No orders found")

# Check for trading logs/activity
print(f"\nTRADING LOGS (Last 5):")
logs_ref = db.collection('users').document(user_id).collection('tradingLogs')
logs = list(logs_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(5).stream())
if logs:
    print(f"   Found {len(logs)} recent logs:")
    for log in logs:
        log_data = log.to_dict()
        print(f"   - {log.id}: {json.dumps(log_data, indent=6, default=str)}")
else:
    print("   [EMPTY] No trading logs found")

# Check system-wide trading state
print(f"\nSYSTEM-WIDE STATE:")
system_ref = db.collection('system').document('tradingState')
system_doc = system_ref.get()
if system_doc.exists:
    system_data = system_doc.to_dict()
    print(f"   {json.dumps(system_data, indent=3, default=str)}")
else:
    print("   [EMPTY] No system trading state found")

print("\n" + "=" * 80)
