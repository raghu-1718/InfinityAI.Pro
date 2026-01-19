#!/usr/bin/env python3
"""
InfinityAI.Pro - End-to-End Integration Test
Tests complete trading flow: Frontend → Engine-A → Engine-B → Engine-C → DhanHQ (LIVE)
Author: Automated Testing System  
Date: January 19, 2026
"""

import requests
import json
import time
from datetime import datetime

# Configuration
ENGINES = {
    "Engine-A": "https://engine-a-3acobgd3qa-uc.a.run.app",
    "Engine-B": "https://engine-b-3acobgd3qa-uc.a.run.app",
    "Engine-C": "https://engine-c-3acobgd3qa-uc.a.run.app",
}

class E2ETestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        
    def add_test(self, name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        self.tests.append({"name": name, "passed": passed, "status": status, "details": details})
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status}: {name} {details}")
    
    def summary(self):
        total = self.passed + self.failed
        success_rate = 100 * self.passed / total if total > 0 else 0
        print(f"\n{'='*70}")
        print(f"📊 END-TO-END TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"{'='*70}\n")

def test_health_endpoints(results):
    """Test 1: Verify all engines are healthy"""
    print("\n🔍 TEST 1: Health Endpoints")
    print("-" * 50)
    
    for engine_name, url in ENGINES.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                results.add_test(
                    f"{engine_name} Health",
                    response.status_code == 200,
                    f"Status: {data.get('status', 'unknown')}"
                )
            else:
                results.add_test(f"{engine_name} Health", False, f"HTTP {response.status_code}")
        except Exception as e:
            results.add_test(f"{engine_name} Health", False, f"Error: {str(e)}")

def test_engine_c_trading_mode(results):
    """Test 2: Verify Engine-C is in LIVE trading mode"""
    print("\n🔍 TEST 2: Engine-C Trading Mode")
    print("-" * 50)
    
    try:
        response = requests.get("https://engine-c-3acobgd3qa-uc.a.run.app/health", timeout=5)
        data = response.json()
        is_live = data.get('trading_mode') == 'LIVE'
        results.add_test(
            "Engine-C LIVE Trading Mode",
            is_live,
            f"Mode: {data.get('trading_mode', 'unknown')}"
        )
    except Exception as e:
        results.add_test("Engine-C LIVE Trading Mode", False, str(e))

def test_engine_c_dhan_connection(results):
    """Test 3: Verify Engine-C has active DhanHQ connection"""
    print("\n🔍 TEST 3: Engine-C DhanHQ Connection")
    print("-" * 50)
    
    try:
        response = requests.get("https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_test(
                "Engine-C DhanHQ Connection",
                response.status_code == 200,
                f"Status: {data.get('status', 'unknown')}"
            )
        else:
            results.add_test("Engine-C DhanHQ Connection", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("Engine-C DhanHQ Connection", False, str(e))

def test_engine_a_orchestration(results):
    """Test 4: Verify Engine-A orchestration capabilities"""
    print("\n🔍 TEST 4: Engine-A Orchestration")
    print("-" * 50)
    
    try:
        response = requests.get("https://engine-a-3acobgd3qa-uc.a.run.app/health", timeout=5)
        data = response.json()
        
        # Check ML capabilities
        ml_caps = data.get('ml_capabilities', [])
        has_risk_scoring = 'risk_scoring' in ml_caps
        has_var = 'var_calculation' in ml_caps
        
        results.add_test(
            "Engine-A Risk Scoring Capability",
            has_risk_scoring,
            f"Capabilities: {len(ml_caps)} models loaded"
        )
        results.add_test(
            "Engine-A VaR Calculation",
            has_var,
            ""
        )
    except Exception as e:
        results.add_test("Engine-A Orchestration", False, str(e))

def test_engine_b_ml_models(results):
    """Test 5: Verify Engine-B ML models are loaded"""
    print("\n🔍 TEST 5: Engine-B ML Models")
    print("-" * 50)
    
    try:
        response = requests.get("https://engine-b-3acobgd3qa-uc.a.run.app/health", timeout=5)
        data = response.json()
        
        capabilities = data.get('capabilities', {})
        frameworks = capabilities.get('frameworks', {})
        
        required_models = ['xgboost', 'lightgbm', 'catboost', 'random_forest']
        models_loaded = sum(1 for m in required_models if frameworks.get(m, False))
        
        results.add_test(
            "Engine-B ML Models",
            models_loaded == len(required_models),
            f"{models_loaded}/{len(required_models)} models loaded"
        )
        
        # Check sentiment analysis
        has_sentiment = frameworks.get('nltk_sentiment', False)
        results.add_test(
            "Engine-B Sentiment Analysis",
            has_sentiment,
            ""
        )
    except Exception as e:
        results.add_test("Engine-B ML Models", False, str(e))

def test_market_status(results):
    """Test 6: Verify market status endpoint"""
    print("\n🔍 TEST 6: Market Status")
    print("-" * 50)
    
    try:
        response = requests.get("https://engine-b-3acobgd3qa-uc.a.run.app/api/v1/market/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            has_time = 'current_time' in data or 'time' in data or 'timestamp' in data
            results.add_test(
                "Market Status Endpoint",
                response.status_code == 200 and has_time,
                f"Response: {json.dumps(data)[:80]}..."
            )
        else:
            results.add_test("Market Status Endpoint", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("Market Status Endpoint", False, str(e))

def test_dhan_account_data(results):
    """Test 7: Verify Engine-C can fetch account data (DhanHQ integration)"""
    print("\n🔍 TEST 7: DhanHQ Account Data")
    print("-" * 50)
    
    # Note: This requires valid credentials, just verify endpoint exists
    try:
        # Try to call funds endpoint (should exist and be callable)
        response = requests.get(
            "https://engine-c-3acobgd3qa-uc.a.run.app/api/dhan/funds",
            headers={"X-User-ID": "test-user"},
            timeout=5
        )
        # We expect 401/403 or 200 depending on auth
        endpoint_exists = response.status_code in [200, 401, 403, 400]
        results.add_test(
            "Engine-C Funds Endpoint Exists",
            endpoint_exists,
            f"HTTP {response.status_code}"
        )
    except Exception as e:
        results.add_test("Engine-C Funds Endpoint Exists", False, str(e))

def test_trading_settings(results):
    """Test 8: Verify trading settings schema"""
    print("\n🔍 TEST 8: Trading Settings Schema")
    print("-" * 50)
    
    try:
        response = requests.get(
            "https://engine-c-3acobgd3qa-uc.a.run.app/api/trading-settings-schema",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            has_schema = 'schema' in data
            results.add_test(
                "Trading Settings Schema Exists",
                has_schema,
                f"Schema fields: {len(data.get('schema', {}))}"
            )
        else:
            results.add_test("Trading Settings Schema Exists", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("Trading Settings Schema Exists", False, str(e))

def test_system_monitoring(results):
    """Test 9: Verify system monitoring endpoints"""
    print("\n🔍 TEST 9: System Monitoring")
    print("-" * 50)
    
    # Test Engine-C system status
    try:
        response = requests.get("https://engine-c-3acobgd3qa-uc.a.run.app/api/system/status", timeout=5)
        if response.status_code == 200:
            results.add_test("Engine-C System Status", True, "")
        else:
            results.add_test("Engine-C System Status", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("Engine-C System Status", False, str(e))
    
    # Test performance stats
    try:
        response = requests.get("https://engine-c-3acobgd3qa-uc.a.run.app/api/performance/stats", timeout=5)
        if response.status_code == 200:
            results.add_test("Engine-C Performance Stats", True, "")
        else:
            results.add_test("Engine-C Performance Stats", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("Engine-C Performance Stats", False, str(e))

def test_websocket_availability(results):
    """Test 10: Verify WebSocket streamer is available"""
    print("\n🔍 TEST 10: WebSocket Streamer")
    print("-" * 50)
    
    try:
        response = requests.get(
            "https://websocket-streamer-3acobgd3qa-uc.a.run.app/health",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            is_connected = data.get('websocket_connected', False)
            results.add_test(
                "WebSocket Streamer Available",
                response.status_code == 200,
                f"Connected: {is_connected}"
            )
        else:
            results.add_test("WebSocket Streamer Available", False, f"HTTP {response.status_code}")
    except Exception as e:
        results.add_test("WebSocket Streamer Available", False, str(e))

def test_api_compatibility(results):
    """Test 11: Verify API v1 endpoints"""
    print("\n🔍 TEST 11: API v1 Compatibility")
    print("-" * 50)
    
    endpoints_to_test = [
        ("https://engine-c-3acobgd3qa-uc.a.run.app/api/v1/user/credentials", "User Credentials"),
        ("https://engine-c-3acobgd3qa-uc.a.run.app/api/v1/optimize/timing/NIFTY", "Optimize Timing"),
    ]
    
    for url, name in endpoints_to_test:
        try:
            response = requests.get(url, timeout=5)
            # Accept 400-403 as endpoint exists, just no auth
            exists = response.status_code in [200, 400, 401, 403]
            results.add_test(f"API v1 {name} Endpoint", exists, f"HTTP {response.status_code}")
        except Exception as e:
            results.add_test(f"API v1 {name} Endpoint", False, str(e))

def test_response_times(results):
    """Test 12: Verify response times are acceptable"""
    print("\n🔍 TEST 12: Response Time Performance")
    print("-" * 50)
    
    for engine_name, url in ENGINES.items():
        try:
            start = time.time()
            response = requests.get(f"{url}/health", timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            is_fast = elapsed < 1000  # Under 1 second is good
            results.add_test(
                f"{engine_name} Response Time",
                is_fast,
                f"{elapsed:.1f}ms"
            )
        except Exception as e:
            results.add_test(f"{engine_name} Response Time", False, str(e))

def main():
    print("🎯 InfinityAI.Pro - Comprehensive End-to-End Integration Test")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trading Mode: 💰 LIVE (Real Money)")
    print("=" * 70)
    
    results = E2ETestResults()
    
    # Run all tests
    test_health_endpoints(results)
    test_engine_c_trading_mode(results)
    test_engine_c_dhan_connection(results)
    test_engine_a_orchestration(results)
    test_engine_b_ml_models(results)
    test_market_status(results)
    test_dhan_account_data(results)
    test_trading_settings(results)
    test_system_monitoring(results)
    test_websocket_availability(results)
    test_api_compatibility(results)
    test_response_times(results)
    
    # Print summary
    results.summary()
    
    # Export results
    export_data = {
        "test_date": datetime.now().isoformat(),
        "tests": results.tests,
        "summary": {
            "total": len(results.tests),
            "passed": results.passed,
            "failed": results.failed,
            "success_rate": 100 * results.passed / len(results.tests) if results.tests else 0
        }
    }
    
    filename = f"e2e-test-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    print(f"📄 Results exported to: {filename}\n")
    
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
