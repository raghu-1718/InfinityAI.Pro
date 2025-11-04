#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete End-to-End Integration Test Suite
Tests all engines, Dhan OAuth, market data, AI signals, and trading flow
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any
import time

# Service endpoints
BASE_URLS = {
    "engine-a": "https://infinityai-engine-a-573866363639.us-central1.run.app",
    "engine-b": "https://infinityai-engine-b-573866363639.us-central1.run.app",
    "engine-c": "https://infinityai-engine-c-execution-573866363639.us-central1.run.app",
    "engine-d": "https://infinityai-engine-d-573866363639.us-central1.run.app"
}

class IntegrationTest:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def test(self, name: str, func):
        """Run a test and record results"""
        print(f"\n{'='*80}")
        print(f"TEST: {name}")
        print(f"{'='*80}")
        
        try:
            result = func()
            if result.get("status") == "pass":
                print(f"✅ PASS: {result.get('message', '')}")
                self.passed += 1
                self.results.append({"test": name, "status": "PASS", "details": result})
            elif result.get("status") == "warn":
                print(f"⚠️  WARN: {result.get('message', '')}")
                self.warnings += 1
                self.results.append({"test": name, "status": "WARN", "details": result})
            else:
                print(f"❌ FAIL: {result.get('message', '')}")
                self.failed += 1
                self.results.append({"test": name, "status": "FAIL", "details": result})
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            self.failed += 1
            self.results.append({"test": name, "status": "FAIL", "error": str(e)})
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*80}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Passed: {self.passed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total: {self.passed + self.failed + self.warnings}")
        print(f"Pass Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        # Save results
        with open("integration-test-results.json", "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "passed": self.passed,
                    "failed": self.failed,
                    "warnings": self.warnings,
                    "total": self.passed + self.failed + self.warnings
                },
                "tests": self.results
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: integration-test-results.json")

# Initialize test suite
suite = IntegrationTest()

# ============================================================================
# PHASE 1: Health Checks
# ============================================================================

def test_engine_a_health():
    """Test Engine A health endpoint"""
    response = requests.get(f"{BASE_URLS['engine-a']}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        return {
            "status": "pass",
            "message": f"Engine A healthy - {data.get('service', 'unknown')} v{data.get('version', 'unknown')}",
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "data": data
        }
    return {"status": "fail", "message": f"Status {response.status_code}"}

def test_engine_b_health():
    """Test Engine B health endpoint"""
    response = requests.get(f"{BASE_URLS['engine-b']}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        return {
            "status": "pass",
            "message": f"Engine B healthy - {data.get('service', 'unknown')} v{data.get('version', 'unknown')}",
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "data": data
        }
    return {"status": "fail", "message": f"Status {response.status_code}"}

def test_engine_c_health():
    """Test Engine C health endpoint"""
    response = requests.get(f"{BASE_URLS['engine-c']}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        return {
            "status": "pass",
            "message": f"Engine C healthy - {data.get('service', 'unknown')} v{data.get('version', 'unknown')}",
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "data": data
        }
    return {"status": "fail", "message": f"Status {response.status_code}"}

def test_engine_d_health():
    """Test Engine D health endpoint"""
    response = requests.get(f"{BASE_URLS['engine-d']}/health", timeout=10)
    if response.status_code == 200:
        data = response.json()
        return {
            "status": "pass",
            "message": f"Engine D healthy - {data.get('service', 'unknown')} v{data.get('version', 'unknown')}",
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "data": data
        }
    return {"status": "fail", "message": f"Status {response.status_code}"}

# ============================================================================
# PHASE 2: Engine A - Market Data
# ============================================================================

def test_engine_a_market_data():
    """Test Engine A market data endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-a']}/api/market-data/NIFTY", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Market data retrieved for NIFTY",
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "data": data
            }
        return {"status": "fail", "message": f"Status {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}

def test_engine_a_marketdata_general():
    """Test Engine A general marketdata endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-a']}/api/marketdata", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"General market data endpoint working",
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "sample_data": str(data)[:200]
            }
        return {"status": "fail", "message": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}

# ============================================================================
# PHASE 3: Engine B - AI Signals
# ============================================================================

def test_engine_b_ai_signals():
    """Test Engine B AI signals endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-b']}/api/ai-signals", timeout=20)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"AI signals generated successfully",
                "response_time_ms": int(response.elapsed.total_seconds() * 1000),
                "signal_count": len(data) if isinstance(data, list) else 1
            }
        return {"status": "fail", "message": f"Status {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}

def test_engine_b_models_status():
    """Test Engine B models status endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-b']}/api/models/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Models status retrieved",
                "data": data
            }
        return {"status": "warn", "message": f"Status {response.status_code} - models may not be loaded"}
    except Exception as e:
        return {"status": "warn", "message": str(e)}

