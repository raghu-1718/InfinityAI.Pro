#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=${PROJECT_ID:-infinity-ai-5ec7c}
REGION=${REGION:-us-central1}
APP_ENGINE_REGION=${APP_ENGINE_REGION:-us-central}
REPO=${REPO:-raghu-1718/InfinityAI.Pro}
GITHUB_SA_JSON_PATH=${GITHUB_SA_JSON_PATH:-}
NON_INTERACTIVE=${NON_INTERACTIVE:-false}

require() { command -v "$1" >/dev/null 2>&1 || { echo "'$1' not found" >&2; exit 1; }; }
require gcloud
# firebase and gh are optional; warn if missing
if ! command -v firebase >/dev/null 2>&1; then echo "[WARN] firebase CLI not found; Firebase config step will be skipped." >&2; FIREBASE_MISSING=1; else FIREBASE_MISSING=0; fi
if ! command -v gh >/dev/null 2>&1; then echo "[WARN] gh CLI not found; GitHub secrets step will be skipped." >&2; GH_MISSING=1; else GH_MISSING=0; fi

OUTDIR="$(cd "$(dirname "$0")" && pwd)/out"
mkdir -p "$OUTDIR"

echo "Using Project: $PROJECT_ID | Region: $REGION"

gcloud config set project "$PROJECT_ID" >/dev/null
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
APPENGINE_SA="${PROJECT_ID}@appspot.gserviceaccount.com"

echo "Checking billing status..."
BILLING_ENABLED=$(gcloud beta billing projects describe "$PROJECT_ID" --format='value(billingEnabled)' || true)
echo "Billing enabled: $BILLING_ENABLED"

APIS=(
  cloudbuild.googleapis.com
  run.googleapis.com
  cloudfunctions.googleapis.com
  eventarc.googleapis.com
  artifactregistry.googleapis.com
  secretmanager.googleapis.com
  firebase.googleapis.com
  firestore.googleapis.com
  appengine.googleapis.com
)
echo "Enabling required APIs (best-effort)..."
for api in "${APIS[@]}"; do gcloud services enable "$api" --project "$PROJECT_ID" || true; done

echo "Ensuring App Engine app exists..."
if ! gcloud app describe --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud app create --project "$PROJECT_ID" --region "$APP_ENGINE_REGION" || true
fi

grant_role() {
  local member="$1" role="$2"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="$member" \
    --role="$role" \
    --condition=None >/dev/null 2>&1 || true
}

DEPLOY_SA_EMAIL=""
if [[ -n "${GITHUB_SA_JSON_PATH}" && -f "${GITHUB_SA_JSON_PATH}" ]]; then
  DEPLOY_SA_EMAIL=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["client_email"])' "$GITHUB_SA_JSON_PATH")
  echo "Using deployer SA: ${DEPLOY_SA_EMAIL}"
fi

if [[ -n "$DEPLOY_SA_EMAIL" ]]; then
  echo "Granting deployer roles..."
  for r in \
    roles/cloudfunctions.developer \
    roles/iam.serviceAccountUser \
    roles/artifactregistry.writer \
    roles/run.admin \
    roles/eventarc.admin \
    roles/cloudbuild.builds.editor; do
    grant_role "serviceAccount:${DEPLOY_SA_EMAIL}" "$r"
  done
fi

echo "Granting runtime roles..."
for r in roles/secretmanager.secretAccessor; do
  grant_role "serviceAccount:${COMPUTE_SA}" "$r"
  grant_role "serviceAccount:${APPENGINE_SA}" "$r"
done

ensure_secret() {
  local name="$1"
  if [[ -z $(gcloud secrets list --filter "name:$name" --format 'value(name)') ]]; then
    gcloud secrets create "$name" --replication-policy=automatic >/dev/null
    echo "Created secret: $name"
  fi
}
add_secret_version() {
  local name="$1" value="$2"
  [[ -z "$value" ]] && return 0
  printf "%s" "$value" | gcloud secrets versions add "$name" --data-file=- >/dev/null
}

