#!/bin/bash
# =====================================================================
# InfinityAI.Pro - Test ML Integration Locally
# =====================================================================

echo "🧪 Testing ML/AI Integration for Engine B"
echo ""

# Check if we're in the right directory
if [ ! -f "backend/engine-core/src/main.py" ]; then
    echo "❌ Error: Please run this script from the project root"
    exit 1
fi

echo "📦 Step 1: Installing ML dependencies..."
cd backend/engine-core
pip install -q -r requirements.txt

echo ""
echo "📥 Step 2: Downloading NLP models..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)" 2>/dev/null || true

echo ""
echo "🔍 Step 3: Checking installed libraries..."
python -c "
import sys
libraries = [
    ('tensorflow', 'TensorFlow'),
    ('torch', 'PyTorch'),
    ('sklearn', 'Scikit-learn'),
    ('xgboost', 'XGBoost'),
    ('lightgbm', 'LightGBM'),
    ('transformers', 'Transformers'),
    ('cv2', 'OpenCV'),
    ('nltk', 'NLTK'),
    ('spacy', 'spaCy'),
    ('mlflow', 'MLflow'),
    ('h2o', 'H2O.ai')
]

print('\n📊 ML Library Status:\n')
for lib, name in libraries:
    try:
        __import__(lib)
        print(f'  ✅ {name:20s} - Installed')
    except ImportError:
        print(f'  ⚠️  {name:20s} - Not installed (optional)')
"

echo ""
echo "🚀 Step 4: Starting Engine B locally..."
echo "   Access at: http://localhost:8080"
echo "   Health check: http://localhost:8080/healthz"
echo "   API docs: http://localhost:8080/docs"
echo ""

# Set environment variables
export GOOGLE_CLOUD_PROJECT="after-yesterday-473512-k3"
export DHAN_CLIENT_ID="test-client-id"
export DHAN_ACCESS_TOKEN="test-access-token"

# Run the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
