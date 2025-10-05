# InfinityAI.Pro Trading Platform - Production Deployment Guide

## 🚀 Quick Start Production Deployment

### Prerequisites

1. **Docker Desktop** (Required)
   ```bash
   # Download and install Docker Desktop from:
   # https://docs.docker.com/desktop/install/windows-install/
   ```

2. **System Requirements**
   - Windows 10/11 Pro, Enterprise, or Education
   - 16GB RAM (minimum 8GB)
   - 50GB free disk space
   - Multi-core CPU (4+ cores recommended)

3. **GPU Support (Optional - for Engine B AI processing)**
   - NVIDIA GPU with CUDA support
   - NVIDIA Docker runtime

### 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Engine A      │    │   Engine B      │    │   Engine C      │
│ Market Data     │────│ AI Signals      │────│ Trade Execution │
│ Ingestion       │    │ Processing      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Kafka        │    │   PostgreSQL    │    │     Redis       │
│  Event Bus      │    │   Database      │    │     Cache       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Step-by-Step Deployment

### Step 1: Prepare Environment

1. **Clone and Navigate**
   ```bash
   cd C:\Users\Raghu\InfinityAI.Pro\infinityai-pro\backend
   ```

2. **Create Environment File**
   ```bash
   copy .env.template .env
   ```

3. **Edit .env with your settings:**
   ```env
   # Required - Add your Dhan credentials
   DHAN_ACCESS_TOKEN=your_dhan_access_token_here
   DHAN_CLIENT_ID=your_dhan_client_id_here
   
   # Security - Generate secure keys
   SECRET_KEY=your_super_secure_secret_key_here
   INFINITYAI_VAULT_KEY=your_vault_encryption_key_here
   INFINITYAI_VAULT_SALT=your_vault_salt_here
   
   # Database passwords
   DATABASE_URL=postgresql://infinityai:your_secure_password@postgres:5432/infinityai
   ```

### Step 2: Deploy Infrastructure

```bash
# Start infrastructure services
docker-compose up -d zookeeper kafka schema-registry redis postgres timescaledb

# Wait for services to be ready (2-3 minutes)
docker-compose ps
```

### Step 3: Initialize Database

```bash
# Check if database is ready
docker-compose exec postgres pg_isready -U infinityai

# Initialize schema (if needed)
docker-compose exec postgres psql -U infinityai -d infinityai -f /docker-entrypoint-initdb.d/01_init_schema.sql
```

### Step 4: Deploy Trading Engines

```bash
# Deploy engines in sequence
docker-compose up -d engine-a
sleep 20

docker-compose up -d engine-b  
sleep 30  # AI models need more time to load

docker-compose up -d engine-c
sleep 20

# Deploy main API
docker-compose up -d infinityai-api
```

### Step 5: Deploy Monitoring & Proxy

```bash
# Start monitoring stack
docker-compose up -d prometheus grafana jaeger

# Start reverse proxy
docker-compose up -d nginx
```

### Step 6: Verify Deployment

**Check Service Health:**
```bash
# Check all services
docker-compose ps

# Health check endpoints
curl http://localhost:8001/health  # Engine A
curl http://localhost:8002/health  # Engine B  
curl http://localhost:8003/health  # Engine C
curl http://localhost:8000/health  # Main API
```

**Access Dashboards:**
- **Main Platform:** http://localhost
- **Grafana:** http://localhost:3000 (admin/infinityai_admin)
- **Prometheus:** http://localhost:9090
- **Jaeger Tracing:** http://localhost:16686

## 🔧 Configuration Management

### Engine-Specific Configuration

#### Engine A - Market Data Ingestion
- **WebSocket Connection:** Auto-reconnects to Dhan
- **Technical Indicators:** RSI, EMA, Bollinger Bands, MACD, ADX
- **Signal Generation:** Momentum and mean-reversion strategies
- **Kafka Publishing:** Real-time market signals

#### Engine B - AI Signal Processing
- **Models:** Transformer, Random Forest, Gradient Boosting
- **GPU Acceleration:** CUDA-enabled PyTorch
- **Risk Assessment:** Multi-factor risk scoring
- **Position Sizing:** Kelly Criterion with risk adjustment

#### Engine C - Trade Execution
- **Idempotency:** Duplicate trade prevention
- **Safety Checks:** Position limits, exposure limits, daily loss limits
- **Circuit Breakers:** Automatic failure handling
- **Kill Switches:** Emergency trade stopping

### Risk Management Settings

```env
# Risk limits (adjust based on your capital)
DEFAULT_DAILY_MAX_LOSS=10000.0
DEFAULT_POSITION_LIMIT=100000.0
DEFAULT_MAX_POSITION_SIZE_PERCENT=20.0
DEFAULT_SYMBOL_EXPOSURE_LIMIT=10.0

# Circuit breakers
BROKER_CIRCUIT_BREAKER_THRESHOLD=5
BROKER_CIRCUIT_BREAKER_TIMEOUT=60
```

### Trading Mode

