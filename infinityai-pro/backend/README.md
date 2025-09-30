# InfinityAI.Pro - Complete AI Trading Platform

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-red.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7+-red.svg)

A comprehensive AI-powered trading platform with secure broker integration, real-time market data, and advanced trading algorithms.

## 🚀 Features

### 🔐 Authentication & Security
- **JWT-based authentication** with access & refresh tokens
- **Secure user registration/login** with bcrypt password hashing
- **Session management** with automatic cleanup and IP tracking
- **Fernet encryption** for sensitive broker tokens (AES-128)
- **OAuth2-compatible endpoints** for seamless frontend integration

### 🏦 Broker Integration
- **Multi-broker support**: Dhan, Zerodha, Upstox, Angel Broking
- **Encrypted token storage** - no plaintext credentials in database
- **Automatic token validation** via background Celery tasks
- **Token expiry management** with notifications
- **Real-time broker status tracking**
- **Secure CRUD operations** for broker connections

### 🤖 AI Trading Engine
- **Advanced ML models** for price prediction and signal generation
- **Real-time market data** from multiple providers with fallback
- **Options chain analysis** and volatility modeling
- **Risk management** and position sizing algorithms
- **Backtesting engine** with performance analytics
- **Portfolio optimization** using modern portfolio theory

### 📊 Market Data & Analytics
- **Multi-provider fallback system**: Alpha Vantage, Yahoo Finance, Polygon.io
- **Real-time WebSocket feeds** for live market updates
- **Technical indicators** and chart pattern recognition
- **Options Greeks** calculation and volatility analysis
- **Market sentiment analysis** using news and social media

### ⚡ High-Performance Infrastructure
- **Async FastAPI backend** with connection pooling
- **Redis caching** for market data and AI computations
- **Celery background tasks** for broker validation and cleanup
- **PostgreSQL database** with optimized queries and indexing
- **Auto-scaling ready** with health checks and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (React/Next)  │◄──►│   Backend       │◄──►│   (Users +      │
│                 │    │   - Auth        │    │   Brokers)      │
│                 │    │   - Trading     │    └─────────────────┘
│                 │    │   - AI/ML       │
└─────────────────┘    │   - Market Data │    ┌─────────────────┐
                       └─────────────────┘    │   Cassandra     │
                              │               │   (Trading Data │
                              │               │   Time Series)  │
                              ▼               └─────────────────┘
                       ┌─────────────────┐    
                       │   Celery        │    ┌─────────────────┐
                       │   - Validation  │◄──►│   Redis         │
                       │   - Cleanup     │    │   (Caching +    │
                       │   - AI Tasks    │    │   Message Q)    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-username/InfinityAI.Pro.git
cd InfinityAI.Pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements-railway.txt

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(f'FERNET_KEY={Fernet.generate_key().decode()}')"
```

### 2. Database Setup

```bash
# Install PostgreSQL and create database
createdb infinityai

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/infinityai"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="your-super-secret-jwt-key-here"
export FERNET_KEY="your-generated-fernet-key-here"
```

### 3. Start Services

#### Option A: Docker Compose (Recommended)
```bash
# Start all services
docker-compose up --build

# Services will be available at:
# - Backend API: http://localhost:8000
# - API Documentation: http://localhost:8000/docs
# - Celery Flower: http://localhost:5555
# - pgAdmin: http://localhost:5050
```

#### Option B: Manual Setup
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start PostgreSQL
pg_ctl start

# Terminal 3: Start Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 4: Start Celery Worker
cd backend
python -m app.celery_worker

# Terminal 5: Start Celery Beat (Optional - for periodic tasks)
cd backend
celery -A app.tasks beat --loglevel=info
```

## 📖 API Documentation

### 🔐 Authentication Endpoints

#### Register New User
```http
POST /auth/signup
Content-Type: application/json

{
    "username": "trader123",
    "email": "trader@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
    "username": "trader123",
    "password": "SecurePass123!"
}

# Response:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "trader123"
}
```

#### Get User Profile
```http
GET /auth/me
Authorization: Bearer <access_token>
```

### 🏦 Broker Management

#### Add Broker Connection
```http
POST /brokers
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "broker_name": "dhan",
    "token": "YOUR_DHAN_ACCESS_TOKEN",
    "expiry_timestamp": "2025-12-31T23:59:59Z",
    "metadata": {
        "account_type": "equity",
        "notes": "Primary trading account"
    }
}
```

#### List Broker Connections
```http
GET /brokers
Authorization: Bearer <access_token>

# Response:
[
    {
        "id": "456e7890-e89b-12d3-a456-426614174001",
        "broker_name": "dhan",
        "status": "connected",
        "expiry_timestamp": "2025-12-31T23:59:59Z",
        "last_validated_at": "2025-09-30T02:00:00Z",
        "validation_attempts": 1,
        "metadata": {
            "account_info": {
                "account_id": "D12345",
                "client_name": "John Doe",
                "balance": 150000.50
            }
        }
    }
]
```

### 📈 Trading Endpoints

#### Place Order
```http
POST /trading/orders
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "symbol": "RELIANCE",
    "quantity": 10,
    "price": 2500.00,
    "side": "BUY",
    "order_type": "LIMIT",
    "product": "MIS"
}
```

#### Get Positions
```http
GET /trading/positions
Authorization: Bearer <access_token>
```

#### Get Portfolio
```http
GET /trading/portfolio
Authorization: Bearer <access_token>
```

### 🤖 AI Trading Signals

#### Get AI Predictions
```http
GET /ai/predictions?symbol=RELIANCE&timeframe=1D
Authorization: Bearer <access_token>

# Response:
{
    "symbol": "RELIANCE",
    "current_price": 2485.50,
    "prediction": {
        "direction": "BULLISH",
        "target_price": 2650.00,
        "confidence": 0.78,
        "timeframe": "5-10 days"
    },
    "technical_indicators": {
        "rsi": 68.5,
        "macd": "BULLISH_CROSSOVER",
        "support": 2450.00,
        "resistance": 2550.00
    }
}
```

