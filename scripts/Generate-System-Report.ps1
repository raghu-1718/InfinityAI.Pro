#!/usr/bin/env pwsh
<#!
.SYNOPSIS
  InfinityAI.Pro - Complete System Analysis Report Generator (PowerShell)
.DESCRIPTION
  Generates a timestamped markdown report with real-time details from Cloud Run, Firebase Functions,
  Firestore, Secret Manager, IAM, and more. Designed for Windows/PowerShell environments.
.PARAMETER Project
  GCP Project ID. If omitted, uses gcloud config core/project.
.PARAMETER Region
  Region for Cloud Run / Vertex AI queries. Defaults to us-central1.
.EXAMPLE
  ./scripts/Generate-System-Report.ps1 -Project after-yesterday-473512-k3 -Region us-central1
#>
param(
  [string]$Project,
  [string]$Region = "us-central1"
)

$ErrorActionPreference = 'Stop'

function Ensure-Project {
  param([string]$Project)
  if ([string]::IsNullOrWhiteSpace($Project)) {
    try {
      $Project = (& gcloud config get-value core/project) 2>$null
    } catch { }
  }
  if ([string]::IsNullOrWhiteSpace($Project)) {
    throw "GCP project not provided and not set in gcloud config. Use -Project <ID> or 'gcloud config set project <ID>'."
  }
  return $Project
}

$Project = Ensure-Project -Project $Project

$reportsDir = Join-Path -Path (Get-Location) -ChildPath 'system-reports'
New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportFile = Join-Path $reportsDir -ChildPath "$Project-full-report-$ts.md"

function Add-SectionDivider {
  Add-Content -Path $reportFile -Value ""
  Add-Content -Path $reportFile -Value "---"
  Add-Content -Path $reportFile -Value ""
}

# Header
@(
  "# InfinityAI.Pro - Complete System Analysis Report",
  "",
  "**Generated:** $(Get-Date)",
  "**Project ID:** $Project",
  "**Region:** $Region",
  "",
  "## 📊 EXECUTIVE SUMMARY",
  ""
) | Set-Content -Path $reportFile

