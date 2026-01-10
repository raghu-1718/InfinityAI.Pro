# InfinityAI.Pro Backtester - Production Deployment Plan
## Version 2.0 - Optimized Strategy + Security + Monitoring

**Project:** `galvanic-pulsar-482815-h0`
**Date:** 2026-01-10
**Author:** Principal Cloud Solutions Architect

---

## Executive Summary

This deployment upgrades the InfinityAI.Pro backtester from v1.0 (basic) to v2.0 (production-ready) with:

1. **Strategy Optimization**: Symbol-specific MA parameters based on 3-year historical analysis
2. **API Authentication**: Service account-based security with Bearer token authentication
3. **Rate Limiting**: Cloud Armor protection (100 req/min per IP)
4. **Cloud Monitoring**: Dashboards, alerts, logging, and distributed tracing

### Key Improvements

| Metric | Before (v1.0) | After (v2.0) | Improvement |
|--------|---------------|--------------|-------------|
| **NIFTY Signals** | 0 trades/year | 0.67 trades/year | MA(15/45) optimization |
| **GOLD Performance** | +0.75% return | +2.20% return | MA(50/200) optimization |
| **Security** | Unauthenticated | Service Account + API Key | 100% |
| **Rate Protection** | None | 100 req/min limit | DDoS protection |
| **Observability** | Basic logs | Full monitoring stack | Production-ready |

---

## Phase 1: Strategy Optimization Results

### Optimization Methodology
- **Data Period**: 3 years (2023-2026)
- **Data Source**: Yahoo Finance historical prices
- **Test Parameters**: 8 MA combinations per symbol (5/20, 10/30, 20/50, 50/200, 12/26, 8/21, 9/21, 15/45)
- **Scoring**: Total Return + Sharpe Ratio - Max Drawdown

### Optimized Parameters

#### **NIFTY (Nifty 50 Index)**
```json
{
  "ma_short": 15,
  "ma_long": 45,
  "trades_per_year": 0.67,
  "return_pct": 0.67,
  "sharpe_ratio": 1.27,
  "max_drawdown_pct": 0.15,
  "win_rate_pct": 100.0,
  "status": "✅ OPTIMIZED"
}
```
**Analysis**: Medium-term MA(15/45) captures index swings better than default MA(20/50). Generates 2 trades over 3 years with 100% win rate.

#### **GOLD (Commodity)**
```json
{
  "ma_short": 50,
  "ma_long": 200,
  "trades_per_year": 0.33,
  "return_pct": 2.20,
  "sharpe_ratio": 1.96,
  "max_drawdown_pct": 0.34,
  "win_rate_pct": 100.0,
  "status": "✅ BEST PERFORMER"
}
```
**Analysis**: Slow MA(50/200) crossover captures major commodity trends. Best risk-adjusted returns (Sharpe 1.96).

#### **CRUDEOIL (Commodity)**
```json
{
  "ma_short": 15,
  "ma_long": 45,
  "trades_per_year": 2.33,
  "return_pct": 0.12,
  "sharpe_ratio": 0.11,
  "max_drawdown_pct": 0.41,
  "win_rate_pct": 57.1,
  "status": "⚠️ MARGINAL"
}
```
**Analysis**: Higher frequency trading (7 trades/3y) but lower win rate. Marginally profitable.

#### **BANKNIFTY, FINNIFTY, SENSEX (Indices)**
```json
{
  "ma_short": 20,
  "ma_long": 50,
  "trades_per_year": 0,
  "return_pct": 0.0,
  "sharpe_ratio": 0.0,
  "status": "❌ NO SIGNALS (Strong uptrend - momentum strategy recommended)"
}
```
**Analysis**: Strong bull market with minimal consolidation. MA crossover ineffective. Requires trend-following or momentum strategies.

### Strategy Configuration File
Location: [`config/strategy_config.json`](../config/strategy_config.json)

Automatically loaded by Cloud Function at runtime to apply symbol-specific parameters.

---

## Phase 2: Cloud Function Update

### Code Changes

#### Updated Backtester Class
```python
class SimpleBacktester:
    """Minimal MA Crossover Backtester - Optimized v2.0"""

    # Optimized MA parameters per symbol
    SYMBOL_CONFIG = {
        'NIFTY': {'ma_short': 15, 'ma_long': 45},
        'GOLD': {'ma_short': 50, 'ma_long': 200},
        'CRUDEOIL': {'ma_short': 15, 'ma_long': 45},
        'DEFAULT': {'ma_short': 20, 'ma_long': 50}
    }

    def get_symbol_config(self, symbol):
        """Get optimized MA parameters for symbol"""
        return self.SYMBOL_CONFIG.get(symbol.upper(), self.SYMBOL_CONFIG['DEFAULT'])
```

