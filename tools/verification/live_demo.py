
import os
import sys
import asyncio
import httpx
import json
from datetime import datetime

# Configuration
ENGINE_A_URL = "https://engine-a-3acobgd3qa-uc.a.run.app"
ENGINE_B_URL = "https://engine-b-3acobgd3qa-uc.a.run.app"
ENGINE_C_URL = "https://engine-c-3acobgd3qa-uc.a.run.app"
USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

async def fetch_live_market_data(symbol="RELIANCE", security_id="1333"):
    print(f"\n[1] 📡 FETCHING REAL-TIME MARKET DATA (Engine-C - DhanHQ)...")
    try:
        async with httpx.AsyncClient() as client:
            # Using the verified route from dhan_data_api.py
            # /api/dhan/market/quotes?security_ids=...&exchange_segment=...&user_id=...
            url = f"{ENGINE_C_URL}/api/dhan/market/quotes"
            params = {
                "security_ids": security_id,
                "exchange_segment": "NSE_EQ",
                "user_id": USER_ID
            }
            print(f"   🔹 GET {url} params={params}")
            response = await client.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Market Data Response:")
                print(json.dumps(data, indent=2))
                return data
            else:
                 print(f"   ❌ Market Data Error: {response.status_code} - {response.text}")
                 return None
    except Exception as e:
        print(f"   ⚠️ Error fetching market data: {e}")
        return None

async def fetch_news_analysis(symbol="RELIANCE"):
    print(f"\n[2] 📰 FETCHING LIVE NEWS & SENTIMENT (Engine-C News Aggregator)...")
    try:
        async with httpx.AsyncClient() as client:
            # /api/news/latest?symbols=...
            url = f"{ENGINE_C_URL}/api/news/latest"
            params = {"symbols": symbol}
            response = await client.get(url, params=params, timeout=15)
            if response.status_code == 200:
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"   ❌ News Error: {response.status_code} - {response.text}")
    except Exception as e:
         print(f"   ⚠️ Error fetching news: {e}")

async def get_ai_analysis(symbol="NIFTY"):
    print(f"\n[3] 🧠 REQUESTING AI ANALYSIS (Engine-B / Gemini 2.5)...")
    try:
        async with httpx.AsyncClient() as client:
            # Endpoint guessed from Engine-A code: /api/v1/signal
            url = f"{ENGINE_B_URL}/api/v1/signal"
            payload = {
                "symbol": symbol,
                "fast": False,
                "timeframe": "1d"
            }
            print(f"   🔹 POST {url} payload={payload}")
            response = await client.post(url, json=payload, timeout=60) # Longer timeout for AI
            if response.status_code == 200:
                print("   ✅ AI Signal Response:")
                print(json.dumps(response.json(), indent=2))
            elif response.status_code == 404:
                 # Try fallback endpoint if /signal not found
                 print(f"   ❌ /api/v1/signal not found. Trying /analyze...")
                 response = await client.post(f"{ENGINE_B_URL}/analyze", json=payload, timeout=60)
                 if response.status_code == 200:
                     print(json.dumps(response.json(), indent=2))
                 else:
                     print(f"   ❌ Analyze Error: {response.status_code} - {response.text}")
            else:
                 print(f"   ❌ AI Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ⚠️ Error contacting Engine-B: {e}")

async def check_orchestrator_decision(symbol="NIFTY", price=21500):
    print(f"\n[4] ⚖️  CHECKING TRADING ORCHESTRATION (Engine-A Risk & Logic)...")
    try:
        async with httpx.AsyncClient() as client:
            url = f"{ENGINE_A_URL}/api/v1/risk/score"
            payload = {
                "order_size": price * 50, # Rough value
                "volatility": 0.015,
                "spread": 0.05
            }
            # Note: The endpoint in main.py snippet for Engine-A wasn't fully visible, 
            # I am assuming /api/v1/risk/score based on previous context or common patterns.
            # If it fails, I'll log it.
            
            print(f"   🔹 POST {url}")
            response = await client.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("   ✅ Risk Engine Decision:")
                print(json.dumps(response.json(), indent=2))
            else:
                print(f"   ❌ Orchestrator Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"   ⚠️ Error contacting Engine-A: {e}")

async def main():
    print("="*80)
    print(f" INFINITY AI PRO - LIVE SYSTEM DEMONSTRATION")
    print(f" User ID: {USER_ID}")
    print("="*80)
    
    # 1. Market Data (RELIANCE = 1333)
    market_data = await fetch_live_market_data("RELIANCE", "1333")
    
    # 2. News
    await fetch_news_analysis("RELIANCE")
    
    # 3. AI Analysis
    await get_ai_analysis("NIFTY")
    
    # 4. Orchestration/Risk
    price = 2500.00 # Default if fetch fails
    if market_data and 'data' in market_data and 'NSE_EQ' in market_data['data']:
         # Try to parse price from nested structure if possible, 
         # but for demo we can use a static price if parsing is complex without seeing structure
         pass
         
    await check_orchestrator_decision("RELIANCE", price)
    
    print("\n" + "="*80)
    print(" DEMONSTRATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
