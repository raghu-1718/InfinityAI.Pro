#!/usr/bin/env bash
set -euo pipefail
mkdir -p scripts/e2e/cloud-verifier/output
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: gcloud project not configured. Run: gcloud config set project <PROJECT_ID>" >&2
  exit 1
fi
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUT="scripts/e2e/cloud-verifier/output/inventory_$TIMESTAMP.json"

echo "{" > "$OUT"

### GCP PROJECT INFO
echo '"gcp_project":' >> "$OUT"
gcloud projects describe "$PROJECT_ID" --format=json >> "$OUT"
echo "," >> "$OUT"

### CLOUD RUN SERVICES (ALL REGIONS)
echo '"cloud_run_services":' >> "$OUT"
gcloud run services list --platform=managed --format=json >> "$OUT"
echo "," >> "$OUT"

### CLOUD RUN SERVICE DETAILS (ENGINE A/B/C)
echo '"cloud_run_details":{' >> "$OUT"
for svc in engine-a engine-b engine-c; do
  echo "\"$svc\":" >> "$OUT"
  gcloud run services describe "$svc" --region=us-central1 --format=json >> "$OUT" || echo "null" >> "$OUT"
  echo "," >> "$OUT"
done
echo '},' >> "$OUT"

### SECRET MANAGER (METADATA ONLY)
echo '"secret_manager":{' >> "$OUT"
echo '"secrets":' >> "$OUT"
gcloud secrets list --format=json >> "$OUT"
echo "," >> "$OUT"
echo '"secret_versions":' >> "$OUT"
for s in $(gcloud secrets list --format="value(name)"); do
  echo "\"$s\":" >> "$OUT"
  gcloud secrets versions list "$s" --format=json >> "$OUT" || echo "null" >> "$OUT"
  echo "," >> "$OUT"
done
echo '},' >> "$OUT"

### FIREBASE INVENTORY
echo '"firebase":{' >> "$OUT"
echo '"projects":' >> "$OUT"
# firebase CLI may require auth; wrap calls so script keeps running
firebase projects:list --json >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"apps":' >> "$OUT"
firebase apps:list --json >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"functions":' >> "$OUT"
firebase functions:list --json >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"hosting":' >> "$OUT"
firebase hosting:sites:list --json >> "$OUT" || echo "null" >> "$OUT"
echo '},' >> "$OUT"

### FIRESTORE INVENTORY
echo '"firestore":{' >> "$OUT"
echo '"databases":' >> "$OUT"
gcloud firestore databases list --format=json >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"indexes":' >> "$OUT"
gcloud firestore indexes list --format=json >> "$OUT" || echo "null" >> "$OUT"
echo '},' >> "$OUT"

### IAM & SERVICE ACCOUNTS
echo '"iam":{' >> "$OUT"
echo '"service_accounts":' >> "$OUT"
gcloud iam service-accounts list --format=json >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"project_policy":' >> "$OUT"
gcloud projects get-iam-policy "$PROJECT_ID" --format=json >> "$OUT" || echo "null" >> "$OUT"
echo '},' >> "$OUT"

### GITHUB INVENTORY
echo '"github":{' >> "$OUT"
echo '"repo":' >> "$OUT"
gh repo view raghu-1718/InfinityAI.Pro --json name,visibility,defaultBranchRef >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"workflows":' >> "$OUT"
gh workflow list --json name,state >> "$OUT" || echo "null" >> "$OUT"
echo "," >> "$OUT"
echo '"secrets":' >> "$OUT"
gh secret list --json name >> "$OUT" || echo "null" >> "$OUT"
echo '}' >> "$OUT"

echo "}" >> "$OUT"

echo "✅ Inventory generated: $OUT"
