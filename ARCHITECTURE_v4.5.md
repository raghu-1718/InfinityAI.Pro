# InfinityAI.Pro — Architecture v4.5

This document captures the final project layout and the consolidation plan to remove duplicates and promote the advanced implementations.

## Final Structure (target)

InfinityAI.Pro/
- backend/
  - engine-a/          # Real-time Market & Option Data Ingestion (proxy to engines/engine-a)
  - engine-b/          # AI & ML Strategy Engine (proxy to engines/engine-b)
  - engine-c/          # Trade Execution + Portfolio Reconciliation (proxy to engines/engine-c-execution)
  - engine-d/          # AI Chatbot & System Orchestration (proxy to engines/engine-d)
  - engines/           # Canonical codebases for A–D (kept as the source of truth)
  - services/          # Shared internal libraries (Engine C libs consolidated to engine_c/)
- frontend/            # Unified React + Vite + Tailwind dashboard (promoted v4.5 app under frontend/app-v4.5)

## Canonical Engines

- Engine A: backend/engines/engine-a (advanced; providers, analytics, core, routes, tests)
- Engine B: backend/engines/engine-b (advanced; strategies, services, models, config)
- Engine C: backend/engines/engine-c-execution (advanced; execution microservice)
- Engine D: backend/engines/engine-d (advanced orchestrator; includes health_orchestrator)

Top-level engine folders (backend/engine-a, engine-b, engine-c, engine-d) now expose thin entrypoints that import the canonical apps from backend/engines/* for a clean v4.5 layout without breaking existing code.

## Frontend

- Promoted new React + Vite app (v4.5) under frontend/app-v4.5
- Old CRA-based frontend and frontend-legacy kept only for reference.
- Use frontend/app-v4.5 for development and Cloud Run deployment.

## Cleanup Steps (safe order)

1) Frontend
- Use frontend/app-v4.5 as the only deployable frontend.
- Archive previous frontend and frontend-legacy after validating new app in Cloud Run.

2) Engines A–D
- Keep backend/engines/* as canonical code locations.
- The top-level backend/engine-* folders are stable entrypoints; Docker builds can target them.
- Optional: Fold deploy-only variants (engine-a-market-data, engine-b-ai-ml, engine-d-chatbot) into the canonical engines as subfolders for their Dockerfiles/scripts, then remove the extra engine-* variant folders.

3) Shared Libraries
- Consolidate Engine C libraries to backend/services/engine_c (single underscore form). Remove duplicate backend/services/engine-c after updating imports inside engine-c-execution.

## Cloud Run URLs (production)

- Engine A: https://engine-a-market-data-prod-573866363639.us-central1.run.app
- Engine B: https://engine-b-ai-ml-prod-573866363639.us-central1.run.app
- Engine C: https://engine-c-execution-prod-573866363639.us-central1.run.app
- Engine D: https://engine-d-chatbot-prod-573866363639.us-central1.run.app
- Frontend: infinityai-frontend (Cloud Run URL printed on deploy)

## Security & Connectivity

- JWT issued by Engine D; Frontend consumes JWT.
- HTTPS + WSS only; CSP enabled in NGINX for frontend.
- WebSocket channels: /ws/dashboard and /ws/{user_id} via Engine D.

## Notes

- This v4.5 structure provides clean top-level folders for engines while preserving the advanced canonical implementations under backend/engines.
- Next step: update Docker build contexts to target backend/engine-* folders in CI/CD.