```env
# For testing - no real trades
PAPER_TRADE=true

# For live trading - real trades
PAPER_TRADE=false
```

## 📊 Monitoring & Observability

### Key Metrics to Monitor

1. **Market Data Engine (Engine A)**
   - WebSocket connection status
   - Market data throughput (ticks/sec)
   - Signal generation rate
   - Technical indicator accuracy

2. **AI Processing Engine (Engine B)**
   - Model prediction latency
   - GPU utilization
   - Signal confidence distribution
   - Risk assessment accuracy

3. **Trade Execution Engine (Engine C)**
   - Trade submission success rate
   - Order execution latency
   - Safety check rejections
   - Position tracking accuracy

### Grafana Dashboards

Access Grafana at `http://localhost:3000` with credentials:
- **Username:** admin
- **Password:** infinityai_admin

**Key Dashboard Panels:**
- Real-time P&L tracking
- Position exposure heatmap
- Signal performance analytics
- System health overview
- Risk metrics dashboard

## 🛠️ Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U infinityai

# Reset database
docker-compose down postgres
docker volume rm backend_postgres-data
docker-compose up -d postgres
```

#### 3. Kafka Connection Issues
```bash
# Check Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Reset Kafka
docker-compose down kafka zookeeper
docker volume rm backend_kafka-data backend_zookeeper-data
docker-compose up -d zookeeper kafka
```

#### 4. Engine B (AI) Issues
```bash
# Check GPU availability
docker-compose exec engine-b python -c "import torch; print(torch.cuda.is_available())"

# Check model loading
docker-compose logs engine-b | grep "model"
```

#### 5. Memory Issues
```bash
# Check container resource usage
docker stats

# Increase Docker Desktop memory allocation
# Settings > Resources > Advanced > Memory
```

### Performance Optimization

#### For High-Frequency Trading:
1. **Increase Docker Resources**
   - Memory: 8GB minimum, 16GB recommended
   - CPU: All available cores
   
2. **Optimize Kafka**
   ```yaml
   # In docker-compose.yml
   KAFKA_NUM_IO_THREADS: 16
   KAFKA_SOCKET_SEND_BUFFER_BYTES: 102400
   KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: 102400
   ```

3. **Database Tuning**
   ```yaml
   # PostgreSQL optimization
   shared_buffers: 256MB
   effective_cache_size: 1GB
   max_connections: 200
   ```

## 🔐 Security Considerations

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Use strong encryption keys
- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up VPN access for monitoring
- [ ] Implement API rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates

### Network Security

```yaml
# Add to docker-compose.yml for production
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Multiple Engine Instances**
   ```yaml
   engine-a:
     deploy:
       replicas: 3
   ```

2. **Load Balancing**
   - NGINX upstream configuration
   - Kafka consumer groups
   - Database read replicas

3. **Cloud Deployment**
   - Azure Container Apps
   - AWS ECS/Fargate
   - Google Cloud Run

### Vertical Scaling

- Increase container memory/CPU limits
- Optimize AI model parameters
- Database connection pooling
- Redis clustering

## 🚨 Emergency Procedures

### Kill Switch Activation
```bash
# Global kill switch (stops all trading)
curl -X POST http://localhost:8003/kill-switch/GLOBAL \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency stop - manual intervention"}'

# Account-specific kill switch
curl -X POST http://localhost:8003/kill-switch/ACCOUNT \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "account_123", "reason": "Account risk limit exceeded"}'
```

### System Shutdown
```bash
# Graceful shutdown (completes pending trades)
docker-compose down --timeout 60

# Force shutdown (immediate stop)
docker-compose down --timeout 10
```

### Data Backup
```bash
# Backup database
docker-compose exec postgres pg_dump -U infinityai infinityai > backup_$(date +%Y%m%d).sql

# Backup Redis
docker-compose exec redis redis-cli --rdb /data/dump.rdb
```

## 📞 Support & Maintenance

### Daily Maintenance Tasks
- [ ] Check service health status
- [ ] Review trading performance metrics
- [ ] Monitor system resource usage
- [ ] Verify data backup completion
- [ ] Review error logs

### Weekly Tasks
- [ ] Update market data feeds
- [ ] Retrain AI models if needed
- [ ] Review risk management settings
- [ ] Performance optimization analysis
- [ ] Security audit review

### Monthly Tasks
- [ ] System update deployment
- [ ] Disaster recovery testing
- [ ] Capacity planning review
- [ ] Trading strategy optimization
- [ ] Compliance reporting

---

## 🎯 Ready to Trade!

Your InfinityAI.Pro trading platform is now deployed and ready for algorithmic trading. The system provides:

✅ **Real-time market data ingestion** from Dhan
✅ **AI-powered signal processing** with GPU acceleration  
✅ **Safe trade execution** with comprehensive risk controls
✅ **Complete monitoring** and observability stack
✅ **Production-ready** infrastructure with Docker

### Next Steps:
1. Configure your Dhan API credentials
2. Set appropriate risk limits
3. Start with paper trading mode
4. Monitor system performance
5. Gradually transition to live trading

**Happy Trading! 📈🚀**