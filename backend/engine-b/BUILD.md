# Engine B - Build and Deploy

## Local Build (Updated for Shared Libraries)

The Dockerfile now uses the parent `backend/` directory as build context to access shared libraries.

### Build Command

From the **repository root**:

```bash
docker build -f backend/engine-b/Dockerfile -t engine-b:latest backend/
```

**Note**: The build context is `backend/` (the entire backend directory), not `backend/engine-b/`.

### Cloud Build (Automatic)

When deploying to Cloud Run, ensure the build is triggered from the `backend/` directory:

```bash
cd backend
gcloud run deploy engine-b \
  --source=. \
  --dockerfile=engine-b/Dockerfile \
  --region=us-central1
```

## Shared Library Integration

Engine B now imports Google integrations from `backend/shared/google_integrations/`:

- `GenAIClient`, `EnhancedGenAIClient`
- `TradingLogger`, `ModelStorage`
- `TradingSignalAgent`, `RiskAssessmentAgent`, etc.

## ML Pipeline

Engine B is configured to load production models from Google Cloud Storage:

- Bucket: `{PROJECT_ID}-ml-models`
- Prefix: `xgb/`

The Root `ml/` directory contains the official training pipeline.
