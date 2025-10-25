# InfinityAI.Pro - Platform Architecture Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        INFINITYAI.PRO TRADING PLATFORM                          │
│                     Google Cloud Platform (us-central1)                         │
│                           Production Environment                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │         Frontend Application (React + TypeScript)              │            │
│  │                                                                │            │
│  │  • Vite Build System                                          │            │
│  │  • Material-UI + TailwindCSS                                  │            │
│  │  • WebSocket Real-time Updates                                │            │
│  │  • Firebase Authentication                                     │            │
│  │                                                                │            │
│  │  URL: https://infinityai.pro                                  │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                             ↕                                                   │
│                      HTTPS / WebSocket                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND MICROSERVICES                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             │
│  │   Engine A       │  │   Engine B       │  │   Engine C       │             │
│  │  Market Data     │  │   AI/ML Core     │  │ Trade Execution  │             │
│  │                  │  │                  │  │                  │             │
│  │ • NSE/BSE Feeds  │  │ • TensorFlow     │  │ • Dhan OAuth     │             │
│  │ • MCX Data       │  │ • Scikit-learn   │  │ • Order Mgmt     │             │
│  │ • Technical      │  │ • Price Predict  │  │ • Risk Mgmt      │             │
│  │   Indicators     │  │ • Sentiment      │  │ • Position Sync  │             │
│  │                  │  │   Analysis       │  │                  │             │
│  │ FastAPI          │  │ FastAPI          │  │ FastAPI          │             │
│  │ Python 3.9+      │  │ Python 3.9+      │  │ Python 3.9+      │             │
│  │                  │  │                  │  │                  │             │
│  │ 9 dependencies   │  │ 17 dependencies  │  │ 9 dependencies   │             │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘             │
│          ↓                      ↓                      ↓                        │
│          └──────────────────────┼──────────────────────┘                        │
│                                 ↓                                               │
│  ┌────────────────────────────────────────────────────────┐                    │
│  │              Engine D - AI Chatbot Orchestrator        │                    │
│  │                                                         │                    │
│  │  • Multi-Engine Coordination                          │                    │
│  │  • WebSocket Broadcasting                              │                    │
│  │  • Real-time Data Aggregation                          │                    │
│  │  • NLU Processing                                       │                    │
│  │                                                         │                    │
│  │  FastAPI | Python 3.9+ | 11 dependencies               │                    │
│  └────────────────────────────────────────────────────────┘                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SERVERLESS FUNCTIONS                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────┐            │
│  │              Firebase Functions (18 deployed)                  │            │
│  │                                                                │            │
│  │  • User Management          • Portfolio Sync                  │            │
│  │  • AI Analysis              • Dhan Credentials                │            │
│  │  • Trading Controls         • Holdings Sync                   │            │
│  │  • Batch Operations         • Analytics                       │            │
│  │                                                                │            │
│  │  Node.js | 5 dependencies per function group                 │            │
│  └────────────────────────────────────────────────────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          DATA & AI SERVICES                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │  Cloud          │  │  Vertex AI      │  │  Secret         │                │
│  │  Firestore      │  │  Gemini 1.5 Pro │  │  Manager        │                │
│  │                 │  │                 │  │                 │                │
│  │ • Users         │  │ • AI Models     │  │ • API Keys      │                │
│  │ • Portfolios    │  │ • Predictions   │  │ • OAuth Tokens  │                │
│  │ • Positions     │  │ • Analysis      │  │ • DB Creds      │                │
│  │ • Orders        │  │ • Insights      │  │                 │                │
│  │ • Watchlists    │  │                 │  │                 │                │
│  │                 │  │                 │  │                 │                │
│  │ NoSQL Database  │  │ ML/AI Service   │  │ Secure Storage  │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL INTEGRATIONS                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │  Dhan Broker    │  │  NSE/BSE        │  │  MCX            │                │
│  │  API            │  │  Market Data    │  │  Commodity Data │                │
│  │                 │  │                 │  │                 │                │
│  │ • OAuth 2.0     │  │ • Live Quotes   │  │ • Futures       │                │
│  │ • Order Exec    │  │ • Historical    │  │ • Options       │                │
│  │ • Position Sync │  │ • Corporate     │  │ • Spot Prices   │                │
│  │ • Portfolio     │  │   Actions       │  │                 │                │
│  │                 │  │                 │  │                 │                │
│  │ REST API        │  │ WebSocket/REST  │  │ REST API        │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Flow 1: Market Data Processing Pipeline

