# InfinityGT-Project

This folder provides a repository-root view and developer mapping for the InfinityGT monorepo.

NOTE: The actual source code for the platform lives at the repository root. This folder provides a simple, Vercel-friendly layout and quick pointers for maintainers and deployers.

Repository layout (developer view):

```
InfinityGT-Project/
│
├── frontend/        # React + Vite app (actual code lives at ../frontend)
├── functions/       # Firebase Functions (actual code lives at ../functions)
├── engines/         # Microservices (actual code lives at ../engines)
```

How this maps to the repository:

- `InfinityGT-Project/frontend` -> Please use the existing `frontend/` folder at the repository root for the full app. When configuring Vercel, point the "Root Directory" to `frontend/`.
- `InfinityGT-Project/functions` -> Points to the repository root `functions/` folder. Use `cd functions && npm ci && npm run build` for CI deploys.
- `InfinityGT-Project/engines` -> Points to the repository root `engines/` folder. Each engine has a Dockerfile under `engines/<engine-name>/Dockerfile`.

Quick deploy notes

- Vercel: Set the project root to `frontend/` in the Vercel settings and configure the required environment variables (do NOT commit `.env` to git).
- Firebase Functions: Use `firebase deploy --only functions` from the repository root (or `cd functions && firebase deploy`). Ensure `FIREBASE_TOKEN` is set in CI secrets.
- Northflank: Create a service and point to the repository. Use the Dockerfile path: `engines/<engine-name>/Dockerfile` for each engine service.

This folder is intentionally lightweight and acts as a convenience entry point for maintainers and deploy scripts.
# InfinityGT-Project

This directory is a clean, opinionated scaffold of the InfinityGT platform extracted from the larger repository. It's intended to be the canonical project layout for a fresh repository (frontend + functions + engines).

Structure summary

- `frontend/` - React + Vite frontend (deployed to Vercel). Uses Tailwind and Firebase for auth.
- `functions/` - Firebase Cloud Functions (TypeScript)
- `engines/` - Containerized backend microservices (FastAPI examples) deployable to Northflank or any container platform.

How to use

1. Frontend
   - cd into `frontend/` and run `npm install` then `npm run dev`.
   - Provide Firebase web config via a local `.env` (see `.env.example`).

2. Functions
   - cd into `functions/` and run `npm install` then `npm run build` and `npm run deploy` (if using Firebase CLI).

3. Engines
   - Each engine has a Dockerfile and `requirements.txt`. Build and run with Docker as needed.

This scaffold is intentionally minimal and ready to be extended. It mirrors the recommended structure discussed earlier.
