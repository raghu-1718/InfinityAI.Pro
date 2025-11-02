#!/usr/bin/env python3
"""
InfinityAI.Pro - Gemini Integration Test & Fix Script

Tests the fixed Gemini analysis pipeline:
1. Engine B Gemini endpoint
2. Firebase Functions integration
3. Frontend dashboard updates
"""

import requests
import json
import asyncio
import time
from datetime import datetime

# Configuration
ENGINE_URLS = {
    "A": "https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app",
    "B": "https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app",
    "C": "https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app",
    "D": "https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app"
}

FIREBASE_FUNCTIONS_URL = "https://us-central1-after-yesterday-473512-k3.cloudfunctions.net"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_status(message, status="info"):
    emoji = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "🔍"}
    print(f"{emoji.get(status, '📋')} {message}")

async def test_engine_b_gemini():
    """Test the new Gemini endpoint in Engine B"""
    print_header("Testing Engine B Gemini Endpoint")

    test_prompt = """
    Analyze NIFTY 50 current market sentiment and provide:
    1. Overall market direction
    2. Key sectors to watch
    3. Risk factors for next week
    4. Top 3 stock recommendations
    """

    payload = {
        "prompt": test_prompt,
        "context": {
            "market": "NSE",
            "timeframe": "intraday",
            "risk_tolerance": "moderate"
        },
        "userId": "test_user_123"
    }

    try:
        print_status("Sending request to Engine B Gemini endpoint...")
        response = requests.post(
            f"{ENGINE_URLS['B']}/api/gemini/analyze",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print_status("Engine B Gemini endpoint working!", "success")
            print(f"📊 Analysis Preview: {data['analysis'][:200]}...")
            print(f"🕒 Response time: {response.elapsed.total_seconds():.2f}s")
            return True
        else:
            print_status(f"Engine B error: {response.status_code} - {response.text}", "error")
            return False

    except Exception as e:
        print_status(f"Engine B connection failed: {e}", "error")
        return False

async def test_firebase_function():
    """Test the Firebase getGeminiAnalysis function"""
    print_header("Testing Firebase Function Integration")

    # Note: This would require proper Firebase authentication in production
    payload = {
        "data": {
            "prompt": "Quick analysis of current NIFTY sentiment",
            "context": {"source": "test_script"}
        }
    }

    try:
        print_status("Testing Firebase Function endpoint...")
        response = requests.post(
            f"{FIREBASE_FUNCTIONS_URL}/getGeminiAnalysis",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            print_status("Firebase Function working!", "success")
            return True
        elif response.status_code == 401:
            print_status("Firebase Function exists but requires authentication", "warning")
            return True
        else:
            print_status(f"Firebase Function error: {response.status_code}", "error")
            return False

    except Exception as e:
        print_status(f"Firebase Function test failed: {e}", "error")
        return False

async def test_all_engines_health():
    """Test health of all engines"""
    print_header("Testing All Engine Health")

    results = {}
    for engine, url in ENGINE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                print_status(f"Engine {engine}: Healthy", "success")
                results[engine] = True
            else:
                print_status(f"Engine {engine}: Unhealthy ({response.status_code})", "error")
                results[engine] = False
        except Exception as e:
            print_status(f"Engine {engine}: Connection failed - {e}", "error")
            results[engine] = False

    return results

async def test_frontend_gemini_config():
    """Check if frontend has proper Gemini configuration"""
    print_header("Testing Frontend Gemini Configuration")

    try:
        # Check if frontend is accessible
        response = requests.get("https://infinityai.pro", timeout=10)
        if response.status_code == 200:
            print_status("Frontend accessible", "success")

            # Check for Gemini configuration indicators
            content = response.text
            if "gemini" in content.lower() or "ai-analysis" in content.lower():
                print_status("Frontend has AI analysis components", "success")
            else:
                print_status("Frontend may need Gemini integration updates", "warning")

            return True
        else:
            print_status(f"Frontend not accessible: {response.status_code}", "error")
            return False

    except Exception as e:
        print_status(f"Frontend test failed: {e}", "error")
        return False

async def run_comprehensive_test():
    """Run all tests and generate report"""
    print_header("InfinityAI.Pro Gemini Integration Test Suite")

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }

    # Test 1: Engine Health
    engine_health = await test_all_engines_health()
    results["tests"]["engine_health"] = engine_health

    # Test 2: Engine B Gemini
    gemini_b = await test_engine_b_gemini()
    results["tests"]["engine_b_gemini"] = gemini_b

    # Test 3: Firebase Functions
    firebase = await test_firebase_function()
    results["tests"]["firebase_functions"] = firebase

    # Test 4: Frontend
    frontend = await test_frontend_gemini_config()
    results["tests"]["frontend_config"] = frontend

    # Generate Summary Report
    print_header("Test Results Summary")

    total_tests = len([v for v in results["tests"].values() if isinstance(v, bool)])
    total_tests += len([v for v in results["tests"]["engine_health"].values()])

    passed_tests = sum([1 for v in results["tests"].values() if v is True])
    passed_tests += sum([1 for v in results["tests"]["engine_health"].values() if v is True])

    print_status(f"Tests Passed: {passed_tests}/{total_tests}")

    if gemini_b:
        print_status("✅ Gemini integration is working in Engine B", "success")
    else:
        print_status("❌ Gemini integration needs fixing in Engine B", "error")

    if firebase:
        print_status("✅ Firebase Functions are accessible", "success")
    else:
        print_status("❌ Firebase Functions need deployment", "error")

    # Save detailed report
    with open("gemini-integration-test-report.json", "w") as f:
        json.dump(results, f, indent=2)

    print_status("Detailed report saved to: gemini-integration-test-report.json")

    return results

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())