```
┌──────────────┐
│ NSE/BSE/MCX  │ Real-time Market Feeds
│  Data Feeds  │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│    Engine A              │ Step 1: Data Ingestion
│    Market Data Service   │ • Fetch live quotes
│                          │ • Parse data streams
│    • WebSocket Listener  │ • Calculate indicators
│    • Data Normalization  │
│    • Tech Indicators     │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Engine B              │ Step 2: AI Analysis
│    AI/ML Service         │ • Feature engineering
│                          │ • Model inference
│    • Feature Extract     │ • Signal generation
│    • Model Inference     │
│    • Prediction          │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Engine C              │ Step 3: Trade Decision
│    Execution Service     │ • Risk validation
│                          │ • Position checks
│    • Risk Check          │ • Order preparation
│    • Position Mgmt       │
│    • Order Validation    │
└──────────┬───────────────┘
           │
           ↓ (if validated)
┌──────────────────────────┐
│    Dhan API              │ Step 4: Execution
│    Trade Execution       │ • OAuth verification
│                          │ • Order placement
│    • OAuth Flow          │ • Confirmation
│    • Order Placement     │
│    • Confirmation        │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Cloud Firestore       │ Step 5: Persistence
│    Database              │ • Save position
│                          │ • Update portfolio
│    • Position Update     │ • Log transaction
│    • Portfolio Sync      │
│    • Trade History       │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Frontend              │ Step 6: User Notification
│    Dashboard             │ • Real-time update
│                          │ • Position display
│    • WebSocket Update    │ • Alert notification
│    • UI Refresh          │
│    • Notification        │
└──────────────────────────┘
```

### Flow 2: User Authentication & Session

```
┌──────────────┐
│   User       │ Login Request
│   Browser    │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│    Frontend              │ Step 1: Auth Request
│    React App             │
│                          │
│    • Login Form          │
│    • Firebase Auth SDK   │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Firebase Auth         │ Step 2: Authentication
│    Identity Platform     │
│                          │
│    • Email/Password      │
│    • Social Login        │
│    • Token Generation    │
└──────────┬───────────────┘
           │
           ↓ (JWT Token)
┌──────────────────────────┐
│    Frontend              │ Step 3: Token Storage
│    Local Storage         │
│                          │
│    • Store JWT           │
│    • Set Auth Header     │
└──────────┬───────────────┘
           │
           ↓ (Authenticated Requests)
┌──────────────────────────┐
│    Backend Services      │ Step 4: Token Validation
│    Engines A/B/C/D       │
│                          │
│    • Verify JWT          │
│    • Check Permissions   │
│    • Process Request     │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Cloud Firestore       │ Step 5: User Data
│    User Collection       │
│                          │
│    • User Profile        │
│    • Preferences         │
│    • Portfolio           │
└──────────────────────────┘
```

### Flow 3: AI Chatbot Query Processing

```
┌──────────────┐
│   User       │ "What's my portfolio performance?"
│   Query      │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│    Engine D              │ Step 1: Query Analysis
│    Chatbot Service       │
│                          │
│    • NLU Processing      │
│    • Intent Detection    │
│    • Entity Extraction   │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Vertex AI Gemini      │ Step 2: Context Understanding
│    AI Model              │
│                          │
│    • Semantic Analysis   │
│    • Context Building    │
│    • Response Planning   │
└──────────┬───────────────┘
           │
           ↓ (Data Requests)
┌──────────────────────────┐
│    Parallel Queries      │ Step 3: Data Gathering
│    to Multiple Engines   │
│                          │
│    • Engine A: Prices    │
│    • Engine B: Analytics │
│    • Engine C: Positions │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Cloud Firestore       │ Step 4: Historical Data
│    Database              │
│                          │
│    • Portfolio History   │
│    • Transaction Log     │
│    • Performance Metrics │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Engine D              │ Step 5: Response Synthesis
│    Response Builder      │
│                          │
│    • Aggregate Data      │
│    • Format Response     │
│    • Generate Answer     │
└──────────┬───────────────┘
           │
           ↓
┌──────────────────────────┐
│    Frontend              │ Step 6: Display
│    Chat Interface        │
│                          │
│    • Show Response       │
│    • Update UI           │
│    • Store in History    │
└──────────────────────────┘
```

## CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GITHUB REPOSITORY                          │
│                  raghu-1718/InfinityAI.Pro                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓ (git push)
┌─────────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS                               │
│                   18 Workflow Pipelines                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │  Build        │  │  Test         │  │  Deploy       │      │
│  │  Workflows    │  │  Workflows    │  │  Workflows    │      │
│  │               │  │               │  │               │      │
│  │ • Compile     │  │ • Unit Tests  │  │ • Engine A    │      │
│  │ • Lint        │  │ • Integration │  │ • Engine B    │      │
│  │ • Docker      │  │ • E2E Tests   │  │ • Engine C    │      │
│  │   Build       │  │ • Health      │  │ • Engine D    │      │
│  │               │  │   Checks      │  │ • Frontend    │      │
│  │               │  │               │  │ • Functions   │      │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘      │
│          │                  │                  │              │
│          └──────────────────┼──────────────────┘              │
│                             ↓                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓ (Docker images)
┌─────────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD BUILD                             │
│                  Automated Container Build                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  • Build Docker images                                          │
│  • Push to Container Registry                                   │
│  • Deploy to Cloud Run                                          │
│  • Health verification                                          │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓ (deployment)
┌─────────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD RUN                               │
│                  Production Services                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Engine A    │  │ Engine B    │  │ Engine C    │            │
│  │ RUNNING     │  │ RUNNING     │  │ RUNNING     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────────────────────┐             │
│  │ Engine D    │  │ Frontend                    │             │
│  │ RUNNING     │  │ RUNNING                     │             │
│  └─────────────┘  └─────────────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ↓ (accessible at)
┌─────────────────────────────────────────────────────────────────┐
│                  PRODUCTION URLS                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  • https://infinityai.pro                    (Frontend)        │
│  • https://infinityai-engine-a-*.run.app     (Engine A)        │
│  • https://infinityai-engine-b-*.run.app     (Engine B)        │
│  • https://infinityai-engine-c-*.run.app     (Engine C)        │
│  • https://infinityai-engine-d-*.run.app     (Engine D)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Network Security
┌─────────────────────────────────────────────────────────────────┐
│  • HTTPS/TLS encryption                                         │
│  • Cloud Armor (DDoS protection) - Recommended                  │
│  • VPC networking                                               │
│  • Firewall rules                                               │
└─────────────────────────────────────────────────────────────────┘

Layer 2: Authentication & Authorization
┌─────────────────────────────────────────────────────────────────┐
│  • Firebase Authentication                                      │
│  • OAuth 2.0 (Dhan API)                                         │
│  • JWT token validation                                         │
│  • Role-based access control                                    │
└─────────────────────────────────────────────────────────────────┘

Layer 3: API Security
┌─────────────────────────────────────────────────────────────────┐
│  • CORS configuration                                           │
│  • Security headers                                             │
│  • Input validation                                             │
│  • Rate limiting - TO BE IMPLEMENTED                            │
└─────────────────────────────────────────────────────────────────┘

Layer 4: Secret Management
┌─────────────────────────────────────────────────────────────────┐
│  • GCP Secret Manager                                           │
│  • Environment variables (.env in .gitignore)                   │
│  • No hardcoded credentials                                     │
│  • Automatic secret rotation                                    │
└─────────────────────────────────────────────────────────────────┘

Layer 5: Data Security
┌─────────────────────────────────────────────────────────────────┐
│  • Firestore security rules                                     │
│  • Encrypted at rest                                            │
│  • Encrypted in transit                                         │
│  • Audit logging                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Deployment Topology

```
                        PRODUCTION ENVIRONMENT
                        
┌─────────────────────────────────────────────────────────────────┐
│                     us-central1 (Iowa)                          │
│                  Google Cloud Platform Region                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Cloud Run Services                      │      │
│  │  • Auto-scaling: 0-100 instances per service        │      │
│  │  • CPU: 1-2 vCPUs per instance                      │      │
│  │  • Memory: 512 MB - 2 GB per instance               │      │
│  │  • Concurrency: 80 requests per instance            │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Cloud Firestore                         │      │
│  │  • Multi-region replication                          │      │
│  │  • Automatic scaling                                 │      │
│  │  • 99.99% uptime SLA                                 │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Firebase Functions                      │      │
│  │  • Serverless execution                              │      │
│  │  • Auto-scaling                                      │      │
│  │  • Event-driven triggers                             │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Secret Manager                          │      │
│  │  • Encrypted secrets storage                         │      │
│  │  • Version management                                │      │
│  │  • Access control                                    │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Cloud Logging & Monitoring              │      │
│  │  • Centralized logging                               │      │
│  │  • Real-time metrics                                 │      │
│  │  • Error reporting                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Monitoring & Observability

```
┌─────────────────────────────────────────────────────────────────┐
│                   MONITORING STACK                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Application Metrics                                            │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Request latency                       │                   │
│  │ • Error rates                           │                   │
│  │ • Throughput (req/sec)                  │                   │
│  │ • Success rates                         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Infrastructure Metrics                                         │
│  ┌─────────────────────────────────────────┐                   │
│  │ • CPU utilization                       │                   │
│  │ • Memory usage                          │                   │
│  │ • Network I/O                           │                   │
│  │ • Instance count                        │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Business Metrics                                               │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Active users                          │                   │
│  │ • Trade volume                          │                   │
│  │ • API calls per service                 │                   │
│  │ • Conversion rates                      │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
│  Alerts & Notifications                                         │
│  ┌─────────────────────────────────────────┐                   │
│  │ • Service downtime                      │                   │
│  │ • High error rates (>5%)                │                   │
│  │ • Slow response times (>2s)             │                   │
│  │ • Resource exhaustion                   │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**Generated:** October 25, 2025  
**Platform:** InfinityAI.Pro v3.0  
**Documentation Version:** 1.0
