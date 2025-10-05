# 🚀 InfinityAI.Pro Quick Deployment Guide

## 🏃‍♂️ Quick Start

### Local Development
```bash
# Start all services
docker-compose -f docker-compose.engines.yml up -d

# Check engine health
curl http://localhost:8001/health  # Engine A
curl http://localhost:8002/health  # Engine B

# Build frontend
cd frontend
npm run build

# Deploy frontend locally
npm start
```

### Production Deployment

#### 1️⃣ AWS EKS Deployment
```bash
# Configure kubectl
aws eks update-kubeconfig --name infinityai-pro-cluster --region us-west-2

# Deploy all components
kubectl apply -f k8s/

# Check status
kubectl get pods -n infinityai -w
kubectl get services -n infinityai
```

#### 2️⃣ Frontend Deployment (Vercel)
```bash
cd frontend
npm run build
vercel --prod
```

#### 3️⃣ Terraform Infrastructure (AWS)
```bash
cd aws
terraform init
terraform plan
terraform apply -auto-approve
```

## 🛠️ Maintenance Commands

### Health Checks
```bash
# System status
./deploy_system.ps1 -TestEngines

# Docker status
docker ps
docker-compose ps

# Service logs
docker logs infinityai-engine-a-prod
docker logs infinityai-engine-b-prod
```

### Scaling
```bash
# Scale engines
kubectl scale deployment engine-a-deployment --replicas=3 -n infinityai

# Check resource usage
kubectl top pods -n infinityai
```

### Troubleshooting
```bash
# Restart unhealthy engines
docker restart infinityai-engine-c-prod infinityai-engine-d-prod

# View engine logs
docker logs infinityai-engine-c-prod --tail 50
docker logs infinityai-engine-d-prod --tail 50

# Database connection test
docker exec infinityai-postgres psql -U infinityai_user -d infinityai_db -c "SELECT version();"
```

## 📊 Monitoring URLs

- **Grafana:** http://localhost:3000
- **Prometheus:** http://localhost:9090  
- **Jaeger:** http://localhost:16686
- **Engine A:** http://localhost:8001/health
- **Engine B:** http://localhost:8002/health

## 🔧 Configuration

### Environment Variables
```bash
# Production API URL
export REACT_APP_API_URL="https://api.infinityai.pro"
export REACT_APP_ENVIRONMENT="production"

# Database
export POSTGRES_PASSWORD="infinityai_secure_pass"
export POSTGRES_USER="infinityai_user"
export POSTGRES_DB="infinityai_db"
```

### Kubernetes Secrets
```bash
kubectl create secret generic app-secrets \
  --from-literal=db-password="infinityai_secure_pass" \
  --from-literal=api-key="your-api-key" \
  -n infinityai
```

## 🆘 Emergency Procedures

### System Down
1. Check infrastructure: `docker ps`
2. Restart services: `docker-compose restart`
3. Check logs: `docker logs [container]`
4. Escalate if needed

### Data Loss Prevention
1. Database backups are automated
2. Check backup status: `kubectl get jobs -n infinityai`
3. Manual backup: `pg_dump infinityai_db > backup.sql`

---

**Last Updated:** October 4, 2025  
**Status:** Production Ready ✅