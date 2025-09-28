# HuggingFace Spaces Deployment for GPU AI Models

## 🚀 Models to Deploy on HuggingFace Spaces (FREE GPU)

### 1. YOLO Object Detection Space
**Space Name:** `infinityai-yolo-detection`
**Hardware:** GPU (FREE tier)
**Files needed:**
- `app.py` - FastAPI app for YOLO inference
- `requirements.txt` - YOLO dependencies
- `README.md` - Space documentation

### 2. Whisper STT Space
**Space Name:** `infinityai-whisper-stt`
**Hardware:** GPU (FREE tier)
**Files needed:**
- `app.py` - FastAPI app for speech-to-text
- `requirements.txt` - Whisper dependencies
- `README.md` - Space documentation

### 3. Stable Diffusion Space
**Space Name:** `infinityai-image-generation`
**Hardware:** GPU (FREE tier)
**Files needed:**
- `app.py` - FastAPI app for image generation
- `requirements.txt` - Diffusion model dependencies
- `README.md` - Space documentation

### 4. Sentence Transformers Space
**Space Name:** `infinityai-embeddings`
**Hardware:** CPU (FREE)
**Files needed:**
- `app.py` - FastAPI app for embeddings
- `requirements.txt` - Sentence transformers
- `README.md` - Space documentation

## 📝 Deployment Commands

### Create Spaces
```bash
# Install Hugging Face CLI
pip install huggingface_hub[cli]

# Login to HuggingFace
huggingface-cli login

# Create spaces (run these commands)
huggingface-cli repo create infinityai-yolo-detection --type space --space_sdk gradio
huggingface-cli repo create infinityai-whisper-stt --type space --space_sdk gradio
huggingface-cli repo create infinityai-image-generation --type space --space_sdk gradio
huggingface-cli repo create infinityai-embeddings --type space --space_sdk gradio
```

### Configure Space Headers
Each space needs a header in README.md:

```yaml
---
title: InfinityAI YOLO Detection
emoji: 🎯
colorFrom: blue
colorTo: red
sdk: gradio
sdk_version: 4.7.1
app_file: app.py
pinned: false
license: mit
hardware: t4-small
---
```

## 🔗 Integration with Backend

Your Railway backend will call these HuggingFace Space APIs:

```python
# In your backend AI services
HUGGINGFACE_SPACES = {
    'yolo': 'https://huggingface.co/spaces/yourusername/infinityai-yolo-detection',
    'whisper': 'https://huggingface.co/spaces/yourusername/infinityai-whisper-stt',
    'diffusion': 'https://huggingface.co/spaces/yourusername/infinityai-image-generation',
    'embeddings': 'https://huggingface.co/spaces/yourusername/infinityai-embeddings'
}
```