#!/usr/bin/env python3
"""Test placing orders in DhanHQ sandbox environment."""
import requests
import json
import time
from datetime import datetime

# Sandbox credentials
CLIENT_ID = "2508215064"
ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# DhanHQ sandbox base URL
BASE_URL = "https://sandbox.dhan.co/v2"

# Common headers
HEADERS = {
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def api_call(endpoint, method="GET", payload=None):
    """Make an API call to DhanHQ sandbox."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=payload, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=10)
        
        print(f"\n[{method}] {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"[OK] SUCCESS")
            print(f"Response: {json.dumps(data, indent=2)}")
            return True, data
        else:
            print(f"[FAIL] Failed")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False, None

def test_place_limit_order():
    """Test placing a LIMIT order for RELIANCE."""
    print_section("TEST 1: Place LIMIT BUY Order (RELIANCE)")
    
    # RELIANCE NSE_EQ security ID
    order_payload = {
        "dhanClientId": CLIENT_ID,
        "transactionType": "BUY",
        "exchangeSegment": "NSE_EQ",
        "productType": "INTRADAY",
        "orderType": "LIMIT",
        "validity": "DAY",
        "securityId": "2885",  # RELIANCE
        "quantity": 1,
        "disclosedQuantity": 0,
        "price": 1200.0,
        "afterMarketOrder": False
    }
    
    success, data = api_call("/orders", method="POST", payload=order_payload)
    
    if success and data:
        order_id = data.get("orderId")
        print(f"\n[OK] Order placed successfully!")
        print(f"Order ID: {order_id}")
        return order_id
    else:
        print("\n[FAIL] Order placement failed")
        return None

def test_place_market_order():
    """Test placing a MARKET order for INFY."""
    print_section("TEST 2: Place MARKET BUY Order (INFY)")
    
    # INFY NSE_EQ security ID
    order_payload = {
        "dhanClientId": CLIENT_ID,
        "transactionType": "BUY",
        "exchangeSegment": "NSE_EQ",
        "productType": "INTRADAY",
        "orderType": "MARKET",
        "validity": "DAY",
        "securityId": "1594",  # INFY
        "quantity": 1,
        "disclosedQuantity": 0,
        "price": 0,
        "afterMarketOrder": False
    }
    
    success, data = api_call("/orders", method="POST", payload=order_payload)
    
    if success and data:
        order_id = data.get("orderId")
        print(f"\n[OK] Order placed successfully!")
        print(f"Order ID: {order_id}")
        return order_id
    else:
        print("\n[FAIL] Order placement failed")
        return None

def test_modify_order(order_id):
    """Test modifying an order."""
    if not order_id:
        print_section("TEST 3: Modify Order - SKIPPED (no order ID)")
        return False
    
    print_section(f"TEST 3: Modify Order {order_id}")
    
    modify_payload = {
        "dhanClientId": CLIENT_ID,
        "orderId": order_id,
        "orderType": "LIMIT",
        "legName": "ENTRY_LEG",
        "quantity": 2,  # Change quantity from 1 to 2
        "price": 1210.0,  # Change price
        "disclosedQuantity": 0,
        "triggerPrice": 0,
        "validity": "DAY"
    }
    
    success, data = api_call(f"/orders/{order_id}", method="PUT", payload=modify_payload)
    
    if success:
        print(f"\n[OK] Order modified successfully!")
        return True
    else:
        print("\n[FAIL] Order modification failed")
        return False

def test_get_order_status(order_id):
    """Test getting order status."""
    if not order_id:
        print_section("TEST 4: Get Order Status - SKIPPED (no order ID)")
        return
    
    print_section(f"TEST 4: Get Order Status {order_id}")
    
    success, data = api_call(f"/orders/{order_id}", method="GET")
    
    if success and data:
        print(f"\n[OK] Order status retrieved!")
        # API returns a list, get the first order
        order = data[0] if isinstance(data, list) and len(data) > 0 else data
        print(f"Status: {order.get('orderStatus')}")
        print(f"Quantity: {order.get('quantity')}")
        print(f"Price: {order.get('price')}")

def test_cancel_order(order_id):
    """Test canceling an order."""
    if not order_id:
        print_section("TEST 5: Cancel Order - SKIPPED (no order ID)")
        return False
    
    print_section(f"TEST 5: Cancel Order {order_id}")
    
    success, data = api_call(f"/orders/{order_id}", method="DELETE")
    
    if success:
        print(f"\n[OK] Order cancelled successfully!")
        return True
    else:
        print("\n[FAIL] Order cancellation failed")
        return False

def test_get_order_book():
    """Test getting the order book."""
    print_section("TEST 6: Get Order Book")
    
    success, data = api_call("/orders", method="GET")
    
    if success and data:
        print(f"\n[OK] Order book retrieved!")
        print(f"Total orders: {len(data) if isinstance(data, list) else 'N/A'}")

def test_get_positions():
    """Test getting positions."""
    print_section("TEST 7: Get Positions")
    
    success, data = api_call("/positions", method="GET")
    
    if success and data:
        print(f"\n[OK] Positions retrieved!")
        print(f"Total positions: {len(data) if isinstance(data, list) else 'N/A'}")

def main():
    """Run all sandbox order tests."""
    
    print_section("DHAN SANDBOX ORDER TESTING")
    print(f"\nClient ID: {CLIENT_ID}")
    print(f"Environment: SANDBOX")
    print(f"Base URL: {BASE_URL}")
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Place LIMIT order
    limit_order_id = test_place_limit_order()
    time.sleep(1)
    
    # Test 2: Place MARKET order
    market_order_id = test_place_market_order()
    time.sleep(1)
    
    # Test 3: Modify the LIMIT order
    if limit_order_id:
        test_modify_order(limit_order_id)
        time.sleep(1)
    
    # Test 4: Get order status
    if limit_order_id:
        test_get_order_status(limit_order_id)
        time.sleep(1)
    
    # Test 5: Cancel the LIMIT order
    if limit_order_id:
        test_cancel_order(limit_order_id)
        time.sleep(1)
    
    # Test 6: Get order book
    test_get_order_book()
    time.sleep(1)
    
    # Test 7: Get positions
    test_get_positions()
    
    print_section("TEST SUMMARY")
    print("\n[OK] All sandbox order tests completed!")
    print("\nNote: Orders in sandbox are simulated and do not affect real trading.")
    print("All funds and positions are virtual for testing purposes.\n")

if __name__ == "__main__":
    main()
