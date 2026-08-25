"""
Complete End-to-End Integration Verification Script
Tests all options infrastructure components
"""
import requests
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ENGINE_C_URL = "https://engine-c-228557716858.asia-south1.run.app"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: HEALTH CHECK")
    print("="*70)
    try:
        r = requests.get(f"{ENGINE_C_URL}/health", timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"[PASS] Status: {data.get('status')}")
            print(f"       Version: {data.get('version')}")
            print(f"       Service: {data.get('service')}")
            return True
        else:
            print(f"[FAIL] Status code: {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_greeks():
    """Test Greeks calculator"""
    print("\n" + "="*70)
    print("TEST 2: GREEKS CALCULATOR")
    print("="*70)
    try:
        payload = {
            "spot_price": 18100,
            "strike_price": 18000,
            "time_to_expiry_days": 15,
            "implied_volatility": 0.15,
            "option_type": "call"
        }
        r = requests.post(f"{ENGINE_C_URL}/api/dhan/options/greeks/calculate", 
                         json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            greeks = data.get('greeks', {})
            print(f"[PASS] Theoretical Price: Rs. {greeks.get('theoretical_price')}")
            print(f"       Delta: {greeks.get('delta')}")
            print(f"       Gamma: {greeks.get('gamma')}")
            print(f"       Theta: {greeks.get('theta')}")
            print(f"       Vega: {greeks.get('vega')}")
            return True
        else:
            print(f"[FAIL] Status: {r.status_code}, Response: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_portfolio_greeks():
    """Test portfolio Greeks"""
    print("\n" + "="*70)
    print("TEST 3: PORTFOLIO GREEKS (IRON CONDOR)")
    print("="*70)
    try:
        payload = {
            "positions": [
                {"qty": 50, "spot_price": 18000, "strike_price": 17900, 
                 "time_to_expiry": 0.041, "implied_volatility": 0.15, "option_type": "put"},
                {"qty": -50, "spot_price": 18000, "strike_price": 17800, 
                 "time_to_expiry": 0.041, "implied_volatility": 0.16, "option_type": "put"},
                {"qty": 50, "spot_price": 18000, "strike_price": 18100, 
                 "time_to_expiry": 0.041, "implied_volatility": 0.15, "option_type": "call"},
                {"qty": -50, "spot_price": 18000, "strike_price": 18200, 
                 "time_to_expiry": 0.041, "implied_volatility": 0.16, "option_type": "call"}
            ]
        }
        r = requests.post(f"{ENGINE_C_URL}/api/dhan/options/greeks/portfolio", 
                         json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            pf = data.get('portfolio_greeks', {})
            print(f"[PASS] Portfolio Delta: {pf.get('portfolio_delta')}")
            print(f"       Portfolio Theta: {pf.get('portfolio_theta')}")
            print(f"       Portfolio Vega: {pf.get('portfolio_vega')}")
            return True
        else:
            print(f"[FAIL] Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_pcr():
    """Test PCR calculation"""
    print("\n" + "="*70)
    print("TEST 4: PUT-CALL RATIO (PCR)")
    print("="*70)
    try:
        payload = [
            {"strike": 17800, "call_oi": 10000, "put_oi": 8000},
            {"strike": 18000, "call_oi": 25000, "put_oi": 30000},
            {"strike": 18200, "call_oi": 12000, "put_oi": 15000}
        ]
        r = requests.post(f"{ENGINE_C_URL}/api/dhan/options/analytics/pcr", 
                         json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"[PASS] PCR: {data.get('pcr')}")
            print(f"       Sentiment: {data.get('sentiment')}")
            print(f"       Total Call OI: {data.get('total_call_oi'):,}")
            print(f"       Total Put OI: {data.get('total_put_oi'):,}")
            return True
        else:
            print(f"[FAIL] Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_max_pain():
    """Test Max Pain calculation"""
    print("\n" + "="*70)
    print("TEST 5: MAX PAIN ANALYSIS")
    print("="*70)
    try:
        payload = [
            {"strike": 17800, "call_oi": 10000, "put_oi": 8000},
            {"strike": 18000, "call_oi": 25000, "put_oi": 30000},
            {"strike": 18200, "call_oi": 12000, "put_oi": 15000}
        ]
        r = requests.post(f"{ENGINE_C_URL}/api/dhan/options/analytics/max-pain", 
                         json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            print(f"[PASS] Max Pain Strike: {data.get('max_pain_strike')}")
            print(f"       Total Value: {data.get('total_value_at_max_pain'):,}")
            return True
        else:
            print(f"[FAIL] Status: {r.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_local_strategies():
    """Test local strategy implementations"""
    print("\n" + "="*70)
    print("TEST 6: LOCAL OPTION STRATEGIES")
    print("="*70)
    try:
        import subprocess
        result = subprocess.run(['python', 'backend/options/strategies/advanced_strategies.py'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[PASS] Basic strategies (Bear Put, Straddle, Strangle, Butterfly)")
        else:
            print(f"[FAIL] {result.stderr[:200]}")
            return False
        
        result = subprocess.run(['python', 'backend/options/strategies/advanced_strategies_2.py'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[PASS] Advanced strategies (Calendar, Collar, Ratio)")
        else:
            print(f"[FAIL] {result.stderr[:200]}")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_iv_surface():
    """Test IV Surface calculator"""
    print("\n" + "="*70)
    print("TEST 7: IV SURFACE CALCULATOR")
    print("="*70)
    try:
        import subprocess
        result = subprocess.run(['python', 'backend/options/iv_surface.py'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and 'READY' in result.stdout:
            print("[PASS] IV Surface calculator working")
            return True
        else:
            print(f"[FAIL] {result.stderr[:200] if result.stderr else result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_scenario_analysis():
    """Test Scenario Analysis"""
    print("\n" + "="*70)
    print("TEST 8: SCENARIO ANALYSIS")
    print("="*70)
    try:
        import subprocess
        result = subprocess.run(['python', 'backend/options/scenario_analysis.py'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and 'READY' in result.stdout:
            print("[PASS] Scenario analysis engine working")
            return True
        else:
            print(f"[FAIL] {result.stderr[:200] if result.stderr else result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def test_backtester():
    """Test Backtesting Framework"""
    print("\n" + "="*70)
    print("TEST 9: BACKTESTING FRAMEWORK")
    print("="*70)
    try:
        import subprocess
        result = subprocess.run(['python', 'backend/options/backtester.py'], 
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and 'READY' in result.stdout:
            print("[PASS] Backtesting framework working")
            return True
        else:
            print(f"[FAIL] {result.stderr[:200] if result.stderr else result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False

def run_all_tests():
    """Run all verification tests"""
    print("="*70)
    print("  COMPLETE END-TO-END INTEGRATION VERIFICATION")
    print("  Engine C Options Infrastructure")
    print("="*70)
    
    results = {}
    
    # API Tests
    results['Health Check'] = test_health()
    results['Greeks Calculator'] = test_greeks()
    results['Portfolio Greeks'] = test_portfolio_greeks()
    results['PCR Calculation'] = test_pcr()
    results['Max Pain'] = test_max_pain()
    
    # Local Tests  
    results['Local Strategies'] = test_local_strategies()
    results['IV Surface'] = test_iv_surface()
    results['Scenario Analysis'] = test_scenario_analysis()
    results['Backtester'] = test_backtester()
    
    # Summary
    print("\n" + "="*70)
    print("  VERIFICATION SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n  SUCCESS: All components verified!")
    else:
        print(f"\n  WARNING: {total-passed} test(s) need attention")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
