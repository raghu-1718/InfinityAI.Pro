# RunPod Endpoint Management

## Current Endpoints (as of Sep 27, 2025):
- Stable Diffusion: https://ga4sxq6i6mrw72-8888.proxy.runpod.net
- YOLO: https://s2415wou493ooq-8888.proxy.runpod.net
- Whisper: https://wmca1dz5qqm7kn-8888.proxy.runpod.net

## Endpoint Stability:
✅ Endpoints typically remain the same when stopping/starting pods
✅ Same pod ID = same endpoint (99% of the time)
⚠️  May change if pod is terminated/recreated or hardware reassigned

## Update Process:
1. Start pods in RunPod console
2. Check if endpoints changed
3. If changed: Update in Render dashboard (no redeployment needed)
4. If same: No action required

## Quick Endpoint Check:
After starting pods, visit:
- https://runpod.io/console/pods
- Copy new endpoints if different
- Update Render environment variables</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/RUNPOD_ENDPOINTS.md