"""
Real-Time Gemini Live Verification with Full Institutional Output
================================================================
Executes:
1. Direct GCP Vertex AI Gemini Generation via ADC (us-central1).
2. Live Cloud Run Engine B Gemini Macro Intelligence Endpoint.
3. Quant Options & Indian Capital Markets Context Synthesis.
"""

import os
import sys
import time
import json
import requests

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
LOCATION_ID = "us-central1"
ENGINE_B_URL = "https://engine-b-313407263327.asia-south1.run.app"

def verify_vertex_gemini_direct():
    print("=" * 85)
    print("  PROBE 1: DIRECT VERTEX AI GEMINI GENERATION (ADC - US-CENTRAL1)")
    print("=" * 85)
    
    prompt = (
        "You are the Chief Quantitative Strategist for InfinityAI.Pro analyzing Indian Capital Markets.\n"
        "Analyze the current macroeconomic regime for NIFTY 50 and BANKNIFTY index options trading:\n"
        "1. Current Market Regime & Volatility Expectation (India VIX at 14.5).\n"
        "2. Key Gamma Exposure (GEX) implications around 24,200 Call Wall and 23,900 Put Floor.\n"
        "3. Recommended Option Strategy (Long ITM-1 Call vs Put with Morning Expansion Regime).\n"
        "Provide a concise, institutional 3-bullet briefing."
    )
    
    print(f"Project ID:    {PROJECT_ID}")
    print(f"Routing Loc:   {LOCATION_ID}")
    print(f"Model ID:      gemini-2.5-flash (Vertex AI Production Catalog)")
    print(f"Prompt Sent:\n---\n{prompt}\n---")
    
    t0 = time.time()
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION_ID)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2048,
                thinking_config=types.ThinkingConfig(thinking_budget=256)
            )
        )
        latency_ms = round((time.time() - t0) * 1000, 2)
        print(f"\nStatus:        SUCCESS (HTTP 200 OK)")
        print(f"Latency:       {latency_ms} ms")
        print("\n--- GEMINI GENERATED OUTPUT ---")
        print(response.text.strip())
        print("-------------------------------")
        return True, response.text.strip(), latency_ms
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 2)
        print(f"\nStatus:        FAILED ({latency_ms} ms): {e}")
        return False, str(e), latency_ms

def verify_engine_b_gemini_endpoint():
    print("\n" + "=" * 85)
    print("  PROBE 2: LIVE CLOUD RUN ENGINE B GEMINI MACRO-SIGNAL ENDPOINT")
    print("=" * 85)
    
    url = f"{ENGINE_B_URL}/api/v1/gemini/macro-signal/NIFTY"
    print(f"Target URL:    {url}")
    
    t0 = time.time()
    try:
        resp = requests.get(url, timeout=15)
        latency_ms = round((time.time() - t0) * 1000, 2)
        print(f"HTTP Status:   {resp.status_code}")
        print(f"Latency:       {latency_ms} ms")
        print("\n--- ENGINE B GEMINI MACRO RESPONSE JSON ---")
        data = resp.json()
        print(json.dumps(data, indent=2))
        print("------------------------------------------")
        return True, data, latency_ms
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 2)
        print(f"FAILED ({latency_ms} ms): {e}")
        return False, str(e), latency_ms

if __name__ == "__main__":
    p1_ok, p1_out, p1_lat = verify_vertex_gemini_direct()
    p2_ok, p2_out, p2_lat = verify_engine_b_gemini_endpoint()
    
    print("\n" + "=" * 85)
    print("  VERIFICATION SUMMARY")
    print("=" * 85)
    print(f"  Probe 1 (Direct Vertex AI Gemini): {'PASSED' if p1_ok else 'FAILED'} ({p1_lat} ms)")
    print(f"  Probe 2 (Cloud Run Engine B API):  {'PASSED' if p2_ok else 'FAILED'} ({p2_lat} ms)")
    print("=" * 85)
