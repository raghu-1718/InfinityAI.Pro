#!/usr/bin/env python3
"""
InfinityAI.Pro Project Restructuring Script
Reorganizes the project into an optimized multi-cloud architecture
"""

import os
import shutil
import json
from pathlib import Path

def create_directory_structure():
    """Create the new optimized directory structure"""
    
    base_path = Path("C:/Users/Raghu/InfinityAI.Pro")
    
    # New directory structure
    directories = [
        # Infrastructure
        "infrastructure/aws/terraform",
        "infrastructure/aws/kubernetes", 
        "infrastructure/aws/scripts",
        "infrastructure/azure/bicep",
        "infrastructure/azure/kubernetes",
        "infrastructure/azure/scripts",
        "infrastructure/gcp/terraform",
        "infrastructure/gcp/kubernetes", 
        "infrastructure/gcp/scripts",
        "infrastructure/shared/kafka",
        "infrastructure/shared/monitoring",
        "infrastructure/shared/security",
        
        # Engines
        "engines/engine-a-market-data/src",
        "engines/engine-a-market-data/tests",
        "engines/engine-a-market-data/docker",
        "engines/engine-a-market-data/k8s",
        "engines/engine-b-ai-ml/src",
        "engines/engine-b-ai-ml/models",
        "engines/engine-b-ai-ml/tests",
        "engines/engine-b-ai-ml/docker",
        "engines/engine-b-ai-ml/k8s",
        "engines/engine-c-execution/src",
        "engines/engine-c-execution/tests",
        "engines/engine-c-execution/docker",
        "engines/engine-c-execution/k8s",
        "engines/engine-d-chatbot/src",
        "engines/engine-d-chatbot/tests",
        "engines/engine-d-chatbot/docker",
        "engines/engine-d-chatbot/serverless",
        
        # Frontend
        "frontend/web-app/src",
        "frontend/web-app/public",
        "frontend/web-app/build",
        "frontend/mobile-app",
        "frontend/shared-components",
        
        # Shared
        "shared/libraries/auth",
        "shared/libraries/messaging",
        "shared/libraries/monitoring",
        "shared/libraries/utils",
        "shared/schemas",
        "shared/configs",
        "shared/scripts",
        
        # Monitoring
        "monitoring/dashboards",
        "monitoring/alerts",
        "monitoring/logs",
        
        # Testing
        "testing/integration",
        "testing/load",
        "testing/e2e",
        
        # Documentation
        "docs/architecture",
        "docs/deployment",
        "docs/api",
        "docs/user-guides"
    ]
    
    # Create directories
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")
    
    return base_path

def move_existing_files(base_path):
    """Move existing files to new structure"""
    
    old_path = base_path / "infinityai-pro"
    
    # Move engine files
    engine_mappings = {
        "backend/engines/engine-a": "engines/engine-a-market-data/src",
        "backend/engines/engine-b": "engines/engine-b-ai-ml/src", 
        "backend/engines/engine-c": "engines/engine-c-execution/src",
        "backend/engines/engine-d": "engines/engine-d-chatbot/src"
    }
    
    for old_engine, new_engine in engine_mappings.items():
        old_engine_path = old_path / old_engine
        new_engine_path = base_path / new_engine
        
        if old_engine_path.exists():
            try:
                shutil.copytree(old_engine_path, new_engine_path, dirs_exist_ok=True)
                print(f"Moved: {old_engine} -> {new_engine}")
            except Exception as e:
                print(f"Error moving {old_engine}: {e}")
    
    # Move frontend files
    frontend_mappings = {
        "frontend": "frontend/web-app",
        "frontend-azure": "frontend/web-app/azure-build"
    }
    
    for old_frontend, new_frontend in frontend_mappings.items():
        old_frontend_path = old_path / old_frontend
        new_frontend_path = base_path / new_frontend
        
        if old_frontend_path.exists():
            try:
                shutil.copytree(old_frontend_path, new_frontend_path, dirs_exist_ok=True)
                print(f"Moved: {old_frontend} -> {new_frontend}")
            except Exception as e:
                print(f"Error moving {old_frontend}: {e}")
    
    # Move infrastructure files
    infra_mappings = {
        "aws": "infrastructure/aws",
        "azure": "infrastructure/azure",
        "gcp": "infrastructure/gcp",
        "k8s": "infrastructure/shared/kubernetes"
    }
    
    for old_infra, new_infra in infra_mappings.items():
        old_infra_path = old_path / old_infra
        new_infra_path = base_path / new_infra
        
        if old_infra_path.exists():
            try:
                shutil.copytree(old_infra_path, new_infra_path, dirs_exist_ok=True)
                print(f"Moved: {old_infra} -> {new_infra}")
            except Exception as e:
                print(f"Error moving {old_infra}: {e}")

