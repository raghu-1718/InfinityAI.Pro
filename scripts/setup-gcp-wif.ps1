<#
Setup GCP Workload Identity Federation for GitHub Actions.
Requires: gcloud with appropriate IAM permissions.
#>
param(
  [string]$ProjectId,
  [string]$PoolId = 'github-pool',
  [string]$ProviderId = 'github-provider',
  [string]$ServiceAccount = 'github-deployer',
  [string]$Repo = 'raghu-1718/InfinityAI.Pro',
  [switch]$DryRun
)

if(-not $ProjectId){ Write-Error 'ProjectId required'; exit 1 }

Write-Host "[INFO] Configuring GCP project $ProjectId" -ForegroundColor Cyan
if(-not $DryRun){ gcloud config set project $ProjectId | Out-Null } else { Write-Host "[DRYRUN] Would set project $ProjectId" }

Write-Host "[INFO] Ensuring service account exists" -ForegroundColor Cyan
if(-not $DryRun){ if(-not (gcloud iam service-accounts list --format='value(email)' --filter="email:$ServiceAccount@$ProjectId.iam.gserviceaccount.com")){ gcloud iam service-accounts create $ServiceAccount --display-name 'GitHub Deploy SA' } } else { Write-Host "[DRYRUN] Would ensure service account $ServiceAccount" }

$SaEmail = "$ServiceAccount@$ProjectId.iam.gserviceaccount.com"

Write-Host "[INFO] Ensuring WIF pool" -ForegroundColor Cyan
if(-not $DryRun){
  gcloud iam workload-identity-pools describe $PoolId --location=global 2>$null | Out-Null
  if($LASTEXITCODE -ne 0){
    gcloud iam workload-identity-pools create $PoolId --location=global --display-name 'GitHub Pool'
  }
} else { Write-Host "[DRYRUN] Would create/verify pool $PoolId" }

Write-Host "[INFO] Ensuring WIF provider" -ForegroundColor Cyan
if(-not $DryRun){
  gcloud iam workload-identity-pools providers describe $ProviderId --workload-identity-pool=$PoolId --location=global 2>$null | Out-Null
  if($LASTEXITCODE -ne 0){
    gcloud iam workload-identity-pools providers create-oidc $ProviderId `
      --workload-identity-pool=$PoolId `
      --location=global `
      --display-name='GitHub Provider' `
      --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" `
      --issuer-uri="https://token.actions.githubusercontent.com"
  }
} else { Write-Host "[DRYRUN] Would create/verify provider $ProviderId" }

Write-Host "[INFO] Granting service account impersonation" -ForegroundColor Cyan
if(-not $DryRun){
  gcloud iam service-accounts add-iam-policy-binding $SaEmail `
    --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $ProjectId --format='value(projectNumber)')/locations/global/workloadIdentityPools/$PoolId/attribute.repository=$Repo" `
    --role='roles/iam.workloadIdentityUser'
  # Some environments require Token Creator for access tokens
  gcloud iam service-accounts add-iam-policy-binding $SaEmail `
    --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $ProjectId --format='value(projectNumber)')/locations/global/workloadIdentityPools/$PoolId/attribute.repository=$Repo" `
    --role='roles/iam.serviceAccountTokenCreator' 2>$null | Out-Null
  # Project-level roles for deployments (build, artifact registry, run)
  gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SaEmail" `
    --role='roles/cloudbuild.builds.editor' 2>$null | Out-Null
  gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SaEmail" `
    --role='roles/artifactregistry.writer' 2>$null | Out-Null
  gcloud projects add-iam-policy-binding $ProjectId `
    --member="serviceAccount:$SaEmail" `
    --role='roles/run.admin' 2>$null | Out-Null
} else { Write-Host "[DRYRUN] Would bind workload identity user role" }

if(-not $DryRun){
  Write-Host "[RESULT] WORKLOAD_IDENTITY_PROVIDER=projects/$(gcloud projects describe $ProjectId --format='value(projectNumber)')/locations/global/workloadIdentityPools/$PoolId/providers/$ProviderId"
  Write-Host "[RESULT] SERVICE_ACCOUNT_EMAIL=$SaEmail"
} else {
  Write-Host "[RESULT][DRYRUN] WORKLOAD_IDENTITY_PROVIDER=projects/<PROJECT_NUM>/locations/global/workloadIdentityPools/$PoolId/providers/$ProviderId"
  Write-Host "[RESULT][DRYRUN] SERVICE_ACCOUNT_EMAIL=$SaEmail"
}
