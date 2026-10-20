"""
InfinityAI.Pro - Comprehensive Deep E2E Production System Audit & Verification
Author: Institutional Algorithmic Trading Engineer & Senior GCP Cloud Architect
Date: October 16, 2026
Target Environment: 100% GCP & Firebase (asia-south1)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
ENGINE_A_URL = "https://engine-a-313407263327.asia-south1.run.app"
ENGINE_B_URL = "https://engine-b-313407263327.asia-south1.run.app"
ENGINE_C_URL = "https://engine-c-313407263327.asia-south1.run.app"
FRONTEND_URL = "https://project-841b7f97-5ee3-4fbe-920.web.app"
INTERNAL_TOKEN = os.environ.get("INTERNAL_AUTH_TOKEN") or os.environ.get("INTERNAL_TOKEN", "")
if not INTERNAL_TOKEN:
    raise ValueError("INTERNAL_AUTH_TOKEN environment variable must be set")

HEADERS_AUTH = {
    "User-Agent": "InfinityAI-DeepAudit/2.0",
    "X-Internal-Token": INTERNAL_TOKEN,
    "Authorization": f"Bearer {INTERNAL_TOKEN}",
    "Content-Type": "application/json"
}

def http_get(url: str, headers: dict = None, timeout: int = 25):
    h = dict(HEADERS_AUTH)
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            lat = (time.perf_counter() - t0) * 1000
            data = resp.read().decode('utf-8')
            try:
                return resp.status, json.loads(data), lat, None
            except Exception:
                return resp.status, data, lat, None
    except urllib.error.HTTPError as e:
        lat = (time.perf_counter() - t0) * 1000
        try:
            err_data = json.loads(e.read().decode('utf-8'))
        except Exception:
            err_data = str(e)
        return e.code, err_data, lat, str(e)
    except Exception as e:
        lat = (time.perf_counter() - t0) * 1000
        return 0, None, lat, str(e)

def http_post(url: str, body: dict = None, headers: dict = None, timeout: int = 25):
    h = dict(HEADERS_AUTH)
    if headers:
        h.update(headers)
    data_bytes = json.dumps(body or {}).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers=h, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            lat = (time.perf_counter() - t0) * 1000
            data = resp.read().decode('utf-8')
            try:
                return resp.status, json.loads(data), lat, None
            except Exception:
                return resp.status, data, lat, None
    except urllib.error.HTTPError as e:
        lat = (time.perf_counter() - t0) * 1000
        try:
            err_data = json.loads(e.read().decode('utf-8'))
        except Exception:
            err_data = str(e)
        return e.code, err_data, lat, str(e)
    except Exception as e:
        lat = (time.perf_counter() - t0) * 1000
        return 0, None, lat, str(e)

def run_deep_audit():
    print("=" * 115)
    print("🚀 INFINITYAI.PRO — INSTITUTIONAL END-TO-END DEEP PRODUCTION AUDIT & VERIFICATION")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Project: {PROJECT_ID}")
    print(f"Engine A: {ENGINE_A_URL}")
    print(f"Engine B: {ENGINE_B_URL}")
    print(f"Engine C: {ENGINE_C_URL}")
    print("=" * 115)

    audit_summary = {}

    # --------------------------------------------------------------------------
    # 1. CORE SUBSYSTEM CONNECTIVITY & REVISIONS
    # --------------------------------------------------------------------------
    print("\n[SECTION 1: CORE SUBSYSTEM HEALTH & REVISIONS]")
    subsystems = [
        ("Frontend", f"{FRONTEND_URL}/signals", "GET"),
        ("Engine A (Orchestrator)", f"{ENGINE_A_URL}/health", "GET"),
        ("Engine B (AI Intelligence)", f"{ENGINE_B_URL}/health", "GET"),
        ("Engine C (Execution Proxy)", f"{ENGINE_C_URL}/health", "GET"),
    ]
    sub_results = []
    for name, url, method in subsystems:
        st, body, lat, err = http_get(url) if method == "GET" else http_post(url)
        ok = st == 200
        status_sym = "🟢 HEALTHY" if ok else f"❌ HTTP {st}"
        details = ""
        if isinstance(body, dict):
            details = f"Service: {body.get('service', 'N/A')}, Version: {body.get('version', 'N/A')}, Status: {body.get('status', 'N/A')}"
        elif isinstance(body, str):
            details = f"HTML page received ({len(body)} bytes)"
        else:
            details = err or "Connection failed"
        sub_results.append({"name": name, "status": status_sym, "latency_ms": round(lat, 1), "details": details})
        print(f"  • {name:<28}: {status_sym} | {lat:6.1f} ms | {details}")
    audit_summary["subsystems"] = sub_results

    # --------------------------------------------------------------------------
    # 2. SYMBOL MAPPING & DHANHQ SPOT MARKET QUOTES
    # --------------------------------------------------------------------------
    print("\n[SECTION 2: SYMBOL MAPPING & DHANHQ SPOT MARKET QUOTES]")
    symbols_to_test = [
        {"symbol": "NIFTY", "sec_id": "13", "seg": "IDX_I", "lot": 65, "step": 50, "cycle": "Weekly (NSE Benchmark)", "next_expiry": "2026-10-19"},
        {"symbol": "BANKNIFTY", "sec_id": "25", "seg": "IDX_I", "lot": 30, "step": 100, "cycle": "Monthly Only (SEBI Discontinued Weekly)", "next_expiry": "2026-10-27"},
        {"symbol": "FINNIFTY", "sec_id": "27", "seg": "IDX_I", "lot": 60, "step": 50, "cycle": "Monthly Only (SEBI Discontinued Weekly)", "next_expiry": "2026-10-27"},
        {"symbol": "MIDCPNIFTY", "sec_id": "442", "seg": "IDX_I", "lot": 120, "step": 25, "cycle": "Monthly Only (SEBI Discontinued Weekly)", "next_expiry": "2026-10-27"},
        {"symbol": "SENSEX", "sec_id": "51", "seg": "IDX_I", "lot": 20, "step": 100, "cycle": "Weekly (BSE Benchmark)", "next_expiry": "2026-10-22"},
    ]
    
    # Primary: batch quotes endpoint
    quote_url = f"{ENGINE_C_URL}/api/dhan/market/quotes?security_ids=13,25,27,442,51&exchange_segment=IDX_I&user_id=raghu_primary"
    st, q_body, q_lat, q_err = http_get(quote_url)
    symbol_results = []
    
    ohlc_data = {}
    if st == 200 and isinstance(q_body, dict):
        raw_ohlc = q_body.get("data", {})
        if isinstance(raw_ohlc, dict):
            ohlc_data = raw_ohlc.get("data", raw_ohlc)
            print(f"  • DhanHQ Batch Quotes Retrieved: {len(ohlc_data)} indices ({q_lat:.1f} ms)")

    for s in symbols_to_test:
        sym = s["symbol"]
        sec_id = s["sec_id"]
        # Check in batch quotes or fallback to individual LTP
        quote = ohlc_data.get(sec_id) or ohlc_data.get(int(sec_id)) if isinstance(ohlc_data, dict) else None
        if not quote:
            # Query /api/dhan/market/ltp
            ltp_url = f"{ENGINE_C_URL}/api/dhan/market/ltp?security_id={sec_id}&exchange_segment=IDX_I&user_id=raghu_primary"
            lst, lbody, llat, lerr = http_get(ltp_url)
            if lst == 200 and isinstance(lbody, dict):
                quote = lbody.get("data", lbody)

        if quote and isinstance(quote, dict):
            ltp = quote.get("last_price") or quote.get("ltp") or quote.get("close")
            open_p = quote.get("open") or quote.get("ohlc", {}).get("open")
            high_p = quote.get("high") or quote.get("ohlc", {}).get("high")
            low_p = quote.get("low") or quote.get("ohlc", {}).get("low")
            close_p = quote.get("close") or quote.get("ohlc", {}).get("close")
            print(f"  • {sym:<12} (sec_id={sec_id:>3}): LTP: {ltp:>10.2f} | O: {open_p} | H: {high_p} | L: {low_p} | C: {close_p} | Lot: {s['lot']} | Step: {s['step']}")
            symbol_results.append({
                "symbol": sym, "sec_id": sec_id, "ltp": ltp, "open": open_p,
                "high": high_p, "low": low_p, "close": close_p, "lot": s['lot'], "step": s['step'], "status": "🟢 VALID"
            })
        else:
            print(f"  • {sym:<12} (sec_id={sec_id:>3}): ⚠️ Fallback spot check: {quote}")
            symbol_results.append({"symbol": sym, "sec_id": sec_id, "status": "PENDING"})

    audit_summary["symbols"] = symbol_results

    # --------------------------------------------------------------------------
    # 3. LIVE DHANHQ OPTION CHAIN DEPTH & TICK SIZE CONFORMANCE
    # --------------------------------------------------------------------------
    print("\n[SECTION 3: LIVE DHANHQ OPTION CHAIN DEPTH & ₹0.05 TICK SIZE CONFORMANCE]")
    option_tests = [
        {"symbol": "NIFTY", "strike": 23150, "type": "CE"},
        {"symbol": "BANKNIFTY", "strike": 55800, "type": "CE"},
        {"symbol": "FINNIFTY", "strike": 25400, "type": "CE"},
        {"symbol": "MIDCPNIFTY", "strike": 13700, "type": "CE"},
    ]
    option_results = []
    for opt in option_tests:
        sym = opt["symbol"]
        strike = opt["strike"]
        otype = opt["type"]
        url = f"{ENGINE_C_URL}/api/dhan/option-chain/{sym}?strike={strike}&option_type={otype}"
        st, body, lat, err = http_get(url)
        if st == 200 and isinstance(body, dict) and body.get("status") == "success":
            sec_id = body.get("security_id")
            bid = body.get("bid_price", 0.0)
            ask = body.get("ask_price", 0.0)
            ltp = body.get("last_price", 0.0)
            oi = body.get("open_interest", 0)
            vol = body.get("volume", 0)
            exp = body.get("expiry")
            src = body.get("source")

            def check_tick(p):
                return abs(round(p / 0.05) * 0.05 - p) < 1e-4

            tick_ok = check_tick(bid) and check_tick(ask) and check_tick(ltp)
            tick_status = "🟢 ₹0.05 Valid" if tick_ok else "❌ Non-Tick Decimals"

            print(f"  • {sym:<10} {strike} {otype}: SecID={sec_id} | LTP={ltp:>6.2f} | Bid={bid:>6.2f} | Ask={ask:>6.2f} | OI={oi:>9,} | Vol={vol:>11,} | Exp={exp} | Src={src} | {tick_status}")
            option_results.append({
                "symbol": sym, "strike": strike, "type": otype, "security_id": sec_id,
                "ltp": ltp, "bid": bid, "ask": ask, "oi": oi, "vol": vol,
                "expiry": exp, "source": src, "tick_ok": tick_ok
            })
        else:
            print(f"  • {sym:<10} {strike} {otype}: ❌ Failed: HTTP {st} | {err}")
            option_results.append({"symbol": sym, "strike": strike, "status": f"❌ HTTP {st}"})
    audit_summary["options"] = option_results

    # --------------------------------------------------------------------------
    # 4. ENGINE B AI/ML TRI-MODEL INFERENCES & ENSEMBLE WEIGHTS
    # --------------------------------------------------------------------------
    print("\n[SECTION 4: ENGINE B AI/ML TRI-MODEL INFERENCES & ENSEMBLE WEIGHTS]")
    st, weights_body, lat, err = http_get(f"{ENGINE_B_URL}/api/v1/models/ensemble-weights")
    if st == 200 and isinstance(weights_body, dict):
        weights = weights_body.get('weights', weights_body)
        print(f"  • Dynamic Ensemble Weights: {weights} (Latency: {lat:.1f} ms)")
        audit_summary["ensemble_weights"] = weights

    st, macro_body, lat, err = http_get(f"{ENGINE_B_URL}/api/ai/live-state")
    if st == 200 and isinstance(macro_body, dict):
        m_data = macro_body.get("data", {})
        print(f"  • Live Macro AI State: Bias={m_data.get('macro_bias')} | Score={m_data.get('macro_score')} | RegimeMult={m_data.get('regime_multiplier')}")
        print(f"    GIFT Nifty Basis: {m_data.get('gift_nifty_points')} pts | Crude Status: {m_data.get('crude_oil_status')} | FII Flow: {m_data.get('institutional_flow_bias')}")
        print(f"    Gemini Synthesis: {m_data.get('gemini_synthesis')}")
        audit_summary["macro_state"] = m_data

    # Test Live Ensemble Signals across Core Indices (Timeout: 40s)
    print("\n  • Testing Live Ensemble Signals across All Core Indices:")
    signals_tested = []
    for sym in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]:
        url = f"{ENGINE_B_URL}/api/v1/ensemble/signal/{sym}"
        st, s_body, lat, err = http_get(url, timeout=40)
        if st == 200 and isinstance(s_body, dict):
            data = s_body.get("data", s_body)
            direction = data.get("signal") or data.get("direction")
            conf = data.get("confidence")
            veto = data.get("veto_applied") or data.get("veto")
            reason = data.get("veto_reason") or data.get("reason", "")
            probs = data.get("signal_proba") or data.get("probabilities")
            driver = data.get("dominant_driver", "N/A")
            print(f"    - {sym:<10}: Signal={direction:<8} | Conf={conf} | Driver: {driver} | Proba={probs} | Latency={lat:5.1f} ms")
            signals_tested.append({"symbol": sym, "signal": direction, "confidence": conf, "veto": veto, "reason": reason, "probs": probs, "driver": driver})
        else:
            print(f"    - {sym:<10}: HTTP {st} | {err}")
            signals_tested.append({"symbol": sym, "status": f"❌ HTTP {st}"})
    audit_summary["signals_tested"] = signals_tested

    # --------------------------------------------------------------------------
    # 5. ENGINE A RISK & SHADOW SIGNALS LEDGER
    # --------------------------------------------------------------------------
    print("\n[SECTION 5: ENGINE A RISK GOVERNANCE & SHADOW SIGNALS LEDGER]")
    st, cap_body, lat, err = http_get(f"{ENGINE_A_URL}/api/v1/capital/live-summary")
    if st == 200 and isinstance(cap_body, dict):
        print(f"  • Engine A Live Capital & VaR Summary: {cap_body} ({lat:.1f} ms)")
        audit_summary["capital_summary"] = cap_body

    st, cb_body, lat, err = http_get(f"{ENGINE_A_URL}/api/v1/circuit-breaker/status")
    if st == 200 and isinstance(cb_body, dict):
        print(f"  • Circuit Breaker Status: {cb_body} ({lat:.1f} ms)")
        audit_summary["circuit_breaker"] = cb_body

    st, moe_body, lat, err = http_get(f"{ENGINE_A_URL}/api/v1/risk/moe-gate/status")
    if st == 200 and isinstance(moe_body, dict):
        print(f"  • MoE Discordance Gate Status: {moe_body} ({lat:.1f} ms)")
        audit_summary["moe_gate"] = moe_body

    # Query Firestore signals ledger via Engine A
    st, sigs_body, lat, err = http_get(f"{ENGINE_A_URL}/api/v1/shadow-signals?limit=5")
    if st == 200 and isinstance(sigs_body, dict):
        signals = sigs_body.get("signals", sigs_body.get("data", []))
        print(f"  • Retrieved {len(signals)} recent shadow signals from Firestore:")
        for s in signals[:5]:
            sig_id = s.get("signal_id") or s.get("id")
            sym = s.get("symbol")
            dec = s.get("decision")
            spot = s.get("underlying_spot") or s.get("spot_price")
            prem = s.get("entry_premium")
            status = s.get("status") or s.get("outcome_status")
            pnl = s.get("realized_pnl_inr") or s.get("current_pnl_inr")
            src = s.get("pricing_source") or s.get("source")
            print(f"    - {sig_id}: {sym} {dec} | Spot: {spot} | Entry Prem: ₹{prem} | Status: {status} | PnL: ₹{pnl} | Source: {src}")
        audit_summary["signals"] = signals[:5]
    else:
        print(f"  • Engine A shadow signals query: HTTP {st} | {err}")

    # --------------------------------------------------------------------------
    # 6. DHANHQ BROKER CONNECTION & VAULT STATUS
    # --------------------------------------------------------------------------
    print("\n[SECTION 6: DHANHQ BROKER CONNECTION & VAULT STATUS]")
    st, funds_body, lat, err = http_get(f"{ENGINE_C_URL}/api/dhan/funds?user_id=raghu_primary")
    if st == 200 and isinstance(funds_body, dict):
        f_data = funds_body.get("funds", funds_body.get("data", {}))
        avail = f_data.get("availableBalance") or f_data.get("availabelBalance") or 0.0
        collateral = f_data.get("collateralAmount") or 0.0
        print(f"  • DhanHQ Live Account Funds: Available Cash=₹{avail:,.2f} | Collateral=₹{collateral:,.2f} ({lat:.1f} ms)")
        audit_summary["funds"] = {"available": avail, "collateral": collateral}

    st, auth_body, lat, err = http_get(f"{ENGINE_C_URL}/api/auth/status?user_id=raghu_primary")
    if st == 200 and isinstance(auth_body, dict):
        print(f"  • Vault Auth Status: {auth_body} ({lat:.1f} ms)")
        audit_summary["vault_auth"] = auth_body

    print("\n" + "=" * 115)
    print("✅ DEEP END-TO-END PRODUCTION VERIFICATION AUDIT COMPLETE")
    print("=" * 115)

    return audit_summary

if __name__ == "__main__":
    run_deep_audit()
