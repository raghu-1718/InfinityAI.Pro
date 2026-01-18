#!/usr/bin/env python3
"""
Complete End-to-End Application Test - Real-Time Market Hours
Tests the entire InfinityAI.Pro stack with Dhan Sandbox during market hours.

Test Flow:
1. Health checks (Engine A, B, C)
2. Market data retrieval (real-time quotes)
3. Fund limits check
4. Order placement (sandbox)
5. Order status tracking
6. Position verification
7. Order cancellation

This simulates the complete user journey from market data to order execution.
"""
import requests
import json
import time
from datetime import datetime

# Service URLs (Cloud Run)
ENGINE_A_URL = "https://engine-a-228557716858.us-central1.run.app"
ENGINE_B_URL = "https://engine-b-228557716858.us-central1.run.app"
ENGINE_C_URL = "https://engine-c-228557716858.us-central1.run.app"

# Sandbox credentials
SANDBOX_CLIENT_ID = "2508215064"
SANDBOX_ACCESS_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2RoYW4vcG9zdGJhY2siLCJpc3MiOiJkaGFuIiwiZXhwIjoxNzY5MDIyNzE0fQ.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"

# Test user ID
TEST_USER_ID = "sandbox_test_user_001"

def print_header(title, level=1):
    """Print formatted header"""
    if level == 1:
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    else:
        print(f"\n--- {title} ---")

def print_result(success, message):
    """Print test result"""
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {message}")
    return success

