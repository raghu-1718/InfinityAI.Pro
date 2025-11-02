# Cloud Run Services Audit (us-central1)

This report summarizes currently deployed Cloud Run services (including 2nd‑gen Firebase Functions backed by Cloud Run) based on `services.json` captured from `gcloud run services list --format=json`.

Last audited: 2025-10-26
Project: infinity-ai-5ec7c (number: 26140490557)
Region: us-central1

## Summary
- Engines (Core microservices):
  - infinityai-engine-a (market data) — READY
  - infinityai-engine-b (AI/ML) — READY (minScale=2)
  - infinityai-engine-c-execution (trade execution) — READY (minScale=1)
  - infinityai-engine-c (aux) — READY
  - infinityai-engine-d (chat/orchestrator) — READY (minScale=1)
- Frontend:
  - infinityai-frontend — READY
- Firebase Functions (2nd gen; surfaced as Cloud Run services):
  - getGeminiAnalysis, getVertexAiAnalysis, getAiSignals, getBatchAiSignals, getDhanOverview,
    submitDhanCredentialsV2, startTrading, getEngineBStatus, analyzePortfolio,
    analyzeImageWithRoboticsER, and others.

All core engines and frontend are healthy. Functions are deployed and reachable (401/403 expected when auth required), confirmed by the verifier.

## Categorized Inventory

### Core Engines
- infinityai-engine-a — https://infinityai-engine-a-26140490557.us-central1.run.app
- infinityai-engine-b — https://infinityai-engine-b-26140490557.us-central1.run.app
- infinityai-engine-c-execution — https://infinityai-engine-c-execution-26140490557.us-central1.run.app
- infinityai-engine-c — https://infinityai-engine-c-26140490557.us-central1.run.app
- infinityai-engine-d — https://infinityai-engine-d-26140490557.us-central1.run.app

### Frontend
- infinityai-frontend — https://infinityai-frontend-26140490557.us-central1.run.app

### Firebase Functions (HTTP)
- getGeminiAnalysis — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getGeminiAnalysis
- getVertexAiAnalysis — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getVertexAiAnalysis
- getAiSignals — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getAiSignals
- getBatchAiSignals — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getBatchAiSignals
- getDhanOverview — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getDhanOverview
- submitDhanCredentialsV2 — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/submitDhanCredentialsV2
- startTrading — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/startTrading
- getEngineBStatus — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/getEngineBStatus
- analyzePortfolio — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/analyzePortfolio
- analyzeImageWithRoboticsER — https://us-central1-infinity-ai-5ec7c.cloudfunctions.net/analyzeImageWithRoboticsER

Note: These appear as separate Cloud Run services due to Cloud Functions 2nd‑gen architecture.

## Potential Duplicates / Cleanup Candidates
- getAiSignals vs getBatchAiSignals — If both are used by different clients (single vs batch), keep both; otherwise consolidate to one endpoint to reduce surface area and cost.
- getEngineBStatus — May be redundant with `engine-b /health` and `/version`. If not used by mobile or web clients, consider removal.
- analyzeImageWithRoboticsER — Name suggests experimental/legacy feature. If not referenced by frontend/mobile or automations, consider removal.

Before deletion:
- Search references in code (web, mobile, functions, scripts)
- Check logs/metrics for recent traffic
- Tag deprecations and communicate to stakeholders

Deletion command (documentation only; verify before running):
- gcloud run services delete <service-name> --region us-central1 --project infinity-ai-5ec7c --quiet

## Recommendations
1) Keep the 4 Engines (A, B, C-Execution, D) and Frontend as-is.
2) For Firebase functions, maintain only actively used business endpoints; deprecate low/no‑traffic functions.
3) Align naming and documentation so each function’s purpose is clear.
4) Add cost/traffic dashboard to monitor per-service usage.
5) Re-run the verifier after each cleanup to confirm 100% coverage.

## Verification Snapshot
- See latest: `infinityai_verification_report_YYYYMMDD_HHMMSS.json`
- Current overall status: NEAR_PRODUCTION (Gemini integration marked as WARNING due to upstream latency; functional).
