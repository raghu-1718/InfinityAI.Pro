# Engine C - Build and Deploy

## Local Build (Updated for Shared Libraries)

The Dockerfile now uses the parent `backend/` directory as build context to access shared libraries.

### Build Command

From the **repository root**:

```bash
docker build -f backend/engine-c/Dockerfile -t engine-c:latest backend/
```

**Note**: The build context is `backend/` (the entire backend directory), not `backend/engine-c/`.

### Cloud Build (Automatic)

When deploying to Cloud Run, ensure the build is triggered from the `backend/` directory:

```bash
cd backend
gcloud run deploy engine-c \
  --source=. \
  --dockerfile=engine-c/Dockerfile \
  --region=us-central1
```

## Shared Library Integration

Engine C now imports performance modules and google integrations from `backend/shared/`:

- `shared.performance`: Connection pooling, caching, rate limiting.
- `shared.google_integrations`: Unified GCP interactions (where applicable).

## Order Execution ML

Engine C includes an `ExecutionOptimizer` for:

- Slippage Prediction
- TWAP/VWAP Order Splitting
- Intraday Volume Profile Analysis

Ensure `numpy`, `pandas`, `scikit-learn`, and `statsmodels` are installed (managed via `requirements.txt`).
