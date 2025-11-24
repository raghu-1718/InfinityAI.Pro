# backend/engine-execution/README.md

## Engine Execution - Trade Execution & Real-time Coordination

**Purpose**: Secure trade execution via Dhan broker OAuth, WebSocket data aggregation, order management, and multi-engine orchestration (formerly Engine D responsibilities).

**Technology**: Python, FastAPI, WebSocket, Dhan OAuth, Firestore

### Directory Structure

```
engine-execution/
├── src/
│   ├── api/
│   │   ├── routes_public/    # Order, trade, WebSocket endpoints
│   │   └── routes_internal/  # Health, orchestration
│   ├── services/
│   │   ├── dhan_broker/      # Dhan OAuth, order execution
│   │   ├── order_manager/    # Order tracking, risk management
│   │   ├── ws_manager/       # WebSocket aggregation (migrated from Engine D)
│   │   ├── event_broadcaster/  # Real-time event distribution (Engine D)
│   │   ├── auth_service/     # JWT validation (Engine D)
│   │   ├── health_orchestrator/  # Multi-engine health monitoring (Engine D)
│   │   ├── chatbot/          # AI chatbot service (Engine D)
│   │   ├── firestore/        # Firestore R/W
│   │   └── orchestrators/    # Service orchestration
│   ├── models/               # Order schemas, execution models
│   ├── config/               # Config, risk rules
│   └── __init__.py
├── tests/
│   ├── unit/                 # Order, risk management tests
│   └── integration/          # Dhan OAuth, Firestore
├── Dockerfile
├── cloudrun.yaml
├── requirements.txt
└── README.md
```

### Environment Variables

```bash
# Development (.env)
PORT=8002
DEBUG=true
FIRESTORE_PROJECT=after-yesterday-473512-k3
DHAN_CLIENT_ID=your-client-id
DHAN_CLIENT_SECRET=your-client-secret
DHAN_REDIRECT_URI=http://localhost:8002/api/dhan/callback
ENGINE_CORE_URL=http://localhost:8000
ENGINE_ANALYTICS_URL=http://localhost:8001
JWT_SECRET_KEY=dev-key
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Production (from Secret Manager)
DHAN_CLIENT_ID=<from Secret Manager>
DHAN_CLIENT_SECRET=<from Secret Manager>
DHAN_REDIRECT_URI=https://infinityai-engine-execution-{hash}.a.run.app/api/dhan/callback
```

### API Endpoints

#### Public
- `GET /ws/dashboard` - WebSocket: Real-time market, signals, orders to frontend
- `POST /api/orders` - Place trade order
- `GET /api/orders/{order_id}` - Order status
- `POST /api/dhan/callback` - Dhan OAuth callback
- `GET /api/dhan/authorize` - Initiate OAuth flow

#### WebSocket Messages
```json
{
  "type": "market_update|signal|order_update|chatbot_message",
  "data": {...},
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Internal
- `GET /health` - Multi-engine health check
- `POST /api/internal/signals/subscribe` - Receive Engine Analytics signals

### Local Development

```bash
# Setup
cp config/env/dev/engine-execution.env.example .env
# Update DHAN credentials
pip install -r requirements.txt

# Run server
python src/main.py

# Run tests
pytest tests/
```

### Cloud Run Deployment

```bash
gcloud run deploy engine-execution \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DHAN_CLIENT_ID=projects/after-yesterday-473512-k3/secrets/dhan-client-id/versions/latest"
```

### Dhan OAuth Flow

1. User clicks "Connect Dhan Broker" in frontend
2. Frontend redirects to `/api/dhan/authorize`
3. User logs into Dhan and authorizes
4. Dhan redirects to `/api/dhan/callback` with auth code
5. Engine Execution exchanges code for access token (stored in Secret Manager)
6. Frontend receives JWT token for API access

### Order Management

**Risk Management Rules** (from `config/trading_config.ini`):
- Max single order size: 5% portfolio
- Max daily loss: 2% portfolio
- Max open positions: 10
- Min stop loss: 0.5%

### WebSocket Integration

Aggregates real-time data and broadcasts to frontend:
- Market data updates from Engine Core
- Trading signals from Engine Analytics
- Order execution status
- Chatbot responses
- System health alerts

### Integration Points

- **Subscribes to**: Engine Core (`/api/market-data/*`), Engine Analytics (`/api/ai-signals/*`)
- **Authenticates**: Via Dhan OAuth (user broking account)
- **Executes**: Orders via Dhan NSE/BSE bridge
- **Publishes**: Order updates, execution status to Firestore and WebSocket
- **Frontend**: Connected via `/ws/dashboard` WebSocket

### Chatbot Service (Migrated from Engine D)

Handles user inquiries about:
- Portfolio status
- Signal explanations
- Order management
- Market analysis
- Risk metrics

Access via WebSocket message: `{"type": "chatbot_message", "message": "..."}`

### Monitoring

```bash
# Check order execution pipeline
curl http://localhost:8002/api/orders/status | jq '.pending | length'

# Monitor WebSocket connections
curl http://localhost:8002/health | jq '.components.websocket.active_connections'

# Check Dhan OAuth status
curl http://localhost:8002/health | jq '.components.dhan_broker.authorized'
```

### Troubleshooting

- **Dhan OAuth fails**: Verify client ID/secret in Secret Manager; check redirect URI matches exactly
- **WebSocket drops**: Ensure frontend reconnection logic enabled; check Cloud Run memory (min 512MB)
- **Order execution timeout**: Verify Dhan API status; check market hours (NSE 9:15-15:30, BSE 9:15-15:30)
- **High WebSocket latency**: Monitor Firestore write throughput; may need to increase Cloud Run CPU
