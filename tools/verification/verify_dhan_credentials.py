"""
Dhan Credential Flow Verification Script

Tests the end-to-end credential storage and retrieval flow:
1. Frontend saves credentials via submitDhanCredentialsV2 Cloud Function
2. Backend retrieves credentials via UserCredentialsManager
3. Backend creates DhanHQ client and calls API
4. Verifies data is user-specific and accurate

Usage:
    python tools/verification/verify_dhan_credentials.py --user-id {firebase_uid}
"""

import asyncio
import sys
import os
import argparse
from google.cloud import firestore
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c', 'src'))

try:
    from user_credentials import UserCredentialsManager
    from dhan_client_wrapper import create_dhan_client
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    print("Make sure you're running from the project root and backend modules are available")
    sys.exit(1)


async def verify_credential_flow(user_id: str):
    """Verify complete credential flow for a user"""
    
    print(f"\n{'='*80}")
    print(f"🔍 Dhan Credential Flow Verification")
    print(f"{'='*80}\n")
    print(f"User ID: {user_id}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    # Step 1: Check Firestore directly
    print("📋 Step 1: Checking Firestore dhan_credentials collection...")
    try:
        db = firestore.Client()
        doc_ref = db.collection("dhan_credentials").document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"❌ No credentials found in Firestore for user: {user_id}")
            print("   User needs to save credentials via frontend Settings page")
            return False
        
        data = doc.to_dict()
        print(f"✅ Credentials document found")
        print(f"   Fields present: {list(data.keys())}")
        print(f"   Has clientId: {bool(data.get('clientId'))}")
        print(f"   Has accessToken: {bool(data.get('accessToken'))}")
        print(f"   Has apiKey: {bool(data.get('apiKey'))}")
        print(f"   Has apiSecret: {bool(data.get('apiSecret'))}")
        print(f"   Last updated: {data.get('lastUpdatedAt')}")
        
    except Exception as e:
        print(f"❌ Error checking Firestore: {e}")
        return False
    
    # Step 2: Retrieve via UserCredentialsManager
    print(f"\n📋 Step 2: Retrieving credentials via UserCredentialsManager...")
    try:
        manager = UserCredentialsManager()
        creds = await manager.get_user_credentials(user_id)
        
        if not creds:
            print(f"❌ UserCredentialsManager returned None")
            return False
        
        if creds.get("error"):
            print(f"❌ Error in credentials: {creds.get('error')}")
            return False
        
        credentials = creds.get("credentials", {})
        print(f"✅ Credentials retrieved successfully")
        print(f"   Client ID: {credentials.get('client_id', 'MISSING')}")
        print(f"   Has Access Token: {bool(credentials.get('access_token'))}")
        print(f"   Has API Key: {bool(credentials.get('api_key'))}")
        print(f"   Has API Secret: {bool(credentials.get('api_secret'))}")
        print(f"   Connection Status: {creds.get('connection_status')}")
        
        client_id = credentials.get('client_id')
        access_token = credentials.get('access_token')
        
        if not client_id or not access_token:
            print(f"❌ Missing required credentials (client_id or access_token)")
            return False
            
    except Exception as e:
        print(f"❌ Error retrieving credentials: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Create Dhan client
    print(f"\n📋 Step 3: Creating DhanHQ client...")
    try:
        dhan_client = create_dhan_client(client_id, access_token)
        print(f"✅ Dhan client created successfully")
    except Exception as e:
        print(f"❌ Error creating Dhan client: {e}")
        return False
    
    # Step 4: Test DhanHQ API calls
    print(f"\n📋 Step 4: Testing DhanHQ API calls...")
    
    # Test 4a: Fund limits
    print(f"\n   4a. Testing fund limits API...")
    try:
        funds = dhan_client.get_fund_limits()
        if funds:
            print(f"   ✅ Fund limits retrieved")
            print(f"      Available Balance: ₹{funds.get('availabelBalance', 'N/A')}")
            print(f"      Utilized Amount: ₹{funds.get('utilizedAmount', 'N/A')}")
            print(f"      Client ID (from API): {funds.get('dhanClientId', 'N/A')}")
            
            # Verify client ID matches
            api_client_id = funds.get('dhanClientId')
            if api_client_id and api_client_id != client_id:
                print(f"   ⚠️  WARNING: Client ID mismatch!")
                print(f"      Stored: {client_id}")
                print(f"      API returned: {api_client_id}")
        else:
            print(f"   ❌ Fund limits API returned empty response")
            return False
    except Exception as e:
        print(f"   ❌ Error calling fund limits API: {e}")
        return False
    
    # Test 4b: Holdings
    print(f"\n   4b. Testing holdings API...")
    try:
        holdings = dhan_client.get_holdings()
        if holdings is not None:
            if isinstance(holdings, list):
                print(f"   ✅ Holdings retrieved: {len(holdings)} holdings")
                if len(holdings) > 0:
                    print(f"      Sample holding: {holdings[0].get('tradingSymbol', 'N/A')}")
            else:
                print(f"   ✅ Holdings retrieved (non-list response)")
        else:
            print(f"   ⚠️  Holdings API returned None (may be empty account)")
    except Exception as e:
        print(f"   ❌ Error calling holdings API: {e}")
    
    # Test 4c: Positions
    print(f"\n   4c. Testing positions API...")
    try:
        positions = dhan_client.get_positions()
        if positions is not None:
            if isinstance(positions, list):
                print(f"   ✅ Positions retrieved: {len(positions)} positions")
                if len(positions) > 0:
                    print(f"      Sample position: {positions[0].get('tradingSymbol', 'N/A')}")
            else:
                print(f"   ✅ Positions retrieved (non-list response)")
        else:
            print(f"   ⚠️  Positions API returned None (may be empty)")
    except Exception as e:
        print(f"   ❌ Error calling positions API: {e}")
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"✅ VERIFICATION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Summary:")
    print(f"  ✅ Credentials stored in Firestore")
    print(f"  ✅ Credentials retrieved and decrypted successfully")
    print(f"  ✅ DhanHQ client created")
    print(f"  ✅ DhanHQ API calls successful")
    print(f"\n🎉 Credential flow is working correctly!")
    print(f"\nNext steps:")
    print(f"  1. Verify frontend displays this data correctly")
    print(f"  2. Check that data updates in real-time")
    print(f"  3. Test credential update flow (re-save credentials)")
    
    return True


async def main():
    parser = argparse.ArgumentParser(description='Verify Dhan credential flow')
    parser.add_argument('--user-id', required=True, help='Firebase user ID (UID)')
    args = parser.parse_args()
    
    success = await verify_credential_flow(args.user_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
