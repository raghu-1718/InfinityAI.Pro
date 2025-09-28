# RunPod GPU Setup Script
#!/bin/bash

# InfinityAI.Pro - RunPod GPU Pod Setup
# Configures GPU pods for AI workloads

set -e

# Configuration
TEMPLATE_NAME="infinityai-pro-gpu"
REGION="US"  # US, EU, AP
GPU_TYPE="NVIDIA RTX A4000"  # or other GPU types
CONTAINER_IMAGE="runpod/stable-diffusion:web-automatic"
MIN_VRAM="8"  # GB
MAX_PRICE="1.0"  # Max price per hour

echo "🚀 Setting up RunPod GPU pods for InfinityAI.Pro..."

# Check if RunPod CLI is installed
if ! command -v runpodctl &> /dev/null; then
    echo "❌ RunPod CLI not installed. Please install from https://github.com/runpod/runpodctl"
    exit 1
fi

# Check authentication
if ! runpodctl config --check; then
    echo "❌ RunPod not authenticated. Please run 'runpodctl config'"
    exit 1
fi

# Create pod template
cat > pod_template.yaml << EOF
version: "1.0"
name: "$TEMPLATE_NAME"
image: "$CONTAINER_IMAGE"
gpu: "$GPU_TYPE"
minVram: $MIN_VRAM
ports: "22/tcp,80/tcp,443/tcp,7860/tcp"
volumeMountPath: "/workspace"
env:
  - key: "JUPYTER_PASSWORD"
    value: "infinityai2024"
  - key: "PUBLIC_KEY"
    value: "\${PUBLIC_KEY}"
networks:
  - name: "public"
    port: 80
    protocol: "http"
  - name: "api"
    port: 443
    protocol: "https"
EOF

echo "📝 Created pod template: pod_template.yaml"

# Deploy pod
echo "🚀 Deploying GPU pod..."
POD_ID=$(runpodctl create pod --template pod_template.yaml --region "$REGION" --maxPrice "$MAX_PRICE")

if [ -z "$POD_ID" ]; then
    echo "❌ Failed to create pod"
    exit 1
fi

echo "✅ Pod created with ID: $POD_ID"

# Wait for pod to be ready
echo "⏳ Waiting for pod to be ready..."
runpodctl wait "$POD_ID"

# Get pod details
POD_INFO=$(runpodctl get pod "$POD_ID" --json)
POD_IP=$(echo "$POD_INFO" | jq -r '.publicIp')

echo "🎉 Pod is ready!"
echo "🌐 Public IP: $POD_IP"
echo "🔗 Web UI: http://$POD_IP:7860"
echo "🔑 Jupyter: http://$POD_IP:8888 (password: infinityai2024)"

# Save pod information
cat > pod_info.env << EOF
# InfinityAI.Pro RunPod Configuration
RUNPOD_POD_ID=$POD_ID
RUNPOD_PUBLIC_IP=$POD_IP
RUNPOD_WEB_UI=http://$POD_IP:7860
RUNPOD_JUPYTER=http://$POD_IP:8888
RUNPOD_SSH=ssh root@$POD_IP
EOF

echo "💾 Pod information saved to pod_info.env"

# Setup endpoints for different AI services
echo "🔧 Setting up AI service endpoints..."

# YOLO endpoint
runpodctl exec "$POD_ID" -- bash -c "
cd /workspace &&
git clone https://github.com/ultralytics/ultralytics.git &&
cd ultralytics &&
pip install -e . &&
python -c 'from ultralytics import YOLO; model = YOLO(\"yolov8n.pt\"); print(\"YOLO ready\")'
"

# Stable Diffusion endpoint
runpodctl exec "$POD_ID" -- bash -c "
cd /workspace &&
pip install diffusers transformers accelerate &&
python -c 'from diffusers import StableDiffusionPipeline; print(\"Stable Diffusion ready\")'
"

# Whisper endpoint
runpodctl exec "$POD_ID" -- bash -c "
cd /workspace &&
pip install openai-whisper &&
python -c 'import whisper; model = whisper.load_model(\"base\"); print(\"Whisper ready\")'
"

echo "🎯 AI services configured!"
echo "📋 Endpoints:"
echo "  YOLO: http://$POD_IP:8001"
echo "  Stable Diffusion: http://$POD_IP:8002"
echo "  Whisper: http://$POD_IP:8003"

echo "💡 To stop the pod: runpodctl stop $POD_ID"
echo "💡 To delete the pod: runpodctl delete $POD_ID"