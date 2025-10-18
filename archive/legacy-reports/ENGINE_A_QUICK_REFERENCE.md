# Engine A Consolidation - Quick Reference
**Generated:** October 17, 2025

---

## 📊 At a Glance

### Current State
```
❌ engine-a/              (Mock data, basic endpoints, v2.0.0)
❌ engine-a-market-data/  (Dhan REST, Gemini/HF, v3.0.0)
```

### Target State
```
✅ engine-a-market-data/  (DhanHQ WebSocket + REST, TA-Lib, v7.0.0)
```

---

## 🎯 What's Being Consolidated

### From engine-a/ → Merging In
- ✅ GET /api/exchanges (NSE/BSE/MCX metadata)
- ✅ GET /api/symbols (symbol listing)
- ✅ GET /api/market-data/{symbol} (detailed symbol view)
- ✅ POST /api/refresh (cache refresh)
- ✅ Broader symbol set (10 symbols vs 5)

### From engine-a-market-data/ → Base
- ✅ Dhan API integration (REST positions/orders/optionchain)
- ✅ Real technical indicators (pandas/numpy)
- ✅ Google Secret Manager
- ✅ Enhanced Docker (healthcheck, non-root, system deps)
- ✅ Verification script (PowerShell)
- ✅ Production logging

### New v7.0 Features → Adding
- 🆕 DhanHQ WebSocket marketfeed (real-time streaming)
- 🆕 WebSocket API endpoint /ws/live
- 🆕 TA-Lib integration (advanced indicators)
- 🆕 yfinance fallback provider
- 🆕 NewsAPI + scraping
- 🆕 Historical OHLCV data
- 🆕 Modular architecture (routes/services/providers/analytics)
- 🆕 YAML configuration support

---

## 📁 New Folder Structure (37 files)

```
engine-a-market-data/
├── 📄 main.py
├── 📄 requirements.txt
├── 📄 Dockerfile
├── 📄 .dockerignore
├── 📄 README.md
│
├── 📂 config/
│   ├── __init__.py
│   └── settings.py          # YAML + env + Secret Manager
│
├── 📂 core/
│   ├── __init__.py
│   ├── logger.py            # Stdout-first logging
│   ├── security.py          # Embedded security headers
│   └── utils.py             # Common helpers
│
├── 📂 providers/
│   ├── __init__.py
│   ├── dhan_provider.py     # WebSocket feed
│   ├── dhan_rest.py         # REST API
│   ├── option_chain.py      # Option chain
│   ├── fallback_market.py   # yfinance
│   ├── news_provider.py     # NewsAPI + scraping
│   └── historical_provider.py
│
├── 📂 analytics/
│   ├── __init__.py
│   ├── ta_indicators.py     # RSI, MACD, EMA, Bollinger
│   ├── signal_generator.py  # Multi-indicator logic
│   └── sentiment_analyzer.py
│
├── 📂 routes/
│   ├── __init__.py
│   ├── health.py            # /, /health
│   ├── signals.py           # /api/signals, /api/signal/{symbol}
│   ├── market.py            # /api/market, /api/market/{symbol}, etc.
│   ├── dhan.py              # /api/dhan/*
│   ├── options.py           # /api/options/{security_id}
│   ├── news.py              # /api/news
│   ├── websocket.py         # /ws/live
│   └── legacy.py            # 410 responses
│
├── 📂 services/
│   ├── __init__.py
│   ├── market_data_service.py
│   ├── signal_service.py
│   ├── cache_service.py
│   └── secret_service.py
│
├── 📂 models/
│   ├── __init__.py
│   ├── schemas.py           # Pydantic models
│   └── domain.py            # Domain objects
│
├── 📂 scripts/
│   ├── verify_engine_a.ps1
│   ├── deploy-cloudrun.ps1
│   └── test-local.ps1
│
├── 📂 tests/
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_signals.py
│   └── test_dhan.py
│
└── 📂 samples/
    ├── settings.yaml.example
    ├── test_payload.json
    ├── gemini_test.json
    └── hf_test.json
```

---

## 🔌 Complete API Map (25 endpoints)

### Core (2)
- GET  `/` - Service info
- GET  `/health` - Health check

