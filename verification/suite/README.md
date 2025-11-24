# verification/suite/README.md

## Verification & Testing Suite

**Purpose**: Automated end-to-end testing, health monitoring, and deployment verification for InfinityAI.Pro.

**Technology**: Python, pytest, requests, Firebase Admin SDK

### Directory Structure

```
suite/
├── checks/
│   ├── check_engine_core.py        # Engine Core health and API validation
│   ├── check_engine_analytics.py   # Engine Analytics health and signals
│   ├── check_engine_execution.py   # Engine Execution, orders, WebSocket
│   ├── check_firestore_rw.py       # Firestore read/write verification
│   ├── check_firebase_auth.py      # Firebase authentication flow
│   ├── check_firebase_hosting.py   # Frontend deployment health
│   └── __init__.py
├── config/
│   ├── environments.py             # Environment configurations (dev, staging, prod)
│   ├── test_data.py                # Test fixtures and sample data
│   └── __init__.py
├── conftest.py                     # pytest fixtures and hooks
├── infinityai_verification_suite.py # Main entrypoint
├── requirements-test.txt           # Test dependencies
└── README.md (this file)
```

### Running Verification Suite

#### Full Suite (All Checks)
```bash
cd verification/suite

# Install test dependencies
pip install -r requirements-test.txt

# Run all checks (requires GCP credentials and deployed services)
python infinityai_verification_suite.py

# Run with specific environment
python infinityai_verification_suite.py --environment production
```

#### Individual Checks
```bash
# Check specific engine
pytest checks/check_engine_core.py -v

# Check Firestore connectivity
pytest checks/check_firestore_rw.py -v

# Check Firebase authentication
pytest checks/check_firebase_auth.py -v

# Check frontend availability
pytest checks/check_firebase_hosting.py -v
```

#### Continuous Monitoring
```bash
# Run verification every 5 minutes
watch -n 300 'python infinityai_verification_suite.py'

# Or use cron (Linux/Mac)
*/5 * * * * cd ~/InfinityAI.Pro && python verification/suite/infinityai_verification_suite.py
```

### Environment Configuration

Verification suite supports three environments:

#### Development
```bash
python infinityai_verification_suite.py --environment development
# Checks: localhost:8000/8001/8002, local Firestore emulator
```

#### Staging
```bash
python infinityai_verification_suite.py --environment staging
# Checks: staging Cloud Run deployments
```

#### Production
```bash
python infinityai_verification_suite.py --environment production
# Checks: production Cloud Run services at infinityai.pro
```

### Verification Checks

#### Engine Core (check_engine_core.py)
- ✅ Service health endpoint (`/health`)
- ✅ Market data API (`/api/market-data/{symbol}`)
- ✅ Symbols endpoint (`/api/symbols`)
- ✅ Response time < 500ms
- ✅ Firestore connectivity

#### Engine Analytics (check_engine_analytics.py)
- ✅ Service health and model status
- ✅ AI signals endpoint (`/api/ai-signals/{symbol}`)
- ✅ Predictions API (`/api/predictions/{symbol}`)
- ✅ Gemini API connectivity
- ✅ Model loading (TensorFlow)
- ✅ Response time < 1s

#### Engine Execution (check_engine_execution.py)
- ✅ Service health
- ✅ Order API (`/api/orders`, `/api/orders/{id}`)
- ✅ Dhan OAuth callback URL configured
- ✅ WebSocket endpoint availability
- ✅ Multi-engine orchestration (pinging Core, Analytics)
- ✅ Order placement (test trade)

#### Firestore Verification (check_firestore_rw.py)
- ✅ Write operation (create test document)
- ✅ Read operation (retrieve document)
- ✅ Update operation
- ✅ Delete operation
- ✅ Collection queries
- ✅ Indexes available
- ✅ Cleanup (delete test data)

#### Firebase Auth (check_firebase_auth.py)
- ✅ Firebase project connectivity
- ✅ User registration
- ✅ Email/password login
- ✅ JWT token generation
- ✅ Token validation
- ✅ User logout/cleanup

