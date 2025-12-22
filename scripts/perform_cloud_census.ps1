$ErrorActionPreference = "Continue"

$CensusDir = "artifacts/cloud_census"
Write-Host "Starting Cloud Forensic Census..."
Write-Host "Target Directory: $CensusDir"

# Create Directories
New-Item -ItemType Directory -Force -Path "$CensusDir/compute" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/data" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/ai" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/iam" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/orchestration" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/network" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/firebase" | Out-Null
New-Item -ItemType Directory -Force -Path "$CensusDir/billing" | Out-Null

# 1. Compute & Serverless
Write-Host "[1/8] Enumerating Compute..."
gcloud run services list --format="json" | Out-File -Encoding UTF8 "$CensusDir/compute/cloud_run.json"
gcloud functions list --format="json" | Out-File -Encoding UTF8 "$CensusDir/compute/functions.json"
gcloud app services list --format="json" | Out-File -Encoding UTF8 "$CensusDir/compute/app_engine.json"

# 2. Data & Storage
Write-Host "[2/8] Enumerating Data..."
gcloud storage buckets list --format="json" | Out-File -Encoding UTF8 "$CensusDir/data/storage_buckets.json"
# Note: Firestore indexes command requires specific location potentially, defaulting to standard
gcloud firestore indexes composite list --format="json" | Out-File -Encoding UTF8 "$CensusDir/data/firestore_indexes.json"
gcloud artifacts repositories list --format="json" | Out-File -Encoding UTF8 "$CensusDir/data/artifact_repos.json"

# 3. AI
Write-Host "[3/8] Enumerating AI..."
# Vertex AI requires region. Checking us-central1 as primary.
gcloud ai models list --region=us-central1 --format="json" | Out-File -Encoding UTF8 "$CensusDir/ai/vertex_models.json"
gcloud ai endpoints list --region=us-central1 --format="json" | Out-File -Encoding UTF8 "$CensusDir/ai/vertex_endpoints.json"

# 4. Orchestration
Write-Host "[4/8] Enumerating Orchestration..."
gcloud scheduler jobs list --format="json" | Out-File -Encoding UTF8 "$CensusDir/orchestration/scheduler_jobs.json"
gcloud pubsub topics list --format="json" | Out-File -Encoding UTF8 "$CensusDir/orchestration/pubsub_topics.json"
gcloud pubsub subscriptions list --format="json" | Out-File -Encoding UTF8 "$CensusDir/orchestration/pubsub_subscriptions.json"
gcloud eventarc triggers list --format="json" | Out-File -Encoding UTF8 "$CensusDir/orchestration/eventarc_triggers.json"

# 5. IAM & Secrets
Write-Host "[5/8] Enumerating IAM..."
gcloud iam service-accounts list --format="json" | Out-File -Encoding UTF8 "$CensusDir/iam/service_accounts.json"
$project = gcloud config get-value project 2>$null
gcloud projects get-iam-policy $project --format="json" | Out-File -Encoding UTF8 "$CensusDir/iam/policy_bindings.json"
gcloud secrets list --format="json" | Out-File -Encoding UTF8 "$CensusDir/iam/secrets.json"

# 6. Networking
Write-Host "[6/8] Enumerating Network..."
gcloud compute networks list --format="json" | Out-File -Encoding UTF8 "$CensusDir/network/networks.json"
gcloud compute firewall-rules list --format="json" | Out-File -Encoding UTF8 "$CensusDir/network/firewalls.json"

# 7. APIs
Write-Host "[7/8] Enumerating APIs..."
gcloud services list --enabled --format="json" | Out-File -Encoding UTF8 "$CensusDir/enabled_apis.json"

# 8. Firebase
Write-Host "[8/8] Enumerating Firebase..."
firebase projects:list --json | Out-File -Encoding UTF8 "$CensusDir/firebase/projects.json"
firebase hosting:sites:list --json | Out-File -Encoding UTF8 "$CensusDir/firebase/hosting_sites.json"

Write-Host "Census Complete. Artifacts saved to $CensusDir"