def create_deployment_scripts(base_path):
    """Create deployment scripts for each engine"""
    
    # Engine A deployment script (Azure AKS)
    engine_a_deploy = base_path / "engines/engine-a-market-data/deploy-to-azure.sh"
    engine_a_deploy.write_text("""#!/bin/bash
# Deploy Engine A to Azure AKS

set -e

echo "🚀 Deploying Engine A to Azure AKS..."

# Build and push Docker image
az acr build --registry infinityai --image engine-a:latest .

# Deploy to AKS
kubectl apply -f k8s/

# Wait for deployment
kubectl rollout status deployment/engine-a -n infinityai

echo "✅ Engine A deployed successfully!"
""")
    
    # Engine B deployment script (Google GKE)
    engine_b_deploy = base_path / "engines/engine-b-ai-ml/deploy-to-gcp.sh"
    engine_b_deploy.write_text("""#!/bin/bash
# Deploy Engine B to Google Cloud GKE

set -e

echo "🚀 Deploying Engine B to Google Cloud GKE..."

# Build and push Docker image
gcloud builds submit --tag gcr.io/infinityai-pro/engine-b:latest .

# Deploy to GKE
kubectl apply -f k8s/

# Wait for deployment
kubectl rollout status deployment/engine-b -n infinityai

echo "✅ Engine B deployed successfully!"
""")
    
    # Engine C deployment script (AWS ECS)
    engine_c_deploy = base_path / "engines/engine-c-execution/deploy-to-aws.sh"
    engine_c_deploy.write_text("""#!/bin/bash
# Deploy Engine C to AWS ECS

set -e

echo "🚀 Deploying Engine C to AWS ECS..."

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 152687308610.dkr.ecr.us-east-1.amazonaws.com

# Build and push Docker image
docker build -t engine-c:latest .
docker tag engine-c:latest 152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:engine-c
docker push 152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:engine-c

# Register task definition
aws ecs register-task-definition --cli-input-json file://k8s/task-definition.json

# Create or update service
aws ecs create-service --cluster infinityai-pro-cluster --service-name engine-c --task-definition engine-c --desired-count 2 --launch-type FARGATE

echo "✅ Engine C deployed successfully!"
""")
    
    # Engine D deployment script (AWS ECS + Vercel)
    engine_d_deploy = base_path / "engines/engine-d-chatbot/deploy-to-aws.sh"
    engine_d_deploy.write_text("""#!/bin/bash
# Deploy Engine D to AWS ECS and Vercel

set -e

echo "🚀 Deploying Engine D to AWS ECS and Vercel..."

# Deploy to AWS ECS
docker build -t engine-d:latest .
docker tag engine-d:latest 152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:engine-d
docker push 152687308610.dkr.ecr.us-east-1.amazonaws.com/infinityai-pro-backend:engine-d

aws ecs register-task-definition --cli-input-json file://k8s/task-definition.json
aws ecs create-service --cluster infinityai-pro-cluster --service-name engine-d --task-definition engine-d --desired-count 2 --launch-type FARGATE

# Deploy to Vercel (serverless functions)
cd serverless/
vercel --prod

echo "✅ Engine D deployed successfully!"
""")
    
    # Make scripts executable
    for script in [engine_a_deploy, engine_b_deploy, engine_c_deploy, engine_d_deploy]:
        script.chmod(0o755)
        print(f"Created deployment script: {script}")

