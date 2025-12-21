# PowerShell version of collect_env.sh
# Save as collect_env.ps1 in infra/

# === REAL CONFIGURATION FOR RAGHU ===
$GCP_PROJECT_ID = "gen-lang-client-0779271931"
$GITHUB_REPO = "raghu-1718/InfinityAI.Pro"
$FIREBASE_PROJECT_ID = "gen-lang-client-0779271931"
$CLOUD_RUN_REGION = "us-central1"
$VERTEX_REGION = "us-central1"

$COLLECT_DIR = "infra/collected"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$ARCHIVE_NAME = "infra_collected_${TIMESTAMP}.zip"

# === Preflight checks ===
function Check-Command($cmd) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "$cmd not found" -ForegroundColor Red
        return $false
    }
    return $true
}

$gitOk = Check-Command git
$gcloudOk = Check-Command gcloud
$jOk = Check-Command jq
$ghOk = Check-Command gh
$firebaseOk = Check-Command firebase

if (-not $gitOk -or -not $gcloudOk) {
    Write-Host "git and gcloud are required. Exiting." -ForegroundColor Red
    exit 1
}

# === Prepare collection directory ===
New-Item -ItemType Directory -Force -Path $COLLECT_DIR | Out-Null
Push-Location $COLLECT_DIR

# === 1. Git basics ===
git rev-parse --show-toplevel > repo_root.txt 2>&1
(git remote -v) > git_remotes.txt 2>&1
(git branch --show-current) > current_branch.txt 2>&1
(git rev-parse HEAD) > current_commit.txt 2>&1
(git ls-tree -r HEAD --name-only) > git_tracked_files.txt 2>&1
(git log --oneline -n 200) > git_recent_commits.txt 2>&1

# === 2. GitHub metadata ===
if ($ghOk) {
    gh repo view $GITHUB_REPO --json nameWithOwner,description,visibility,defaultBranchRef,createdAt,updatedAt > github_repo_meta.json 2>&1
    gh api repos/$GITHUB_REPO > github_repo_raw.json 2>&1
    if (Test-Path ../../.github/workflows) {
        Get-ChildItem ../../.github/workflows | Out-File github_workflows_list.txt
    }
    gh run list -R $GITHUB_REPO --limit 50 --json databaseId,status,conclusion,createdAt,headBranch > github_actions_runs.json 2>&1
    gh secret list -R $GITHUB_REPO --json name > github_repo_secrets.json 2>&1
}

# === 3. Firebase metadata ===
if ($firebaseOk) {
    firebase projects:list --json > firebase_projects.json 2>&1
    firebase apps:list --project $FIREBASE_PROJECT_ID --json > firebase_apps.json 2>&1
    firebase hosting:sites:list --project $FIREBASE_PROJECT_ID --json > firebase_hosting_sites.json 2>&1
    firebase hosting:channels:list --project $FIREBASE_PROJECT_ID --json > firebase_hosting_channels.json 2>&1
    firebase hosting:domains:list --project $FIREBASE_PROJECT_ID --json > firebase_hosting_domains.json 2>&1
}

# === 4. Firestore ===
gcloud firestore databases list --project $GCP_PROJECT_ID --format=json > gcloud_firestore_databases.json 2>&1
gcloud firestore indexes composite list --project $GCP_PROJECT_ID --format=json > gcloud_firestore_indexes.json 2>&1

# === 5. Cloud Run services ===
gcloud run services list --platform managed --project $GCP_PROJECT_ID --format=json > gcloud_run_services.json 2>&1

if ($jOk) {
    $services = (Get-Content gcloud_run_services.json | jq -r '.[].metadata.name')
} else {
    $services = (gcloud run services list --platform managed --project $GCP_PROJECT_ID --format="value(metadata.name)")
}

foreach ($svc in $services) {
    $safe = $svc -replace '[^a-zA-Z0-9._-]', '_'
    gcloud run services describe $svc --platform managed --project $GCP_PROJECT_ID --region $CLOUD_RUN_REGION --format=json > "gcloud_run_${safe}_describe.json" 2>$null
    gcloud run services get-iam-policy $svc --platform managed --project $GCP_PROJECT_ID --region $CLOUD_RUN_REGION --format=json > "gcloud_run_${safe}_iam.json" 2>$null
}

gcloud run revisions list --platform managed --project $GCP_PROJECT_ID --region $CLOUD_RUN_REGION --format=json > gcloud_run_revisions.json 2>&1

# === 6. Vertex AI ===
gcloud ai models list --project $GCP_PROJECT_ID --region $VERTEX_REGION --format=json > gcloud_ai_models.json 2>&1
gcloud ai endpoints list --project $GCP_PROJECT_ID --region $VERTEX_REGION --format=json > gcloud_ai_endpoints.json 2>&1

# === 7. Secret Manager ===
gcloud secrets list --project $GCP_PROJECT_ID --format=json > gcloud_secrets_list.json 2>&1

# === 8. IAM ===
gcloud iam service-accounts list --project $GCP_PROJECT_ID --format=json > gcloud_service_accounts.json 2>&1
gcloud projects get-iam-policy $GCP_PROJECT_ID --format=json > gcloud_project_iam_policy.json 2>&1

# === 9. DNS ===
gcloud dns managed-zones list --project $GCP_PROJECT_ID --format=json > gcloud_dns_managed_zones.json 2>&1

# === 10. Billing + APIs ===
gcloud beta billing projects describe $GCP_PROJECT_ID --format=json > gcloud_billing_project.json 2>&1
gcloud services list --project $GCP_PROJECT_ID --format=json > gcloud_enabled_apis.json 2>&1

# === 11. Summary ===
@"
# InfinityAI.Pro Environment Collection
Generated at: $TIMESTAMP

## Project
- GCP Project ID: $GCP_PROJECT_ID
- Firebase Project ID: $FIREBASE_PROJECT_ID
- Cloud Run Region: $CLOUD_RUN_REGION
- Vertex Region: $VERTEX_REGION

## Outputs
All collected files are stored in infra/collected/.
"@ | Set-Content summary.md

Pop-Location
Compress-Archive -Path $COLLECT_DIR -DestinationPath $ARCHIVE_NAME -Force

Write-Host "✅ Collection complete."
Write-Host "📁 Outputs stored in: $COLLECT_DIR"
Write-Host "📦 Archive created: $ARCHIVE_NAME"