# 1. Project overview
Add-Content -Path $reportFile -Value "## 1️⃣ PROJECT OVERVIEW & CONFIGURATION"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Project Information"
try { (& gcloud config list) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Active APIs & Services"
try { (& gcloud services list --enabled --project=$Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# 2. Cloud Run services
Add-Content -Path $reportFile -Value "## 2️⃣ CLOUD RUN SERVICES - COMPLETE ANALYSIS"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### All Deployed Services"
try { (& gcloud run services list --platform managed --region $Region --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# Enumerate services
$services = @()
try {
  $services = (& gcloud run services list --platform managed --region $Region --project $Project --format=value(metadata.name)) -split "\r?\n" | Where-Object { $_ -and $_.Trim() -ne '' }
} catch { }
foreach ($svc in $services) {
  Add-Content -Path $reportFile -Value "### 📦 Service: $svc"
  Add-Content -Path $reportFile -Value ""
  Add-Content -Path $reportFile -Value "#### Service Details"
  try { (& gcloud run services describe $svc --platform managed --region $Region --project $Project --format=yaml) | Out-String | Add-Content -Path $reportFile } catch { }
  Add-Content -Path $reportFile -Value ""
  Add-Content -Path $reportFile -Value "#### Resource Configuration"
  try { (& gcloud run services describe $svc --platform managed --region $Region --project $Project --format='value(spec.template.spec.containers[0].resources)') | Out-String | Add-Content -Path $reportFile } catch { }
  Add-Content -Path $reportFile -Value ""
  Add-Content -Path $reportFile -Value "#### Environment Variables"
  try { (& gcloud run services describe $svc --platform managed --region $Region --project $Project --format='value(spec.template.spec.containers[0].env)') | Out-String | Add-Content -Path $reportFile } catch { }
  Add-Content -Path $reportFile -Value ""
  Add-Content -Path $reportFile -Value "#### Service URL"
  try { (& gcloud run services describe $svc --platform managed --region $Region --project $Project --format='value(status.url)') | Out-String | Add-Content -Path $reportFile } catch { }
  Add-SectionDivider
}

# 3. Firebase Functions
Add-Content -Path $reportFile -Value "## 3️⃣ FIREBASE FUNCTIONS - COMPLETE ANALYSIS"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### All Deployed Functions"
$firebaseOk = $true
try { (& firebase functions:list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { $firebaseOk = $false }
Add-Content -Path $reportFile -Value ""

if ($firebaseOk) {
  try {
    $funcListJson = (& firebase functions:list --project $Project --json) | ConvertFrom-Json
    $funcIds = @()
    if ($funcListJson) {
      $funcIds = $funcListJson | ForEach-Object { $_.id }
    }
    foreach ($fn in $funcIds) {
      if ([string]::IsNullOrWhiteSpace($fn)) { continue }
      Add-Content -Path $reportFile -Value "### 🔧 Function: $fn"
      Add-Content -Path $reportFile -Value ""
      Add-Content -Path $reportFile -Value "#### Function Configuration (gcloud describe v1/v2 best-effort)"
      try { (& gcloud functions describe $fn --region $Region --project $Project --format=yaml) | Out-String | Add-Content -Path $reportFile } catch { }
      Add-Content -Path $reportFile -Value ""
      Add-Content -Path $reportFile -Value "#### Runtime & Resources"
      try { (& gcloud functions describe $fn --region $Region --project $Project --format='value(runtime,availableMemoryMb,timeout,maxInstances)') | Out-String | Add-Content -Path $reportFile } catch { }
      Add-Content -Path $reportFile -Value ""
      Add-Content -Path $reportFile -Value "#### HTTPS Trigger (if any)"
      try { (& gcloud functions describe $fn --region $Region --project $Project --format='value(httpsTrigger.url)') | Out-String | Add-Content -Path $reportFile } catch { }
      Add-SectionDivider
    }
  } catch { }
}

# 4. Firebase & Firestore
Add-Content -Path $reportFile -Value "## 4️⃣ FIREBASE CONFIGURATION & INTEGRATIONS"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Firebase Project Info"
try { (& firebase projects:list) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Firestore Database"
try { (& gcloud firestore databases list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# 5. AI/ML
Add-Content -Path $reportFile -Value "## 5️⃣ AI/ML INTEGRATIONS & SERVICES"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Vertex AI Models (region $Region)"
try { (& gcloud ai models list --region $Region --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# 6. Secrets
Add-Content -Path $reportFile -Value "## 6️⃣ SECRET MANAGER & SECURITY"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### All Secrets"
try { (& gcloud secrets list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Secret Access Permissions"
try {
  $secrets = (& gcloud secrets list --project $Project --format=value(name)) -split "\r?\n" | Where-Object { $_ }
  foreach ($sec in $secrets) {
    Add-Content -Path $reportFile -Value "#### Secret: $sec"
    try { (& gcloud secrets get-iam-policy $sec --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
    Add-Content -Path $reportFile -Value ""
  }
} catch { }

# 7. IAM
Add-Content -Path $reportFile -Value "## 7️⃣ IAM ROLES & PERMISSIONS"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Service Accounts"
try { (& gcloud iam service-accounts list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### IAM Policy Bindings"
try { (& gcloud projects get-iam-policy $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# 8. Networking
Add-Content -Path $reportFile -Value "## 8️⃣ NETWORKING & CONNECTIVITY"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### VPC Networks"
try { (& gcloud compute networks list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Firewall Rules"
try { (& gcloud compute firewall-rules list --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

# 9. Monitoring (placeholder)
Add-Content -Path $reportFile -Value "## 9️⃣ MONITORING & LOGGING"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "(Tip: Use Cloud Logging filters for deep dives.)"
Add-Content -Path $reportFile -Value ""

# 10. Quotas
Add-Content -Path $reportFile -Value "## 🔟 QUOTAS & RESOURCE LIMITS"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "### Current Quota Usage"
try { (& gcloud compute project-info describe --project $Project) | Out-String | Add-Content -Path $reportFile } catch { }
Add-Content -Path $reportFile -Value ""

Add-Content -Path $reportFile -Value "---"
Add-Content -Path $reportFile -Value ""
Add-Content -Path $reportFile -Value "## 🎯 REPORT GENERATION COMPLETE"
Add-Content -Path $reportFile -Value "Generated: $(Get-Date)"
Add-Content -Path $reportFile -Value "Report Location: $reportFile"

Write-Host "✅ Report generation complete!" -ForegroundColor Green
Write-Host "📄 Report saved to: $reportFile"
