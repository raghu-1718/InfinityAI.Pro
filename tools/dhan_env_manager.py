#!/usr/bin/env python3
"""
Environment Switcher for DhanHQ Integration

This script helps switch between sandbox and production environments
for testing and deployment.
"""
import os
import sys
import argparse
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False
    print("Warning: Firebase not available - some features will be limited")


class EnvironmentManager:
    """Manage DhanHQ environment configuration"""
    
    SANDBOX_URL = "https://sandbox.dhan.co/v2"
    PRODUCTION_URL = "https://api.dhan.co/v2"
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "galvanic-pulsar-482815-h0")
    
    def set_environment(self, env: str):
        """Set the DHAN_ENVIRONMENT variable."""
        if env not in ["sandbox", "production"]:
            raise ValueError("Environment must be 'sandbox' or 'production'")
        
        # Set in current session
        os.environ["DHAN_ENVIRONMENT"] = env
        
        print(f"\n✅ Environment set to: {env.upper()}")
        print(f"   Base URL: {self.SANDBOX_URL if env == 'sandbox' else self.PRODUCTION_URL}")
        
        return env
    
    def get_environment(self) -> str:
        """Get current environment."""
        return os.getenv("DHAN_ENVIRONMENT", "production")
    
    def show_status(self):
        """Display current environment status."""
        current = self.get_environment()
        url = self.SANDBOX_URL if current == "sandbox" else self.PRODUCTION_URL
        
        print("\n" + "=" * 70)
        print("  DHAN ENVIRONMENT STATUS")
        print("=" * 70)
        print(f"  Current Environment: {current.upper()}")
        print(f"  API Base URL: {url}")
        print(f"  Project ID: {self.project_id}")
        print("=" * 70 + "\n")
    
    def test_credentials(self, client_id: str, access_token: str, environment: str = None):
        """Test credentials against the specified environment."""
        if environment is None:
            environment = self.get_environment()
        
        import requests
        
        base_url = self.SANDBOX_URL if environment == "sandbox" else self.PRODUCTION_URL
        
        headers = {
            "access-token": access_token,
            "Content-Type": "application/json"
        }
        
        print(f"\n🔍 Testing credentials against {environment.upper()} environment...")
        print(f"   Client ID: {client_id}")
        print(f"   Base URL: {base_url}")
        
        try:
            response = requests.get(f"{base_url}/fundlimit", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ SUCCESS - Credentials are valid!")
                print(f"   Available Balance: ₹{data.get('availabelBalance', 0):,.2f}")
                return True
            else:
                print(f"\n❌ FAILED - Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            return False
    
    def list_firestore_credentials(self):
        """List all credentials stored in Firestore."""
        if not HAS_FIREBASE:
            print("❌ Firebase not available")
            return
        
        try:
            if not firebase_admin._apps:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
            
            db = firestore.client()
            
            print("\n" + "=" * 70)
            print("  STORED CREDENTIALS (Firestore)")
            print("=" * 70)
            
            creds_ref = db.collection('dhan_credentials')
            docs = creds_ref.stream()
            
            count = 0
            for doc in docs:
                count += 1
                data = doc.to_dict()
                print(f"\n  User ID: {doc.id}")
                print(f"  Connection Status: {data.get('connection_status', 'unknown')}")
                print(f"  Updated: {data.get('updated_at', 'unknown')}")
            
            if count == 0:
                print("\n  No credentials found in Firestore")
            else:
                print(f"\n  Total: {count} credential(s)")
            
            print("=" * 70 + "\n")
            
        except Exception as e:
            print(f"❌ Error listing credentials: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DhanHQ Environment Manager - Switch between sandbox and production"
    )
    
    parser.add_argument(
        "command",
        choices=["set", "get", "status", "test", "list"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--env",
        choices=["sandbox", "production"],
        help="Environment to set (required for 'set' command)"
    )
    
    parser.add_argument(
        "--client-id",
        help="Dhan client ID (for test command)"
    )
    
    parser.add_argument(
        "--access-token",
        help="Dhan access token (for test command)"
    )
    
    args = parser.parse_args()
    
    manager = EnvironmentManager()
    
    if args.command == "set":
        if not args.env:
            print("❌ Error: --env required for 'set' command")
            sys.exit(1)
        manager.set_environment(args.env)
        manager.show_status()
    
    elif args.command == "get":
        current = manager.get_environment()
        print(f"\nCurrent environment: {current}")
    
    elif args.command == "status":
        manager.show_status()
    
    elif args.command == "test":
        if not args.client_id or not args.access_token:
            print("❌ Error: --client-id and --access-token required for 'test' command")
            sys.exit(1)
        manager.test_credentials(args.client_id, args.access_token, args.env)
    
    elif args.command == "list":
        manager.list_firestore_credentials()


if __name__ == "__main__":
    main()
