# backend/engine-core/README.md

## Engine Core - Market Data Ingestion

**Purpose**: Real-time market data aggregation from NSE/BSE with technical analysis and broadcasting to other engines.

**Technology**: Python, FastAPI, Firestore, WebSocket

### Directory Structure

```
engine-core/
├── src/
│   ├── api/
│   │   ├── routes_public/    # Public API endpoints (market data, symbols)
│   │   └── routes_internal/  # Internal endpoints (health, orchestration)
│   ├── services/
│   │   ├── orchestrators/    # Service orchestration logic
│   │   ├── auth/             # JWT token validation
│   │   └── firestore/        # Firestore R/W operations
│   ├── models/               # Pydantic models, TypedDict schemas
│   ├── config/               # Configuration loading
│   └── __init__.py
├── tests/
│   ├── unit/                 # Unit tests for services
│   └── integration/          # Integration tests with Firestore
├── Dockerfile
├── cloudrun.yaml
├── requirements.txt
└── README.md
```

### Environment Variables

```bash
# Development (.env)
PORT=8000
DEBUG=true
FIRESTORE_PROJECT=gen-lang-client-0779271931
CORS_ORIGINS=https://gen-lang-client-0779271931.web.app/
JWT_SECRET_KEY=<from Secret Manager>
```

### API Endpoints

#### Public
- `GET /api/market-data/{symbol}` - Live OHLCV data for symbol
- `GET /api/symbols` - List available symbols (NSE/BSE/MCX)
- `GET /api/indices` - Index data (Nifty50, Sensex, Bank Nifty)

#### Internal
- `GET /health` - Health check with service status
- `POST /api/internal/broadcast` - Receive market updates (from data feeds)

### Local Development

```bash
# Set environment variables
cp config/env/dev/engine-core.env.example .env
# Edit .env with local values

# Install dependencies
pip install -r requirements.txt

# Run server
python src/main.py

# Run tests
pytest tests/
```

### Cloud Run Deployment

```bash
# Build and deploy
# Build and deploy
gcloud run deploy engine-b \
  --source . \
  --region us-central1 \
  --set-env-vars="FIRESTORE_PROJECT=gen-lang-client-0779271931"
```

### Integration Points

- **Receives from**: Market data feeds (NSE, BSE, MCX APIs)
- **Sends to**: Engine Analytics (signals), Engine Execution (market context)
- **Firestore collections**: `market_data`, `symbols`, `indices`
- **Frontend**: WebSocket relay via Engine Execution

### Health Monitoring

```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "timestamp": "...", "components": {...}}
```

### Troubleshooting

- **Firestore permission denied**: Ensure GOOGLE_APPLICATION_CREDENTIALS set or Cloud Run service account has Datastore roles
- **Market data stale**: Check data feed connectivity; verify feed API keys in Secret Manager
- **High latency**: Check Firestore query indexes; verify regional configuration matches deployment