def create_integration_config(base_path):
    """Create integration configuration files"""
    
    # Main integration config
    integration_config = {
        "engines": {
            "engine-a": {
                "name": "Market Data Ingestion",
                "cloud": "azure",
                "service": "aks",
                "url": "https://engine-a.infinityai.pro",
                "health_endpoint": "/health",
                "dependencies": ["kafka", "redis"]
            },
            "engine-b": {
                "name": "AI/ML Processing", 
                "cloud": "gcp",
                "service": "gke",
                "url": "https://engine-b.infinityai.pro",
                "health_endpoint": "/health",
                "dependencies": ["kafka", "redis", "gpu"]
            },
            "engine-c": {
                "name": "Trade Execution",
                "cloud": "aws", 
                "service": "ecs",
                "url": "https://engine-c.infinityai.pro",
                "health_endpoint": "/health",
                "dependencies": ["kafka", "redis", "postgres"]
            },
            "engine-d": {
                "name": "AI Chatbot",
                "cloud": "aws-vercel",
                "service": "ecs-serverless",
                "url": "https://engine-d.infinityai.pro", 
                "health_endpoint": "/health",
                "dependencies": ["openai", "websocket"]
            }
        },
        "shared_services": {
            "kafka": {
                "bootstrap_servers": "kafka.infinityai.pro:9092",
                "topics": ["market_data", "signals", "trades", "notifications"]
            },
            "redis": {
                "url": "redis://redis.infinityai.pro:6379",
                "clusters": ["cache", "sessions", "realtime"]
            },
            "postgres": {
                "url": "postgresql://postgres.infinityai.pro:5432/infinityai",
                "replicas": ["read-replica-1", "read-replica-2"]
            }
        },
        "monitoring": {
            "prometheus": "https://prometheus.infinityai.pro",
            "grafana": "https://grafana.infinityai.pro",
            "jaeger": "https://jaeger.infinityai.pro"
        }
    }
    
    config_file = base_path / "shared/configs/integration.json"
    config_file.write_text(json.dumps(integration_config, indent=2))
    print(f"Created integration config: {config_file}")

def create_master_deployment_script(base_path):
    """Create master deployment script"""
    
    master_deploy = base_path / "deploy-all.sh"
    master_deploy.write_text("""#!/bin/bash
# Master deployment script for InfinityAI.Pro

set -e

echo "🚀 Starting InfinityAI.Pro Multi-Cloud Deployment..."

# Phase 1: Deploy shared infrastructure
echo "📊 Phase 1: Deploying shared infrastructure..."
cd infrastructure/shared/
./deploy-kafka.sh
./deploy-redis.sh
./deploy-postgres.sh

# Phase 2: Deploy engines
echo "🔧 Phase 2: Deploying engines..."

# Engine A (Azure AKS)
cd ../../engines/engine-a-market-data/
./deploy-to-azure.sh

# Engine B (Google GKE) 
cd ../engine-b-ai-ml/
./deploy-to-gcp.sh

# Engine C (AWS ECS)
cd ../engine-c-execution/
./deploy-to-aws.sh

# Engine D (AWS ECS + Vercel)
cd ../engine-d-chatbot/
./deploy-to-aws.sh

# Phase 3: Deploy frontend
echo "🌐 Phase 3: Deploying frontend..."
cd ../../frontend/web-app/
npm run build
vercel --prod

# Phase 4: Configure DNS and SSL
echo "🌍 Phase 4: Configuring DNS and SSL..."
cd ../../infrastructure/shared/
./configure-dns.sh
./setup-ssl.sh

# Phase 5: Run integration tests
echo "🧪 Phase 5: Running integration tests..."
cd ../../testing/integration/
python run_all_tests.py

echo "✅ InfinityAI.Pro deployment completed successfully!"
echo "🌐 Access your application at: https://infinityai.pro"
""")
    
    master_deploy.chmod(0o755)
    print(f"Created master deployment script: {master_deploy}")