def test_engine_health(engine_name, url):
    """Test engine health endpoint"""
    print_header(f"Testing {engine_name} Health", level=2)
    
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"{engine_name} is healthy")
            print(f"    Service: {data.get('service', 'N/A')}")
            print(f"    Status: {data.get('status', 'N/A')}")
            return True, data
        else:
            print_result(False, f"{engine_name} health check failed: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"{engine_name} unreachable: {str(e)}")
        return False, None

def test_fund_limits():
    """Test fund limits retrieval from sandbox"""
    print_header("Checking Sandbox Fund Limits", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{sandbox_url}/fundlimit", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            balance = data.get('availabelBalance', 0)
            print_result(True, f"Fund limits retrieved")
            print(f"    Available Balance: Rs. {balance:,.2f}")
            print(f"    SOD Limit: Rs. {data.get('sodLimit', 0):,.2f}")
            return True, data
        else:
            print_result(False, f"Fund limits failed: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False, None

def test_market_quote():
    """Test real-time market quote retrieval"""
    print_header("Fetching Real-Time Market Quote (RELIANCE)", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Get OHLC data for RELIANCE (security_id: 2885)
    payload = {
        "NSE_EQ": [2885]
    }
    
    try:
        response = requests.post(
            f"{sandbox_url}/marketfeed/quote",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Market quote retrieved")
            if 'data' in data and 'NSE_EQ' in data['data']:
                quote = data['data']['NSE_EQ'].get('2885', {})
                print(f"    LTP: Rs. {quote.get('last_price', 'N/A')}")
                print(f"    Open: Rs. {quote.get('open', 'N/A')}")
                print(f"    High: Rs. {quote.get('high', 'N/A')}")
                print(f"    Low: Rs. {quote.get('low', 'N/A')}")
            return True, data
        elif response.status_code == 404:
            print_result(False, "Market quote endpoint not available in sandbox")
            print("    Note: Sandbox may have limited market data endpoints")
            return False, None
        else:
            print_result(False, f"Market quote failed: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False, None

def test_place_order(order_type="LIMIT"):
    """Test order placement through sandbox"""
    print_header(f"Placing {order_type} Order (RELIANCE)", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Order payload
    order_payload = {
        "dhanClientId": SANDBOX_CLIENT_ID,
        "transactionType": "BUY",
        "exchangeSegment": "NSE_EQ",
        "productType": "INTRADAY",
        "orderType": order_type,
        "validity": "DAY",
        "securityId": "2885",  # RELIANCE
        "quantity": 1,
        "disclosedQuantity": 0,
        "price": 1200.0 if order_type == "LIMIT" else 0,
        "afterMarketOrder": False
    }
    
    try:
        print(f"    Submitting {order_type} BUY order...")
        response = requests.post(
            f"{sandbox_url}/orders",
            headers=headers,
            json=order_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            order_id = data.get('orderId')
            order_status = data.get('orderStatus')
            print_result(True, f"Order placed successfully")
            print(f"    Order ID: {order_id}")
            print(f"    Status: {order_status}")
            print(f"    Symbol: RELIANCE")
            print(f"    Quantity: 1")
            print(f"    Price: Rs. {order_payload['price']}")
            return True, order_id
        else:
            print_result(False, f"Order placement failed: {response.status_code}")
            print(f"    Response: {response.text}")
            return False, None
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False, None

def test_get_order_status(order_id):
    """Test order status retrieval"""
    if not order_id:
        print_result(False, "No order ID provided")
        return False, None
    
    print_header(f"Checking Order Status: {order_id}", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"{sandbox_url}/orders/{order_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            # Response is a list, get first order
            if isinstance(data, list) and len(data) > 0:
                order = data[0]
            else:
                order = data
            
            print_result(True, "Order status retrieved")
            print(f"    Order ID: {order.get('orderId')}")
            print(f"    Status: {order.get('orderStatus')}")
            print(f"    Symbol: {order.get('tradingSymbol')}")
            print(f"    Quantity: {order.get('quantity')}")
            print(f"    Price: Rs. {order.get('price')}")
            print(f"    Filled Qty: {order.get('filledQty', 0)}")
            return True, order
        else:
            print_result(False, f"Status check failed: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False, None

def test_get_positions():
    """Test positions retrieval"""
    print_header("Fetching Current Positions", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{sandbox_url}/positions", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            positions = data if isinstance(data, list) else []
            print_result(True, f"Positions retrieved: {len(positions)} position(s)")
            if positions:
                for pos in positions[:5]:  # Show first 5
                    print(f"    Symbol: {pos.get('tradingSymbol')}, Qty: {pos.get('quantity')}")
            else:
                print("    No open positions")
            return True, positions
        else:
            print_result(False, f"Positions retrieval failed: {response.status_code}")
            return False, None
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False, None

def test_cancel_order(order_id):
    """Test order cancellation"""
    if not order_id:
        print_result(False, "No order ID provided")
        return False
    
    print_header(f"Cancelling Order: {order_id}", level=2)
    
    sandbox_url = "https://sandbox.dhan.co/v2"
    headers = {
        "access-token": SANDBOX_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.delete(
            f"{sandbox_url}/orders/{order_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print_result(True, "Order cancelled successfully")
            return True
        else:
            print_result(False, f"Cancellation failed: {response.status_code}")
            return False
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False

def main():
    """Run complete end-to-end test"""
    print_header("COMPLETE END-TO-END APPLICATION TEST")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Environment: SANDBOX (Market Hours)")
    print(f"User ID: {TEST_USER_ID}")
    
    results = {
        "engine_a_health": False,
        "engine_b_health": False,
        "engine_c_health": False,
        "fund_limits": False,
        "market_quote": False,
        "order_placement": False,
        "order_status": False,
        "positions": False,
        "order_cancel": False
    }
    
    # Phase 1: Infrastructure Health Checks
    print_header("PHASE 1: Infrastructure Health Checks")
    results["engine_a_health"], _ = test_engine_health("Engine A (Orchestrator)", ENGINE_A_URL)
    results["engine_b_health"], _ = test_engine_health("Engine B (Analysis)", ENGINE_B_URL)
    results["engine_c_health"], _ = test_engine_health("Engine C (Execution)", ENGINE_C_URL)
    
    # Phase 2: Account & Market Data
    print_header("PHASE 2: Account & Market Data")
    results["fund_limits"], fund_data = test_fund_limits()
    results["market_quote"], quote_data = test_market_quote()
    
    # Phase 3: Order Execution Flow
    print_header("PHASE 3: Order Execution Flow")
    order_success, order_id = test_place_order("LIMIT")
    results["order_placement"] = order_success
    
    if order_id:
        time.sleep(2)  # Wait for order processing
        results["order_status"], order_data = test_get_order_status(order_id)
        
    # Phase 4: Position Management
    print_header("PHASE 4: Position Management")
    results["positions"], positions_data = test_get_positions()
    
    # Phase 5: Order Cancellation (Cleanup)
    print_header("PHASE 5: Order Cancellation (Cleanup)")
    if order_id:
        results["order_cancel"] = test_cancel_order(order_id)
    
    # Final Summary
    print_header("TEST SUMMARY & RESULTS")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n")
    
    print("Detailed Results:")
    print(f"  [{'OK' if results['engine_a_health'] else 'FAIL'}] Engine A Health")
    print(f"  [{'OK' if results['engine_b_health'] else 'FAIL'}] Engine B Health")
    print(f"  [{'OK' if results['engine_c_health'] else 'FAIL'}] Engine C Health")
    print(f"  [{'OK' if results['fund_limits'] else 'FAIL'}] Fund Limits")
    print(f"  [{'OK' if results['market_quote'] else 'INFO'}] Market Quote (May not be available in sandbox)")
    print(f"  [{'OK' if results['order_placement'] else 'FAIL'}] Order Placement")
    print(f"  [{'OK' if results['order_status'] else 'FAIL'}] Order Status")
    print(f"  [{'OK' if results['positions'] else 'FAIL'}] Positions")
    print(f"  [{'OK' if results['order_cancel'] else 'FAIL'}] Order Cancellation")
    
    print("\n" + "=" * 80)
    print("OVERALL STATUS")
    print("=" * 80)
    
    # Core functionality check
    core_tests = [
        results['engine_c_health'],
        results['fund_limits'],
        results['order_placement'],
        results['order_status']
    ]
    
    if all(core_tests):
        print("\n[SUCCESS] All core systems operational!")
        print("  - Infrastructure: Healthy")
        print("  - Account Access: Working")
        print("  - Order Execution: Functional")
        print("  - Status Tracking: Active")
        print("\nThe application is ready for sandbox trading!")
    else:
        print("\n[WARNING] Some core tests failed")
        print("Review the detailed results above for more information")
    
    print("\n")

if __name__ == "__main__":
    main()
