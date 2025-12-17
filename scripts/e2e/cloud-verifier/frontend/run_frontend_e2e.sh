#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Validate env
: ${BASE_URL:?"BASE_URL is required"}
: ${FIREBASE_TEST_EMAIL:?"FIREBASE_TEST_EMAIL is required"}
: ${FIREBASE_TEST_PASSWORD:?"FIREBASE_TEST_PASSWORD is required"}

OUT_DIR="$DIR/../output/frontend"
mkdir -p "$OUT_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
  echo "Installing Playwright... (this may take a minute)"
  npm ci || npm i
  npx playwright install --with-deps
fi

# Run tests
echo "Running Playwright frontend E2E..."
set +e
npm test
RC=$?
set -e

# Collect results
if [ $RC -ne 0 ]; then
  echo "Playwright tests failed (exit code $RC). See output folder for artifacts: $OUT_DIR"
  exit $RC
fi

echo "Playwright tests passed. Reports are in $OUT_DIR"
exit 0
