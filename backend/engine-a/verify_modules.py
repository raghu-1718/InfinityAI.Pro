"""
Verification Suite for InfinityAI.Pro Backend Integration
Tests:
  1. Restricted Options Open Interest (OI) Acceleration Tracker (SFATM Hardening)
  2. Dynamic Microstructure Slippage Function
  3. Real Macro News Sentiment Ingestor with live RSS feeds & SentimentSafetyGate
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

def test_oi_acceleration_tracker():
    print("=" * 70)
    print("1. TESTING: Restricted Options Open Interest (OI) Acceleration Tracker (SFATM)")
    print("=" * 70)
    from src.services.options_oi_acceleration_tracker import OI_ACCELERATION_TRACKER

    symbol = "NIFTY"
    spot = 24219.05  # ATM is 24200, Step is 50 -> Scan window strictly [24050, 24350]

    # Initial baseline strikes (t0) including noisy far-OTM strikes (24850, 24900)
    strikes_t0 = [
        {"strike": 24050, "call_oi": 1500000, "put_oi": 6000000},
        {"strike": 24100, "call_oi": 2000000, "put_oi": 7500000},
        {"strike": 24150, "call_oi": 2500000, "put_oi": 5000000},
        {"strike": 24200, "call_oi": 4000000, "put_oi": 4500000}, # ATM
        {"strike": 24250, "call_oi": 6000000, "put_oi": 3000000},
        {"strike": 24300, "call_oi": 7500000, "put_oi": 2000000},
        {"strike": 24350, "call_oi": 8000000, "put_oi": 1500000},
        # Far OTM noisy strikes (>600 pts out of the money)
        {"strike": 24850, "call_oi": 500000, "put_oi": 20000},
        {"strike": 24900, "call_oi": 300000, "put_oi": 10000},
    ]

    r0 = OI_ACCELERATION_TRACKER.evaluate_oi_velocity(symbol, spot, strikes_t0)
    print(f"[*] T0 Baseline: ATM={r0['atm_strike']}, Window={r0['scan_window']}, Walls={r0['active_walls']}")
    assert r0["atm_strike"] == 24200
    assert r0["scan_window"] == [24050, 24350]
    assert r0["conviction_multiplier"] == 1.00

    # Simulate t1:
    # 1. Noisy far-OTM jump at 24850 (+60% Delta OI) and 24900 (+80% Delta OI)
    # 2. Legitimate near-the-money Call Wall at 24250 (+33.3% Delta OI) inside window
    strikes_t1 = [
        {"strike": 24050, "call_oi": 1520000, "put_oi": 6050000},
        {"strike": 24100, "call_oi": 2010000, "put_oi": 7520000},
        {"strike": 24150, "call_oi": 2510000, "put_oi": 5030000},
        {"strike": 24200, "call_oi": 4050000, "put_oi": 4510000},
        {"strike": 24250, "call_oi": 8000000, "put_oi": 3050000}, # +33.3% Call OI (VALID CALL WALL)
        {"strike": 24300, "call_oi": 7600000, "put_oi": 2020000},
        {"strike": 24350, "call_oi": 8050000, "put_oi": 1510000},
        # Far OTM spikes that MUST BE BLOCKED
        {"strike": 24850, "call_oi": 800000, "put_oi": 21000},   # +60.0% Call OI (NOISE)
        {"strike": 24900, "call_oi": 540000, "put_oi": 10500},   # +80.0% Call OI (NOISE)
    ]

    r1 = OI_ACCELERATION_TRACKER.evaluate_oi_velocity(symbol, spot, strikes_t1)
    print(f"[*] T1 SFATM Filtered Result: CallWall={r1['call_wall_detected']}, PutWall={r1['put_wall_detected']}")
    print(f"    Conviction Multiplier: {r1['conviction_multiplier']}")
    print(f"    Summary: {r1['wall_summary']}")
    for w in r1["active_walls"]:
        print(f"    -> {w['description']}")

    # 1. Assert valid near-ATM call wall detected
    assert r1["call_wall_detected"] is True
    assert r1["conviction_multiplier"] == 0.80
    assert any(w["strike"] == 24250 for w in r1["active_walls"])

    # 2. Assert that far OTM metrics were successfully blocked (NOISE LEAKAGE ZERO)
    assert not any("24850" in w["description"] or w["strike"] == 24850 for w in r1["active_walls"]), "❌ Failure: Noise leakage detected on 24850!"
    assert not any("24900" in w["description"] or w["strike"] == 24900 for w in r1["active_walls"]), "❌ Failure: Noise leakage detected on 24900!"

    print("\n[OK] VERIFICATION SIGN-OFF: STRUCTURAL NOISE ELIMINATED FROM PERFORMANCE LEDGER")
    print(">>> PASS: Strikes-From-ATM (SFATM) Restrictor Verified Successfully!\n")



def test_microstructure_slippage():
    print("=" * 70)
    print("2. TESTING: Dynamic Microstructure Slippage Function")
    print("=" * 70)
    from src.services.tax_calculator import calculate_microstructure_slippage as calc_slip_tax
    from src.services.shadow_signal_logger import calculate_microstructure_slippage as calc_slip_shadow

    premium = 150.0

    # Scenario 1: Institutional dump (OBI <= -0.70) -> 1.5% slippage penalty
    p1 = calc_slip_tax(premium, -0.85, lot_size=65)
    p1_sh = calc_slip_shadow(premium, -0.85, lot_size=65)
    print(f"[*] OBI = -0.85 (Institutional Dump): Raw INR {premium} -> Realized INR {p1} (-1.5% slippage)")
    assert p1 == 147.75 and p1_sh == 147.75

    # Scenario 2: Moderate ask pressure (-0.70 < OBI <= -0.30) -> 0.5% slippage penalty
    p2 = calc_slip_tax(premium, -0.45, lot_size=65)
    p2_sh = calc_slip_shadow(premium, -0.45, lot_size=65)
    print(f"[*] OBI = -0.45 (Moderate Ask Pressure): Raw INR {premium} -> Realized INR {p2} (-0.5% slippage)")
    assert p2 == 149.25 and p2_sh == 149.25

    # Scenario 3: Normal liquidity (OBI > -0.30) -> 0.1% baseline friction
    p3 = calc_slip_tax(premium, 0.20, lot_size=65)
    p3_sh = calc_slip_shadow(premium, 0.20, lot_size=65)
    print(f"[*] OBI = +0.20 (Balanced / Bid Support): Raw INR {premium} -> Realized INR {p3} (-0.1% slippage)")
    assert p3 == 149.85 and p3_sh == 149.85

    print(">>> PASS: Microstructure Slippage Function Verified Successfully!\n")


async def test_news_sentiment_ingestor():
    print("=" * 70)
    print("3. TESTING: Real-Time News Sentiment Ingestion with Live RSS Feeds")
    print("=" * 70)
    from src.services.news_sentiment_ingestor import NEWS_SENTIMENT_INGESTOR, SAFETY_GATE

    # 1. Fetch live breaking headlines across verified financial news sources
    print("[*] Fetching live breaking headlines from Google News, Economic Times, Moneycontrol...")
    headlines, active_feeds = NEWS_SENTIMENT_INGESTOR.fetch_breaking_headlines(limit_per_source=3)
    print(f"    Active Verified RSS Feeds: {active_feeds}/4")
    print(f"    Total Headlines Ingested: {len(headlines)}")
    for idx, item in enumerate(headlines[:5], 1):
        print(f"    [{idx}] ({item['source']}) {item['title'][:85]}... [{item['published']}]")
    assert active_feeds >= 2, "Must have at least 2 active live RSS feeds"
    assert len(headlines) > 0, "Must have fetched real headlines"

    # 2. Test Execution Window Gate
    res_gated = await NEWS_SENTIMENT_INGESTOR.analyze_and_sync_news_sentiment(force_execution=False)
    print(f"[*] Standard Market Hours Gate Check: {res_gated.get('status', 'EXECUTED')}")
    if res_gated.get("status") == "SKIPPED_OUTSIDE_MARKET_HOURS":
        print(f"    Gate Message: {res_gated['message']}")

    # 3. Test Forced Ingestion & Vector Grounding
    print("[*] Running Live News Grounding & Sentiment Vectorization (force_execution=True)...")
    res_live = await NEWS_SENTIMENT_INGESTOR.analyze_and_sync_news_sentiment(force_execution=True)
    print(f"    Regime Status:       {res_live['regime_status']}")
    print(f"    Sentiment Scalar:    {res_live['sentiment_scalar']:+.3f}")
    print(f"    Sentiment Direction: {res_live['sentiment_direction']}")
    print(f"    Catalyst:            {res_live['breaking_catalyst']}")
    print(f"    Timestamp (IST):     {res_live['timestamp_ist']}")
    print(f"    Active Feeds Count:  {res_live['active_feeds_count']}")
    assert -1.0 <= res_live["sentiment_scalar"] <= 1.0
    assert res_live["regime_status"] in ["BULLISH_ACCUMULATION", "BEARISH_DISTRIBUTION", "RANGEBOUND_EQUILIBRIUM"]

    # 4. Test Macro Bias Retrieval
    cached_bias = NEWS_SENTIMENT_INGESTOR.get_current_macro_bias()
    print(f"[*] Cached Macro Bias: Regime={cached_bias.get('regime_status')}, Scalar={cached_bias.get('sentiment_scalar')}")
    print(">>> PASS: News Sentiment Ingestion Engine Verified with Live Real-World Data!\n")


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("STARTING FULL PRODUCTION VERIFICATION FOR ENGINE A & C (SFATM HARDENED)")
    print("#" * 70 + "\n")
    test_oi_acceleration_tracker()
    test_microstructure_slippage()
    asyncio.run(test_news_sentiment_ingestor())
    print("#" * 70)
    print("ALL MODULES SUCCESSFULLY INTEGRATED AND VERIFIED WITH REAL DATA!")
    print("#" * 70 + "\n")