#### Get Trading Signals
```http
GET /ai/signals
Authorization: Bearer <access_token>

# Response:
[
    {
        "symbol": "TATAMOTORS",
        "signal": "BUY",
        "entry_price": 920.00,
        "stop_loss": 890.00,
        "target": 980.00,
        "confidence": 0.82,
        "reasoning": "Bullish breakout with high volume"
    }
]
```

### 📊 Market Data

#### Get Real-time Quote
```http
GET /trading/quote/RELIANCE
Authorization: Bearer <access_token>

# Response:
{
    "symbol": "RELIANCE",
    "price": 2485.50,
    "change": 15.25,
    "change_percent": 0.62,
    "volume": 2450000,
    "high": 2495.00,
    "low": 2470.00,
    "timestamp": "2025-09-30T09:15:00Z"
}
```

#### Get Historical Data
```http
GET /trading/historical/RELIANCE?period=1M&interval=1D
Authorization: Bearer <access_token>
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/infinityai
CASSANDRA_HOSTS=localhost:9042
CASSANDRA_KEYSPACE=infinityai_keyspace

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-in-production
FERNET_KEY=your-fernet-encryption-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Celery
CELERY_BROKER=redis://localhost:6379/0
CELERY_BACKEND=redis://localhost:6379/1

# Trading APIs
DHAN_CLIENT_ID=your_dhan_client_id
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
OPENAI_API_KEY=your_openai_api_key

# Cloud Services (Optional)
AZURE_KEYVAULT_URL=https://your-vault.vault.azure.net/
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

## 🏥 Health Monitoring

### Health Check Endpoint
```http
GET /health

# Response:
{
    "status": "healthy",
    "timestamp": "2025-09-30T02:00:00Z",
    "version": "2.0.0",
    "services": {
        "postgresql": {"status": "healthy"},
        "cassandra": {"status": "healthy"},
        "redis": {"status": "healthy"},
        "cryptography": {"status": "healthy"},
        "market_data": {"status": "healthy"}
    }
}
```

### Celery Monitoring
- **Flower Dashboard**: http://localhost:5555
- Monitor active tasks, worker status, and queue statistics
- View task history and failure logs

## 🚀 Production Deployment

### Railway Deployment

```bash
# Login to Railway
railway login

# Deploy
railway up

# Set environment variables
railway variables set DATABASE_URL="postgresql://..."
railway variables set JWT_SECRET="..."
railway variables set FERNET_KEY="..."
```

### Docker Production

```bash
# Build production image
docker build -t infinityai-pro:latest .

# Run with production environment
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET="..." \
  infinityai-pro:latest
```

## 🧪 Testing

### Run Tests
```bash
# Unit tests
pytest backend/tests/ -v

# Integration tests
pytest backend/tests/integration/ -v

# Load tests
locust -f backend/tests/load_test.py
```

### Test Broker Connection
```bash
# Test with curl
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'

# Use the token to test broker endpoints
curl -X GET http://localhost:8000/brokers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 Live Trading Capabilities

### ✅ Current Live Trading Features:
1. **Real-time Order Execution**
   - Market, Limit, Stop-loss orders
   - Multi-broker support (Dhan, Zerodha, Upstox)
   - Order status tracking and updates

2. **Position Management**
   - Real-time position tracking
   - P&L calculations
   - Risk management alerts

3. **Portfolio Analytics**
   - Live portfolio valuation
   - Performance metrics
   - Risk analysis

4. **AI-Driven Decisions**
   - Real-time signal generation
   - Automated entry/exit strategies
   - Risk-adjusted position sizing

5. **Market Data Integration**
   - Live price feeds
   - Technical indicator calculations
   - Volume and liquidity analysis

### 🚀 Ready for Live Trading:
- **Secure Authentication**: JWT tokens with session management
- **Encrypted Broker Tokens**: Fernet encryption for API keys
- **Real-time Validation**: Background tasks verify broker connectivity
- **Error Handling**: Comprehensive error handling and retry mechanisms
- **Monitoring**: Health checks and performance monitoring
- **Scaling**: Redis caching and connection pooling for high throughput

## 📁 Project Structure

```
InfinityAI.Pro/
├── backend/
│   ├── app/                    # New authentication & broker system
│   │   ├── auth.py            # JWT authentication
│   │   ├── brokers.py         # Broker management
│   │   ├── database.py        # PostgreSQL connection
│   │   ├── crypto.py          # Encryption utilities
│   │   ├── tasks.py           # Celery background tasks
│   │   └── schemas.py         # Pydantic models
│   ├── api/                    # Existing trading APIs
│   │   ├── trading.py         # Trading operations
│   │   ├── options.py         # Options trading
│   │   ├── ai.py              # AI predictions
│   │   └── user.py            # User management
│   ├── services/               # Core services
│   │   ├── cache/             # Redis caching
│   │   ├── database/          # Database connections
│   │   ├── security/          # Security services
│   │   └── market_data/       # Market data providers
│   ├── sql/
│   │   └── schema.sql         # Database schema
│   ├── main.py                # FastAPI application
│   ├── requirements-railway.txt
│   └── Dockerfile
├── docker-compose.yml          # Local development
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary. All rights reserved.

## 📞 Support

For support and questions:
- 📧 Email: support@infinityai.pro
- 🌐 Website: https://infinityai.pro
- 📚 Documentation: https://docs.infinityai.pro

---

**InfinityAI.Pro** - Empowering traders with AI-driven insights and secure broker integration. 🚀📈