def create_readme_files(base_path):
    """Create README files for each major component"""
    
    # Main README
    main_readme = base_path / "README.md"
    main_readme.write_text("""# 🚀 InfinityAI.Pro - Multi-Cloud AI Trading Platform

## Architecture Overview

InfinityAI.Pro is a sophisticated multi-cloud AI trading platform that spans across AWS, Azure, Google Cloud, and Vercel to provide enterprise-grade trading capabilities.

### 🏗️ System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Engine A   │    │  Engine B   │    │  Engine C   │    │  Engine D   │
│ (Azure AKS) │────│ (GCP GKE)   │────│ (AWS ECS)   │────│(AWS/Vercel) │
│Market Data  │    │ AI/ML GPU   │    │Trade Exec   │    │AI Chatbot   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 🚀 Quick Start

1. **Deploy All Services:**
   ```bash
   ./deploy-all.sh
   ```

2. **Access the Application:**
   - Frontend: https://infinityai.pro
   - API: https://api.infinityai.pro
   - WebSocket: wss://ws.infinityai.pro

### 📁 Project Structure

- `engines/` - Four specialized trading engines
- `frontend/` - React-based web application
- `infrastructure/` - Multi-cloud infrastructure as code
- `shared/` - Common libraries and configurations
- `monitoring/` - Observability and monitoring
- `testing/` - Integration and load tests

### 🔧 Development

Each engine can be developed and deployed independently:

```bash
cd engines/engine-a-market-data/
./deploy-to-azure.sh
```

### 📊 Monitoring

- Grafana: https://grafana.infinityai.pro
- Prometheus: https://prometheus.infinityai.pro
- Jaeger: https://jaeger.infinityai.pro

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `cd testing && python run_all_tests.py`
5. Submit a pull request

### 📄 License

MIT License - see LICENSE file for details.
""")
    
    # Engine-specific READMEs
    engine_readmes = {
        "engines/engine-a-market-data/README.md": """# Engine A - Market Data Ingestion

Real-time market data processing and signal generation engine deployed on Azure AKS.

## Features
- Dhan WebSocket integration
- Technical indicator calculations
- Signal generation with confidence scoring
- Kafka event publishing

## Deployment
```bash
./deploy-to-azure.sh
```
""",
        "engines/engine-b-ai-ml/README.md": """# Engine B - AI/ML Processing

GPU-accelerated AI/ML processing engine deployed on Google Cloud GKE.

## Features
- Transformer-based price prediction
- Ensemble ML models
- GPU acceleration
- Real-time risk assessment

## Deployment
```bash
./deploy-to-gcp.sh
```
""",
        "engines/engine-c-execution/README.md": """# Engine C - Trade Execution

Idempotent trade execution engine with comprehensive safety features deployed on AWS ECS.

## Features
- Dhan broker API integration
- Pre-trade risk validation
- Kill switch implementation
- Audit logging

## Deployment
```bash
./deploy-to-aws.sh
```
""",
        "engines/engine-d-chatbot/README.md": """# Engine D - AI Chatbot

Conversational AI trading assistant deployed on AWS ECS and Vercel Edge.

## Features
- Natural language processing
- Portfolio queries
- Real-time notifications
- WebSocket communication

## Deployment
```bash
./deploy-to-aws.sh
```
"""
    }
    
    for readme_path, content in engine_readmes.items():
        readme_file = base_path / readme_path
        readme_file.write_text(content)
        print(f"Created README: {readme_path}")

def main():
    """Main restructuring function"""
    print("🏗️ Starting InfinityAI.Pro project restructuring...")
    
    # Create new directory structure
    base_path = create_directory_structure()
    
    # Move existing files
    print("\n📁 Moving existing files...")
    move_existing_files(base_path)
    
    # Create deployment scripts
    print("\n🚀 Creating deployment scripts...")
    create_deployment_scripts(base_path)
    
    # Create integration config
    print("\n⚙️ Creating integration configuration...")
    create_integration_config(base_path)
    
    # Create master deployment script
    print("\n🎯 Creating master deployment script...")
    create_master_deployment_script(base_path)
    
    # Create README files
    print("\n📚 Creating documentation...")
    create_readme_files(base_path)
    
    print("\n✅ Project restructuring completed successfully!")
    print("\n🎯 Next steps:")
    print("1. Review the new structure in the project directory")
    print("2. Update any hardcoded paths in your code")
    print("3. Run ./deploy-all.sh to deploy the complete system")
    print("4. Access your application at https://infinityai.pro")

if __name__ == "__main__":
    main()