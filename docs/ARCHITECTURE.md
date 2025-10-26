InfinityAI.Pro Architecture Notes

- Engines: A (market data), B (AI/ML), C-Execution (trades/OAuth), D (chat/orchestrator)
- Frontend: React + Vite served via Cloud Run; exposes /health JSON
- Secrets: Google Secret Manager only; no hardcoded credentials

Recent operational improvements:
- Engine B now supports fast health mode for signals: GET /api/ai-signals?fast=true
	- Limits to 3 symbols, skips heavy sentiment, per-symbol timeout 3s
	- Use this in monitors/verifiers to avoid cold-start tails
- Gemini analyze endpoint guarded by hard timeout (default 8s) to fail fast with 503 if upstream is slow

Verifier alignment:
- System verifier calls /api/ai-signals?fast=true and treats 503/504 from Gemini as WARNING

Cloud Run inventory:
- See docs/CLOUD_RUN_AUDIT.md for categorized list and cleanup candidates
