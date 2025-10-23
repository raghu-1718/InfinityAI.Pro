#!/usr/bin/env python3
"""
Firebase Authentication Verification Script
Tests authentication setup after manual configuration
"""

import requests
import json
import time

def test_firebase_auth_api():
    """Test Firebase Authentication API"""

    print("🔥 Firebase Authentication API Test")
    print("=" * 50)

    project_id = "infinity-ai-5ec7c"
    api_key = "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU"

    # Test 1: Check if Auth API is responding
    print("1. Testing Authentication API availability...")

    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"

        # This should fail with invalid token, not configuration error
        response = requests.post(
            url,
            json={"idToken": "invalid_token_test"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "")

                if "CONFIGURATION_NOT_FOUND" in error_message:
                    print("   ❌ STILL NOT CONFIGURED: Authentication not set up")
                    print("   🔧 Please follow the Firebase Auth Setup Guide")
                    return False
                elif "INVALID_ID_TOKEN" in error_message:
                    print("   ✅ CONFIGURED: Authentication is set up correctly")
                    print("   📝 API responding with expected validation error")
                    return True
                else:
                    print(f"   ⚠️ Unexpected error: {error_message}")
                    return False

            except:
                print("   ⚠️ Could not parse error response")
                return False

        else:
            print(f"   ⚠️ Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

def test_frontend_auth_config():
    """Test if frontend can load with auth configuration"""

    print("\n2. Testing Frontend Authentication Configuration...")

    try:
        frontend_url = "https://infinity-ai-5ec7c.web.app"
        response = requests.get(frontend_url, timeout=10)

        if response.status_code == 200:
            print("   ✅ Frontend accessible")

            # Check if Firebase config is present
            content = response.text
            if "infinity-ai-5ec7c" in content and "firebaseapp.com" in content:
                print("   ✅ Firebase configuration detected in frontend")
                return True
            else:
                print("   ⚠️ Firebase configuration might be missing")
                return False
        else:
            print(f"   ❌ Frontend not accessible: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Frontend test error: {e}")
        return False

def test_auth_endpoints():
    """Test various auth endpoints"""

    print("\n3. Testing Authentication Endpoints...")

    api_key = "AIzaSyDjD8D3UYwM_PvPkPoBNZ5soOpsN7hoNVU"

    endpoints_to_test = [
        {
            "name": "Sign In",
            "url": f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            "data": {"email": "test@example.com", "password": "testpass", "returnSecureToken": True}
        },
        {
            "name": "Sign Up",
            "url": f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}",
            "data": {"email": "test@example.com", "password": "testpass", "returnSecureToken": True}
        }
    ]

    auth_configured = True

    for endpoint in endpoints_to_test:
        print(f"   Testing {endpoint['name']}...")

        try:
            response = requests.post(
                endpoint["url"],
                json=endpoint["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "")

                if "CONFIGURATION_NOT_FOUND" in error_message:
                    print(f"      ❌ {endpoint['name']}: Not configured")
                    auth_configured = False
                else:
                    print(f"      ✅ {endpoint['name']}: Configured (validation error expected)")
            else:
                print(f"      ⚠️ {endpoint['name']}: Unexpected response {response.status_code}")

        except Exception as e:
            print(f"      ❌ {endpoint['name']}: Error - {e}")
            auth_configured = False

    return auth_configured

def main():
    """Main verification function"""

    print("🚀 Firebase Authentication Verification")
    print("=" * 60)
    print("This script verifies if Firebase Authentication is properly configured")
    print("Run this AFTER setting up authentication in Firebase Console\n")

    # Run all tests
    api_test = test_firebase_auth_api()
    frontend_test = test_frontend_auth_config()
    endpoints_test = test_auth_endpoints()

    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)

    print(f"🔥 Authentication API: {'✅ Configured' if api_test else '❌ Not Configured'}")
    print(f"🌐 Frontend Configuration: {'✅ Working' if frontend_test else '❌ Issues'}")
    print(f"🔗 Auth Endpoints: {'✅ All Working' if endpoints_test else '❌ Some Issues'}")

    if api_test and frontend_test and endpoints_test:
        print("\n🎉 SUCCESS: Firebase Authentication is properly configured!")
        print("✅ Your app should now work without auth/configuration-not-found errors")
        print("🔄 Try logging in at: https://infinity-ai-5ec7c.web.app/login")
    else:
        print("\n⚠️ ISSUES DETECTED: Authentication setup incomplete")
        print("📖 Please follow the Firebase Auth Setup Guide:")
        print("   1. Go to https://console.firebase.google.com/project/infinity-ai-5ec7c/authentication")
        print("   2. Click 'Get Started' if shown")
        print("   3. Enable Email/Password provider")
        print("   4. Run this script again to verify")

    print(f"\n🕐 Verification completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()