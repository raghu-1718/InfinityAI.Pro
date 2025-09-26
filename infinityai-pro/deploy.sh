#!/bin/bash

# InfinityAI.Pro Automated Deployment Script for Hetzner VPS
# This script sets up the Hetzner server and deploys the application
# Designed for VS Code Remote Development workflow

set -e  # Exit on any error

echo "Starting InfinityAI.Pro deployment on Hetzner..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo "Installing Docker Compose..."
sudo apt install docker-compose-plugin -y

# Add user to docker group (optional, but recommended)
sudo usermod -aG docker $USER

# Check if .env exists, if not create template
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << EOF
# API Keys and Endpoints - Replace with your actual values
OPENAI_API_KEY=your_openai_api_key_here
RUNPOD_SD_ENDPOINT=https://your-runpod-stable-diffusion-endpoint.runpod.net
RUNPOD_YOLO_ENDPOINT=https://your-runpod-yolo-endpoint.runpod.net
RUNPOD_WHISPER_ENDPOINT=https://your-runpod-whisper-endpoint.runpod.net
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
DHAN_CLIENT_ID=your_dhan_client_id
DHAN_ACCESS_TOKEN=your_dhan_access_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
DATABASE_URL=sqlite:///./chroma_db/chroma.sqlite3
OLLAMA_BASE_URL=http://ollama:11434
CHROMA_HOST=chroma
CHROMA_PORT=8000
BACKEND_URL=http://backend:8000
FRONTEND_URL=http://frontend:3000
TRAEFIK_URL=http://traefik:8080
EOF
    echo "Please edit the .env file with your actual API keys and endpoints before proceeding."
    echo "Press Enter to continue after editing..."
    read
else
    echo ".env file already exists."
fi

# Run Docker Compose
echo "Starting Docker containers..."
docker-compose up -d

# Check status
echo "Checking container status..."
docker-compose ps

echo "Deployment complete!"
echo "Application should be accessible at:"
echo "- Frontend: http://<your-hetzner-ip>"
echo "- Backend API: http://<your-hetzner-ip>/api"
echo "- Traefik Dashboard: http://<your-hetzner-ip>:8080 (if enabled)"
echo ""
echo "For VS Code Remote Development:"
echo "1. Install 'Remote - SSH' extension in VS Code"
echo "2. Connect to: ssh root@<your-hetzner-ip>"
echo "3. Open the InfinityAI.Pro folder for full IDE control"
echo ""
echo "For SSL and custom domain, update DNS to point infinityai.pro to <your-hetzner-ip>"
echo "Traefik will automatically handle SSL certificates."
echo ""
echo "RunPod GPUs: Configure endpoints in .env and route via Traefik"
echo "Hugging Face: Use APIs directly in backend code"