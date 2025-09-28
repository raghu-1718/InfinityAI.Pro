#!/usr/bin/env python3
"""
Test script for DhanHQ October 2025 authentication system
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_dhan_auth():
    print("🧪 Testing DhanHQ October 2025 Authentication")
    print("=" * 50)
    
    # Check configuration
    api_key = os.getenv("DHAN_API_KEY")
    api_secret = os.getenv("DHAN_API_SECRET") 
    totp_secret = os.getenv("DHAN_TOTP_SECRET")
    static_ip = os.getenv("DHAN_STATIC_IP")
    
    print("📋 Configuration Status:")
    print(f"  API Key: {'✅' if api_key and api_key != 'your_dhan_api_key_here' else '❌'}")
    print(f"  API Secret: {'✅' if api_secret and api_secret != 'your_dhan_api_secret_here' else '❌'}")
    print(f"  TOTP Secret: {'✅' if totp_secret and totp_secret != 'your_dhan_totp_secret_here' else '❌'}")
    print(f"  Static IP: {'✅' if static_ip and static_ip != 'your_static_ip_address_here' else '❌'}")
    
    # Calculate completion
    config_items = [api_key, api_secret, totp_secret, static_ip]
    valid_items = sum(1 for item in config_items if item and item not in ['your_dhan_api_key_here', 'your_dhan_api_secret_here', 'your_dhan_totp_secret_here', 'your_static_ip_address_here'])
    
    completion_pct = (valid_items / 4) * 100
    print(f"\n📊 Setup Completion: {completion_pct:.1f}%")
    
    if completion_pct == 100:
        print("🎉 Ready for DhanHQ October 2025 API changes!")
        
        # Test authentication
        try:
            from services.broker_dhan import DhanAdapter
            
            print("\n🔐 Testing Authentication...")
            adapter = DhanAdapter(
                api_key=api_key,
                api_secret=api_secret,
                totp_secret=totp_secret,
                static_ip=static_ip
            )
            
            # First try to use existing token if available
            existing_token = os.getenv("DHAN_ACCESS_TOKEN")
            if existing_token:
                adapter.access_token = existing_token
                print("📋 Using existing access token from environment")
            
            # Test token validity
            is_valid = adapter.ensure_valid_token()
            
            if is_valid and adapter.access_token:
                print("✅ Authentication successful!")
                print("🔑 Access token is valid and ready for API calls")
                
                # Test a simple API call
                import requests
                headers = {
                    'access-token': adapter.access_token,
                    'X-Client-Id': os.getenv("DHAN_CLIENT_ID", ""),
                    'Content-Type': 'application/json'
                }
                
                # Test fund limit endpoint (v2)
                response = requests.get('https://api.dhan.co/v2/fundlimit', headers=headers, timeout=10)
                if response.status_code == 200:
                    print("✅ API connectivity confirmed - fund limit endpoint works")
                else:
                    print(f"⚠️  API call returned status {response.status_code}")
                
                return True
            else:
                print("❌ Token validation failed")
                print("💡 The existing token may be expired or invalid")
                print("🔄 Attempting new authentication with API key + TOTP...")
                
                # Try new authentication
                token = adapter.authenticate_with_api_key()
                if token:
                    print("✅ New authentication successful!")
                    return True
                else:
                    print("❌ New authentication also failed")
                    return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
    else:
        print("⚠️  Setup incomplete. Complete the following:")
        if not (api_key and api_key != 'your_dhan_api_key_here'):
            print("  - Configure DHAN_API_KEY")
        if not (api_secret and api_secret != 'your_dhan_api_secret_here'):
            print("  - Configure DHAN_API_SECRET")
        if not (totp_secret and totp_secret != 'your_dhan_totp_secret_here'):
            print("  - Configure DHAN_TOTP_SECRET")
        if not (static_ip and static_ip != 'your_static_ip_address_here'):
            print("  - Configure DHAN_STATIC_IP")
        
        print("\n📖 See DHAN_API_MIGRATION_2025.md for setup instructions")
        return False

if __name__ == "__main__":
    test_dhan_auth()
