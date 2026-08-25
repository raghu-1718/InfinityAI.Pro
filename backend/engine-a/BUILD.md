# Engine A - Build and Deploy

## Local Build (Updated for Shared Libraries)

The Dockerfile now uses the parent `backend/` directory as build context to access shared libraries.

### Build Command

From the **repository root**:

```bash
docker build -f backend/engine-a/Dockerfile -t engine-a:latest backend/
```

**Note**: The build context is `backend/` (the entire backend directory), not `backend/engine-a/`.

### Cloud Build (Automatic)

When deploying to Cloud Run, ensure the build is triggered from the `backend/` directory:

```bash
cd backend
gcloud run deploy engine-a \
  --source=. \
  --dockerfile=engine-a/Dockerfile \
  --region=asia-south1
```

## Shared Library Integration

Engine A now imports Google integrations from `backend/shared/google_integrations/`:

- `GenAIClient`, `GeminiModel`, `ModelTier`
- `TradingLogger`, `TradingEventType`
- `ModelStorage`, `TradingHistoryStorage`
- `AgentOrchestrator`, `create_trading_workflow`

This eliminates code duplication and ensures all engines use the same library versions.
