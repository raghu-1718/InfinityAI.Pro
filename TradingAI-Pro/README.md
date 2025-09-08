# TradingAI-Pro

A modular trading automation platform for cloud and local deployment.

## Monorepo Structure

- `shared/`: Common utilities and settings across workloads.
- `api-webhooks/`: FastAPI app for webhooks, chat, and user management (deploy to Vercel).
- `engine/`: Always-on trading engine (deploy to Northflank/Fly.io/DO).
- `config/`: Environment variables and user store examples.
- `infra/`: GitHub Actions, Kubernetes manifests, and deployment docs.

## Quick Start

1. **Local Dev**:
   - Copy `config/.env.example` to `config/.env` and fill in your credentials.
   - Copy `config/user_store.example.json` to `config/user_store.json` and add your users.
   - Install deps: `pip install -r api-webhooks/requirements.txt` and `pip install -r engine/requirements.txt`.
   - Run API: `cd api-webhooks && uvicorn api.main:app --reload`.
   - Run Engine: `cd engine && python app/run_engine.py`.

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
