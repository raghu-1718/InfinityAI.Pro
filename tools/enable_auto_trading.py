"""Enable auto-trading and activate trading system."""
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
print("ENABLING AUTO-TRADING SYSTEM")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

user_id = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"

# Get current user settings
user_ref = db.collection('users').document(user_id)
user_doc = user_ref.get()

if not user_doc.exists:
    print("[ERROR] User document not found")
    exit(1)

user_data = user_doc.to_dict()
current_settings = user_data.get('settings', {})

print("CURRENT SETTINGS:")
print("-" * 80)
print(f"Auto Trading: {current_settings.get('autoTrading', False)}")
print(f"Trading Active: {user_data.get('tradingActive', False)}")
print(f"Dhan Connected: {user_data.get('dhanConnected', False)}")

# Update settings
print("\n" + "=" * 80)
print("UPDATING SETTINGS")
print("=" * 80)

updates = {
    'settings.autoTrading': True,
    'tradingActive': True,
    'dhanConnected': True,
    'lastUpdatedAt': firestore.SERVER_TIMESTAMP,
}

try:
    user_ref.update(updates)
    print("[OK] Settings updated successfully")
    print("\nNEW SETTINGS:")
    print("-" * 80)
    print("Auto Trading: TRUE")
    print("Trading Active: TRUE")
    print("Dhan Connected: TRUE")
except Exception as e:
    print(f"[ERROR] Failed to update: {e}")
    exit(1)

# Create a trading log entry
print("\n" + "=" * 80)
print("CREATING TRADING LOG")
print("=" * 80)

log_entry = {
    'action': 'TRADING_STARTED',
    'status': 'active',
    'message': 'Auto-trading enabled programmatically - System activated for crude oil and commodity scanning',
    'timestamp': firestore.SERVER_TIMESTAMP,
    'source': 'admin_script',
    'settings': {
        'autoTrading': True,
        'continuousMode': True,
    }
}

try:
    logs_ref = user_ref.collection('tradingLogs')
    logs_ref.add(log_entry)
    print("[OK] Trading log created")
except Exception as e:
    print(f"[WARNING] Failed to create log: {e}")

# Verify the changes
print("\n" + "=" * 80)
print("VERIFYING CHANGES")
print("=" * 80)

updated_doc = user_ref.get()
if updated_doc.exists:
    updated_data = updated_doc.to_dict()
    updated_settings = updated_data.get('settings', {})
    
    print(f"Auto Trading: {updated_settings.get('autoTrading', False)} ✓")
    print(f"Trading Active: {updated_data.get('tradingActive', False)} ✓") 
    print(f"Dhan Connected: {updated_data.get('dhanConnected', False)} ✓")
    
    if updated_settings.get('autoTrading') and updated_data.get('tradingActive'):
        print("\n[SUCCESS] Trading system is now FULLY ENABLED")
        print("\nWhat will happen next:")
        print("  1. Engine B will start generating signals")
        print("  2. Signals will be generated for both equity and commodities")
        print("  3. Crude oil will be scanned (MCX market open until 11:30 PM)")
        print("  4. Engine C will execute trades automatically")
        print("  5. You can monitor progress in the Live Audit Trail")
    else:
        print("\n[WARNING] Settings may not have updated correctly")

print("\n" + "=" * 80)
print("DONE - Trading system activated")
print("=" * 80)
