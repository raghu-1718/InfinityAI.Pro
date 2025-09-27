#!/bin/bash
# Linode GPU Migration Script for InfinityAI.Pro
# This script sets up a Linode GPU instance with Docker and deploys the InfinityAI.Pro stack

set -e

echo "🚀 Starting InfinityAI.Pro migration to Linode GPU instance..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTANCE_TYPE="g2-gpu-rtx4000a1-l"  # RTX4000 Ada x1 Large
REGION="us-east"
LABEL="infinityai-gpu"
IMAGE="linode/ubuntu22.04"

# Check if Linode CLI is installed
if ! command -v linode-cli &> /dev/null; then
    echo -e "${RED}❌ Linode CLI not found. Installing...${NC}"
    pip3 install linode-cli
fi

# Authenticate with Linode (you'll need to do this manually first)
echo -e "${YELLOW}⚠️  Please ensure you're authenticated with Linode CLI:${NC}"
echo "linode-cli configure"
echo ""

read -p "Press Enter when authenticated..."

# Create Linode instance
echo -e "${GREEN}📦 Creating Linode GPU instance...${NC}"
INSTANCE_ID=$(linode-cli linodes create \
    --type $INSTANCE_TYPE \
    --region $REGION \
    --image $IMAGE \
    --label $LABEL \
    --tags ai,trading,gpu \
    --root-pass $(openssl rand -base64 32) \
    --authorized-keys "$(cat ~/.ssh/id_rsa.pub 2>/dev/null || echo '')" \
    --json | jq -r '.[0].id')

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${RED}❌ Failed to create instance${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Instance created with ID: $INSTANCE_ID${NC}"

# Get instance IP
INSTANCE_IP=$(linode-cli linodes view $INSTANCE_ID --json | jq -r '.[0].ipv4[0]')
echo -e "${GREEN}🌐 Instance IP: $INSTANCE_IP${NC}"

# Wait for instance to boot
echo -e "${YELLOW}⏳ Waiting for instance to boot...${NC}"
sleep 60

# Setup script for the instance
cat > setup_gpu_instance.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up GPU instance..."

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git htop nvtop jq

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install NVIDIA drivers and container toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update && apt-get install -y nvidia-docker2
systemctl restart docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /opt/infinityai-pro
cd /opt/infinityai-pro

# Clone repository (you'll need to add your SSH key or use HTTPS)
echo "📥 Cloning InfinityAI.Pro repository..."
git clone https://github.com/raghu-1718/InfinityAI.Pro.git .

# Create .env file (you'll need to fill in actual values)
cat > .env << 'ENV_EOF'
# Backend Config
DB_URL=postgresql://user:password@db:5432/infinityai
HF_TOKEN=your_huggingface_token
RUNPOD_API_KEY=your_runpod_api_key
SECRET_KEY=your_secret_key

# Broker API
DHAN_API_KEY=your_dhan_api_key

# Ollama Configuration
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2

# Whisper Configuration
WHISPER_MODEL=tiny
WHISPER_LANGUAGE=en

# Stable Diffusion Configuration
DIFFUSERS_MODEL=stabilityai/sd-turbo

# YOLO Configuration
YOLO_MODEL=yolov8n.pt

# Sentence Transformers Configuration
SBERT_MODEL=all-MiniLM-L6-v2

# Vector Database Configuration
VECTOR_DB=chromadb
VECTOR_DB_URL=http://localhost:8080
VECTOR_DB_COLLECTION=infinity_ai_docs

# Additional API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
HUGGINGFACE_API_KEY=your_huggingface_key
OLLAMA_BASE_URL=http://ollama:11434
OPENAI_API_KEY=your_openai_key
ENV_EOF

echo "⚠️  IMPORTANT: Edit /opt/infinityai-pro/.env with your actual API keys!"

# Enable GPU support in Docker Compose
cat >> docker-compose.yml << 'DOCKER_EOF'

    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
DOCKER_EOF

# Create systemd service for auto-start
cat > /etc/systemd/system/infinityai.service << EOF
[Unit]
Description=InfinityAI.Pro Trading Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/infinityai-pro
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl enable infinityai.service

echo "✅ GPU instance setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /opt/infinityai-pro/.env with your API keys"
echo "2. Run: cd /opt/infinityai-pro && docker-compose up -d"
echo "3. Check GPU: nvidia-smi"
echo "4. Monitor: nvtop"
echo ""
echo "🌐 Your instance IP: $(curl -s ifconfig.me)"
EOF

# Copy setup script to instance
echo -e "${GREEN}📤 Copying setup script to instance...${NC}"
scp -o StrictHostKeyChecking=no setup_gpu_instance.sh root@$INSTANCE_IP:/root/

# Execute setup script
echo -e "${GREEN}⚙️  Running setup script on instance...${NC}"
ssh -o StrictHostKeyChecking=no root@$INSTANCE_IP "chmod +x setup_gpu_instance.sh && ./setup_gpu_instance.sh"

# Clean up
rm setup_gpu_instance.sh

echo ""
echo -e "${GREEN}🎉 Migration complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "Instance ID: $INSTANCE_ID"
echo "IP Address: $INSTANCE_IP"
echo "GPU: RTX4000 Ada (48GB VRAM)"
echo "Cost: ~$638/month"
echo ""
echo -e "${YELLOW}🔑 Next steps:${NC}"
echo "1. SSH to instance: ssh root@$INSTANCE_IP"
echo "2. Edit .env file with your API keys"
echo "3. Start services: cd /opt/infinityai-pro && docker-compose up -d"
echo "4. Update DNS to point to $INSTANCE_IP"
echo "5. Test AI services with GPU acceleration"
echo ""
echo -e "${GREEN}💡 Pro tip: Consider using local GPU instead of RunPod for cost savings!${NC}"