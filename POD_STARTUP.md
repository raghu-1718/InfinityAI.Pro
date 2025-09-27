# Pod Startup Commands

## Run these commands on your LOCAL machine (not in GitHub Codespaces)

## Step 1: Copy scripts to pods
scp -i ~/.ssh/id_ed25519 whisper_app.py wmca1dz5qqm7kn-64411980@ssh.runpod.io:/workspace/
scp -i ~/.ssh/id_ed25519 yolo_app.py s2415wou493ooq-64411020@ssh.runpod.io:/workspace/

## Step 2: Start Whisper service
ssh wmca1dz5qqm7kn-64411980@ssh.runpod.io -i ~/.ssh/id_ed25519
cd /workspace
pip install fastapi uvicorn whisper torch
python whisper_app.py

## Step 3: Start YOLO service (in new terminal)
ssh s2415wou493ooq-64411020@ssh.runpod.io -i ~/.ssh/id_ed25519
cd /workspace
pip install fastapi uvicorn ultralytics opencv-python pillow
python yolo_app.py

## Step 4: Check Stable Diffusion pod
ssh ga4sxq6i6mrw72-XXXXX@ssh.runpod.io -i ~/.ssh/id_ed25519
ps aux | grep webui
# If not running, start Automatic1111 webui</content>
<parameter name="filePath">/workspaces/InfinityAI.Pro/POD_STARTUP.md