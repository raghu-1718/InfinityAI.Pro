# Quick Reference - InfinityAI.Pro Developer Guide

Fast lookup guide for common tasks and commands.

---

## 🚀 Getting Started (5 minutes)

```bash
# Clone repo
git clone https://github.com/raghu-1718/InfinityAI.Pro.git
cd InfinityAI.Pro

# Run all services with Docker Compose
docker-compose -f docker-compose.engines.yml up -d

# Check health
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Start frontend
cd frontend/web && npm install && npm run dev
# Open http://localhost:5173
```

---

## 📂 Project Structure Map

```
backend/engine-core/        → Market data ingestion (Port 8000)
backend/engine-analytics/   → ML/AI signals (Port 8001)
backend/engine-execution/   → Trade execution + WebSocket (Port 8002)
backend/shared/             → Common Python utilities & clients
frontend/web/               → React + Vite dashboard
infra/firebase/             → Firestore rules
infra/gcp/                  → Terraform infrastructure
infra/ci-cd/                → GitHub Actions workflows
verification/suite/         → E2E tests
config/env/                 → Environment templates
```

---

## 🛠️ Common Tasks

### Setup Local Environment

```bash
# Backend (in separate terminal)
cd backend/engine-core
cp ../../config/env/dev/engine-core.env.example .env
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/main.py

# Frontend
cd frontend/web
cp ../../config/env/dev/firebase.env.example .env.development
npm install
npm run dev
```

### Run Tests

```bash
# Backend (from any engine directory)
pytest tests/ -v

# Frontend
npm run test

# Full E2E verification
cd verification/suite
python infinityai_verification_suite.py --environment development
```

### Build & Deploy

```bash
# Local Docker build
docker build -t infinityai-engine-core:latest backend/engine-core/

# Deploy to Cloud Run (manual)
gcloud run deploy engine-core \
  --image gcr.io/after-yesterday-473512-k3/engine-core:latest \
  --region us-central1

# Deploy via CI/CD (automatic)
git push origin main  # Triggers automatic deployment
```

---

## 🔌 API Endpoints

### Engine Core (Market Data)
```
GET /health                    # Health check
GET /api/market-data/{symbol}  # OHLCV data (e.g., NIFTY)
GET /api/symbols               # Available symbols
GET /api/indices               # Index data
```

### Engine Analytics (AI Signals)
```
GET /health                    # Health + model status
GET /api/ai-signals/{symbol}   # Trading signal
GET /api/predictions/{symbol}  # Price predictions
POST /api/sentiment            # Sentiment analysis
```

### Engine Execution (Trading)
```
GET /health                    # Multi-engine health
POST /api/orders               # Place order
GET /api/orders/{id}           # Order status
WS /ws/dashboard               # Real-time WebSocket
GET /api/dhan/authorize        # Dhan OAuth
```

---

## 🔐 Secrets & Configuration

### Development (.env)
```bash
PORT=8000
DEBUG=true
FIRESTORE_PROJECT=after-yesterday-473512-k3
JWT_SECRET_KEY=dev-key-change-in-production
```

### Production (Secret Manager)
```bash
# Access secrets via API
GEMINI_API_KEY=projects/after-yesterday-473512-k3/secrets/gemini-api-key/versions/latest
DHAN_CLIENT_SECRET=projects/after-yesterday-473512-k3/secrets/dhan-client-secret/versions/latest
```

### GCP Authentication
```bash
gcloud auth login
gcloud config set project after-yesterday-473512-k3
export GOOGLE_APPLICATION_CREDENTIALS=$HOME/gcp-key.json
```

---

## 🚢 Deployment Checklist

```
☐ Code review passed
☐ Tests passing locally (pytest, npm test)
☐ Environment variables configured (.env)
☐ Secrets available in Secret Manager (if prod)
☐ Firestore connection verified
☐ Firebase config updated
☐ Docker build successful
☐ Health endpoints respond 200
☐ WebSocket connects
☐ E2E verification passes
☐ Monitoring/alerts configured
☐ Rollback plan documented
```

---

## 🐛 Troubleshooting

### Engine won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Firestore permission denied
```bash
gcloud auth login
gcloud config set project after-yesterday-473512-k3
gcloud auth application-default login
```

### WebSocket connection fails
```bash
# Check Engine Execution health
curl https://infinityai-engine-execution-{hash}.a.run.app/health

# Verify CORS headers
curl -H "Origin: https://infinityai.pro" \
  https://infinityai-engine-execution-{hash}.a.run.app/ws/dashboard
```

### Import errors in Python
```bash
# Verify backend/shared is installed
cd backend/engine-core
pip install -e ../shared

# Check Python path
python -c "from backend.shared import clients; print('OK')"
```

---

## 📊 Monitoring & Logs

### Real-time Logs (Cloud Run)
```bash
gcloud run services log read engine-core --follow
gcloud run services log read engine-analytics --follow
gcloud run services log read engine-execution --follow
```

### Health Status
```bash
# All services
curl http://localhost:8000/health | jq '.status'
curl http://localhost:8001/health | jq '.status'
curl http://localhost:8002/health | jq '.status'
```

### Verify Deployment
```bash
gcloud run services list --region us-central1
gcloud run services describe engine-core --region us-central1
```

---

## 📚 Documentation Links

| Resource | Location |
|----------|----------|
| Project Overview | `README.md` |
| Deployment Guide | `DEPLOYMENT_GUIDE.md` |
| Engine Core | `backend/engine-core/README.md` |
| Engine Analytics | `backend/engine-analytics/README.md` |
| Engine Execution | `backend/engine-execution/README.md` |
| Shared Utilities | `backend/shared/README.md` |
| Frontend | `frontend/web/README.md` |
| GCP Infrastructure | `infra/gcp/README.md` |
| CI/CD | `infra/ci-cd/README.md` |
| Verification | `verification/suite/README.md` |
| Architecture | `.github/copilot-instructions.md` |

---

## 🔄 Git Workflow

```bash
# Create feature branch
git checkout -b feat/my-feature

# Make changes, commit
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feat/my-feature
# Open Pull Request on GitHub

# After approval, merge to main
# CI/CD automatically deploys to production
```

---

## ⚡ Performance Tips

### Local Development
- Use Docker Compose for consistent multi-service setup
- Enable file watching: `npm run dev` (frontend), `--reload` (Python)
- Check logs frequently: `docker-compose logs -f`

### Production
- Monitor Cloud Run metrics: https://console.cloud.google.com/run
- Scale services: `--max-instances=10`
- Enable caching for static assets
- Use CDN for frontend (included with Firebase Hosting)

---

## 🔗 Useful Links

- **GitHub**: https://github.com/raghu-1718/InfinityAI.Pro
- **GCP Console**: https://console.cloud.google.com
- **Firebase Console**: https://console.firebase.google.com
- **Cloud Run**: https://console.cloud.google.com/run
- **Frontend**: https://infinityai.pro (production)
- **Firestore**: https://console.cloud.google.com/firestore
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager

---

## 📞 Support

- **Issues**: GitHub Issues tab
- **Questions**: See README files in relevant directories
- **Team**: InfinityAI Team
- **Docs**: `/docs` directory

---

**Last Updated**: 2025-01-15
**Version**: 3.0.0
**Audience**: Developers, DevOps, QA
