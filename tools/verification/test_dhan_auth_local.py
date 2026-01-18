
from dhanhq import dhanhq
import sys

CLIENT_ID = "2508215064"
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

def test_auth():
    print(f"Testing DhanHQ Auth Locally...")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Token Length: {len(ACCESS_TOKEN)}")
    
    try:
        dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
        print("Client initialized.")
        
        print("Fetching Fund Limits...")
        response = dhan.get_fund_limits()
        print(f"Response: {response}")
        
        if response.get("status") == "success":
            print("[OK] Auth Success!")
            return True
        else:
            print("[FAIL] Auth Failed (API Response)")
            return False
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_auth()
