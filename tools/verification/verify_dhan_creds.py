
import logging
from dhanhq import dhanhq
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Provided Credentials
CLIENT_ID = "1101302170"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJwX2lwIjoiNC4yNDAuMzkuMTkzIiwic19pcCI6IiIsImlzcyI6ImRoYW4iLCJwYXJ0bmVySWQiOiIiLCJleHAiOjE3NjgyMzUxMzUsImlhdCI6MTc2ODE0ODczNSwidG9rZW5Db25zdW1lclR5cGUiOiJTRUxGIiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJkaGFuQ2xpZW50SWQiOiIxMTAxMzAyMTcwIn0.YlMQEsP56qmF_lIANKz7lXuNEXgJGiCwsTzwJZmMB21AjVS4BrLcSQpXBbDhJze71rU_azCnTauEFslUkMhQQA"

def verify_credentials():
    print(f"Testing credentials for Client ID: {CLIENT_ID}")
    
    try:
        dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)
        
        # 1. Get Fund Limits
        print("\n[1] Fetching Fund Limits...")
        funds = dhan.get_fund_limits()
        print(f"Status: {funds.get('status')}")
        if funds.get('status') == 'success':
            print("Funds Data:")
            print(json.dumps(funds.get('data'), indent=2))
        else:
            print(f"Error: {funds}")

        # 2. Get Holdings (to check connectivity depth)
        print("\n[2] Fetching Holdings...")
        holdings = dhan.get_holdings()
        print(f"Status: {holdings.get('status')}")
        if holdings.get('status') == 'success':
            data = holdings.get('data', [])
            print(f"Holdings Count: {len(data)}")
        else:
            print(f"Error: {holdings}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    verify_credentials()
