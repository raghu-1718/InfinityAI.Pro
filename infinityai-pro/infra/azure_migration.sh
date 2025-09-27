#!/bin/bash
# Azure GPU Migration Script for InfinityAI.Pro
# This script creates an Azure GPU VM and deploys the InfinityAI.Pro stack

set -e

echo "🚀 Starting InfinityAI.Pro migration to Azure GPU VM..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="infinityai-rg"
VM_NAME="infinityai-gpu-vm"
LOCATION="eastus"
VM_SIZE="Standard_NC6s_v3"  # Tesla K80 GPU, 6 vCPUs, 112GB RAM, 736GB SSD
ADMIN_USER="infinityai"
OS_DISK_SIZE=1024

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Installing...${NC}"
    curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
fi

# Login to Azure (you'll need to do this manually first)
echo -e "${YELLOW}⚠️  Please ensure you're logged in to Azure CLI:${NC}"
echo "az login"
echo ""

read -p "Press Enter when logged in..."

# Create resource group
echo -e "${GREEN}📦 Creating Azure resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Key Vault for secrets
echo -e "${GREEN}🔐 Creating Key Vault...${NC}"
az keyvault create --name "${VM_NAME}-kv" --resource-group $RESOURCE_GROUP --location $LOCATION

# Deploy GPU VM using Bicep template
echo -e "${GREEN}🚀 Deploying GPU VM...${NC}"
az deployment group create \
    --resource-group $RESOURCE_GROUP \
    --template-file infra/azure-bicep/gpu-vm.bicep \
    --parameters \
        vmName=$VM_NAME \
        adminUsername=$ADMIN_USER \
        vmSize=$VM_SIZE \
        osDiskSizeGB=$OS_DISK_SIZE \
        location=$LOCATION

# Get VM public IP
VM_IP=$(az vm show --resource-group $RESOURCE_GROUP --name $VM_NAME --show-details --query [publicIps] -o tsv)
echo -e "${GREEN}🌐 VM Public IP: $VM_IP${NC}"

# Setup script for the VM
cat > setup_azure_gpu.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up Azure GPU VM..."

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git htop jq

# Install NVIDIA drivers
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get install -y cuda-drivers

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install NVIDIA Docker support
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

# Clone repository
echo "📥 Cloning InfinityAI.Pro repository..."
git clone https://github.com/raghu-1718/InfinityAI.Pro.git .

# Create .env file
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

# Create systemd service
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

echo "✅ Azure GPU VM setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /opt/infinityai-pro/.env with your API keys"
echo "2. Run: cd /opt/infinityai-pro && docker-compose up -d"
echo "3. Check GPU: nvidia-smi"
echo ""
echo "🌐 Your VM IP: $(curl -s ifconfig.me)"
EOF

# Copy setup script to VM
echo -e "${GREEN}📤 Copying setup script to VM...${NC}"
scp -o StrictHostKeyChecking=no setup_azure_gpu.sh $ADMIN_USER@$VM_IP:/home/$ADMIN_USER/

# Execute setup script
echo -e "${GREEN}⚙️  Running setup script on VM...${NC}"
ssh -o StrictHostKeyChecking=no $ADMIN_USER@$VM_IP "chmod +x setup_azure_gpu.sh && sudo ./setup_azure_gpu.sh"

# Clean up
rm setup_azure_gpu.sh

echo ""
echo -e "${GREEN}🎉 Azure migration complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "Resource Group: $RESOURCE_GROUP"
echo "VM Name: $VM_NAME"
echo "IP Address: $VM_IP"
echo "GPU: Tesla K80 (12GB VRAM)"
echo "Cost: ~$800/month"
echo ""
echo -e "${YELLOW}🔑 Next steps:${NC}"
echo "1. SSH to VM: ssh $ADMIN_USER@$VM_IP"
echo "2. Edit .env file with your API keys"
echo "3. Start services: cd /opt/infinityai-pro && docker-compose up -d"
echo "4. Update DNS to point to $VM_IP"
echo "5. Test AI services with GPU acceleration"
EOF