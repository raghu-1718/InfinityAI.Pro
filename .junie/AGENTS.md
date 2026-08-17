# InfinityAI.Pro Development Guidelines

## 1. Build/Configuration Instructions
- **Monorepo Structure**: The project is split into `frontend` (Next.js) and `backend` (FastAPI Cloud Run engines).
- **Backend (Cloud Run)**: 
  - Each engine (`engine-a`, `engine-b`, `engine-c`) is a FastAPI application in `backend/`.
  - Deployment is handled via Google Cloud Build using `cloudbuild_*.yaml` configuration files in the root or `backend/` directory.
- **Frontend (Firebase)**: 
  - Managed via `package.json` workspaces (`frontend/web-app`).
  - Build/deploy using `npm run build` and `firebase deploy`.

## 2. Testing Information
- **Cloud Verification**: Use `verify_full_stack.ps1` to run an end-to-end audit of the production environment (requires active GCP credentials).
- **Local Testing**:
  - Use `local_e2e_test.py` to start engines locally (ports 8001-8003) and verify health endpoints (`/health`).
  - *Note*: Ensure local environment (e.g., Python `PYTHONPATH`) includes `backend` directories.

## 3. Additional Development Information
- **Code Style**:
  - Follow FastAPI patterns for backend services.
  - Maintain strict typing and `async/await` patterns due to high-concurrency trading requirements.
  - Ensure all sensitive configurations are managed via Firestore Vault or secure environment variables.
