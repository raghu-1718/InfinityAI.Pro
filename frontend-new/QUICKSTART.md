# 🚀 Quick Start Guide - InfinityAI.Pro Frontend

## Prerequisites

- Node.js 20+ installed
- npm or yarn
- Google Cloud SDK (`gcloud` CLI)
- Docker (for local testing)
- Access to GCP project: `after-yesterday-473512-k3`

## 1. Install Dependencies

```bash
cd frontend-new
npm install
```

## 2. Configure Environment

The `.env` file should be configured with canonical Cloud Run URLs:

```env
VITE_ENGINE_A_URL=https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app
VITE_ENGINE_B_URL=https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app
VITE_ENGINE_C_URL=https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app
VITE_ENGINE_D_URL=https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app
```

**Production URLs** (after custom domain DNS configuration):
- Engine A (Market Data): `https://api.infinityai.pro`
- Engine C (Execution): `https://api.infinityai.pro`
- Engine D (Orchestration): `https://engine.infinityai.pro`

## 3. Run Locally

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## 4. Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` folder.

## 5. Test Production Build Locally

```bash
npm run preview
```

Or with Docker:

```bash
docker build -t infinityai-frontend:test .
docker run -p 8080:8080 infinityai-frontend:test
```

Visit: `http://localhost:8080`

## 6. Deploy to GCP Cloud Run

### Automated Deployment

```powershell
.\deploy.ps1
```

### Manual Deployment

```bash
# Build and push image
gcloud builds submit --tag gcr.io/after-yesterday-473512-k3/infinityai-frontend:v4.0.0

# Deploy to Cloud Run
gcloud run deploy infinityai-frontend \
  --image gcr.io/after-yesterday-473512-k3/infinityai-frontend:v4.0.0 \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=512Mi \
  --cpu=1
```

## 7. Verify Deployment

```bash
# Get service URL
gcloud run services describe infinityai-frontend \
  --region=us-central1 \
  --format='value(status.url)'

# Check logs
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=infinityai-frontend' \
  --limit=50 \
  --format=json
```

## 🔧 Development Tips

### Hot Reload

The dev server supports hot module replacement. Changes to React components will be reflected immediately.

### Type Checking

```bash
npm run lint
```

### Build Analysis

Check the build output for bundle size:

```bash
npm run build
# Check dist/ folder
```

## 📂 Project Structure

```
frontend-new/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page components
│   ├── hooks/            # Custom React hooks
│   ├── store/            # Zustand state management
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── .env                  # Environment variables
├── package.json          # Dependencies
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS config
├── Dockerfile            # Production container
└── nginx.conf            # NGINX configuration
```

## 🌐 Available Routes

- `/` → Dashboard (redirects)
- `/dashboard` → Main dashboard with engine status
- `/engines` → Engine management
- `/strategies` → Trading strategies
- `/strategies/execute` → Strategy execution panel
- `/analysis` → AI market analysis
- `/assistant` → AI chatbot
- `/settings` → User settings

## 🔌 Engine Integration

The frontend connects to all 4 backend engines:

### Engine A (Market Data)
- Canonical URL: `https://infinityai-engine-a-ckxt6xvshq-uc.a.run.app`
- Production URL: `https://api.infinityai.pro`
- Features: Live market data, option chains

### Engine B (AI/ML)
- Canonical URL: `https://infinityai-engine-b-ckxt6xvshq-uc.a.run.app`
- Features: AI signals, sentiment analysis

### Engine C (Trade Execution)
- Canonical URL: `https://infinityai-engine-c-execution-ckxt6xvshq-uc.a.run.app`
- Production URL: `https://api.infinityai.pro`
- Features: Order placement, portfolio management

### Engine D (Orchestration)
- Canonical URL: `https://infinityai-engine-d-ckxt6xvshq-uc.a.run.app`
- Production URL: `https://engine.infinityai.pro`
- Features: Health monitoring, WebSocket, chatbot

## 🐛 Troubleshooting

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### CORS Issues

Ensure your backend engines have CORS configured to allow requests from the frontend domain.

### WebSocket Connection Fails

Check that Engine D supports WebSocket connections and the URL is correct.

## 📊 Monitoring

View real-time logs in GCP Console:
https://console.cloud.google.com/run/detail/us-central1/infinityai-frontend/logs

## 🔐 Security

- All API requests use HTTPS
- JWT tokens managed by `authStore`
- Secure headers configured in NGINX
- CSP policies enabled

## 🎯 Next Steps

1. **Enhance Components**: Add more detailed visualizations
2. **Real Data Integration**: Connect to actual Engine B AI signals
3. **Trade Execution**: Implement ExecutionPanel for Engine C
4. **Analysis Dashboard**: Add charts and metrics from Engine B
5. **WebSocket Enhancements**: Real-time updates for all pages

---

**🚀 You're ready to deploy InfinityAI.Pro Frontend!**
