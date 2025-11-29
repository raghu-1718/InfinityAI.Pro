# =====================================================================
# InfinityAI.Pro - Test ML Integration Locally (PowerShell)
# =====================================================================

Write-Host "🧪 Testing ML/AI Integration for Engine B" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend\engine-core\src\main.py")) {
    Write-Host "❌ Error: Please run this script from the project root" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Step 1: Installing ML dependencies..." -ForegroundColor Yellow
Set-Location backend\engine-core
pip install -q -r requirements.txt

Write-Host ""
Write-Host "📥 Step 2: Downloading NLP models..." -ForegroundColor Yellow
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)" 2>$null

Write-Host ""
Write-Host "🔍 Step 3: Checking installed libraries..." -ForegroundColor Yellow
python -c @"
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
"@

Write-Host ""
Write-Host "🚀 Step 4: Starting Engine B locally..." -ForegroundColor Green
Write-Host "   Access at: http://localhost:8080" -ForegroundColor Cyan
Write-Host "   Health check: http://localhost:8080/healthz" -ForegroundColor Cyan
Write-Host "   API docs: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:GOOGLE_CLOUD_PROJECT = "after-yesterday-473512-k3"
$env:DHAN_CLIENT_ID = "test-client-id"
$env:DHAN_ACCESS_TOKEN = "test-access-token"

# Run the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
