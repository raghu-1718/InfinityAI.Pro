#!/usr/bin/env bash
set -euo pipefail
OUT_DIR="$(dirname "$0")/output"
mkdir -p "$OUT_DIR"
TS=$(date +"%Y%m%d_%H%M%S")
OUT_FILE="$OUT_DIR/engines_probe_$TS.json"

ENGINES=("https://engine-a-mfvaq54jjq-uc.a.run.app" "https://engine-b-mfvaq54jjq-uc.a.run.app" "https://engine-c-mfvaq54jjq-uc.a.run.app")

echo "{" > "$OUT_FILE"

for url in "${ENGINES[@]}"; do
  name=$(echo "$url" | sed -E 's|https?://([^/]+).*|\1|')
  echo "  \"$name\": {" >> "$OUT_FILE"
  # /health
  if health=$(curl -s -w "%{http_code} %{time_total}" -o /dev/null "$url/health" 2>/dev/null); then
    code=$(echo "$health" | awk '{print $1}')
    time=$(echo "$health" | awk '{print $2}')
    echo "    \"health\": { \"status\": $code, \"latency_s\": $time }," >> "$OUT_FILE"
  else
    echo "    \"health\": { \"status\": "null", \"error\": \"request failed\" }," >> "$OUT_FILE"
  fi

  # /openapi.json (only for engine-c)
  if curl -s -o /dev/null -w "%{http_code}" "$url/openapi.json" 2>/dev/null | grep -q "200"; then
    echo "    \"openapi\": { \"status\": 200 }," >> "$OUT_FILE"
  else
    echo "    \"openapi\": { \"status\": null }," >> "$OUT_FILE"
  fi

  # Optional sample POSTs
  if [ "${RUN_SAMPLE_POSTS:-}" = "true" ]; then
    # Provide sample payloads — PLEASE REVIEW before enabling
    if [[ "$name" == *"engine-b"* ]]; then
      payload='{"text":"sample signal test"}'
      res=$(curl -s -w "%{http_code} %{time_total}" -o /dev/null -X POST "$url/api/v1/signal" -H "Content-Type: application/json" -d "$payload" || true)
      echo "    \"post_signal\": \"$res\"," >> "$OUT_FILE"
    fi
    if [[ "$name" == *"engine-a"* ]]; then
      payload='{"positions":[],"risk_level":"moderate"}'
      res=$(curl -s -w "%{http_code} %{time_total}" -o /dev/null -X POST "$url/api/v1/risk/kelly" -H "Content-Type: application/json" -d "$payload" || true)
      echo "    \"post_risk\": \"$res\"," >> "$OUT_FILE"
    fi
  fi

  echo "  }," >> "$OUT_FILE"

done

echo "  \"timestamp\": \"$TS\"" >> "$OUT_FILE"
echo "}" >> "$OUT_FILE"

echo "Engine probes written to $OUT_FILE"
