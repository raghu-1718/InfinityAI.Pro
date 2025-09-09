# TradingAI-Pro

An advanced, production-grade AI trading platform with real-time execution, comprehensive risk management, and sophisticated strategy engine.

## Monorepo Structure

- `shared/`: Common utilities and settings across workloads.
- `api-webhooks/`: FastAPI app for webhooks, chat, and user management (deploy to Vercel).
- `engine/`: Always-on trading engine (deploy to Northflank/Fly.io/DO).
- `config/`: Environment variables and user store examples.
- `infra/`: GitHub Actions, Kubernetes manifests, and deployment docs.

## New Advanced Features

### Real-Time Execution Engine
- **Order Management**: Advanced order lifecycle management with status tracking
- **Position Management**: Real-time position tracking with P&L calculation
- **Risk Management**: Comprehensive risk controls with real-time monitoring
- **Execution Engine**: Multi-threaded async execution with broker integration

### Market Data Integration
- **Feed Manager**: Multi-feed market data aggregation
- **Real-time Processing**: WebSocket-based live data streaming
- **Symbol Management**: Dynamic subscription/unsubscription
- **Data Validation**: Tick-level data validation and normalization

### Advanced Strategies
- **Breakout Strategy**: Volume and momentum confirmed breakouts
- **Signal Confidence**: ML-based signal confidence scoring
- **Multi-timeframe**: Support for multiple timeframe analysis
- **Risk-adjusted Sizing**: Dynamic position sizing based on risk metrics

### Production Features
- **Async Architecture**: Full async/await implementation for scalability
- **Error Handling**: Comprehensive error handling and recovery
- **Monitoring**: Real-time performance and health monitoring
- **Logging**: Structured logging with multiple levels
- **Graceful Shutdown**: Clean shutdown handling for production deployment

## Quick Start

1. **Local Dev**:
   - Copy `config/.env.example` to `config/.env` and fill in your credentials.
   - Copy `config/user_store.example.json` to `config/user_store.json` and add your users.
   - Install deps: `pip install -r api-webhooks/requirements.txt` and `pip install -r engine/requirements.txt`.
   - Run API: `cd api-webhooks && uvicorn api.main:app --reload`.
   - Run Engine: `cd engine && python app/run_engine.py`.

### Advanced Engine
For the new advanced engine:
- Run Advanced Engine: `cd engine && python app/advanced_engine.py`
- This includes real-time market data, advanced strategies, and comprehensive risk management

## Deploy

### Vercel (API-Webhooks)
- Import `github.com/Raghu-my/InfinityAI.Pro` into Vercel.
- Set Root Directory to `api-webhooks`.
- Add env vars from `config/.env.example`.
- Deploy automatically on push to `main`.

### Engine (Northflank/Fly.io/Render)
- Build from `engine/` folder.
- Use `engine/Dockerfile` or Docker Compose.
- Mount `config/user_store.json` and `.env` as secrets.
- Set restart policy to `always`.

### GitHub Actions
- `infra/github/workflows/deploy-vercel.yml`: Deploys API on changes to `api-webhooks/` or `shared/`.
- `infra/github/workflows/deploy-engine.yml`: Builds engine image and deploys on changes to `engine/` or `shared/`.
- Add secrets: `VERCEL_TOKEN`, `NORTHFLANK_API_TOKEN`, etc.

## Credentials Setup

- **Local**: Use `config/.env` and `config/user_store.json`.
- **Vercel**: Set env vars in project settings.
- **Northflank**: Set secrets in service config.

Important: Never commit real tokens. Use the examples as templates.

## Dhan Postback URL

Set in Dhan developer portal: `https://your-vercel-domain.vercel.app/webhook/{user_id}`

Replace `{user_id}` with your actual user ID (e.g., `LGSU85831L`).
