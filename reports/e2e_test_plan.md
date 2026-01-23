# Task 4: End-to-End Integration Test Plan

**InfinityAI.Pro Trading Platform**
**Test Date:** 2026-01-21
**Test Environment:** PRODUCTION (LIVE mode with guardrails)

---

## Test Objectives

**Primary Goal:** Verify complete frontend → API → broker → database → real-time flow

**Critical Paths to Test:**

1. **Authentication Flow:** Coupon verification → Firebase Auth → Dashboard access
2. **ML Signal Generation:** Frontend request → Engine-B → Market data → ML inference → Firestore → Response
3. **Order Placement:** Frontend → Engine-C → Trading guardrails → DhanHQ broker → Firestore → Ably WebSocket → Frontend
4. **Portfolio Sync:** DhanHQ webhook → Engine-C → Firestore update → Ably broadcast → Frontend update
5. **Real-time Data:** WebSocket connection → Ably channels → Live price updates

**Non-Critical Paths:** 6. Risk analytics (Engine-A) 7. AI analysis (Gemini Pro - disabled) 8. Historical data queries

---

## Pre-Test Verification

**Infrastructure Health (Verified 2026-01-21 21:19 UTC):**

✅ **Engine-A (Orchestrator):**

- URL: https://orchestrator.infinityai.pro
- Status: healthy
- Version: 3.7-google-integrations
- ML Capabilities: 8 (risk_scoring, position_sizing, var, cvar, sortino, kelly, portfolio_risk, max_drawdown)
- Google Integrations: Disabled (expected)

✅ **Engine-B (ML Signals):**

- URL: https://signals.infinityai.pro
- Status: active
- Version: v3.6-instrument-signals
- Models: 5 loaded (xgboost, lightgbm, catboost, random_forest, nltk_sentiment)
- Frameworks: All active (xgboost, lightgbm, catboost, transformers, nltk, ta_lib, yfinance, voting)
- Ensemble Weights: XGBoost 40%, LightGBM 30%, CatBoost 15%, Random Forest 15%
- Trained Symbols: [] (models using pretrained weights or on-demand training)

✅ **Engine-C (Core API):**

- URL: https://api.infinityai.pro
- Status: (Testing in progress)
- Mode: LIVE
- Expected endpoints: 50+ (orders, portfolio, signals, guardrails, webhooks)

**Load Balancer:**

- IP: 34.107.213.171
- SSL: ACTIVE (infinityai-apis-ssl SAN certificate)
- Backend Services: 3 (orchestrator-backend, signals-backend, api-backend)

**Data Layer:**

- Firestore: OPERATIONAL
- Secret Manager: 7 secrets available
- Cloud Storage: 8 buckets

---

## Test Plan

### Test 1: Engine-C Health & API Discovery

**Objective:** Verify Engine-C operational, discover available endpoints

**Steps:**

1. Test /health endpoint
2. Query available endpoints (if introspection endpoint exists)
3. Verify LIVE mode configuration

**Expected Response:**

```json
{
  "status": "healthy" | "operational",
  "service": "engine-c",
  "mode": "live",
  "version": "...",
  "timestamp": "2026-01-21T..."
}
```

**Success Criteria:**

- HTTP 200 response
- Status = healthy/operational
- Mode = live
- Response time < 500ms

---

### Test 2: ML Signal Generation (Engine-B)

**Objective:** Test ML signal generation for a sample symbol

**Steps:**

1. Call Engine-B signal endpoint with test symbol (e.g., "SBIN" - State Bank of India)
2. Verify ensemble model execution
3. Check Firestore signal storage
4. Measure end-to-end latency

**Test Request:**

```bash
curl -X POST https://signals.infinityai.pro/generate-signal \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SBIN",
    "exchange": "NSE",
    "timeframe": "1d"
  }'
```

**Expected Response:**

```json
{
  "symbol": "SBIN",
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0-1.0,
  "models": {
    "xgboost": {...},
    "lightgbm": {...},
    "catboost": {...},
    "random_forest": {...}
  },
  "ensemble_score": 0.0-1.0,
  "timestamp": "2026-01-21T..."
}
```

**Success Criteria:**

- HTTP 200 response
- Valid signal (BUY/SELL/HOLD)
- Confidence score present
- All 4 models executed
- Ensemble score computed
- Response time < 800ms

---

### Test 3: Trading Guardrails Validation

**Objective:** Test trading guardrails without actual order placement

**Test Cases:**

#### 3.1 Order Cap Validation

**Input:** Order value > ₹500,000
**Expected:** Rejection with error "Order value exceeds limit"

#### 3.2 Market Hours Validation

**Input:** Order outside 9:15-15:30 IST
**Expected:** Rejection with error "Market closed"

#### 3.3 Invalid Symbol Validation

**Input:** Non-existent symbol "INVALID123"
**Expected:** Rejection with error "Invalid trading symbol"

#### 3.4 Valid Order (Paper Mode)

**Input:** Valid order within guardrails
**Expected:** Success (paper mode execution)

**Test Request:**

```bash
curl -X POST https://api.infinityai.pro/orders/place \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "symbol": "SBIN",
    "exchange": "NSE",
    "transaction_type": "BUY",
    "quantity": 10,
    "order_type": "MARKET",
    "product_type": "INTRADAY"
  }'
```

**Success Criteria:**

- Guardrails validate correctly
- Errors returned for violations
- Valid orders accepted (paper mode)
- Response time < 1000ms

---

### Test 4: Portfolio Query

**Objective:** Retrieve current portfolio positions

**Test Request:**

```bash
curl -X GET https://api.infinityai.pro/portfolio \
  -H "Authorization: Bearer <test-token>"
```

