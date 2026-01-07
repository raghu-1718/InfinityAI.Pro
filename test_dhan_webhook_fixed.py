#!/usr/bin/env python3
"""
Dhan Postback Webhook Test
Tests the /api/dhan/postback endpoint with realistic order update payloads
"""

import json
import requests
from datetime import datetime
import time

# Configuration
ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
POSTBACK_ENDPOINT = f"{ENGINE_C_URL}/api/dhan/postback"

# Test payloads (corrected field names based on backend schema)
TEST_PAYLOADS = [
    {
        "name": "Order_Placed",
        "payload": {
            "order_id": "12345678",
            "transaction_type": "BUY",
            "exchange_segment": "NSE",
            "product_code": "MIS",
            "orderStatus": "PENDING",
            "order_leg_status": "PENDING",
            "order_price": 100.50,
            "order_quantity": 10,
            "filled_quantity": 0,
            "pending_quantity": 10,
            "order_value": 1005.00,
            "average_price": 0,
            "order_datetime": datetime.now().isoformat(),
            "exchange_order_datetime": datetime.now().isoformat(),
            "order_type": "REGULAR",
            "order_mode": "REGULAR",
            "client_id": "1101302170",
            "trading_symbol": "INFY-EQ",
            "correlation_id": "test_correlation_001"
        }
    },
    {
        "name": "Order_Partial_Fill",
        "payload": {
            "order_id": "12345678",
            "transaction_type": "BUY",
            "exchange_segment": "NSE",
            "product_code": "MIS",
            "orderStatus": "PENDING",
            "order_leg_status": "PENDING",
            "order_price": 100.50,
            "order_quantity": 10,
            "filled_quantity": 5,
            "pending_quantity": 5,
            "order_value": 1005.00,
            "average_price": 100.50,
            "order_datetime": datetime.now().isoformat(),
            "exchange_order_datetime": datetime.now().isoformat(),
            "order_type": "REGULAR",
            "order_mode": "REGULAR",
            "client_id": "1101302170",
            "trading_symbol": "INFY-EQ",
            "correlation_id": "test_correlation_002"
        }
    },
    {
        "name": "Order_Filled",
        "payload": {
            "order_id": "12345678",
            "transaction_type": "BUY",
            "exchange_segment": "NSE",
            "product_code": "MIS",
            "orderStatus": "FILLED",
            "order_leg_status": "FILLED",
            "order_price": 100.50,
            "order_quantity": 10,
            "filled_quantity": 10,
            "pending_quantity": 0,
            "order_value": 1005.00,
            "average_price": 100.50,
            "order_datetime": datetime.now().isoformat(),
            "exchange_order_datetime": datetime.now().isoformat(),
            "order_type": "REGULAR",
            "order_mode": "REGULAR",
            "client_id": "1101302170",
            "trading_symbol": "INFY-EQ",
            "correlation_id": "test_correlation_003"
        }
    },
    {
        "name": "Order_Cancelled",
        "payload": {
            "order_id": "12345679",
            "transaction_type": "BUY",
            "exchange_segment": "NSE",
            "product_code": "MIS",
            "orderStatus": "CANCELLED",
            "order_leg_status": "CANCELLED",
            "order_price": 100.50,
            "order_quantity": 10,
            "filled_quantity": 0,
            "pending_quantity": 10,
            "order_value": 1005.00,
            "average_price": 0,
            "order_datetime": datetime.now().isoformat(),
            "exchange_order_datetime": datetime.now().isoformat(),
            "cancellation_datetime": datetime.now().isoformat(),
            "order_type": "REGULAR",
            "order_mode": "REGULAR",
            "client_id": "1101302170",
            "trading_symbol": "INFY-EQ",
            "correlation_id": "test_correlation_004"
        }
    }
]

def test_webhook(payload_info):
    """Send test webhook payload"""
    name = payload_info["name"]
    payload = payload_info["payload"]

    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    print(f"Endpoint: POST {POSTBACK_ENDPOINT}")
    print(f"Sending request...")

    try:
        response = requests.post(
            POSTBACK_ENDPOINT,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )

        print(f"Status Code: {response.status_code}")

        try:
            resp_json = response.json()
            print(f"Response: {json.dumps(resp_json, indent=2)[:300]}")
        except:
            print(f"Response: {response.text[:300]}")

        if response.status_code in [200, 201, 202, 204]:
            print(f"[OK] Webhook accepted")
            return True
        else:
            print(f"[WARN] Unexpected status: {response.status_code}")
            return False

    except requests.Timeout:
        print(f"[ERROR] Request timeout")
        return False
    except requests.RequestException as e:
        print(f"[ERROR] Connection failed: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False

def main():
    print("\n")
    print("*" * 70)
    print("DHAN POSTBACK WEBHOOK TEST SUITE")
    print("*" * 70)
    print(f"Engine-C URL: {ENGINE_C_URL}")
    print(f"Postback Endpoint: {POSTBACK_ENDPOINT}")
    print(f"Test Start: {datetime.now()}")

    results = []

    for payload_info in TEST_PAYLOADS:
        success = test_webhook(payload_info)
        results.append({
            "test": payload_info["name"],
            "success": success
        })
        time.sleep(1)  # Delay between tests

    # Print summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    for result in results:
        status = "[OK]" if result["success"] else "[FAIL]"
        print(f"{status} {result['test']}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All webhook tests passed!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
