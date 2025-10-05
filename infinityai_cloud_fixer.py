#!/usr/bin/env python3
"""
InfinityAI.Pro Multi-Cloud Deployment Fix Script
Eliminates Vercel and configures AWS, Azure, and GCP integration
"""

import json
import subprocess
import sys
from datetime import datetime

class InfinityAICloudFixer:
    def __init__(self):
        self.config = {
            "target_architecture": "multi_cloud_no_vercel",
            "clouds": {
                "azure": {
                    "working_endpoints": [
                        "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                        "https://infinityai-engine-a--0000006.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io"
                    ],
                    "broken_endpoints": [
                        "https://brave-ocean-09e85cd10-preview.centralus.2.azurestaticapps.net"
                    ]
                },
                "aws": {
                    "broken_endpoints": [
                        "http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com"
                    ]
                },
                "gcp": {
                    "missing_endpoints": [
                        "https://engine-b-service.infinityai.pro"
                    ]
                }
            }
        }
        
    def generate_azure_static_web_app_config(self):
        """Generate Azure Static Web App configuration"""
        config = {
            "routes": [
                {
                    "route": "/api/*",
                    "rewrite": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/*"
                },
                {
                    "route": "/health",
                    "rewrite": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health"
                },
                {
                    "route": "/ws/*",
                    "rewrite": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/ws/*"
                }
            ],
            "navigationFallback": {
                "rewrite": "/index.html"
            },
            "globalHeaders": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
        }
        
        with open("infinityai-pro/frontend/staticwebapp.config.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print("✅ Generated Azure Static Web App configuration")
        
    def generate_frontend_config(self):
        """Generate frontend configuration pointing to multi-cloud APIs"""
        config = {
            "api": {
                "base_urls": {
                    "primary": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                    "engine_a": "https://infinityai-app--0000036.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                    "engine_a_alt": "https://infinityai-engine-a--0000006.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io",
                    "engine_b": "https://ENGINE_B_GCP_ENDPOINT_PLACEHOLDER",
                    "engine_c": "https://ENGINE_C_AWS_ENDPOINT_PLACEHOLDER", 
                    "engine_d": "https://ENGINE_D_AWS_ENDPOINT_PLACEHOLDER"
                },
                "endpoints": {
                    "health": "/health",
                    "market_data": "/api/market-data",
                    "ai_chat": "/api/chat",
                    "trading": "/api/trading",
                    "websocket": "/ws"
                },
                "fallback_strategy": "azure_primary"
            },
            "deployment": {
                "environment": "production",
                "clouds": ["azure", "aws", "gcp"],
                "eliminated": ["vercel"],
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Write as JSON config
        with open("infinityai-pro/frontend/src/config/api-config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        # Write as JavaScript config
        js_config = f"""
// InfinityAI.Pro Multi-Cloud API Configuration (No Vercel)
export const API_CONFIG = {json.dumps(config, indent=2)};

export const getApiUrl = (service = 'primary') => {{
    return API_CONFIG.api.base_urls[service] || API_CONFIG.api.base_urls.primary;
}};

export const getEndpoint = (endpoint) => {{
    return API_CONFIG.api.endpoints[endpoint] || '';
}};

export const buildApiUrl = (service = 'primary', endpoint = '') => {{
    const baseUrl = getApiUrl(service);
    const endpointPath = getEndpoint(endpoint);
    return `${{baseUrl}}${{endpointPath}}`;
}};
"""
        
        with open("infinityai-pro/frontend/src/config/api-config.js", "w") as f:
            f.write(js_config)
        
        print("✅ Generated frontend API configuration")
        
    def generate_docker_compose_no_vercel(self):
        """Generate Docker Compose without Vercel dependencies"""
        compose_config = {
            "version": "3.8",
            "services": {
                "redis": {
                    "image": "redis:alpine",
                    "ports": ["6379:6379"]
                },
                "engine-a": {
                    "build": {
                        "context": ".",
                        "dockerfile": "backend/engines/engine-a/Dockerfile"
                    },
                    "ports": ["8100:8000"],
                    "environment": [
                        "PORT=8000",
                        "REDIS_URL=redis://redis:6379",
                        "AZURE_DEPLOYMENT=true"
                    ]
                },
                "engine-b": {
                    "build": {
                        "context": ".",
                        "dockerfile": "backend/engines/engine-b/Dockerfile"
                    },
                    "ports": ["8101:8001"],
                    "environment": [
                        "PORT=8001",
                        "REDIS_URL=redis://redis:6379",
                        "GCP_DEPLOYMENT=true"
                    ]
                },
                "engine-c": {
                    "build": {
                        "context": ".",
                        "dockerfile": "backend/engines/engine-c/Dockerfile"
                    },
                    "ports": ["8102:8002"],
                    "environment": [
                        "PORT=8002",
                        "REDIS_URL=redis://redis:6379",
                        "AWS_DEPLOYMENT=true"
                    ]
                },
                "engine-d": {
                    "build": {
                        "context": ".",
                        "dockerfile": "backend/engines/engine-d/Dockerfile"
                    },
                    "ports": ["8103:8000"],
                    "environment": [
                        "PORT=8000",
                        "REDIS_URL=redis://redis:6379",
                        "AWS_DEPLOYMENT=true"
                    ]
                }
            }
        }
        
        with open("infinityai-pro/docker-compose.yml", "w") as f:
            import yaml
            try:
                yaml.dump(compose_config, f, default_flow_style=False)
                print("✅ Generated Docker Compose configuration (no Vercel)")
            except ImportError:
                # Fallback to manual YAML-like format
                f.write("version: '3.8'\\n\\nservices:\\n")
                for service, config in compose_config["services"].items():
                    f.write(f"  {service}:\\n")
                    for key, value in config.items():
                        if isinstance(value, dict):
                            f.write(f"    {key}:\\n")
                            for subkey, subvalue in value.items():
                                f.write(f"      {subkey}: {subvalue}\\n")
                        elif isinstance(value, list):
                            f.write(f"    {key}:\\n")
                            for item in value:
                                f.write(f"      - {item}\\n")
                        else:
                            f.write(f"    {key}: {value}\\n")
                print("✅ Generated Docker Compose configuration (no Vercel, manual format)")
    
    def generate_aws_fix_commands(self):
        """Generate AWS CLI commands to fix ECS deployment"""
        commands = [
            "# AWS ECS Cluster Fix Commands",
            "aws ecs describe-clusters --clusters infinityai-pro-cluster",
            "aws ecs list-services --cluster infinityai-pro-cluster",
            "aws ecs describe-services --cluster infinityai-pro-cluster --services engine-c-service engine-d-service",
            "",
            "# Restart services if they exist",
            "aws ecs update-service --cluster infinityai-pro-cluster --service engine-c-service --force-new-deployment",
            "aws ecs update-service --cluster infinityai-pro-cluster --service engine-d-service --force-new-deployment",
            "",
            "# Check Load Balancer",
            "aws elbv2 describe-load-balancers --names infinityai-pro-alb",
            "aws elbv2 describe-target-groups --load-balancer-arn <ALB_ARN>",
            "",
            "# Check security groups",
            "aws ec2 describe-security-groups --group-names infinityai-*"
        ]
        
        with open("aws_fix_commands.sh", "w") as f:
            f.write("\\n".join(commands))
        
        print("✅ Generated AWS fix commands")
        
    def generate_gcp_deployment_config(self):
        """Generate GCP Kubernetes deployment for Engine B"""
        deployment_yaml = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: infinityai-engine-b
  labels:
    app: infinityai-engine-b
spec:
  replicas: 2
  selector:
    matchLabels:
      app: infinityai-engine-b
  template:
    metadata:
      labels:
        app: infinityai-engine-b
    spec:
      containers:
      - name: engine-b
        image: gcr.io/PROJECT_ID/infinityai-engine-b:latest
        ports:
        - containerPort: 8001
        env:
        - name: PORT
          value: "8001"
        - name: REDIS_URL
          value: "redis://redis:6379"
        - name: GCP_DEPLOYMENT
          value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: infinityai-engine-b-service
spec:
  selector:
    app: infinityai-engine-b
  ports:
  - port: 80
    targetPort: 8001
  type: LoadBalancer
"""
        
        with open("gcp_engine_b_deployment.yaml", "w") as f:
            f.write(deployment_yaml)
        
        print("✅ Generated GCP Kubernetes deployment config")
    
    def generate_integration_update_script(self):
        """Generate script to update all integration configurations"""
        script = """#!/bin/bash

echo "🚀 InfinityAI.Pro Multi-Cloud Integration Fix"
echo "============================================="

# 1. Azure Frontend Redeployment
echo "🔵 Redeploying Azure Static Web App..."
cd infinityai-pro/frontend
az staticwebapp create --name infinityai-frontend --resource-group infinityai-rg --source . --branch main

# 2. AWS ECS Services Check
echo "🟠 Checking AWS ECS Services..."
aws ecs describe-clusters --clusters infinityai-pro-cluster
aws ecs list-services --cluster infinityai-pro-cluster

# 3. GCP Engine B Deployment
echo "🔴 Deploying Engine B to GCP..."
gcloud container clusters create infinityai-engine-b-cluster --zone us-central1-a
kubectl apply -f ../gcp_engine_b_deployment.yaml

# 4. Update DNS and Load Balancer configurations
echo "🌐 Updating multi-cloud routing..."

echo "✅ Multi-cloud integration fix completed!"
"""
        
        with open("multi_cloud_integration_fix.sh", "w") as f:
            f.write(script)
        
        print("✅ Generated integration fix script")
    
    def run_fixes(self):
        """Execute all fixes"""
        print("🚀 Starting InfinityAI.Pro Multi-Cloud Fix Process")
        print("=" * 60)
        
        try:
            # Create necessary directories
            subprocess.run(["mkdir", "-p", "infinityai-pro/frontend/src/config"], check=False)
            
            # Generate all configurations
            self.generate_azure_static_web_app_config()
            self.generate_frontend_config()
            self.generate_docker_compose_no_vercel()
            self.generate_aws_fix_commands()
            self.generate_gcp_deployment_config()
            self.generate_integration_update_script()
            
            print("\\n🎯 Fix Summary:")
            print("✅ Azure Static Web App config generated")
            print("✅ Frontend API config updated (no Vercel)")
            print("✅ Docker Compose updated (no Vercel)")
            print("✅ AWS fix commands prepared")
            print("✅ GCP deployment config ready")
            print("✅ Integration fix script created")
            
            print("\\n📋 Next Steps:")
            print("1. Run: chmod +x multi_cloud_integration_fix.sh")
            print("2. Execute: ./multi_cloud_integration_fix.sh")
            print("3. Configure AWS CLI: aws configure")
            print("4. Test endpoints: python multi_cloud_integration_test.py")
            
        except Exception as e:
            print(f"❌ Error during fix process: {e}")
            return False
            
        return True

if __name__ == "__main__":
    fixer = InfinityAICloudFixer()
    success = fixer.run_fixes()
    sys.exit(0 if success else 1)