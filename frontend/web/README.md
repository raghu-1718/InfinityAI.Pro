# frontend/web/README.md

## InfinityAI.Pro Frontend - React + Vite + Firebase

**Purpose**: Real-time trading dashboard with WebSocket data aggregation, portfolio management, and AI signal visualization.

**Technology**: React 18, TypeScript, Vite, TailwindCSS, Firebase Auth, Firestore, WebSocket

### Directory Structure

```
web/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx       # Main trading dashboard
│   │   ├── Portfolio.tsx       # User portfolio view
│   │   ├── SignalAnalysis.tsx  # AI signal explorer
│   │   ├── OrderHistory.tsx    # Trade history
│   │   ├── Settings.tsx        # User preferences, API keys
│   │   └── Login.tsx           # Firebase authentication
│   ├── components/
│   │   ├── MarketChart.tsx     # Real-time price charts
│   │   ├── SignalCard.tsx      # Trading signal display
│   │   ├── OrderForm.tsx       # Place trade order
│   │   ├── Chatbot.tsx         # AI chatbot interface
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── shared/             # Reusable UI components
│   ├── hooks/
│   │   ├── useWebSocket.ts     # WebSocket connection management
│   │   ├── useAuth.ts          # Firebase authentication
│   │   ├── useFirestore.ts     # Firestore R/W operations
│   │   ├── useMarketData.ts    # Real-time market data
│   │   └── useOrders.ts        # Order management
│   ├── lib/
│   │   ├── api-client/
│   │   │   ├── client.ts       # HTTP API client (base)
│   │   │   ├── market-api.ts   # Engine Core endpoints
│   │   │   ├── signals-api.ts  # Engine Analytics endpoints
│   │   │   └── orders-api.ts   # Engine Execution endpoints
│   │   ├── firebase/
│   │   │   ├── config.ts       # Firebase initialization
│   │   │   ├── auth.ts         # Auth service wrapper
│   │   │   └── firestore.ts    # Firestore wrapper
│   │   └── utils/
│   │       ├── formatters.ts   # Format numbers, dates, prices
│   │       ├── validators.ts   # Input validation
│   │       └── constants.ts    # App constants, symbols
│   ├── store/
│   │   ├── slices/
│   │   │   ├── authSlice.ts    # Redux auth state
│   │   │   ├── marketSlice.ts  # Market data state
│   │   │   ├── ordersSlice.ts  # Orders state
│   │   │   └── settingsSlice.ts
│   │   ├── store.ts            # Redux store setup
│   │   └── hooks.ts            # Redux hooks
│   ├── styles/
│   │   ├── tailwind.css        # TailwindCSS overrides
│   │   └── globals.css         # Global styles
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── public/
│   └── index.html
├── .env.example                # Environment variables template
├── .env.production             # Production config (git-ignored)
├── .firebaserc                 # Firebase project config
├── firebase.json               # Firebase hosting config
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md (this file)
```

### Environment Variables

```bash
# Development (.env.development)
VITE_API_ENGINE_CORE=http://localhost:8000
VITE_API_ENGINE_ANALYTICS=http://localhost:8001
VITE_API_ENGINE_EXECUTION=http://localhost:8002
VITE_WS_ENGINE_EXECUTION=ws://localhost:8002
VITE_FIREBASE_PROJECT_ID=after-yesterday-473512-k3
VITE_FIREBASE_API_KEY=<dev-key>
VITE_DEBUG=true

# Production (.env.production)
VITE_API_ENGINE_CORE=https://infinityai-engine-core-{hash}.a.run.app
VITE_API_ENGINE_ANALYTICS=https://infinityai-engine-analytics-{hash}.a.run.app
VITE_API_ENGINE_EXECUTION=https://infinityai-engine-execution-{hash}.a.run.app
VITE_WS_ENGINE_EXECUTION=wss://infinityai-engine-execution-{hash}.a.run.app
VITE_FIREBASE_PROJECT_ID=after-yesterday-473512-k3
VITE_FIREBASE_API_KEY=<prod-key>
VITE_DEBUG=false
```

### Local Development

```bash
# Install dependencies
npm install

# Create .env file (copy from .env.example)
cp .env.example .env.development
# Edit with local backend URLs

# Run dev server
npm run dev
# Open http://localhost:5173

# Run tests
npm run test

# Build for production
npm run build
```

### WebSocket Connection

The frontend maintains a single WebSocket connection to Engine Execution at `/ws/dashboard`:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

function Dashboard() {
  const { data, isConnected } = useWebSocket(
    import.meta.env.VITE_WS_ENGINE_EXECUTION + '/ws/dashboard'
  );

  // Receive real-time updates:
  // - Market data
  // - Trading signals
  // - Order status
  // - Chatbot messages
}
```

### Firebase Authentication

```typescript
import { useAuth } from '@/hooks/useAuth';

function App() {
  const { user, login, logout, loading } = useAuth();

  const handleLogin = async () => {
    await login(email, password);  // Firebase Auth
  };
}
```

### API Client Usage

```typescript
import { marketApi, signalsApi, ordersApi } from '@/lib/api-client';

// Fetch market data
const data = await marketApi.getMarketData('NIFTY');

// Get AI signals
const signals = await signalsApi.getSignals('NIFTY');

// Place order
const order = await ordersApi.createOrder({
  symbol: 'NIFTY',
  quantity: 1,
  price: 19200,
  type: 'LIMIT'
});
```

### Firebase Deployment

```bash
# Deploy to Firebase Hosting
firebase deploy --only hosting

# Deploy functions (if applicable)
firebase deploy --only functions

# Deploy firestore rules
firebase deploy --only firestore:rules
```

### Key Features

1. **Real-time Market Data**: Live charts, price updates via WebSocket
2. **AI Trading Signals**: Visual signal feed with confidence scores
3. **Order Management**: Place, modify, cancel orders; track execution
4. **Portfolio Dashboard**: Position tracking, P&L visualization
5. **Chatbot**: AI assistant for portfolio and market queries
6. **Settings**: User preferences, trading parameters, risk limits

### Components

#### Dashboard.tsx
- Real-time Nifty50, Sensex, BankNifty indices
- Market heatmap
- Recent signals feed
- Active orders
- WebSocket status

#### Portfolio.tsx
- Current holdings
- P&L summary
- Diversification charts
- Risk metrics

#### SignalAnalysis.tsx
- Browsable signal history
- Signal reasoning (Gemini explanations)
- Backtested performance
- Signal statistics

#### Chatbot.tsx
- AI responses to portfolio queries
- Order placement via chat
- Risk analysis
- Market insights

### Styling

TailwindCSS with custom configuration:
- Dark theme by default (trading industry standard)
- Responsive mobile design
- Chart theme consistency (TradingView-style colors)

### Testing

```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Performance Optimization

- Code splitting: lazy-load route components
- Image optimization: WebP with fallbacks
- Bundle analysis: `npm run build -- --analyze`
- Lighthouse score target: 90+

### Troubleshooting

- **WebSocket disconnects**: Check Engine Execution health; verify CORS headers
- **Firestore permission denied**: Ensure user authenticated; check Firestore rules
- **API 404 errors**: Verify backend service URLs in env variables; check Cloud Run deployment
- **Chatbot not responding**: Verify Engine Execution health; check Firestore database availability
