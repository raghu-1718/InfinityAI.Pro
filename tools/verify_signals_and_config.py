"""Verification script for live signals and trade configurations across GCP Cloud Run services."""
import requests
import json
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ENGINE_A = "https://engine-a-313407263327.us-central1.run.app"
ENGINE_B = "https://engine-b-313407263327.us-central1.run.app"
ENGINE_C = "https://engine-c-313407263327.us-central1.run.app"

print("=" * 70)
print("🎯 LIVE SIGNALS & TRADE CONFIGURATION VERIFICATION")
print("=" * 70)

# 1. Test Trading Settings Schema & Strategies from Engine-C
print("\n⚙️ 1. ENGINE-C TRADING CONFIGURATIONS & STRATEGIES")
print("-" * 50)
try:
    url = f"{ENGINE_C}/api/trading-settings-schema"
    r = requests.get(url, timeout=10)
    print(f"Trading Settings Schema: HTTP {r.status_code}")
    if r.status_code == 200:
        schema = r.json().get('schema', {})
        print(f"  Total Configurable Parameters: {len(schema)}")
        for key in list(schema.keys())[:6]:
            field = schema[key]
            print(f"  - {key}: default = {field.get('default')}")
except Exception as e:
    print(f"Request Exception: {e}")

try:
    url = f"{ENGINE_C}/api/strategies/list"
    r = requests.get(url, timeout=10)
    print(f"\nOptions Strategies API: HTTP {r.status_code}")
    if r.status_code == 200:
        strats = r.json()
        print(f"  Available Automated Options Strategies: {len(strats)}")
        for s in strats[:5]:
            print(f"  - {s.get('name')}: {s.get('description', '')[:60]}")
except Exception as e:
    print(f"Request Exception: {e}")

# 2. Test Live Risk Scoring from Engine-A
print("\n\n🛡️ 2. ENGINE-A RISK SCORING & VAR EVALUATION")
print("-" * 50)
try:
    url = f"{ENGINE_A}/api/risk/evaluate"
    payload = {
        "portfolio_value": 50000.0,
        "positions": [{"symbol": "NIFTY", "quantity": 65, "entry_price": 24455.75, "current_price": 24460.00}],
        "daily_loss_pct": 0.5
    }
    r = requests.post(url, json=payload, timeout=10)
    print(f"Risk Evaluation API: HTTP {r.status_code}")
    if r.status_code == 200:
        risk_data = r.json()
        print(f"  Risk Level:        {risk_data.get('risk_level', 'NORMAL')}")
        print(f"  Risk Score:        {risk_data.get('risk_score')}/100")
        print(f"  1-Day 95% VaR:     ₹{risk_data.get('var_95')}")
        print(f"  Trade Allowed:     {risk_data.get('is_allowed')}")
except Exception as e:
    print(f"Request Exception: {e}")

# 3. Test Live Signals from Engine-B
print("\n\n📡 3. ENGINE-B LIVE SIGNAL GENERATION")
print("-" * 50)
symbols = ["NIFTY", "BANKNIFTY", "RELIANCE"]

for sym in symbols:
    try:
        url = f"{ENGINE_B}/api/v1/signal"
        payload = {"symbol": sym, "timeframe": "15m", "include_sentiment": True}
        r = requests.post(url, json=payload, timeout=15)
        print(f"\nInstrument: {sym}")
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Signal:      {data.get('signal')}")
            print(f"  Confidence:  {data.get('confidence')}%")
            print(f"  Price:       ₹{data.get('current_price')}")
            print(f"  Stop Loss:   ₹{data.get('stop_loss')}")
            print(f"  Target:      ₹{data.get('target')}")
            print(f"  Score:       {data.get('score')}")
            print("  Reasons:")
            for reason in data.get('reasons', [])[:3]:
                print(f"    - {reason}")
        else:
            print(f"  Response: {r.text[:150]}")
    except Exception as e:
        print(f"  Request Exception for {sym}: {e}")
    time.sleep(1)

print("\n" + "=" * 70)
print("✅ LIVE SIGNALS AND TRADE CONFIGURATION VERIFICATION COMPLETE")
print("=" * 70)
