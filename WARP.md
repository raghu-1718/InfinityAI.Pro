# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Local Development

```bash
# Start backend services
cd backend
python ultra_aggressive_main.py  # Main trading engine
python integration_test.py       # Run integration tests

# Start frontend (React)
cd frontend/web
npm install
npm start                        # Development server on http://localhost:3000
npm run build                   # Production build
npm test                        # Run frontend tests

# Run integration tests
python backend/integration_test.py
python tests/integration_test_suite.py
python tests/multi_cloud_integration_test.py
```

### Docker Development

```bash
# Run all services with Docker Compose
docker-compose up -d                    # Start all engines + Redis
docker-compose -f docker-compose.engines.yml up  # Start specific engines

# Build individual engines
docker build -f backend/Dockerfile -t infinityai-backend .
docker build -f backend/Dockerfile.engine-a .
docker build -f backend/Dockerfile.engine-b .
docker build -f backend/Dockerfile.engine-c .
docker build -f backend/Dockerfile.engine-d .
```

### Production Deployment

```powershell
# Complete platform deployment to multi-cloud
.\deploy-complete-platform.ps1 -Environment production

# Deploy specific components
.\scripts\deploy-aws-engines.ps1           # AWS ECS deployment
.\scripts\deploy_engine_a_gcp.ps1         # GCP Cloud Run deployment
.\scripts\deploy_frontend_aws.ps1         # S3 + CloudFront deployment

# Health checks and monitoring
.\scripts\cloud_health_check.ps1
.\verify-platform-health.ps1
```

### Testing Commands

```bash
# Backend testing
python backend/performance_test.py
python backend/full_app_test.py
python backend/test_integration.py

# Frontend testing  
cd frontend/web && npm test

# Integration testing
python integration_test.py
python tests/integration_analysis_simple.py

# API testing
curl http://localhost:8000/health
curl http://localhost:8000/api/chatbot/chatbot-status
```

## High-Level Architecture

### Multi-Cloud Engine Architecture

InfinityAI.Pro uses a distributed microservices architecture across multiple cloud providers:

**Engine Distribution:**
- **Engine A (Market Data)**: GCP Cloud Run - Real-time market data processing
- **Engine B (AI/ML)**: GCP Cloud Run - AI model inference and analysis  
- **Engine C (Trade Execution)**: AWS ECS - Live trade execution via Dhan API
- **Engine D (AI Chatbot)**: AWS ECS - Natural language trading interface
- **Ultra Aggressive Engine**: GCP Cloud Run - High-frequency trading strategies

**Data Flow:**
```
Market Data (Engine A) → AI Analysis (Engine B) → Signal Generation → Trade Execution (Engine C)
                                ↓
User Interface ← AI Chatbot (Engine D) ← Trading Signals
```

### Core Components

**Backend (`/backend`):**
- **Main Entry Points**: `ultra_aggressive_main.py`, `auto_trading_system.py`
- **Trading Logic**: `real_ultra_aggressive_trader.py`, `autonomous_trader.py`
- **API Integration**: `dhan_webhook_handler.py`, `dhan_credential_manager.py`
- **Load Balancing**: `load_balancer.py` manages traffic across engines
- **Monitoring**: `continuous_monitor.py`, `trading_dashboard.py`

**Frontend (`/frontend/web`):**
- React 18 with Material-UI components
- Real-time WebSocket connections for live trading updates
- Responsive dashboard for multi-device access
- Proxy configuration points to backend engines

**Infrastructure (`/scripts`, `/infrastructure`):**
- Multi-cloud deployment scripts (AWS + GCP)
- Kubernetes manifests and Docker configurations
- Auto-scaling and health monitoring
- IAM and security configurations

### Trading System Architecture

**Signal Processing Pipeline:**
1. Market data ingestion (multiple sources: Dhan, Yahoo Finance, etc.)
2. AI ensemble analysis (18+ models including GPT-4, Claude, custom models)
3. Risk assessment and position sizing
4. Order execution with trailing stops
5. Real-time monitoring and portfolio adjustment

**Risk Management System:**
- Dynamic position sizing based on volatility
- Trailing stop losses with profit protection
- Daily loss limits and circuit breakers
- Real-time P&L monitoring
- Automatic session termination on risk thresholds

**AI Integration:**
- Multi-model ensemble for trade signal generation
- Natural language processing for chatbot interface
- Real-time sentiment analysis
- Pattern recognition and technical analysis
- Voice command processing (speech-to-text)

### Configuration Management

**Environment Variables** (`.env`):
- Trading API credentials (Dhan, etc.)
- AI service API keys (OpenAI, Azure, AWS)
- Cloud infrastructure credentials
- Database and Redis connections

**Trading Configuration** (`config/trading_config.ini`):
- Risk management parameters
- Trading timeframes and instruments
- AI confidence thresholds
- Position sizing rules
- Notification settings

### Deployment Architecture

**Production Deployment:**
- **Frontend**: Vercel + AWS S3/CloudFront (infinityai.pro)
- **API Gateway**: AWS Application Load Balancer
- **Compute**: AWS ECS + GCP Cloud Run
- **Database**: Redis for caching, persistent storage for trade history
- **Monitoring**: CloudWatch + GCP Operations Suite
- **CDN**: Global edge locations for low latency

**Service Ports:**
- Engine A: 8100 (Market Data)
- Engine B: 8101 (AI/ML)  
- Engine C: 8102 (Trade Execution)
- Engine D: 8103 (AI Chatbot)
- Ultra Aggressive: 8000 (Main trading engine)
- Redis: 6379

### Key Integration Points

**Dhan Trading API:**
- Real-time order execution
- Portfolio monitoring
- Market data feeds
- Webhook-based event handling

**AI Services Integration:**
- Azure OpenAI for GPT-4 Turbo
- AWS SageMaker for YOLO v8
- Anthropic Claude for analysis
- Custom financial BERT models

**Multi-Cloud Orchestration:**
- Cross-cloud service communication
- Health check and failover systems
- Distributed logging and monitoring
- Auto-scaling based on market conditions

## Development Workflow

### Adding New Trading Strategies
1. Create strategy class in `/backend` following existing patterns
2. Add configuration parameters to `config/trading_config.ini`
3. Integrate with risk management system
4. Add tests in `/tests`
5. Update deployment scripts if needed

### Modifying AI Models
1. Update model configurations in respective engine files
2. Test with sandbox/paper trading first
3. Monitor performance metrics and accuracy
4. Deploy incrementally across engines

### Frontend Changes
1. Develop in `/frontend/web` with hot reload (`npm start`)
2. Test responsive design across devices  
3. Ensure real-time data connections work
4. Build and test production bundle

### Infrastructure Updates
1. Test changes in development environment
2. Update Docker configurations and scripts
3. Deploy to staging environment first
4. Run comprehensive integration tests
5. Deploy to production with health monitoring

This architecture enables rapid development while maintaining production-grade reliability and performance for high-frequency trading operations.