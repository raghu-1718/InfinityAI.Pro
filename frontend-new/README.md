# InfinityAI.Pro Frontend

Modern React + Vite + TypeScript + TailwindCSS frontend for InfinityAI.Pro trading platform.

## 🚀 Features

- **Real-time Engine Monitoring**: WebSocket connection to Engine D for live updates
- **Advanced Trading Intelligence**: AI-powered insights from Engine B
- **Trade Execution Control**: Direct integration with Engine C
- **Market Data Visualization**: Live feeds from Engine A
- **JWT Authentication**: Secure token-based auth via Engine D
- **Responsive Design**: Modern, dark-themed UI with TailwindCSS

## 📦 Tech Stack

- React 18
- TypeScript
- Vite
- TailwindCSS
- Zustand (State Management)
- React Query (Data Fetching)
- Axios (HTTP Client)
- Recharts (Data Visualization)
- React Router DOM

## 🛠️ Setup

### Install Dependencies

```bash
npm install
```

### Environment Configuration

Update `.env` with your actual GCP Cloud Run URLs:

```env
VITE_ENGINE_A_URL=https://engine-a-market-data-prod-573866363639.us-central1.run.app
VITE_ENGINE_B_URL=https://engine-b-ai-ml-prod-573866363639.us-central1.run.app
VITE_ENGINE_C_URL=https://engine-c-execution-prod-573866363639.us-central1.run.app
VITE_ENGINE_D_URL=https://engine-d-chatbot-prod-573866363639.us-central1.run.app
```

### Development

```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t infinityai-frontend:latest .
```

### Run Locally

```bash
docker run -p 8080:8080 infinityai-frontend:latest
```

### Deploy to GCP Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/after-yesterday-473512-k3/infinityai-frontend:v4.0.0

# Deploy to Cloud Run
gcloud run deploy infinityai-frontend \
  --image gcr.io/after-yesterday-473512-k3/infinityai-frontend:v4.0.0 \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080
```

## 📁 Project Structure

```
src/
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   └── Topbar.tsx           # Top header bar
│   ├── dashboard/
│   │   ├── LiveEngineGrid.tsx   # Real-time engine status
│   │   └── DashboardCard.tsx    # Metric cards
│   ├── strategy/
│   │   └── ExecutionPanel.tsx   # Trade execution controls
│   └── assistant/
│       └── ChatPanel.tsx        # AI chatbot
│
├── hooks/
│   ├── useEngineHealth.ts       # Engine health monitoring
│   ├── useWebSocketFeed.ts      # WebSocket connection
│   ├── useTradeExecution.ts     # Trade execution hooks
│   └── useAuth.ts               # Authentication
│
├── pages/
│   ├── Dashboard.tsx            # Main dashboard
│   ├── Engines.tsx              # Engine management
│   ├── Strategies.tsx           # Strategy overview
│   ├── StrategyExecution.tsx    # Execute strategies
│   ├── Analysis.tsx             # AI analysis
│   ├── Assistant.tsx            # AI assistant
│   └── Settings.tsx             # User settings
│
└── store/
    ├── authStore.ts             # Authentication state
    └── tradeStore.ts            # Trading state
```

## 🔗 Engine Integration

### Engine A (Market Data)
- Live NSE/BSE/MCX data
- Option chain analysis
- Real-time price feeds

### Engine B (AI/ML)
- AI-powered signals
- Sentiment analysis
- Predictive modeling

### Engine C (Trade Execution)
- Order placement
- Portfolio management
- Risk controls

### Engine D (Orchestration)
- Health monitoring
- WebSocket feeds
- AI chatbot

## 🎨 UI Components

All components use TailwindCSS with a dark theme optimized for trading:
- Primary: Green (#22c55e)
- Background: Dark Gray (#0a0a0a)
- Cards: Gray-800 with green accents

## 📊 Features by Page

### Dashboard
- Real-time engine health grid
- Portfolio summary cards
- P&L tracking
- Live updates via WebSocket

### Engines
- Detailed engine status
- Performance metrics
- Configuration management

### Strategies
- Strategy selection
- Backtesting results
- Performance analytics

### Strategy Execution
- Real-time execution panel
- Trade logs
- Capital allocation
- Start/stop controls

### Analysis
- AI market insights
- Sentiment heatmaps
- Correlation analysis
- Risk metrics

### Assistant
- Natural language interface
- Intent recognition
- Multi-engine queries

## 🔒 Security

- JWT token-based authentication
- Secure WebSocket connections
- HTTPS-only in production
- Token refresh mechanism

## 📝 License

Proprietary - InfinityAI.Pro
