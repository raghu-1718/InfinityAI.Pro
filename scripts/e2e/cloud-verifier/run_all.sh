#!/usr/bin/env bash
set -euo pipefail
DIR=$(dirname "$0")
cd "$DIR"
mkdir -p output

echo "Starting Cloud Verifier run: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

# 1) Inventory (non-sensitive)
bash run_inventory.sh || echo "run_inventory.log: partial or failed (see output folder)"

# 2) Engine probes
bash probe_engines.sh || echo "probe_engines.log: partial or failed"

# 3) Firebase E2E (requires FIREBASE_API_KEY, FIREBASE_TEST_EMAIL, FIREBASE_TEST_PASSWORD)
if [ -n "${FIREBASE_API_KEY:-}" ] && [ -n "${FIREBASE_TEST_EMAIL:-}" ] && [ -n "${FIREBASE_TEST_PASSWORD:-}" ]; then
  echo "Running Firebase e2e..."
  node firebase_e2e.js > output/firebase_e2e_$(date +"%Y%m%d_%H%M%S").log 2>&1 || echo "firebase_e2e.log: failed"
else
  echo "Skipping Firebase E2E (missing env: FIREBASE_API_KEY/FIREBASE_TEST_EMAIL/FIREBASE_TEST_PASSWORD)"
fi

# Final note
echo "Run complete. Output is in $(pwd)/output"
