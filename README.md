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
- ✅ Check prerequisites (Render account)
- ✅ Deploy to Render using Blueprint
- ✅ Configure custom domains (infinityai.pro, api.infinityai.pro)
- ✅ Set up environment variables
- ✅ Configure RunPod GPU endpoints

### Manual Setup

#### 1. Prerequisites
- Render account (https://render.com)
- Domain: infinityai.pro configured
- RunPod account for GPU services
- API keys for trading platforms

#### 2. Render Deployment
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your `raghu-1718/InfinityAI.Pro` repository
4. Render will auto-detect `render.yaml` and deploy all services

#### 3. Environment Variables
Set these in your Render backend service:

```bash
# Trading APIs
DHAN_CLIENT_ID=your_dhan_client_id
DHAN_ACCESS_TOKEN=your_dhan_access_token

# AI Services
OPENAI_API_KEY=your_openai_key
PERPLEXITY_API_KEY=your_perplexity_key
HUGGINGFACE_API_KEY=your_huggingface_key

# GPU Services (RunPod)
RUNPOD_SD_ENDPOINT=https://your-runpod-sd-endpoint.runpod.net
RUNPOD_YOLO_ENDPOINT=https://your-runpod-yolo-endpoint.runpod.net
RUNPOD_WHISPER_ENDPOINT=https://your-runpod-whisper-endpoint.runpod.net
RUNPOD_API_KEY=your_runpod_api_key

# Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SENDGRID_API_KEY=your_sendgrid_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=your_whatsapp_number
```

#### 4. Custom Domains
- Frontend: `infinityai.pro`
- Backend: `api.infinityai.pro`

## 🏗️ Architecture

### Core Components
- **Trading Engine**: Async market data processing and trade execution
- **AI Chatbot**: Natural language trading commands with GPU acceleration
- **Notification System**: Multi-channel alerts (Telegram, Email, WhatsApp)
- **Risk Management**: Position sizing and stop-loss automation
- **Web Dashboard**: Real-time trading interface

### Technology Stack
- **Backend**: Python FastAPI
- **Frontend**: React TypeScript
- **AI Services**: Ollama (LLMs), ChromaDB (Vectors), RunPod (GPU)
- **Database**: ChromaDB for vector storage
- **Deployment**: Render (Web Services + Private Services)
- **Domain**: infinityai.pro
- **Notifications**: Telegram Bot API, SendGrid, Twilio WhatsApp

## 📡 API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - System metrics and status

### AI Endpoints
- `POST /ai/sd` - Stable Diffusion image generation
- `POST /ai/yolo` - Object detection
- `POST /ai/whisper` - Speech to text
- `WebSocket /ai/chat/{user_id}` - AI chat interface

### Trading Endpoints
- `GET /trading/status` - Trading engine status
- `POST /trading/execute` - Execute trade
- `GET /trading/portfolio` - Portfolio data

## 🔧 Configuration

### Domain Setup
- **Domain**: infinityai.pro
- **SSL**: Automatic (Render)
- **CDN**: Built-in (Render)

### Notification Channels
- **Telegram**: Bot alerts for trading signals
- **Email**: Business notifications via SendGrid
- **WhatsApp**: Direct messaging via Twilio

## 📊 Monitoring

### Health Endpoints
- System metrics (CPU, memory, disk)
- Application uptime and performance
- AI service health
- Trading engine status

### Logs
- Render service logs
- Structured logging with correlation IDs

## 🚀 Deployment

### Render Services
- **infinityai-frontend**: Static React site
- **infinityai-backend**: FastAPI web service
- **ollama**: Private Ollama service for LLMs
- **chroma**: Private ChromaDB service for vectors

### Scaling
- Frontend: Auto-scaling static site
- Backend: Web service with manual scaling
- AI Services: Private services with persistent storage

## 🔒 Security

- Environment-based secrets management
- HTTPS everywhere
- CORS configured for production
- API key authentication for external services

## 📞 Support

- **Render**: Render documentation and support
- **RunPod**: RunPod GPU documentation
- **Trading API**: Dhan API documentation
- **AI Services**: Hugging Face, OpenAI documentation

## 📈 Roadmap

- [ ] Multi-broker support (Zerodha, Upstox)
- [ ] Advanced AI strategies (ML-based predictions)
- [ ] Mobile app enhancements
- [ ] Real-time charting
- [ ] Portfolio analytics
- [ ] Risk management dashboard

---

**Contact**: raghuyuvi10@gmail.com | **Domain**: https://infinityai.pro