### Market Data (5)
- GET  `/api/market` - All symbols (live)
- GET  `/api/market/{symbol}` - Single symbol
- GET  `/api/symbols` - Symbol list
- GET  `/api/exchanges` - Exchange metadata
- POST `/api/refresh` - Force refresh

### Signals & Analytics (2)
- GET  `/api/signals` - All signals
- GET  `/api/signal/{symbol}` - Single signal

### Options (2)
- GET  `/api/options/{security_id}` - Option chain
- GET  `/api/dhan/optionchain/{symbol}` - Legacy option chain

### Dhan Integration (4)
- GET  `/api/dhan/positions` - User positions
- GET  `/api/dhan/orders` - User orders
- GET  `/api/dhan/callback` - OAuth callback
- POST `/api/dhan/postback` - Deprecated (410)

### News (1)
- GET  `/api/news` - Latest news

### AI (3) - ⚠️ Decision Required
- POST `/api/gemini/generate` - Text generation
- POST `/api/gemini/summary` - Summarization
- POST `/api/huggingface/sentiment` - Sentiment

### Real-Time (1)
- WS   `/ws/live` - Live tick stream

---

## 🔧 Key Dependencies

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
numpy==1.26.2
TA-Lib==0.4.28            # ⚠️ Requires system install
dhanhq==1.3.3             # 🆕 DhanHQ Python SDK
websockets==12.0          # 🆕 WebSocket support
yfinance==0.2.32          # 🆕 Fallback data
beautifulsoup4==4.12.2    # 🆕 News scraping
google-cloud-secret-manager==2.18.1
```

---

## ⚡ Quick Decision Matrix

| Decision Point | Option A | Option B | Recommendation |
|----------------|----------|----------|----------------|
| **AI Endpoints** | Keep in Engine A | Move to Engine B | **Move generation to B, keep sentiment** |
| **Symbol Set** | 10 symbols (engine-a) | 5 symbols (market-data) | **Merge to 15 symbols, YAML config** |
| **WebSocket** | DhanHQ only | DhanHQ + fallback | **Hybrid (DhanHQ primary)** |
| **Historical** | Include | Skip | **Include (for signals)** |
| **News** | Include | Defer | **Include (for sentiment)** |
| **Port** | 8000 | 8080 | **8080 via os.getenv("PORT")** |
| **Logging** | File + stdout | Stdout only | **Stdout-first** |

---

## ⚠️ Critical Risks

| Risk | Mitigation |
|------|------------|
| TA-Lib Docker build failure | Test Dockerfile locally before deploy |
| WebSocket drops | Auto-reconnect + fallback to REST |
| Secret Manager access denied | Verify service account permissions |
| Frontend breaking changes | Maintain backward-compatible responses |
| Dhan API rate limits | Implement caching + throttling |

---

## ✅ Pre-Execution Checklist

**Must confirm before proceeding:**

1. [ ] Folder structure approved
2. [ ] Symbol list finalized
3. [ ] AI endpoint placement decided (A vs B)
4. [ ] WebSocket strategy confirmed
5. [ ] Historical data inclusion confirmed
6. [ ] News integration priority set
7. [ ] Breaking changes acceptable?
8. [ ] Secrets exist in Secret Manager
9. [ ] Service account has permissions
10. [ ] Backup/branch created

---

## 🚀 Execution Plan (Once Approved)

**Estimated Time:** 8 hours  
**Approach:** Autonomous, systematic, tested

1. ✅ Create new folder structure (30 min)
2. ✅ Build core modules (45 min)
3. ✅ Integrate providers (90 min)
4. ✅ Implement analytics (60 min)
5. ✅ Split routes (90 min)
6. ✅ Create services (45 min)
7. ✅ Wire main.py (30 min)
8. ✅ Update Docker + scripts (45 min)
9. ✅ Test locally (60 min)
10. ✅ Document (30 min)

**Deliverable:** Production-ready Engine A v7.0 with DhanHQ WebSocket streaming, TA-Lib indicators, modular architecture, and comprehensive testing.

---

## 📞 Ready to Proceed?

Please review:
- 📄 **Full Analysis:** `ENGINE_A_CONSOLIDATION_PLAN.md`
- 📄 **Quick Reference:** This file

**Reply with your decisions on the 10 checklist items above, and I'll execute the complete consolidation autonomously.** 🚀

---

**Status:** 🟡 AWAITING APPROVAL
**Last Updated:** October 17, 2025
