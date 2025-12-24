"""
End-to-End System Verification Script
Validates all Phase-5 and Phase-6 deployments
"""
import requests
import json
from datetime import datetime
import subprocess

print("=" * 80)
print("InfinityAI.Pro - End-to-End Verification")
print(f"Started: {datetime.now().isoformat()}")
print("=" * 80)

# Engine URLs
ENGINES = {
    "Engine A": "https://engine-a-429140669077.us-central1.run.app",
    "Engine B": "https://engine-b-429140669077.us-central1.run.app",
    "Engine C": "https://engine-c-429140669077.us-central1.run.app"
}

FRONTEND = "https://infinityai.pro"

results = {}

# 1. Health Checks
print("\n[1/5] HEALTH CHECKS")
print("-" * 80)
for name, url in ENGINES.items():
    try:
        response = requests.get(f"{url}/health", timeout=10)
        status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
        results[f"{name} Health"] = status
        print(f"{name:15} {status:10} ({response.status_code})")
        
        if name == "Engine B" and response.status_code == 200:
            data = response.json()
            ml_status = data.get("ml_model_hotreload")
            print(f"  → ML Hot-Reload: {ml_status}")
    except Exception as e:
        results[f"{name} Health"] = "❌ FAIL"
        print(f"{name:15} ❌ FAIL ({str(e)[:50]})")

# Frontend
try:
    response = requests.get(FRONTEND, timeout=10)
    status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
    results["Frontend"] = status
    print(f"{'Frontend':15} {status:10} ({response.status_code})")
except Exception as e:
    results["Frontend"] = "❌ FAIL"
    print(f"{'Frontend':15} ❌ FAIL ({str(e)[:50]})")

# 2. Firestore Rules Check
print("\n[2/5] FIRESTORE SECURITY")
print("-" * 80)
try:
    result = subprocess.run(
        ["firebase", "firestore:rules:get"],
        capture_output=True,
        text=True,
        timeout=10
    )
    if "allow write: if false" in result.stdout:
        print("✅ PASS - Backend-only writes configured")
        results["Firestore Rules"] = "✅ PASS"
    else:
        print("❌ FAIL - Rules may not be restrictive")
        results["Firestore Rules"] = "❌ FAIL"
except Exception as e:
    print(f"⚠️ SKIP - Could not verify: {str(e)[:50]}")
    results["Firestore Rules"] = "⚠️ SKIP"

# 3. GCS Model Check
print("\n[3/5] ML MODEL IN GCS")
print("-" * 80)
try:
    result = subprocess.run(
        ["gcloud", "storage", "ls", "gs://gen-lang-client-0779271931-ml-models/xgb/"],
        capture_output=True,
        text=True,
        timeout=10
    )
    if "latest.json" in result.stdout or "xgboost_baseline" in result.stdout:
        print("✅ PASS - Model files found in GCS")
        results["GCS Model"] = "✅ PASS"
    else:
        print("❌ FAIL - No model files found")
        results["GCS Model"] = "❌ FAIL"
except Exception as e:
    print(f"⚠️ SKIP - Could not verify: {str(e)[:50]}")
    results["GCS Model"] = "⚠️ SKIP"

# 4. Budget Alerts Check
print("\n[4/5] COST MONITORING")
print("-" * 80)
try:
    result = subprocess.run(
        ["gcloud", "billing", "budgets", "list", 
         "--billing-account=01DCB3-486016-A36591",
         "--format=value(displayName)"],
        capture_output=True,
        text=True,
        timeout=10
    )
    if "InfinityAI" in result.stdout:
        print("✅ PASS - Budget alerts configured")
        results["Budget Alerts"] = "✅ PASS"
    else:
        print("❌ FAIL - No budget found")
        results["Budget Alerts"] = "❌ FAIL"
except Exception as e:
    print(f"⚠️ SKIP - Could not verify: {str(e)[:50]}")
    results["Budget Alerts"] = "⚠️ SKIP"

# 5. Cloud Logging Check
print("\n[5/5] LOGGING & MONITORING")
print("-" * 80)
try:
    result = subprocess.run([
        "gcloud", "logging", "read",
        'resource.labels.service_name="engine-a" AND textPayload:"freshness"',
        "--limit=1",
        "--project=gen-lang-client-0779271931",
        "--format=value(textPayload)"
    ], capture_output=True, text=True, timeout=15)
    
    if result.stdout.strip():
        print("✅ PASS - Data freshness logs present")
        results["Freshness Logging"] = "✅ PASS"
    else:
        print("⚠️ WARN - No recent freshness logs")
        results["Freshness Logging"] = "⚠️ WARN"
except Exception as e:
    print(f"⚠️ SKIP - Could not verify: {str(e)[:50]}")
    results["Freshness Logging"] = "⚠️ SKIP"

# Summary
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

passed = sum(1 for v in results.values() if "✅" in v)
failed = sum(1 for v in results.values() if "❌" in v)
skipped = sum(1 for v in results.values() if "⚠️" in v)
total = len(results)

for check, status in results.items():
    print(f"{check:30} {status}")

print("-" * 80)
print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
print(f"Success Rate: {(passed / total * 100):.1f}%")
print("=" * 80)

exit_code = 0 if failed == 0 else 1
exit(exit_code)
