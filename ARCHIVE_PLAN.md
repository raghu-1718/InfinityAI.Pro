# Cleanup & Archive Plan (v4.5)

This plan consolidates engines and removes duplicates safely.

## Canonical locations
- Engine A: backend/engines/engine-a
- Engine B: backend/engines/engine-b
- Engine C: backend/engines/engine-c-execution
- Engine D: backend/engines/engine-d
- Frontend: frontend-new (to be promoted to frontend)

## Duplicates to archive (after verification)
- backend/engine-a (thin wrapper) — keep only if used by CI build context
- backend/engine-b (thin wrapper) — keep only if used by CI build context
- backend/engine-c (thin wrapper) — keep only if used by CI build context
- backend/engine-d (thin wrapper) — keep only if used by CI build context
- backend/engines/engine-a-market-data (deploy-only variant)
- backend/engines/engine-b-ai-ml (deploy-only variant)
- backend/engines/engine-d-chatbot (deploy-only variant)
- backend/services/engine-c or backend/services/engine_c — pick one
- frontend/ and frontend-legacy/ — archive after promoting frontend-new

## Steps
1) Ensure Docker builds/CI target backend/engine-* entry points or the canonical backend/engines/*.
2) Move variant Dockerfiles and deploy scripts into canonical engine subfolders if still needed.
3) Pick a single shared lib path for Engine C: backend/services/engine_c (recommended) and update imports.
4) Promote frontend-new to frontend and archive legacy folders.
5) Delete archived folders once tests pass.

## Rollback
Original canonical sources remain under backend/engines/* and frontend-new; revert build contexts to those locations if needed.