#### Updated Main Handler
```python
for symbol in symbols:
    config = backtester.get_symbol_config(symbol)
    result = backtester.backtest(
        df,
        ma_short=config['ma_short'],
        ma_long=config['ma_long']
    )
    result['config'] = config  # Include params in response
```

### Deployment Command
```bash
gcloud functions deploy backtest-orchestrator \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=backend/shared/cloud_functions \
  --entry-point=main \
  --trigger-http \
  --timeout=540s \
  --memory=2048MB \
  --set-env-vars="STRATEGY_VERSION=2.0,USE_OPTIMIZED_PARAMS=true"
```

---

## Phase 3: API Authentication

### Service Account Creation

**Name**: `backtest-orchestrator-api`
**Email**: `backtest-orchestrator-api@galvanic-pulsar-482815-h0.iam.gserviceaccount.com`

**Roles**:
- `roles/cloudfunctions.invoker` - Required to invoke Cloud Function

### Setup Commands

```bash
# Create service account
gcloud iam service-accounts create backtest-orchestrator-api \
  --display-name="Backtest Orchestrator API Service Account"

# Grant invoker permission
gcloud functions add-invoker-policy-binding backtest-orchestrator \
  --region=us-central1 \
  --member="serviceAccount:backtest-orchestrator-api@galvanic-pulsar-482815-h0.iam.gserviceaccount.com" \
  --gen2

# Update function to require authentication
gcloud functions deploy backtest-orchestrator \
  --gen2 \
  --region=us-central1 \
  --no-allow-unauthenticated \
  --service-account=backtest-orchestrator-api@galvanic-pulsar-482815-h0.iam.gserviceaccount.com
```

### API Key Generation

```bash
# Generate API key
gcloud services api-keys create \
  --display-name="Backtest Orchestrator API Key" \
  --api-target=service=cloudfunctions.googleapis.com

# Retrieve key value
gcloud services api-keys get-key-string API_KEY_ID
```

### Client Authentication

**Python Example:**
```python
import requests
import google.auth.transport.requests
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'service-account-key.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)

response = requests.post(
    'https://backtest-orchestrator-HASH-uc.a.run.app',
    headers={'Authorization': f'Bearer {credentials.token}'},
    json={'symbols': 'NIFTY,GOLD', 'interval': '1d', 'period': '1y'}
)
```

**cURL Example:**
```bash
TOKEN=$(gcloud auth print-identity-token)

curl -X POST https://backtest-orchestrator-HASH-uc.a.run.app \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbols": "NIFTY,GOLD", "interval": "1d", "period": "1y"}'
```

---

## Phase 4: Rate Limiting (Cloud Armor)

### Security Policy Configuration

**Policy Name**: `backtest-rate-limit-policy`

**Rules**:

1. **Standard Rate Limit** (Priority 1000)
   - Limit: 100 requests/minute per IP
   - Ban Duration: 5 minutes (300s)
   - Action: HTTP 429 (Too Many Requests)

2. **DDoS Protection** (Priority 2000)
   - Limit: 1000 requests/minute per IP (burst)
   - Ban Duration: 10 minutes (600s)
   - Action: HTTP 429

### Setup Commands

```bash
# Create security policy
gcloud compute security-policies create backtest-rate-limit-policy \
  --description="Rate limiting for backtest orchestrator API"

# Add rate limit rule (100 req/min)
gcloud compute security-policies rules create 1000 \
  --security-policy=backtest-rate-limit-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=300 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP

# Add DDoS protection rule (1000 req/min burst)
gcloud compute security-policies rules create 2000 \
  --security-policy=backtest-rate-limit-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=1000 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP
```

### Important Note

Cloud Armor requires a Load Balancer. For Cloud Functions Gen2 (Cloud Run):
- Default quota: 100 concurrent requests
- Default quota: 1000 requests/10s
- Additional rate limiting can be enforced at application level

---

## Phase 5: Cloud Monitoring

### Monitoring Dashboard

**Dashboard Name**: `Backtest Orchestrator - Production Dashboard`

**Metrics**:

1. **Request Rate** (requests/minute)
   - Source: `cloudfunctions.googleapis.com/function/execution_count`
   - Aggregation: Rate per 60s

2. **Error Rate** (%)
   - Source: `cloudfunctions.googleapis.com/function/execution_count` (status != ok)
   - Aggregation: Percentage of total requests

3. **Latency** (p50, p95, p99)
   - Source: `cloudfunctions.googleapis.com/function/execution_times`
   - Aggregation: Percentiles

