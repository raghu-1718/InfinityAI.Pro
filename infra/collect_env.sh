#!/usr/bin/env bash
set -euo pipefail

# === REAL CONFIGURATION FOR RAGHU ===
GCP_PROJECT_ID="gen-lang-client-0779271931"
GITHUB_REPO="raghu-1718/InfinityAI.Pro"
FIREBASE_PROJECT_ID="gen-lang-client-0779271931"

# Cloud Run region discovered from your service URLs
CLOUD_RUN_REGION="us-central1"

# Vertex AI region (enabled but no endpoints/models yet)
VERTEX_REGION="us-central1"

COLLECT_DIR="infra/collected"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="infra_collected_${TIMESTAMP}.tar.gz"

# === Preflight checks ===
command -v git >/dev/null 2>&1 || { echo "git not found"; exit 1; }
command -v gcloud >/dev/null 2>&1 || { echo "gcloud not found"; exit 1; }
command -v jq >/dev/null 2>&1 || echo "jq not found; JSON parsing will be limited"
command -v gh >/dev/null 2>&1 || echo "gh CLI not found; GitHub metadata will be skipped"
command -v firebase >/dev/null 2>&1 || echo "firebase CLI not found; Firebase metadata will be skipped"

# === Prepare collection directory ===
mkdir -p "${COLLECT_DIR}"
cd "${COLLECT_DIR}"

# === 1. Git basics ===
git rev-parse --show-toplevel > repo_root.txt 2>&1 || true
git remote -v > git_remotes.txt 2>&1 || true
git branch --show-current > current_branch.txt 2>&1 || true
git rev-parse HEAD > current_commit.txt 2>&1 || true
git ls-tree -r HEAD --name-only > git_tracked_files.txt 2>&1 || true
git log --oneline -n 200 > git_recent_commits.txt 2>&1 || true

# === 2. GitHub metadata ===
if command -v gh >/dev/null 2>&1; then
  gh repo view "${GITHUB_REPO}" --json nameWithOwner,description,visibility,defaultBranchRef,createdAt,updatedAt > github_repo_meta.json 2>&1 || true
  gh api repos/"${GITHUB_REPO}" > github_repo_raw.json 2>&1 || true
  ls -la ../../.github/workflows > github_workflows_list.txt 2>&1 || true
  gh run list -R "${GITHUB_REPO}" --limit 50 --json databaseId,status,conclusion,createdAt,headBranch > github_actions_runs.json 2>&1 || true
  gh secret list -R "${GITHUB_REPO}" --json name > github_repo_secrets.json 2>&1 || true
fi

# === 3. Firebase metadata ===
if command -v firebase >/dev/null 2>&1; then
  firebase projects:list --json > firebase_projects.json 2>&1 || true
  firebase apps:list --project "${FIREBASE_PROJECT_ID}" --json > firebase_apps.json 2>&1 || true
  firebase hosting:sites:list --project "${FIREBASE_PROJECT_ID}" --json > firebase_hosting_sites.json 2>&1 || true
  firebase hosting:channels:list --project "${FIREBASE_PROJECT_ID}" --json > firebase_hosting_channels.json 2>&1 || true
  firebase hosting:domains:list --project "${FIREBASE_PROJECT_ID}" --json > firebase_hosting_domains.json 2>&1 || true
fi

# === 4. Firestore ===
gcloud firestore databases list --project "${GCP_PROJECT_ID}" --format=json > gcloud_firestore_databases.json 2>&1 || true
gcloud firestore indexes composite list --project "${GCP_PROJECT_ID}" --format=json > gcloud_firestore_indexes.json 2>&1 || true

# === 5. Cloud Run services ===
gcloud run services list --platform managed --project "${GCP_PROJECT_ID}" --format=json > gcloud_run_services.json 2>&1 || true

if command -v jq >/dev/null 2>&1; then
  services=$(jq -r '.[].metadata.name' gcloud_run_services.json)
else
  services=$(gcloud run services list --platform managed --project "${GCP_PROJECT_ID}" --format="value(metadata.name)")
fi

for svc in ${services}; do
  safe=$(echo "${svc}" | sed 's/[^a-zA-Z0-9._-]/_/g')
  gcloud run services describe "${svc}" \
    --platform managed \
    --project "${GCP_PROJECT_ID}" \
    --region "${CLOUD_RUN_REGION}" \
    --format=json > "gcloud_run_${safe}_describe.json" 2>/dev/null || true

  gcloud run services get-iam-policy "${svc}" \
    --platform managed \
    --project "${GCP_PROJECT_ID}" \
    --region "${CLOUD_RUN_REGION}" \
    --format=json > "gcloud_run_${safe}_iam.json" 2>/dev/null || true
done

gcloud run revisions list \
  --platform managed \
  --project "${GCP_PROJECT_ID}" \
  --region "${CLOUD_RUN_REGION}" \
  --format=json > gcloud_run_revisions.json 2>&1 || true

# === 6. Vertex AI ===
gcloud ai models list --project "${GCP_PROJECT_ID}" --region="${VERTEX_REGION}" --format=json > gcloud_ai_models.json 2>&1 || true
gcloud ai endpoints list --project "${GCP_PROJECT_ID}" --region="${VERTEX_REGION}" --format=json > gcloud_ai_endpoints.json 2>&1 || true

# === 7. Secret Manager ===
gcloud secrets list --project "${GCP_PROJECT_ID}" --format=json > gcloud_secrets_list.json 2>&1 || true

# === 8. IAM ===
gcloud iam service-accounts list --project "${GCP_PROJECT_ID}" --format=json > gcloud_service_accounts.json 2>&1 || true
gcloud projects get-iam-policy "${GCP_PROJECT_ID}" --format=json > gcloud_project_iam_policy.json 2>&1 || true

# === 9. DNS ===
gcloud dns managed-zones list --project "${GCP_PROJECT_ID}" --format=json > gcloud_dns_managed_zones.json 2>&1 || true

# === 10. Billing + APIs ===
gcloud beta billing projects describe "${GCP_PROJECT_ID}" --format=json > gcloud_billing_project.json 2>&1 || true
gcloud services list --project "${GCP_PROJECT_ID}" --format=json > gcloud_enabled_apis.json 2>&1 || true

# === 11. Summary ===
cat > summary.md <<EOF
# InfinityAI.Pro Environment Collection
Generated at: ${TIMESTAMP}

## Project
- GCP Project ID: ${GCP_PROJECT_ID}
- Firebase Project ID: ${FIREBASE_PROJECT_ID}
- Cloud Run Region: ${CLOUD_RUN_REGION}
- Vertex Region: ${VERTEX_REGION}

## Outputs
All collected files are stored in infra/collected/.
EOF

cd ..
tar -czf "${ARCHIVE_NAME}" "${COLLECT_DIR}"

echo "✅ Collection complete."
echo "📁 Outputs stored in: ${COLLECT_DIR}"
echo "📦 Archive created: ${ARCHIVE_NAME}"
