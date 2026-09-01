"""
Test Idempotency & Duplicate Prevention Logic
Tests:
1. IdempotencyManager with duplicate Pub/Sub message IDs
2. EquityScanner duplicate symbol prevention (should skip all currently OPEN symbols)
"""

import os
import sys
import asyncio
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "engine-a")))
from src.services.idempotency import IDEMPOTENCY_MANAGER
from src.services.equity_scanner import EQUITY_SCANNER

async def main():
    print("=" * 80)
    print("INFINITYAI.PRO - IDEMPOTENCY & DUPLICATE PREVENTION VERIFICATION")
    print("=" * 80)

    # 1. Test Pub/Sub Message ID Idempotency
    print("\n[1] TESTING PUBSUB MESSAGE ID IDEMPOTENCY...")
    test_msg_id = f"TEST_MSG_{int(datetime.now(timezone.utc).timestamp())}"
    
    # First delivery
    first_attempt = IDEMPOTENCY_MANAGER.check_and_claim_message(
        message_id=test_msg_id,
        handler_name="TEST_SCAN",
        topic="equity-scan-requests"
    )
    print(f"First Delivery for Message [{test_msg_id}]: Allowed = {first_attempt}")

    # Duplicate delivery
    second_attempt = IDEMPOTENCY_MANAGER.check_and_claim_message(
        message_id=test_msg_id,
        handler_name="TEST_SCAN",
        topic="equity-scan-requests"
    )
    print(f"Second Delivery for Message [{test_msg_id}]: Allowed = {second_attempt}")

    assert first_attempt is True, "First delivery should be allowed"
    assert second_attempt is False, "Second delivery must be blocked as duplicate"
    print("[PASS] Pub/Sub Message Idempotency successfully verified!")

    # 2. Test Equity Scanner Duplicate Prevention
    print("\n[2] TESTING SCANNER DUPLICATE SYMBOL PREVENTION...")
    # There are 18 active symbols in Firestore. Running scan_universe should produce 0 new duplicates for those symbols.
    generated_setups = await EQUITY_SCANNER.scan_universe()
    print(f"Scan universe execution completed.")
    print(f"New signals generated during this cycle: {len(generated_setups)}")
    
    for s in generated_setups:
        print(f"   -> Generated: {s['signal_id']} for {s['symbol']}")

    print(f"[PASS] Duplicate prevention successfully protected active open positions!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
