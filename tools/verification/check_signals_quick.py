#!/usr/bin/env python3
"""
Quick verification script to check if signals are being stored to Firestore
"""
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Get user ID from environment or default
USER_ID = os.getenv('USER_ID', 'B79BqvTlaTZltC8uGO3jLxJBBt93')

def check_signals():
    """Check for signals in Firestore"""
    print(f"\nChecking signals for user {USER_ID}...")
    print("=" * 60)
    
    # Get signals from last 30 minutes
    thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
    
    signals_ref = db.collection('users').document(USER_ID).collection('signals')
    signals = signals_ref.order_by('stored_at', direction=firestore.Query.DESCENDING).limit(20).stream()
    
    signal_count = 0
    crude_count = 0
    equity_count = 0
    
    print("\nRecent Signals:")
    print("-" * 60)
    
    for signal in signals:
        signal_data = signal.to_dict()
        signal_count += 1
        
        symbol = signal_data.get('symbol', 'UNKNOWN')
        signal_type = signal_data.get('signal', 'UNKNOWN')
        confidence = signal_data.get('confidence', 0)
        stored_at = signal_data.get('stored_at', 'Unknown')
        
        # Count crude oil vs equity
        if symbol.upper() in ['CRUDEOIL', 'GOLD', 'SILVER']:
            crude_count += 1
        else:
            equity_count += 1
        
        print(f"{signal_count}. {symbol:12} | {signal_type:4} | Conf: {confidence}% | Stored: {stored_at}")
    
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Total Signals: {signal_count}")
    print(f"  Commodity Signals: {crude_count}")
    print(f"  Equity Signals: {equity_count}")
    
    if signal_count > 0:
        print(f"\nSUCCESS! Signals are being stored to Firestore!")
    else:
        print(f"\nNo signals found yet. Engine B may need a few minutes to generate first batch.")
    
    return signal_count

if __name__ == '__main__':
    try:
        check_signals()
    except Exception as e:
        print(f"\nError checking signals: {e}")
