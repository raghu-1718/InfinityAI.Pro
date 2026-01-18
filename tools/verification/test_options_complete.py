"""
Comprehensive End-to-End Test Suite for Options Infrastructure
Tests all new features in DhanHQ sandbox environment
"""
import requests
import time
from datetime import datetime
import json

# Sandbox Configuration
SANDBOX_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MjE1MDY0Iiwid2ViaG9va1VybCI6Imh0dHBzOi8vZW5naW5lLWMtM2Fjb2JnZDNxYS11Yy5hLnJ1bi5hcHAvYXBpL2dhbi9wb3N0YmFjayIsImlzcyI6ImRoYW4iLCJleHAiOjE3NjkwMjI3MTR9.qUauBEyDHG1uZ0naTVOk22kBZUSaHKu_q6zx5fOEf8IgHCFB2HNaOhHaPCZdoDvHJICc2RZkfPJVgc5VlN0yYw"
SANDBOX_CLIENT_ID = "2508215064"
ENGINE_C_URL = "https://engine-c-228557716858.us-central1.run.app"  # Update after deployment

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_greeks_calculator():
    """Test Greeks calculation API"""
    print_section("TEST 1: GREEKS CALCULATOR")
    
    url = f"{ENGINE_C_URL}/api/dhan/options/greeks/calculate"
    payload = {
        "spot_price": 18100,
        "strike_price": 18000,
        "time_to_expiry_days": 15,
        "implied_volatility": 0.15,
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            greeks = data.get('greeks', {})
            
            print(f"[OK] Greeks calculated successfully")
            print(f"  Spot: {payload['spot_price']}, Strike: {payload['strike_price']}")
            print(f"  Delta: {greeks.get('delta')}")
            print(f"  Gamma: {greeks.get('gamma')}")
            print(f"  Theta: {greeks.get('theta')}")
            print(f"  Vega: {greeks.get('vega')}")
            print(f"  Theoretical Price: Rs. {greeks.get('theoretical_price')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def test_portfolio_greeks():
    """Test portfolio Greeks aggregation"""
    print_section("TEST 2: PORTFOLIO GREEKS (IRON CONDOR)")
    
    url = f"{ENGINE_C_URL}/api/dhan/options/greeks/portfolio"
    
    # Iron Condor positions
    payload = {
        "positions": [
            {
                "qty": 50,
                "spot_price": 18000,
                "strike_price": 17900,
                "time_to_expiry": 15/365,
                "implied_volatility": 0.15,
                "option_type": "put"
            },
            {
                "qty": -50,
                "spot_price": 18000,
                "strike_price": 17800,
                "time_to_expiry": 15/365,
                "implied_volatility": 0.16,
                "option_type": "put"
            },
            {
                "qty": 50,
                "spot_price": 18000,
                "strike_price": 18100,
                "time_to_expiry": 15/365,
                "implied_volatility": 0.15,
                "option_type": "call"
            },
            {
                "qty": -50,
                "spot_price": 18000,
                "strike_price": 18200,
                "time_to_expiry": 15/365,
                "implied_volatility": 0.16,
                "option_type": "call"
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pf_greeks = data.get('portfolio_greeks', {})
            
            print(f"[OK] Portfolio Greeks calculated")
            print(f"  Portfolio Delta: {pf_greeks.get('portfolio_delta')}")
            print(f"  Portfolio Gamma: {pf_greeks.get('portfolio_gamma')}")
            print(f"  Portfolio Theta: {pf_greeks.get('portfolio_theta')}")
            print(f"  Portfolio Vega: {pf_greeks.get('portfolio_vega')}")
            print(f"  Positions: {pf_greeks.get('num_positions')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def test_pcr_calculation():
    """Test Put-Call Ratio calculation"""
    print_section("TEST 3: PUT-CALL RATIO (PCR)")
    
    url = f"{ENGINE_C_URL}/api/dhan/options/analytics/pcr"
    
    # Sample option chain data
    payload = [
        {"strike": 17800, "call_oi": 10000, "put_oi": 8000},
        {"strike": 17900, "call_oi": 15000, "put_oi": 12000},
        {"strike": 18000, "call_oi": 25000, "put_oi": 30000},
        {"strike": 18100, "call_oi": 18000, "put_oi": 22000},
        {"strike": 18200, "call_oi": 12000, "put_oi": 15000}
    ]
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"[OK] PCR calculated")
            print(f"  PCR: {data.get('pcr')}")
            print(f"  Total Call OI: {data.get('total_call_oi'):,}")
            print(f"  Total Put OI: {data.get('total_put_oi'):,}")
            print(f"  Sentiment: {data.get('sentiment')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def test_max_pain():
    """Test Max Pain calculation"""
    print_section("TEST 4: MAX PAIN ANALYSIS")
    
    url = f"{ENGINE_C_URL}/api/dhan/options/analytics/max-pain"
    
    payload = [
        {"strike": 17800, "call_oi": 10000, "put_oi": 8000},
        {"strike": 17900, "call_oi": 15000, "put_oi": 12000},
        {"strike": 18000, "call_oi": 25000, "put_oi": 30000},
        {"strike": 18100, "call_oi": 18000, "put_oi": 22000},
        {"strike": 18200, "call_oi": 12000, "put_oi": 15000}
    ]
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"[OK] Max Pain calculated")
            print(f"  Max Pain Strike: {data.get('max_pain_strike')}")
            print(f"  Total Value at Max Pain: {data.get('total_value_at_max_pain'):,}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def test_atm_identification():
    """Test ATM strike identification"""
    print_section("TEST 5: ATM STRIKE IDENTIFICATION")
    
    url = f"{ENGINE_C_URL}/api/dhan/options/analytics/atm-strike"
    
    payload = [
        {"strike": 17700}, {"strike": 17800}, {"strike": 17900},
        {"strike": 18000}, {"strike": 18100}, {"strike": 18200},
        {"strike": 18300}
    ]
    
    params = {"spot_price": 18050}
    
    try:
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"[OK] ATM identified")
            print(f"  Spot Price: {data.get('spot_price')}")
            print(f"  ATM Strike: {data.get('atm_strike')}")
            print(f"  Distance: {data.get('distance_from_spot')}")
            print(f"  ITM Calls: {data.get('itm_call_strikes')}")
            print(f"  OTM Calls: {data.get('otm_call_strikes')}")
            return True
        else:
            print(f"[FAIL] Status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False

def test_option_strategies():
    """Test option strategy calculations"""
    print_section("TEST 6: OPTION STRATEGIES")
    
    from backend.options.strategies.advanced_strategies import (
        BearPutSpreadStrategy, LongStraddleStrategy
    )
    
    print("\n[TEST] Bear Put Spread")
    strategy = BearPutSpreadStrategy(
        buy_strike=3500,
        sell_strike=3400,
        buy_premium=80,
        sell_premium=40,
        quantity=100
    )
    summary = strategy.get_strategy_summary()
    print(f"  Max Profit: Rs. {summary['max_profit']}")
    print(f"  Max Loss: Rs. {summary['max_loss']}")
    print(f"  Risk/Reward: {summary['risk_reward_ratio']}")
    
    print("\n[TEST] Long Straddle")
    strategy2 = LongStraddleStrategy(
        strike=18000,
        call_premium=100,
        put_premium=100,
        quantity=50
    )
    summary2 = strategy2.get_strategy_summary()
    print(f"  Breakeven Range: {summary2['breakeven_lower']} - {summary2['breakeven_upper']}")
    print(f"  Max Loss: Rs. {summary2['max_loss']}")
    
    return True

def test_health_check():
    """Test Engine C health and version"""
    print_section("TEST 0: ENGINE C HEALTH CHECK")
    
    try:
        response = requests.get(f"{ENGINE_C_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"[OK] Engine C is healthy")
            print(f"  Service: {data.get('service')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Status: {data.get('status')}")
            return True
        else:
            print(f"[FAIL] Health check failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"[ERROR] Cannot reach Engine C: {str(e)}")
        return False

def run_all_tests():
    """Run comprehensive test suite"""
    print("=" * 80)
    print("  COMPREHENSIVE OPTIONS INFRASTRUCTURE TEST SUITE")
    print("  Engine C: v3.9-options-analytics")
    print("=" * 80)
    
    results = {
        'Health Check': test_health_check(),
        'Greeks Calculator': test_greeks_calculator(),
        'Portfolio Greeks': test_portfolio_greeks(),
        'PCR Calculation': test_pcr_calculation(),
        'Max Pain': test_max_pain(),
        'ATM Identification': test_atm_identification(),
        'Option Strategies': test_option_strategies()
    }
    
    # Summary
    print_section("TEST RESULTS SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n  [SUCCESS] All tests passed! Options infrastructure is working.")
    else:
        print(f"\n  [WARNING] {total-passed} test(s) failed. Review logs above.")
    
    return results

if __name__ == "__main__":
    run_all_tests()
