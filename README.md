# InfinityAI.Pro
InfinityAI.Pro is a production-grade, event-driven AI trading platform supporting live market data, async trading, and AI chatbot integration for automated, scalable financial operations

## 🚀 Quick Start

### Automated Setup (Recommended)
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
- **Notification System**: Multi-channel alerts (Telegram, Email, WhatsApp)
- **Risk Management**: Position sizing and stop-loss automation
- **Web Dashboard**: Real-time trading interface

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

- [ ] Multi-broker support (Zerodha, Upstox)
- [ ] Advanced AI strategies (ML-based predictions)
- [ ] Mobile app enhancements
- [ ] Real-time charting
- [ ] Portfolio analytics
- [ ] Risk management dashboard

---

**Contact**: raghuyuvi10@gmail.com | **Domain**: https://infinityai.pro
