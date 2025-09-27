# RunPod Cost Optimization Guide

## Current Pod Status:
- Stable Diffusion: ga4sxq6i6mrw72 (Running)
- YOLO: s2415wou493ooq (Running)
- Whisper: wmca1dz5qqm7kn (Running)

## To Stop Pods (Save Costs):
1. Go to https://runpod.io/console/pods
2. Select each pod
3. Click 'Stop' button
4. Pods will stop billing immediately

## To Start Pods When Needed:
1. Go to https://runpod.io/console/pods
2. Click 'Start' on each pod
3. Wait 2-3 minutes for pods to be ready
4. Update endpoints in Render if they change

## Cost Savings:
- RTX A5000: ~$0.69/hour when running
- RTX A40: ~$0.69/hour when running
- Stopped pods: $0.00/hour

## Future Automation Options:
1. API-based start/stop via RunPod API
2. Application-triggered pod management
3. Scheduled start/stop based on trading hours</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/RUNPOD_COST_OPTIMIZATION.md