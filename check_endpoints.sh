#!/bin/bash
# RunPod Endpoint Health Check Script

echo "🔍 Checking RunPod Endpoints..."
echo "================================="

# Current endpoints
SD_ENDPOINT="https://ga4sxq6i6mrw72-8888.proxy.runpod.net"
YOLO_ENDPOINT="https://s2415wou493ooq-8888.proxy.runpod.net"
WHISPER_ENDPOINT="https://wmca1dz5qqm7kn-8888.proxy.runpod.net"

echo "Stable Diffusion: $SD_ENDPOINT"
curl -s -o /dev/null -w "  Status: %{http_code}\n" "$SD_ENDPOINT/sdapi/v1/txt2img" -X POST -H "Content-Type: application/json" -d '{"prompt":"test","steps":1}' || echo "  Status: Not responding"

echo ""
echo "YOLO Detection: $YOLO_ENDPOINT"
curl -s -o /dev/null -w "  Status: %{http_code}\n" "$YOLO_ENDPOINT/detect" -X POST || echo "  Status: Not responding"

echo ""
echo "Whisper STT: $WHISPER_ENDPOINT"
curl -s -o /dev/null -w "  Status: %{http_code}\n" "$WHISPER_ENDPOINT/transcribe" -X POST || echo "  Status: Not responding"

echo ""
echo "📝 If endpoints changed:"
echo "1. Update in Render Dashboard > Environment"
echo "2. No redeployment needed!"
echo ""
echo "💡 Pro tip: Endpoints usually stay the same when just stopping/starting pods"
<parameter name="filePath">/workspaces/InfinityAI.Pro/check_endpoints.sh