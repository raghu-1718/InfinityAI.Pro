from dhanhq import dhanhq
import sys

client_id = "2508215064"
access_token = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"
sandbox_url = "https://sandbox.dhan.co/v2"

print(f"Initializing DhanHQ client with ID: {client_id}")
try:
    client = dhanhq(client_id, access_token)
    # Force sandbox URL
    if hasattr(client, 'base_url'):
        client.base_url = sandbox_url
        print(f"Set base_url to {sandbox_url}")
except Exception as e:
    print("Failed to initialize client:")
    print(e)
    sys.exit(1)

print("\n1. Testing get_fund_limits()...")
try:
    funds = client.get_fund_limits()
    print("Result:")
    print(funds)
except Exception as e:
    print(f"Failed: {e}")

print("\n2. Testing get_positions()...")
try:
    positions = client.get_positions()
    print("Result:")
    print(positions)
except Exception as e:
    print(f"Failed: {e}")

print("\n3. Testing get_holdings()...")
try:
    holdings = client.get_holdings()
    print("Result:")
    print(holdings)
except Exception as e:
    print(f"Failed: {e}")

print("\n4. Testing get_order_list()...")
try:
    orders = client.get_order_list()
    print("Result:")
    print(orders)
except Exception as e:
    print(f"Failed: {e}")