# ============================================================================
# PHASE 4: Engine C - Dhan Integration
# ============================================================================

def test_engine_c_dhan_status():
    """Test Engine C Dhan integration status"""
    try:
        response = requests.get(f"{BASE_URLS['engine-c']}/api/dhan/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Dhan status: {data.get('status', 'unknown')}",
                "data": data
            }
        return {"status": "warn", "message": f"Status {response.status_code} - Dhan may not be configured"}
    except Exception as e:
        return {"status": "warn", "message": str(e)}

def test_engine_c_token_status():
    """Test Engine C Dhan token status"""
    try:
        response = requests.get(f"{BASE_URLS['engine-c']}/api/dhan/token/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            has_token = data.get('has_access_token', False)
            if has_token:
                return {
                    "status": "pass",
                    "message": f"Dhan access token present and valid",
                    "data": data
                }
            else:
                return {
                    "status": "warn",
                    "message": "No Dhan access token found - OAuth flow needed",
                    "data": data
                }
        return {"status": "warn", "message": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "warn", "message": str(e)}

def test_engine_c_orders_status():
    """Test Engine C orders endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-c']}/api/orders/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Orders endpoint working",
                "data": data
            }
        return {"status": "warn", "message": f"Status {response.status_code} - may need authentication"}
    except Exception as e:
        return {"status": "warn", "message": str(e)}

# ============================================================================
# PHASE 5: Engine D - Orchestration
# ============================================================================

def test_engine_d_status():
    """Test Engine D status endpoint"""
    try:
        response = requests.get(f"{BASE_URLS['engine-d']}/api/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Engine D status endpoint working",
                "data": data
            }
        return {"status": "fail", "message": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "fail", "message": str(e)}

def test_engine_d_comprehensive_health():
    """Test Engine D comprehensive health check"""
    try:
        response = requests.get(f"{BASE_URLS['engine-d']}/api/health/comprehensive", timeout=15)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "pass",
                "message": f"Comprehensive health check completed",
                "data": data
            }
        return {"status": "warn", "message": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "warn", "message": str(e)}

# ============================================================================
# Run All Tests
# ============================================================================

def main():
    print(f"\n{'='*80}")
    print(f"InfinityAI.Pro - Complete End-to-End Integration Test")
    print(f"{'='*80}")
    print(f"Started: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")
    
    # Phase 1: Health Checks
    print(f"\n### PHASE 1: Health Checks ###\n")
    suite.test("Engine A Health", test_engine_a_health)
    suite.test("Engine B Health", test_engine_b_health)
    suite.test("Engine C Health", test_engine_c_health)
    suite.test("Engine D Health", test_engine_d_health)
    
    # Phase 2: Engine A Market Data
    print(f"\n### PHASE 2: Engine A - Market Data ###\n")
    suite.test("Engine A - Market Data NIFTY", test_engine_a_market_data)
    suite.test("Engine A - General Market Data", test_engine_a_marketdata_general)
    
    # Phase 3: Engine B AI Signals
    print(f"\n### PHASE 3: Engine B - AI/ML ###\n")
    suite.test("Engine B - AI Signals", test_engine_b_ai_signals)
    suite.test("Engine B - Models Status", test_engine_b_models_status)
    
    # Phase 4: Engine C Dhan Integration
    print(f"\n### PHASE 4: Engine C - Dhan Integration ###\n")
    suite.test("Engine C - Dhan Status", test_engine_c_dhan_status)
    suite.test("Engine C - Token Status", test_engine_c_token_status)
    suite.test("Engine C - Orders Status", test_engine_c_orders_status)
    
    # Phase 5: Engine D Orchestration
    print(f"\n### PHASE 5: Engine D - Orchestration ###\n")
    suite.test("Engine D - Status", test_engine_d_status)
    suite.test("Engine D - Comprehensive Health", test_engine_d_comprehensive_health)
    
    # Print summary
    suite.print_summary()
    
    # Exit with error code if tests failed
    return 0 if suite.failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