SECRETS=(
  gemini-api-key-primary
  gemini-api-key-secondary
  dhan-api-key
  huggingface-token
  trading-engine-secret
  webhook-verification-token
  telegram-bot-token
)

echo "Ensuring secrets exist..."
for s in "${SECRETS[@]}"; do ensure_secret "$s"; done

read_secret() {
  local envname="$1" prompt="$2" val
  val=${!envname:-}
  if [[ -z "$val" && "$NON_INTERACTIVE" != "true" ]]; then
    read -rsp "$prompt: " val; echo
  fi
  printf "%s" "$val"
}

declare -A MAP
MAP[gemini-api-key-primary]="$(read_secret GEMINI_API_KEY_PRIMARY "Enter GEMINI_API_KEY_PRIMARY")"
MAP[gemini-api-key-secondary]="$(read_secret GEMINI_API_KEY_SECONDARY "Enter GEMINI_API_KEY_SECONDARY")"
MAP[dhan-api-key]="$(read_secret DHAN_API_KEY "Enter DHAN_API_KEY")"
MAP[huggingface-token]="$(read_secret HUGGINGFACE_TOKEN "Enter HUGGINGFACE_TOKEN")"
MAP[trading-engine-secret]="$(read_secret TRADING_ENGINE_SECRET "Enter TRADING_ENGINE_SECRET")"
MAP[webhook-verification-token]="$(read_secret WEBHOOK_VERIFICATION_TOKEN "Enter WEBHOOK_VERIFICATION_TOKEN")"
MAP[telegram-bot-token]="$(read_secret TELEGRAM_BOT_TOKEN "Enter TELEGRAM_BOT_TOKEN")"

echo "Adding secret versions (where values provided)..."
for k in "${!MAP[@]}"; do add_secret_version "$k" "${MAP[$k]}"; done

# Firebase functions config
if [[ "$FIREBASE_MISSING" -eq 0 ]]; then
  if [[ -n "${ENCRYPTION_KEY:-}" || "$NON_INTERACTIVE" != "true" ]]; then
    if [[ -z "${ENCRYPTION_KEY:-}" ]]; then read -rsp "Enter ENCRYPTION_KEY for functions config: " ENCRYPTION_KEY; echo; fi
    firebase functions:config:set secrets.encryption_key="$ENCRYPTION_KEY" --project "$PROJECT_ID" >/dev/null || true
  fi
fi

# Dumps
gcloud secrets list --format json > "$OUTDIR/secrets_list.json"
gcloud services list --enabled --format json > "$OUTDIR/services_enabled.json"
gcloud projects get-iam-policy "$PROJECT_ID" --format json > "$OUTDIR/project_iam_policy.json"
gcloud run services list --region "$REGION" --format json > "$OUTDIR/cloud_run_services.json"
for svc in infinityai-engine-a infinityai-engine-b infinityai-engine-c-execution infinityai-engine-d infinityai-frontend; do
  gcloud run services describe "$svc" --region "$REGION" --format json > "$OUTDIR/$svc.json" 2>/dev/null || true
done

# GitHub secrets
if [[ "$GH_MISSING" -eq 0 ]]; then
  if [[ -n "$GITHUB_SA_JSON_PATH" && -f "$GITHUB_SA_JSON_PATH" ]]; then
    gh secret set GCP_SERVICE_ACCOUNT_KEY --repo "$REPO" < "$GITHUB_SA_JSON_PATH"
  fi
  [[ -n "${MAP[gemini-api-key-primary]}" ]] && echo -n "${MAP[gemini-api-key-primary]}" | gh secret set GEMINI_API_KEY_PRIMARY --repo "$REPO" -f -
  [[ -n "${MAP[gemini-api-key-secondary]}" ]] && echo -n "${MAP[gemini-api-key-secondary]}" | gh secret set GEMINI_API_KEY_SECONDARY --repo "$REPO" -f -
  [[ -n "${ENCRYPTION_KEY:-}" ]] && echo -n "$ENCRYPTION_KEY" | gh secret set ENCRYPTION_KEY --repo "$REPO" -f -
fi

echo "\n✅ Completed. Outputs in $OUTDIR. Review IAM bindings and rerun CI/CD."
