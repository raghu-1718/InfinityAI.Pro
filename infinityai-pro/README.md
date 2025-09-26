# InfinityAI.Pro - Enhanced AI Trading Platform
InfinityAI.Pro is a production-grade, event-driven AI trading platform supporting live market data, async trading, and AI chatbot integration for automated, scalable financial operations

## 🤖 AI-Enhanced Trading System

### 🚀 New Features (Latest Update)
- **Perplexity Integration**: Real-time market news analysis and sentiment scoring
- **OpenAI Integration**: AI-powered strategy narration and risk assessment
- **Sentiment-Enhanced Signals**: Combines quantitative analysis with qualitative intelligence
- **Hybrid Decision Making**: Machine learning + AI insights for superior trading decisions
- **MCX Commodity Focus**: Extended trading hours with Gold, Silver, Crude Oil, Natural Gas

### 📊 Trading Capabilities
- **Live Trading**: Real-time execution with Dhan broker integration
- **Risk Management**: 3% risk per trade, 25% daily profit target
- **AI Insights**: Strategy explanations and market intelligence
- **Performance Analytics**: Comprehensive trade logging with AI analysis

### 🧠 AI Components
- **PerplexityClient**: Market news and sentiment analysis
- **OpenAIClient**: Strategy narration and portfolio insights
- **SentimentAnalyzer**: Signal enhancement with news sentiment
- **LiveTrader**: Core engine with AI integration

## 🚀 Quick Start

### Enhanced Trading Setup (Latest)
For the AI-enhanced trading system with Perplexity and OpenAI integration:

```bash
cd backend
pip install -r requirements.txt
python setup_trading.py
```

This will:
- ✅ Configure Perplexity API for market news analysis
- ✅ Configure OpenAI API for strategy narration
- ✅ Start live trading with AI intelligence
- ✅ Enable MCX commodity trading for 25% profit target

### Trading Configuration
- **Capital**: ₹11,000
- **Risk per Trade**: 3%
- **Daily Profit Target**: 25%
- **Scan Frequency**: 15 seconds
- **Minimum Signal Score**: 0.55
- **Focus Markets**: MCX commodities (extended hours)

### Automated Setup (Infrastructure)
Run the complete automated setup script:

```bash
chmod +x setup-infinityai.sh
./setup-infinityai.sh
```

This script will:
- ✅ Check prerequisites (Azure CLI, login status)
- ✅ Set up Azure DNS for infinityai.pro
- ✅ Configure SendGrid for business email
- ✅ Set up Twilio for WhatsApp messaging
- ✅ Collect trading platform credentials
- ✅ Deploy to Azure Container Apps
- ✅ Configure DNS records

### Manual Setup

#### 1. Prerequisites
- Azure CLI installed and logged in (`az login`)
- Domain: infinityai.pro (Namecheap)
- Business Email: raghuyuvi10@gmail.com
- Business Phone: +91 856936854

#### 2. Azure Deployment
```bash
cd azure/container-apps
chmod +x deploy-infinityai.sh
./deploy-infinityai.sh
```

#### 3. Notification Setup

**SendGrid (Business Email):**
1. Sign up at https://sendgrid.com
2. Verify email: raghuyuvi10@gmail.com
3. Create API key in Settings → API Keys
4. Set environment variable: `SENDGRID_API_KEY`

**Twilio (WhatsApp):**
1. Sign up at https://twilio.com
2. Verify phone: +91 856936854
3. Enable WhatsApp in console
4. Get Account SID, Auth Token, and WhatsApp number
5. Set environment variables:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER`

#### 4. Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export DHAN_CLIENT_ID="your_client_id"  # Optional
export DHAN_ACCESS_TOKEN="your_access_token"  # Optional
export FLASK_SECRET_KEY="generated_secret_key"
```

## 🏗️ Architecture

### Core Components
- **Trading Engine**: Async market data processing and trade execution
- **AI Chatbot**: Natural language trading commands
- **AI Intelligence Layer**: Perplexity + OpenAI integration for market insights
- **Sentiment Analysis**: News sentiment enhancement of trading signals
- **Notification System**: Multi-channel alerts (Telegram, Email, WhatsApp)
- **Risk Management**: Position sizing and stop-loss automation
- **Web Dashboard**: Real-time trading interface

