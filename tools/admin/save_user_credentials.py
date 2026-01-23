"""
Save User Credentials to Firestore
Encrypts and stores Dhan credentials for user B79BqvTlaTZltC8uGO3jLxJBBt93
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'engine-c', 'src'))

from user_credentials_enhanced import get_credentials_manager

async def save_credentials():
    """Save user credentials to Firestore"""
    
    user_id = "B79BqvTlaTZltC8uGO3jLxJBBt93"
    client_id = "1101302170"
    access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjkxNTc1NjksImlhdCI6MTc2OTA3MTE2OSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtMjI4NTU3NzE2ODU4LnVzLWNlbnRyYWwxLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0._F2xv6YEcWtmqY_J9Fc6z_J-tivo-79Ixe9L9yhFKANgSq9g9m9kNJfitjCkelTNsiXPDXU_0BTm356x0cxqnQ"
    api_key = "b76a41e2"
    api_secret = "3b27c08e-797c-40e4-8e80-0498ea853236"
    
    print(f"💾 Saving credentials for user: {user_id}")
    print(f"   Client ID: {client_id}")
    print(f"   Access Token: {access_token[:50]}...")
    print(f"   API Key: {api_key}")
    print(f"   API Secret: {api_secret[:20]}...")
    
    try:
        manager = get_credentials_manager()
        result = await manager.save_user_credentials(
            user_id=user_id,
            client_id=client_id,
            access_token=access_token,
            api_key=api_key,
            api_secret=api_secret
        )
        
        print(f"\n✅ SUCCESS: {result['message']}")
        print(f"   Status: {result['status']}")
        print(f"   User ID: {result['user_id']}")
        print(f"   Client ID: {result['client_id']}")
        
        # Verify retrieval
        print(f"\n🔍 Verifying credential retrieval...")
        creds = await manager.get_user_credentials(user_id)
        
        if creds:
            print(f"✅ Credentials retrieved successfully")
            print(f"   Connection Status: {creds.get('connection_status')}")
            print(f"   Has Client ID: {bool(creds.get('credentials', {}).get('client_id'))}")
            print(f"   Has Access Token: {bool(creds.get('credentials', {}).get('access_token'))}")
            print(f"   Has API Key: {bool(creds.get('credentials', {}).get('api_key'))}")
            print(f"   Has API Secret: {bool(creds.get('credentials', {}).get('api_secret'))}")
        else:
            print(f"❌ Failed to retrieve credentials")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(save_credentials())
    sys.exit(0 if success else 1)
