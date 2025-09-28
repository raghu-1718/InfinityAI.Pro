#!/bin/bash

# Environment Switcher for InfinityAI.Pro
# Usage: ./switch-env.sh [local|render|azure|linode]

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 [local|render|azure|linode]"
    echo "Available environments:"
    echo "  local  - Local development with Docker Compose"
    echo "  render - Render deployment"
    echo "  azure  - Azure Container Apps"
    echo "  linode - Linode Kubernetes"
    exit 1
fi

case $ENVIRONMENT in
    "local")
        echo "🔧 Switching to LOCAL development environment..."

        # Update docker-compose.yml for local development
        cat > docker-compose.yml << 'EOF'
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - VECTOR_DB_URL=http://vectordb:8000
    depends_on:
      - vectordb

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  vectordb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma

volumes:
  chroma_data:
EOF

        echo "✅ Local environment configured"
        echo "🚀 Run: docker-compose up --build -d"
        ;;

    "render")
        echo "☁️ Switching to RENDER production environment..."

        # Update .env with Render URLs (placeholder)
        sed -i 's|VECTOR_DB_URL=.*|VECTOR_DB_URL=https://infinityai-vectordb.onrender.com|' .env
        sed -i 's|REACT_APP_API_URL=.*|REACT_APP_API_URL=https://infinityai-backend.onrender.com|' .env

        echo "✅ Render environment configured"
        echo "🚀 Deploy: git push render main"
        ;;

    "azure")
        echo "☁️ Switching to AZURE production environment..."

        # Update .env with Azure URLs (placeholder)
        sed -i 's|VECTOR_DB_URL=.*|VECTOR_DB_URL=https://infinityai-vectordb.azurecontainerapps.io|' .env
        sed -i 's|REACT_APP_API_URL=.*|REACT_APP_API_URL=https://infinityai-backend.azurecontainerapps.io|' .env

        echo "✅ Azure environment configured"
        echo "🚀 Deploy: az deployment group create --template-file infra/azure-bicep/main.bicep"
        ;;

    "linode")
        echo "☁️ Switching to LINODE production environment..."

        # Update .env with Linode URLs (placeholder)
        sed -i 's|VECTOR_DB_URL=.*|VECTOR_DB_URL=http://infinityai-vectordb:8000|' .env
        sed -i 's|REACT_APP_API_URL=.*|REACT_APP_API_URL=http://infinityai-backend:8000|' .env

        echo "✅ Linode environment configured"
        echo "🚀 Deploy: kubectl apply -f infra/linode-k8s/deployment.yaml"
        ;;

    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "Available: local, render, azure, linode"
        exit 1
        ;;
esac

echo ""
echo "📋 Environment switched to: $ENVIRONMENT"
echo "📝 Check CLOUD_DEPLOYMENT_GUIDE.md for detailed instructions"