### AI Architecture
- **PerplexityClient** (`services/perplexity_client.py`): Real-time market news and sentiment analysis
- **OpenAIClient** (`services/openai_client.py`): Strategy narration and risk assessment
- **SentimentAnalyzer** (`services/sentiment_analyzer.py`): Combines news sentiment with ML signals
- **LiveTrader** (`services/live_trader.py`): Core trading engine with AI integration
- **Configuration** (`utils/config.py`): API keys and trading parameters

### Technology Stack
- **Backend**: Python FastAPI, Flask
- **Database**: PostgreSQL (Azure)
- **Deployment**: Azure Container Apps
- **Domain**: infinityai.pro (Azure DNS)
- **Notifications**: Telegram Bot API, SendGrid, Twilio WhatsApp

## 📡 API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - System metrics and status
- `GET /health/notification-status` - Notification channel status

### Testing Notifications
```bash
# Test Telegram
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "telegram", "message": "Test message"}'

# Test Email
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "email", "message": "Test email"}'

# Test WhatsApp
curl -X POST https://infinityai.pro/health/test-notification \
  -H "Content-Type: application/json" \
  -d '{"channel": "whatsapp", "message": "Test WhatsApp"}'
```

### AI Endpoints
- `POST /ai/analyze` - Get market analysis with sentiment
- `POST /ai/strategy` - Generate AI-powered trading strategy
- `GET /ai/sentiment` - Get current market sentiment score
- `POST /ai/narrate` - Get strategy narration for trade decisions

### Testing AI Features
```bash
# Test market analysis
curl -X POST https://infinityai.pro/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "MCX_GOLD_MINI", "context": "current market conditions"}'

# Test strategy narration
curl -X POST https://infinityai.pro/ai/narrate \
  -H "Content-Type: application/json" \
  -d '{"signal": "BUY", "symbol": "MCX_GOLD_MINI", "score": 0.75}'
```

## 🔧 Configuration

### Domain Setup
- **Domain**: infinityai.pro
- **Nameservers**: Azure DNS configured
- **SSL**: Automatic (Azure Container Apps)
- **CDN**: Azure Front Door (optional)

### Notification Channels
- **Telegram**: Bot alerts for trading signals
- **Email**: Business notifications via SendGrid
- **WhatsApp**: Direct messaging via Twilio

## 📊 Monitoring

### Health Endpoints
- System metrics (CPU, memory, disk)
- Application uptime and performance
- Notification channel status
- Trading engine health

### Logs
- Azure Application Insights
- Container logs via Azure CLI
- Structured logging with correlation IDs

## 🚀 Deployment

### Azure Container Apps
```bash
# Build and push container
az acr build --registry infinityaiacr --image infinityai:latest .

# Deploy to Container Apps
az containerapp up \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --source . \
  --ingress external \
  --target-port 8000 \
  --custom-domain infinityai.pro
```

### DNS Configuration
```bash
# Add custom domain
az containerapp hostname set \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --hostname infinityai.pro \
  --validation-method cname-delegation
```

## 🔒 Security

- Environment-based secrets management
- Azure Key Vault integration
- Network security groups
- Azure AD authentication (planned)
- End-to-end encryption

## 📞 Support

- **Domain**: Namecheap support
- **Azure**: Microsoft Azure support
- **SendGrid**: SendGrid documentation
- **Twilio**: Twilio documentation
- **Trading API**: Dhan API documentation

## 📈 Roadmap

- [x] **COMPLETED**: Perplexity API integration for market news
- [x] **COMPLETED**: OpenAI API integration for strategy narration
- [x] **COMPLETED**: Sentiment-enhanced trading signals
- [x] **COMPLETED**: MCX commodity trading optimization
- [ ] Multi-broker support (Zerodha, Upstox)
- [ ] Advanced AI strategies (additional ML models)
- [ ] Mobile app enhancements
- [ ] Real-time charting with AI annotations
- [ ] Portfolio analytics with AI insights
- [ ] Risk management dashboard
- [ ] Voice-based trading commands

---

**Contact**: raghuyuvi10@gmail.com | **Domain**: https://infinityai.pro