#### Firebase Hosting (check_firebase_hosting.py)
- ✅ Domain resolution (infinityai.pro)
- ✅ HTTPS certificate valid
- ✅ Frontend loads successfully
- ✅ Static assets accessible
- ✅ Response headers correct (CSP, CORS)
- ✅ Page load time < 3s

### Output & Reports

All verification runs generate reports:

```bash
# Console output (real-time)
# Sample:
# ✅ Engine Core: HEALTHY (response: 234ms)
# ✅ Engine Analytics: HEALTHY (models loaded)
# ✅ Engine Execution: HEALTHY (WebSocket ready)
# ✅ Firestore: READABLE & WRITABLE (5 collections)
# ✅ Firebase Auth: FUNCTIONAL (test user created/cleaned)
# ✅ Firebase Hosting: LIVE (response: 1.2s)
#
# === FINAL RESULT: ALL SYSTEMS HEALTHY ===
```

JSON report saved to `verification/reports/latest/verification-{timestamp}.json`:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "environment": "production",
  "overall_status": "healthy",
  "checks": {
    "engine_core": {
      "status": "healthy",
      "response_time_ms": 234,
      "version": "1.0.0"
    },
    "engine_analytics": {
      "status": "healthy",
      "models_loaded": true,
      "gemini_api": "accessible"
    },
    "engine_execution": {
      "status": "healthy",
      "websocket_ready": true,
      "orchestration": "ok"
    },
    "firestore": {
      "status": "readable_and_writable",
      "collections": 5,
      "test_passed": true
    },
    "firebase_auth": {
      "status": "functional",
      "test_user_created": true,
      "cleanup": true
    },
    "firebase_hosting": {
      "status": "live",
      "response_time_ms": 1200,
      "ssl_valid": true
    }
  },
  "alerts": []
}
```

### Fixtures & Test Data

Import test fixtures:

```python
from config.test_data import (
    SAMPLE_MARKET_DATA,
    SAMPLE_SIGNAL,
    TEST_USER_EMAIL,
    TEST_ORDER_PAYLOAD
)

# Use in tests
market_data = SAMPLE_MARKET_DATA  # Real-world sample OHLCV data
signal = SAMPLE_SIGNAL  # Example trading signal
```

### CI/CD Integration

In GitHub Actions (`.github/workflows/health-check.yml`):

```yaml
- name: Run Verification Suite
  run: |
    python verification/suite/infinityai_verification_suite.py \
      --environment production \
      --email slack@infinityai.pro
```

### Troubleshooting

#### "Service not reachable (timeout)"
- Verify service deployed: `gcloud run services list`
- Check service URL in env config
- Verify network connectivity: `ping infinityai-engine-core-{hash}.a.run.app`

#### "Firestore permission denied"
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` set (GCP service account key)
- Verify service account has `roles/datastore.user`

#### "Firebase Auth test fails"
- Verify Firebase project ID correct
- Check Firebase config in `config/environments.py`
- Ensure email sign-up enabled in Firebase console

#### "WebSocket timeout"
- Verify Engine Execution healthy: `curl https://infinityai-engine-execution-{hash}.a.run.app/health`
- Check Cloud Run memory (min 512MB for WebSocket)
- Verify CORS configuration includes frontend domain

### Adding New Checks

```python
# checks/check_my_service.py
import pytest
from checks.conftest import get_service_url

def test_my_service_health():
    url = get_service_url("my-service", environment="production")
    response = requests.get(f"{url}/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_my_service_api():
    # Your test logic
    pass
```

Add to `infinityai_verification_suite.py`:
```python
from checks.check_my_service import *

# Will auto-discover and run all test_* functions
```

### Dependencies

```
pytest>=7.0
requests>=2.28.0
firebase-admin>=6.0.0
google-cloud-firestore>=2.0.0
websockets>=10.0
python-dotenv>=0.21.0
```