**Expected Response:**

```json
{
  "positions": [
    {
      "symbol": "...",
      "quantity": 0,
      "avg_price": 0.0,
      "current_price": 0.0,
      "pnl": 0.0,
      "pnl_percent": 0.0
    }
  ],
  "total_value": 0.0,
  "total_pnl": 0.0,
  "timestamp": "2026-01-21T..."
}
```

**Success Criteria:**

- HTTP 200 response
- Valid portfolio structure
- Response time < 500ms

---

### Test 5: Real-Time WebSocket Connection

**Objective:** Test Ably WebSocket integration

**Steps:**

1. Connect to Ably channel (portfolio, orders, signals, system)
2. Subscribe to events
3. Verify message delivery
4. Test reconnection on disconnect

**Channels to Test:**

- `portfolio` - Portfolio updates
- `orders` - Order status changes
- `signals` - ML signal generation
- `system` - System notifications

**Success Criteria:**

- WebSocket connection established
- Subscription successful
- Messages received
- Latency < 100ms

---

### Test 6: DhanHQ Broker Integration (Read-Only)

**Objective:** Test broker API connectivity without placing orders

**Test Request:**

```bash
curl -X GET https://api.infinityai.pro/broker/account \
  -H "Authorization: Bearer <test-token>"
```

**Expected Response:**

```json
{
  "client_id": "...",
  "balance": 0.0,
  "available_margin": 0.0,
  "used_margin": 0.0,
  "status": "active",
  "timestamp": "2026-01-21T..."
}
```

**Success Criteria:**

- HTTP 200 response
- Account data retrieved
- No actual trades placed
- Response time < 2000ms (DhanHQ API latency)

---

### Test 7: Firestore Data Integrity

**Objective:** Verify data persistence and consistency

**Steps:**

1. Generate ML signal → Check Firestore signals collection
2. Query portfolio → Verify Firestore portfolio collection
3. Check audit logs → Verify audit_logs collection

**Success Criteria:**

- Data persisted correctly
- Timestamps accurate
- No data loss
- Query latency < 100ms

---

### Test 8: Error Handling & Circuit Breakers

**Objective:** Test system resilience under failure conditions

**Test Scenarios:**

#### 8.1 Invalid Authentication

**Input:** Missing/invalid bearer token
**Expected:** HTTP 401 Unauthorized

#### 8.2 Rate Limiting

**Input:** 100+ requests in 1 minute
**Expected:** HTTP 429 Too Many Requests

#### 8.3 Invalid Request Payload

**Input:** Malformed JSON
**Expected:** HTTP 400 Bad Request

#### 8.4 Service Degradation

**Input:** Broker API timeout simulation
**Expected:** Graceful error, circuit breaker activation

**Success Criteria:**

- Proper error responses
- Circuit breakers functional
- No cascading failures
- Error messages actionable

---

## Test Execution Timeline

**Phase 1 - Health Checks (5 min):**

- Engine-A, B, C health verification ✅
- Load Balancer connectivity
- DNS resolution

**Phase 2 - API Discovery (10 min):**

- Engine-C endpoint mapping
- Authentication flow test
- Available operations inventory

**Phase 3 - ML Pipeline (15 min):**

- Signal generation (multiple symbols)
- Model inference timing
- Ensemble voting validation
- Firestore persistence check

**Phase 4 - Trading Flow (20 min):**

- Guardrail validation (all test cases)
- Paper mode order placement
- Portfolio query
- Order history retrieval

**Phase 5 - Real-Time Integration (10 min):**

- WebSocket connection test
- Ably channel subscription
- Event streaming verification

**Phase 6 - Broker Integration (10 min):**

- DhanHQ account query
- Holdings retrieval
- Margin availability check

**Phase 7 - Data Layer (10 min):**

- Firestore read/write tests
- Collection statistics
- Index performance

**Phase 8 - Error Scenarios (10 min):**

- Authentication failures
- Rate limiting
- Invalid requests
- Circuit breaker activation

**Total Estimated Time:** ~90 minutes

---

## Success Metrics

**Availability:**

- All 3 engines responding: 100%
- Load Balancer operational: 100%
- Database connectivity: 100%

**Performance:**

- Engine health checks: P95 < 500ms
- ML signal generation: P95 < 800ms
- Order validation: P95 < 1000ms
- Portfolio query: P95 < 500ms
- WebSocket latency: P95 < 100ms
- DhanHQ API calls: P95 < 2000ms

**Reliability:**

- Error rate: < 1%
- Circuit breakers: Functional
- Graceful degradation: Verified

**Data Integrity:**

- Firestore persistence: 100%
- Audit logging: 100%
- Real-time sync: < 500ms lag

---

## Risk Mitigation

**LIVE Mode Safeguards:**

- ✅ Trading guardrails enabled (₹500k cap, market hours, symbol validation)
- ✅ Paper mode testing first (no real orders)
- ✅ Read-only broker queries only
- ✅ No production user credentials used

**Rollback Plan:**

- All tests non-destructive
- No configuration changes during tests
- Production traffic unaffected
- Monitoring active throughout

---

## Next Steps

**Immediate (Starting Now):**

1. Test Engine-C /health endpoint
2. Map available API endpoints
3. Execute ML signal generation test
4. Run trading guardrail validation tests

**After E2E Tests:** 5. Generate test report (e2e_run.md) 6. Collect trace data (e2e_traces.json) 7. Document failures (e2e_failures.md if any) 8. Proceed to Task 5 (Capacity & Performance)

---

**Test Plan Status:** ✅ READY TO EXECUTE
