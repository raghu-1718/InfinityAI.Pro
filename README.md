# InfinityAI.Pro - Enterprise AI-Powered Trading Platform

<div align="center">

![Version](https://img.shields.io/badge/version-3.0--enterprise-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Cloud Run](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28)
![DhanHQ](https://img.shields.io/badge/Broker-DhanHQ-orange)
![License](https://img.shields.io/badge/license-MIT-green)

**An enterprise-grade AI/ML trading platform for Indian markets (NSE/BSE) with real-time signal generation and automated execution**

[Live Demo](https://infinityai.pro) · [API Documentation](https://engine-a.infinityai.pro/docs) · [Architecture](#architecture)

</div>

---

## 🎯 Overview

InfinityAI.Pro is a production-ready algorithmic trading platform that combines **12+ enterprise ML/AI frameworks** with the **DhanHQ brokerage API** to deliver real-time trading signals and automated order execution. Built on Google Cloud Platform with a microservices architecture, it provides:

- 🤖 **AI-Powered Signal Generation** - Ensemble ML models (RandomForest, XGBoost, LightGBM)
- 📈 **Real-Time Trade Execution** - Direct integration with DhanHQ API
- 🔐 **OAuth 2.0 Authentication** - Secure broker authentication flow
- 🌐 **Cloud-Native Architecture** - Deployed on Google Cloud Run
- 📊 **Technical Analysis Engine** - 30+ indicators (RSI, MACD, Bollinger Bands, etc.)
- 🧠 **NLP Sentiment Analysis** - News-driven trading insights via Transformers

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           InfinityAI.Pro Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐    ┌──────────────────────────────────────────────────┐    │
│  │   Frontend  │    │              Google Cloud Platform               │    │
│  │   React.js  │◄──►│  ┌─────────────────────────────────────────────┐ │    │
│  │  Dashboard  │    │  │            Cloud Run Services               │ │    │
│  └─────────────┘    │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐  │ │    │
│         │           │  │  │ Engine A  │ │ Engine B  │ │ Engine C  │  │ │    │
│         │           │  │  │Orchestrat.│►│  AI/ML    │►│ Execution │  │ │    │
│         ▼           │  │  │ + OAuth   │ │ Signals   │ │  DhanHQ   │  │ │    │
│  ┌─────────────┐    │  │  └───────────┘ └───────────┘ └───────────┘  │ │    │
│  │  Firebase   │    │  └─────────────────────────────────────────────┘ │    │
│  │  Hosting    │    │                        │                         │    │
│  └─────────────┘    │  ┌─────────────────────▼───────────────────────┐ │    │
│                     │  │           Google Secret Manager              │ │    │
│                     │  │   (DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)       │ │    │
│                     │  └─────────────────────────────────────────────┘ │    │
│                     │                                                   │    │
│                     │  ┌─────────────────────────────────────────────┐ │    │
│                     │  │              Cloud Firestore                 │ │    │
│                     │  │   (Users, Trades, Signals, Portfolios)      │ │    │
│                     │  └─────────────────────────────────────────────┘ │    │
│                     └──────────────────────────────────────────────────┘    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Three-Engine Microservices Design

| Engine | Service Name | Port | Purpose | Cloud Run URL |
|--------|--------------|------|---------|---------------|
| **Engine A** | `infinityai-engine-a` | 8080 | Orchestration & OAuth | `https://infinityai-engine-a-[hash].run.app` |
| **Engine B** | `infinityai-engine-b` | 8080 | AI/ML Signal Generation | `https://infinityai-engine-b-[hash].run.app` |
| **Engine C** | `infinityai-engine-c-execution` | 8080 | Trade Execution | `https://infinityai-engine-c-execution-[hash].run.app` |

---

## 🔧 Engine Details

### Engine A - Orchestration & Dhan OAuth
**Path:** `backend/engine-analytics/`

The central orchestrator that manages authentication, coordinates between engines, and handles the complete trading workflow.

#### Key Features
- DhanHQ OAuth 2.0 authentication flow
- Request routing between Engine B and Engine C
- Background task execution for async trading
- Health monitoring and status endpoints

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info and status |
| `/healthz` | GET | Health check |
| `/api/auth/dhan/login` | GET | Redirect to DhanHQ OAuth login |
| `/api/auth/dhan/callback` | POST | Exchange auth code for access token |
| `/api/auth/dhan/validate` | GET | Validate current access token |
| `/api/v1/trade/start` | POST | **Main trading endpoint** - orchestrates full flow |

#### Trade Flow Example
```bash
# 1. Start OAuth flow
curl https://engine-a.infinityai.pro/api/auth/dhan/login

# 2. After authentication, execute trade
curl -X POST https://engine-a.infinityai.pro/api/v1/trade/start \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "qty": 1}'
```

#### Response Example
```json
{
  "status": "execution_scheduled",
  "signal": {
    "symbol": "RELIANCE",
    "signal": "BUY",
    "confidence": 78.5,
    "predicted_price": 2850.50
  },
  "execution_payload": {
    "transaction_type": "BUY",
    "exchange_segment": "NSE_EQ",
    "security_id": "1333",
    "quantity": 1
  }
}
```

---

### Engine B - AI/ML Signal Generation
**Path:** `backend/engine-core/`

The intelligence layer powered by 12 enterprise ML/AI frameworks for advanced signal generation.

#### ML/AI Stack

| Framework | Version | Purpose |
|-----------|---------|---------|
| **TensorFlow** | 2.15+ | Deep learning models |
| **PyTorch** | 2.1+ | Neural network training |
| **Keras** | 3.0+ | High-level API for DL |
| **Scikit-learn** | 1.4.2 | Traditional ML algorithms |
| **XGBoost** | 2.1.1 | Gradient boosting |
| **LightGBM** | 4.3.0 | Fast gradient boosting |
| **Transformers** | 4.35+ | NLP sentiment analysis |
| **OpenCV** | 4.8+ | Pattern recognition |
| **NLTK** | 3.8+ | Text processing |
| **spaCy** | 3.7+ | NLP pipeline |
| **MLflow** | 2.9+ | Model versioning |
| **H2O.ai** | 3.44+ | AutoML capabilities |

#### Key Features
- Ensemble ML predictions (RandomForest + XGBoost + LightGBM)
- Sentiment analysis for news-driven trading
- Batch signal processing (up to 50 symbols)
- Model versioning and hot-reload
- 30+ technical indicators computed in real-time

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info with loaded models |
| `/healthz` | GET | Health check with ML capabilities |
| `/api/v1/signal` | POST | Generate single symbol signal |
| `/api/v1/signal/batch` | POST | Batch signal generation |
| `/api/v1/sentiment` | POST | NLP sentiment analysis |
| `/api/v1/models` | GET | List available ML models |
| `/api/v1/train` | POST | Trigger model training |
| `/api/v1/capabilities` | GET | ML framework capabilities |
| `/dhan/holdings` | GET | Fetch user holdings |
| `/dhan/positions` | GET | Fetch open positions |
| `/dhan/funds` | GET | Fetch fund limits |

#### Signal Generation Example
```bash
curl -X POST https://engine-b.infinityai.pro/api/v1/signal \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TCS", "fast": true}'
```

#### Response
```json
{
  "symbol": "TCS",
  "signal": "BUY",
  "confidence": 85.7,
  "predicted_price": 4250.00,
  "timestamp": "2025-11-29T10:30:00.000Z",
  "model_version": "ai-ml-3.0-enterprise"
}
```

#### Batch Processing
```bash
curl -X POST https://engine-b.infinityai.pro/api/v1/signal/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE", "TCS", "INFY", "HDFCBANK"], "fast": true}'
```

---

### Engine C - DhanHQ Trade Execution
**Path:** `backend/engine-execution/`

The execution layer providing direct integration with DhanHQ API for order management.

#### Supported Order Types
- **Market Orders** - Immediate execution at market price
- **Limit Orders** - Execute at specified price
- **Stop-Loss Orders** - Automatic sell on price drop
- **Bracket Orders** - Combined TP and SL
- **After-Market Orders (AMO)** - Queue for next day

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service status |
| `/healthz` | GET | Health check |
| `/api/dhan/place-order` | POST | Place new order |
| `/api/dhan/cancel-order` | POST | Cancel existing order |
| `/api/dhan/modify-order` | POST | Modify order parameters |
| `/api/dhan/orders` | GET | Get all day orders |
| `/api/dhan/order/{id}` | GET | Get specific order |
| `/api/dhan/positions` | GET | Get open positions |
| `/api/dhan/holdings` | GET | Get holdings |

#### Order Placement Example
```bash
curl -X POST https://engine-c.infinityai.pro/api/dhan/place-order \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "BUY",
    "exchange_segment": "NSE_EQ",
    "product_type": "INTRADAY",
    "order_type": "MARKET",
    "validity": "DAY",
    "security_id": "1333",
    "quantity": 1,
    "price": 0.0
  }'
```

#### Response
```json
{
  "status": "success",
  "order_id": "1234567890",
  "dhan_response": {
    "status": "success",
    "data": {
      "orderId": "1234567890",
      "orderStatus": "PENDING"
    }
  }
}
```

---

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── engine-analytics/          # Engine A - Orchestration
│   │   ├── src/
│   │   │   └── main.py            # FastAPI application
│   │   ├── requirements.txt       # Python dependencies
│   │   └── Dockerfile             # Container definition
│   │
│   ├── engine-core/               # Engine B - AI/ML
│   │   ├── src/
│   │   │   ├── main.py            # FastAPI + ML models
│   │   │   └── services/
│   │   │       ├── ml_model_manager.py    # Model lifecycle
│   │   │       └── feature_engineer.py   # Technical indicators
│   │   ├── requirements.txt       # ML dependencies (TF, PyTorch, etc.)
│   │   └── Dockerfile             # ML-optimized container
│   │
│   ├── engine-execution/          # Engine C - Trade Execution
│   │   ├── src/
│   │   │   └── main.py            # FastAPI + DhanHQ integration
│   │   ├── requirements.txt       # DhanHQ SDK
│   │   └── Dockerfile             # Container definition
│   │
│   ├── shared/                    # Shared utilities
│   ├── strategies/                # Trading strategies
│   │   ├── momentum.py
│   │   └── mean_reversion.py
│   └── docker-compose.yml         # Local development
│
├── frontend/
│   ├── web/                       # React.js dashboard
│   │   ├── src/
│   │   ├── functions/             # Firebase Cloud Functions
│   │   └── firebase.json
│   └── dashboard_ui_refinement.py
│
├── config/
│   ├── trading_config.ini
│   └── env/
│
├── infra/
│   ├── gcp/                       # GCP configurations
│   ├── firebase/                  # Firebase rules
│   └── ci-cd/                     # GitHub Actions
│
├── scripts/
│   ├── deploy-3-engine-architecture.ps1
│   ├── cleanup-legacy-gcp-resources.ps1
│   └── ...
│
├── monitoring/
│   ├── alert-error-rate.json
│   ├── alert-high-latency.json
│   └── dashboard-config.json
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FIREBASE_SETUP.md
│   ├── DHAN_OAUTH_SETTINGS.md
│   └── ...
│
└── README.md
```

---

## 🚀 Deployment

### GCP Configuration

| Resource | Configuration |
|----------|---------------|
| **Project ID** | `after-yesterday-473512-k3` |
| **Region** | `us-central1` |
| **Container Registry** | `gcr.io/after-yesterday-473512-k3` |
| **Firebase Project** | `after-yesterday-473512-k3` |

### Cloud Run Services

```bash
# Engine A - Orchestration
gcloud run deploy infinityai-engine-a \
  --image=gcr.io/after-yesterday-473512-k3/engine-analytics:v3-dhan \
  --region=us-central1 \
  --memory=1Gi --cpu=1 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_API_SECRET=dhan-api-secret:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Engine B - AI/ML (requires more resources for ML frameworks)
gcloud run deploy infinityai-engine-b \
  --image=gcr.io/after-yesterday-473512-k3/engine-core:v3-ml \
  --region=us-central1 \
  --memory=4Gi --cpu=2 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"

# Engine C - Execution
gcloud run deploy infinityai-engine-c-execution \
  --image=gcr.io/after-yesterday-473512-k3/engine-execution:v3-dhan \
  --region=us-central1 \
  --memory=1Gi --cpu=1 \
  --set-secrets="DHAN_CLIENT_ID=dhan-client-id:latest,DHAN_ACCESS_TOKEN=dhan-access-token:latest"
```

### Secrets Management

All sensitive credentials are stored in **Google Secret Manager**:

| Secret Name | Description |
|-------------|-------------|
| `dhan-client-id` | DhanHQ OAuth Client ID |
| `dhan-api-secret` | DhanHQ API Secret |
| `dhan-access-token` | DhanHQ Access Token |

---

## 🔥 Firebase Integration

### Firestore Collections

| Collection | Purpose |
|------------|---------|
| `users` | User profiles and preferences |
| `trades` | Trade history and execution logs |
| `signals` | Historical signal data |
| `portfolios` | Portfolio snapshots |
| `credentials` | Encrypted broker credentials |

### Firebase Hosting

Custom domains configured:
- `infinityai.pro` → Firebase Hosting
- `engine-a.infinityai.pro` → Cloud Run Engine A
- `engine-b.infinityai.pro` → Cloud Run Engine B
- `engine-c.infinityai.pro` → Cloud Run Engine C

### Cloud Functions

Located in `frontend/web/functions/`:
- `storeCredentials` - Securely store broker credentials
- `analyzePortfolio` - Portfolio analysis trigger
- `startTrading` - Trading workflow trigger

---

## 💻 Local Development

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+ (for frontend)
- Google Cloud CLI (gcloud)
- DhanHQ account with API access

### Quick Start

```bash
# Clone repository
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro

# Start all engines with Docker Compose
cd backend
docker-compose up --build

# Services available at:
# Engine A: http://localhost:8001
# Engine B: http://localhost:8002
# Engine C: http://localhost:8003
```

### Environment Variables

Create `.env` in `backend/`:

```env
# DhanHQ Credentials
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token
DHAN_API_SECRET=your_api_secret

# Service URLs (Docker Compose)
ENGINE_B_URL=http://engine-core:8080
ENGINE_C_URL=http://engine-execution:8080

# GCP Project
GOOGLE_CLOUD_PROJECT=after-yesterday-473512-k3
```

---

## 📊 Technical Indicators

Engine B calculates 30+ technical indicators:

| Category | Indicators |
|----------|------------|
| **Trend** | SMA (5, 10, 20, 50), EMA (12, 26), MACD, ADX |
| **Momentum** | RSI (14), Stochastic, ROC, Williams %R, MFI |
| **Volatility** | Bollinger Bands, ATR, Standard Deviation |
| **Volume** | OBV, VWAP, Accumulation/Distribution |
| **Price** | Pivot Points, Fibonacci Retracements |

---

## 🔒 Security

- ✅ **No Hardcoded Secrets** - All credentials in Google Secret Manager
- ✅ **OAuth 2.0** - Secure broker authentication
- ✅ **HTTPS Only** - TLS encryption for all traffic
- ✅ **IAM Policies** - Role-based access control
- ✅ **Container Isolation** - Each engine in isolated container
- ✅ **Audit Logging** - Cloud Logging for all operations

---

## 📈 Monitoring

### Cloud Monitoring Dashboards

- **Error Rate Alerts** - `monitoring/alert-error-rate.json`
- **Latency Alerts** - `monitoring/alert-high-latency.json`
- **Memory Alerts** - `monitoring/alert-memory.json`

### Health Check Endpoints

```bash
# Check all engines
curl https://infinityai-engine-a-[hash].run.app/healthz
curl https://infinityai-engine-b-[hash].run.app/healthz
curl https://infinityai-engine-c-execution-[hash].run.app/healthz
```

---

## 🧪 Testing

```bash
# Run local tests
cd backend
pytest tests/

# Test ML integration
python scripts/test-ml-integration.py

# Test E2E flow
./scripts/test-e2e-flow.sh
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Detailed system architecture |
| [FIREBASE_SETUP.md](docs/FIREBASE_SETUP.md) | Firebase configuration guide |
| [DHAN_OAUTH_SETTINGS.md](docs/DHAN_OAUTH_SETTINGS.md) | DhanHQ OAuth setup |
| [ML-INTEGRATION-GUIDE.md](ML-INTEGRATION-GUIDE.md) | ML framework integration |
| [DEPLOYMENT-GUIDE.md](DEPLOYMENT-GUIDE.md) | Production deployment |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Raghu** - [@raghu-1718](https://github.com/raghu-1718)

---

<div align="center">

**Built with ❤️ for the Indian Trading Community**

[![GCP](https://img.shields.io/badge/Powered%20by-Google%20Cloud-4285F4?logo=google-cloud)](https://cloud.google.com)
[![DhanHQ](https://img.shields.io/badge/Broker-DhanHQ-orange)](https://dhan.co)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)

</div>
