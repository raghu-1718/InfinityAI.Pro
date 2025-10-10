<#
.SYNOPSIS
  Grants required GCP IAM bindings for GitHub Actions Workload Identity Federation (WIF)
  to push images to Artifact Registry and deploy to Cloud Run using a target Service Account.

.DESCRIPTION
  This script configures:
    - Workload Identity User + Token Creator on the target Service Account for the GitHub OIDC principal
    - Artifact Registry Writer on the Project for the target Service Account
    - Cloud Run Admin on the Project for the target Service Account

  It assumes you have gcloud installed and authenticated with sufficient permissions.

.PARAMETER ProjectId
  GCP Project ID (e.g., after-yesterday-473512-k3)

.PARAMETER ProjectNumber
  GCP Project Number (e.g., 573866363639)

.PARAMETER ServiceAccountEmail
  Email of the target service account to be impersonated by GitHub WIF (e.g., deployer@project.iam.gserviceaccount.com)

.PARAMETER WifPoolId
  The Workload Identity Pool ID used for GitHub OIDC (not the full resource path)

.PARAMETER GitHubOwner
  GitHub org/user name (e.g., your-org)

.PARAMETER GitHubRepo
  GitHub repo name (e.g., your-repo)

.PARAMETER Region
  GCP region for Artifact Registry/Cloud Run. Defaults to us-central1.

.PARAMETER ArtifactRegistryRepo
  Optional Artifact Registry repository name. If omitted, roles are granted at project scope.

.EXAMPLE
  ./gcp-fix-wif-artifact-registry-auth.ps1 `
    -ProjectId after-yesterday-473512-k3 `
    -ProjectNumber 573866363639 `
    -ServiceAccountEmail deployer@after-yesterday-473512-k3.iam.gserviceaccount.com `
    -WifPoolId github-wif-pool `
    -GitHubOwner my-org `
    -GitHubRepo my-repo `
    -Region us-central1

.NOTES
  - Requires: gcloud CLI with owner/editor or appropriate IAM on the project/SA
  - If your WIF provider uses subject=... instead of attribute.repository, update the MEMBER_SUBJECT below accordingly.
#>
param(
  [Parameter(Mandatory=$true)] [string]$ProjectId,
  [Parameter(Mandatory=$true)] [string]$ProjectNumber,
  [Parameter(Mandatory=$true)] [string]$ServiceAccountEmail,
  [Parameter(Mandatory=$true)] [string]$WifPoolId,
  [Parameter(Mandatory=$true)] [string]$GitHubOwner,
  [Parameter(Mandatory=$true)] [string]$GitHubRepo,
  [string]$Region = "us-central1",
  [string]$ArtifactRegistryRepo
)

$ErrorActionPreference = 'Stop'

function Exec($cmd) {
  Write-Host "--> $cmd" -ForegroundColor Cyan
  try {
    $null = Invoke-Expression $cmd
  } catch {
    throw "Command failed: $cmd`n$_"
  }
  if ($LASTEXITCODE -ne 0) { throw "Command failed with exit ${LASTEXITCODE}: $cmd" }
}

Write-Host "Setting gcloud project to $ProjectId" -ForegroundColor Green
Exec "gcloud config set project $ProjectId | Out-Null"

Write-Host "Ensuring required APIs are enabled" -ForegroundColor Green
Exec "gcloud services enable iamcredentials.googleapis.com artifactregistry.googleapis.com run.googleapis.com | Out-Null"

# Build the WIF principal member using attribute.repository convention
$WifPrincipal = "principalSet://iam.googleapis.com/projects/$ProjectNumber/locations/global/workloadIdentityPools/$WifPoolId/attribute.repository/$GitHubOwner/$GitHubRepo"
Write-Host "Using WIF Principal: $WifPrincipal" -ForegroundColor Yellow

Write-Host "Granting Workload Identity User on $ServiceAccountEmail to GitHub Principal" -ForegroundColor Green
Exec "gcloud iam service-accounts add-iam-policy-binding $ServiceAccountEmail --role=roles/iam.workloadIdentityUser --member=$WifPrincipal"

Write-Host "Granting Service Account Token Creator on $ServiceAccountEmail to GitHub Principal" -ForegroundColor Green
Exec "gcloud iam service-accounts add-iam-policy-binding $ServiceAccountEmail --role=roles/iam.serviceAccountTokenCreator --member=$WifPrincipal"

# Grant Artifact Registry Writer to the Service Account at project scope (covers all repos)
Write-Host "Granting Artifact Registry Writer to $ServiceAccountEmail at project scope" -ForegroundColor Green
Exec "gcloud projects add-iam-policy-binding $ProjectId --member=serviceAccount:$ServiceAccountEmail --role=roles/artifactregistry.writer --condition=None"

# Optionally grant at specific repository scope
if ($ArtifactRegistryRepo) {
  $RepoResource = "projects/$ProjectId/locations/$Region/repositories/$ArtifactRegistryRepo"
  Write-Host "Also granting writer on repository: $RepoResource" -ForegroundColor Green
  Exec "gcloud artifacts repositories add-iam-policy-binding $ArtifactRegistryRepo --location=$Region --member=serviceAccount:$ServiceAccountEmail --role=roles/artifactregistry.writer"
}

Write-Host "Granting Cloud Run Admin to $ServiceAccountEmail at project scope" -ForegroundColor Green
Exec "gcloud projects add-iam-policy-binding $ProjectId --member=serviceAccount:$ServiceAccountEmail --role=roles/run.admin --condition=None"

Write-Host "[Optional] If deploying with a different runtime service account, grant iam.serviceAccountUser on it to the deployer service account." -ForegroundColor DarkYellow
Write-Host "Example: gcloud iam service-accounts add-iam-policy-binding RUNTIME_SA --member=serviceAccount:${ServiceAccountEmail} --role=roles/iam.serviceAccountUser" -ForegroundColor DarkYellow

Write-Host "\nDone. Current IAM policy on ${ServiceAccountEmail}:" -ForegroundColor Green
try {
  $policyJson = & gcloud iam service-accounts get-iam-policy $ServiceAccountEmail --format=json
  # Pretty print if jq is available; otherwise just print JSON
  $jqPath = (Get-Command jq -ErrorAction SilentlyContinue).Path
  if ($jqPath) {
    $policyJson | & $jqPath .
  } else {
    $policyJson
  }
}
catch {
  Write-Warning "Could not fetch policy in JSON format. Showing text output. $_"
  & gcloud iam service-accounts get-iam-policy $ServiceAccountEmail
}

Write-Host "\nNext steps:" -ForegroundColor Green
Write-Host "  - Re-run the GitHub Actions Deploy Production workflow." -ForegroundColor Green
Write-Host "  - Verify the Build & Push step for GCP engines now authenticates and pushes successfully." -ForegroundColor Green