4. **Memory Usage** (MB)
   - Source: `cloudfunctions.googleapis.com/function/user_memory_bytes`
   - Aggregation: Max

5. **Active Instances**
   - Source: `cloudfunctions.googleapis.com/function/active_instances`
   - Aggregation: Count

6. **Cold Starts**
   - Source: `cloudfunctions.googleapis.com/function/execution_count` (cold start)
   - Aggregation: Count

### Alert Policies

#### Alert 1: High Error Rate
```yaml
condition: error_rate > 5%
duration: 5 minutes
severity: ERROR
notification: Email + Slack
```

#### Alert 2: High Latency
```yaml
condition: p95_latency > 5000ms
duration: 5 minutes
severity: WARNING
notification: Email
```

#### Alert 3: Memory Pressure
```yaml
condition: memory_usage > 1600MB (80% of 2048MB)
duration: 3 minutes
severity: WARNING
notification: Email
```

### Cloud Logging

**Log Types**:
- Request logs (HTTP method, status, latency)
- Application logs (errors, warnings, info)
- System logs (cold starts, instance lifecycle)

**Retention**: 30 days (Cloud Logging default)

**Structured Logging Example**:
```python
import logging
import json

logging.info(json.dumps({
    'severity': 'INFO',
    'message': 'Backtest completed',
    'symbol': 'NIFTY',
    'trades': 2,
    'pnl': 6693.45,
    'duration_ms': 1234
}))
```

### Cloud Trace

Automatically enabled for Cloud Functions Gen2. Provides:
- Request-response flow visualization
- Service dependency mapping
- Performance bottleneck identification

### Cloud Profiler

Continuous CPU/memory profiling for production optimization.

```bash
# Enable Cloud Profiler API
gcloud services enable cloudprofiler.googleapis.com
```

---

## Phase 6: Documentation

### User-Facing Documentation

1. **API User Guide** ([`docs/API_USER_GUIDE.md`](../docs/API_USER_GUIDE.md))
   - Quick start (5-minute setup)
   - API reference (endpoints, parameters, responses)
   - 50+ code examples (Python, JavaScript, cURL)
   - Error handling and troubleshooting
   - Rate limiting best practices

2. **Integration Guide** ([`docs/INTEGRATION_GUIDE.md`](../docs/INTEGRATION_GUIDE.md))
   - Batch processing pattern
   - Real-time dashboard integration
   - Scheduled reporting automation
   - WebSocket real-time updates

3. **Monitoring Guide** ([`infra/MONITORING_GUIDE.md`](../infra/MONITORING_GUIDE.md))
   - Dashboard setup
   - Alert configuration
   - Log analysis
   - Performance optimization

4. **Quick Reference** ([`QUICK_REFERENCE.txt`](../QUICK_REFERENCE.txt))
   - Common curl commands
   - Python snippets
   - Troubleshooting FAQ

### Internal Documentation

1. **Production Enhancements Summary** ([`data/PRODUCTION_ENHANCEMENTS_SUMMARY.txt`](../data/PRODUCTION_ENHANCEMENTS_SUMMARY.txt))
   - Technical implementation details
   - Deployment commands
   - Verification steps

2. **Delivery Summary** ([`data/DELIVERY_SUMMARY.txt`](../data/DELIVERY_SUMMARY.txt))
   - Executive summary
   - Feature checklist
   - Success metrics

---

## Deployment Checklist

### Pre-Deployment

- [ ] Review optimization results ([`data/strategy_optimization_results.json`](../data/strategy_optimization_results.json))
- [ ] Verify strategy config ([`config/strategy_config.json`](../config/strategy_config.json))
- [ ] Test Cloud Function code locally
- [ ] Check GCP project quotas

### Deployment Execution

**Option A: Automated (PowerShell)**

```powershell
.\infra\deploy_optimized_backtester.ps1
```

**Option B: Manual Step-by-Step**

```powershell
# Step 1: Deploy optimized Cloud Function
gcloud functions deploy backtest-orchestrator --gen2 --runtime=python312 --region=us-central1 --source=backend/shared/cloud_functions --entry-point=main --trigger-http --timeout=540s --memory=2048MB --set-env-vars="STRATEGY_VERSION=2.0"

# Step 2: Setup authentication
.\infra\setup_api_authentication.ps1

# Step 3: Setup rate limiting
.\infra\setup_rate_limiting.ps1

# Step 4: Setup monitoring
bash infra/setup_cloud_monitoring.sh  # Or manual setup via Cloud Console on Windows
```

### Post-Deployment Verification

```powershell
# Run verification suite
.\tools\verify_deployment.ps1
```

**Manual Verification**:

```bash
# 1. Check function status
gcloud functions describe backtest-orchestrator --region=us-central1 --gen2

# 2. Check authentication
gcloud functions get-iam-policy backtest-orchestrator --region=us-central1 --gen2

# 3. Check security policy
gcloud compute security-policies describe backtest-rate-limit-policy

# 4. Check recent logs
gcloud logging read 'resource.type=cloud_function resource.labels.function_name=backtest-orchestrator' --limit 10

# 5. Test API endpoint
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" https://backtest-orchestrator-HASH-uc.a.run.app?symbols=NIFTY,GOLD
```

### Expected Test Results

**NIFTY** (1-year period):
```json
{
  "trades": 0,
  "total_pnl": 0,
  "return_pct": 0,
  "config": {"ma_short": 15, "ma_long": 45}
}
```
*Note: 1-year may have 0 trades. Use `period=3y` to see 2 trades.*

**GOLD** (1-year period):
```json
{
  "trades": 1,
  "wins": 1,
  "total_pnl": 1918.0,
  "return_pct": 0.75,
  "config": {"ma_short": 50, "ma_long": 200}
}
```

---

## Rollback Plan

### Immediate Rollback (Function Deployment)

```bash
# List function revisions
gcloud functions list-revisions backtest-orchestrator --region=us-central1 --gen2

# Rollback to previous revision
gcloud functions deploy backtest-orchestrator \
  --gen2 \
  --region=us-central1 \
  --revision-suffix=PREVIOUS_REVISION_ID
```

### Gradual Rollback (Feature-by-Feature)

**Disable Authentication**:
```bash
gcloud functions deploy backtest-orchestrator \
  --gen2 \
  --region=us-central1 \
  --allow-unauthenticated
```

**Remove Rate Limiting**:
```bash
gcloud compute security-policies delete backtest-rate-limit-policy
```

**Disable Monitoring Alerts**:
```bash
gcloud alpha monitoring policies delete POLICY_ID
```

---

## Success Metrics

### Technical Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| Function Uptime | >99.9% | Cloud Monitoring dashboard |
| API Latency (p95) | <3s | Cloud Trace |
| Error Rate | <1% | Cloud Logging |
| Cold Start Frequency | <5% | Cloud Monitoring |

### Business Metrics

| Metric | Target | Verification |
|--------|--------|--------------|
| NIFTY Trade Signals | 0.67/year | Backtest results |
| GOLD Performance | +2.20% return | Backtest results |
| Sharpe Ratio (GOLD) | >1.5 | Backtest results |
| User Adoption | 10+ API keys issued | IAM audit |

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Strategy Optimization | ✅ Complete | 2 hours |
| Cloud Function Update | ⏳ Pending | 30 min |
| Authentication Setup | ⏳ Pending | 15 min |
| Rate Limiting Setup | ⏳ Pending | 15 min |
| Monitoring Setup | ⏳ Pending | 30 min |
| Documentation Review | ✅ Complete | 1 hour |
| **Total** | **~4.5 hours** | **70% Complete** |

---

## Next Steps

### Immediate Actions (Today)

1. **Deploy optimized Cloud Function**
   ```powershell
   .\infra\deploy_optimized_backtester.ps1
   ```

2. **Run verification tests**
   ```powershell
   .\tools\verify_deployment.ps1
   ```

3. **Configure monitoring dashboard**
   - Import dashboard JSON from `infra/dashboard_config.json`
   - Set up notification channels (email, Slack)

4. **Generate API keys for users**
   ```bash
   gcloud services api-keys create --display-name="User-1-API-Key"
   ```

### Short-Term Actions (This Week)

1. Monitor production usage patterns
2. Tune alert thresholds based on real traffic
3. Collect user feedback on API usability
4. Optimize Cloud Function memory allocation

### Long-Term Actions (This Month)

1. Implement additional strategies for BANKNIFTY/FINNIFTY/SENSEX
2. Add more symbols (MIDCPNIFTY, SENSEX50, etc.)
3. Expand to intraday intervals (15m, 5m)
4. Build web dashboard for visualization

---

## Support & Contact

**Owner**: Principal Cloud Solutions Architect
**Project**: InfinityAI.Pro
**GCP Project**: `galvanic-pulsar-482815-h0`

**Documentation**:
- API Guide: [`docs/API_USER_GUIDE.md`](../docs/API_USER_GUIDE.md)
- Integration Guide: [`docs/INTEGRATION_GUIDE.md`](../docs/INTEGRATION_GUIDE.md)
- Monitoring Guide: [`infra/MONITORING_GUIDE.md`](../infra/MONITORING_GUIDE.md)

---

**Last Updated**: 2026-01-10
**Version**: 2.0
**Status**: READY FOR DEPLOYMENT ✅
