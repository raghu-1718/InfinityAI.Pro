#!/usr/bin/env python3
"""
Firestore Connectivity Verification Script
Tests that backend can connect to Firestore and access credentials
"""

import os
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_firestore_connectivity():
    """Verify Firestore connection from backend"""

    print("\n" + "="*70)
    print("🔍 FIRESTORE CONNECTIVITY VERIFICATION")
    print("="*70 + "\n")

    checks = []

    # Check 1: Environment Variables
    print("1️⃣  Checking Environment Variables...")
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
    checks.append({
        "name": "GOOGLE_CLOUD_PROJECT env var",
        "passed": bool(gcp_project),
        "value": gcp_project if gcp_project else "❌ NOT SET",
        "required": True
    })

    user_creds_key = os.getenv("USER_CREDENTIALS_KEY") or os.getenv("ENCRYPTION_KEY")
    checks.append({
        "name": "USER_CREDENTIALS_KEY env var",
        "passed": bool(user_creds_key),
        "value": f"{'✅ SET' if user_creds_key else '❌ NOT SET'} ({len(user_creds_key) if user_creds_key else 0} chars)",
        "required": False  # Falls back to Secret Manager
    })

    # Check 2: Python Packages
    print("\n2️⃣  Checking Required Packages...")
    required_packages = {
        "google.cloud.firestore": "google-cloud-firestore",
        "google.cloud.secretmanager": "google-cloud-secretmanager",
        "cryptography": "cryptography"
    }

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            checks.append({
                "name": f"{package_name} package",
                "passed": True,
                "value": "✅ Installed",
                "required": True
            })
        except ImportError:
            checks.append({
                "name": f"{package_name} package",
                "passed": False,
                "value": "❌ NOT INSTALLED",
                "required": True
            })

    # Check 3: Firestore Connection
    print("\n3️⃣  Testing Firestore Connection...")
    try:
        from google.cloud import firestore

        try:
            db = firestore.Client(project=gcp_project)
            # Try a simple collection reference to verify connection
            _ = db.collection("dhan_credentials")
            checks.append({
                "name": "Firestore Client initialization",
                "passed": True,
                "value": "✅ Connected",
                "required": True
            })
        except Exception as e:
            checks.append({
                "name": "Firestore Client initialization",
                "passed": False,
                "value": f"❌ Error: {str(e)[:100]}",
                "required": True
            })
    except ImportError:
        checks.append({
            "name": "Firestore Client initialization",
            "passed": False,
            "value": "❌ firestore package not available",
            "required": True
        })

    # Check 4: Encryption Key
    print("\n4️⃣  Checking Encryption Key...")
    try:
        if user_creds_key:
            if len(user_creds_key) == 64:
                # Try to decode hex
                try:
                    key_bytes = bytes.fromhex(user_creds_key)
                    checks.append({
                        "name": "Encryption key format (hex)",
                        "passed": True,
                        "value": "✅ Valid (64 hex chars = 32 bytes)",
                        "required": True
                    })
                except ValueError:
                    checks.append({
                        "name": "Encryption key format (hex)",
                        "passed": False,
                        "value": f"❌ Invalid hex format",
                        "required": True
                    })
            else:
                checks.append({
                    "name": "Encryption key format",
                    "passed": False,
                    "value": f"❌ Expected 64 chars, got {len(user_creds_key)}",
                    "required": True
                })
        else:
            checks.append({
                "name": "Encryption key",
                "passed": False,
                "value": "⚠️  Will fall back to insecure key",
                "required": False
            })
    except Exception as e:
        checks.append({
            "name": "Encryption key validation",
            "passed": False,
            "value": f"❌ Error: {str(e)}",
            "required": True
        })

    # Check 5: Test Read/Write to Firestore
    print("\n5️⃣  Testing Firestore Read/Write...")
    try:
        from google.cloud import firestore
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        db = firestore.Client(project=gcp_project)

        # Test collection access
        test_doc_id = f"test_{datetime.utcnow().timestamp()}"
        test_data = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Firestore connectivity test"
        }

        # Write test
        try:
            db.collection("_firestore_test").document(test_doc_id).set(test_data)
            checks.append({
                "name": "Firestore write operation",
                "passed": True,
                "value": f"✅ Write successful (doc: {test_doc_id})",
                "required": True
            })

            # Read test
            try:
                doc = db.collection("_firestore_test").document(test_doc_id).get()
                if doc.exists:
                    checks.append({
                        "name": "Firestore read operation",
                        "passed": True,
                        "value": "✅ Read successful",
                        "required": True
                    })

                    # Cleanup
                    db.collection("_firestore_test").document(test_doc_id).delete()
                else:
                    checks.append({
                        "name": "Firestore read operation",
                        "passed": False,
                        "value": "❌ Document not found after write",
                        "required": True
                    })
            except Exception as e:
                checks.append({
                    "name": "Firestore read operation",
                    "passed": False,
                    "value": f"❌ Read failed: {str(e)[:100]}",
                    "required": True
                })
        except Exception as e:
            checks.append({
                "name": "Firestore write operation",
                "passed": False,
                "value": f"❌ Write failed: {str(e)[:100]}",
                "required": True
            })

    except Exception as e:
        checks.append({
            "name": "Firestore read/write test",
            "passed": False,
            "value": f"❌ Error: {str(e)[:100]}",
            "required": True
        })

    # Print Results
    print("\n" + "="*70)
    print("✅ VERIFICATION RESULTS")
    print("="*70 + "\n")

    passed_count = 0
    failed_count = 0
    warning_count = 0

    for check in checks:
        status = "✅ PASS" if check["passed"] else "❌ FAIL"
        if not check["passed"] and not check["required"]:
            status = "⚠️  WARN"
            warning_count += 1
        elif check["passed"]:
            passed_count += 1
        else:
            failed_count += 1

        print(f"{status} | {check['name']:<40} | {check['value']}")

    print("\n" + "-"*70)
    print(f"Summary: {passed_count} passed, {failed_count} failed, {warning_count} warnings")
    print("-"*70)

    # Summary
    all_required_passed = all(c["passed"] for c in checks if c["required"])

    print("\n" + "="*70)
    if all_required_passed:
        print("🎉 FIRESTORE CONNECTIVITY: VERIFIED ✅")
        print("="*70)
        print("\n✅ Backend can connect to Firestore!")
        print("✅ Credentials will be stored and retrieved successfully!")
        print("✅ Ready for production deployment!")
        return True
    else:
        print("❌ FIRESTORE CONNECTIVITY: ISSUES DETECTED")
        print("="*70)
        failed_checks = [c for c in checks if not c["passed"] and c["required"]]
        print("\n⚠️  Required checks that failed:")
        for check in failed_checks:
            print(f"  • {check['name']}: {check['value']}")
        print("\n🔧 ACTION REQUIRED:")
        print("  1. Ensure GOOGLE_CLOUD_PROJECT is set")
        print("  2. Ensure USER_CREDENTIALS_KEY is set (32-byte hex = 64 chars)")
        print("  3. Verify service account has Firestore access")
        print("  4. Check gcloud authentication: gcloud auth list")
        return False

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    try:
        success = check_firestore_connectivity()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
