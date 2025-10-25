#!/usr/bin/env bash
set -euo pipefail

# InfinityAI.Pro - Complete System Analysis Report Generator (Bash)
# Usage:
#   ./scripts/generate-system-report.sh [--project <GCP_PROJECT_ID>] [--region <REGION>]
# Notes:
#   - Requires: gcloud, firebase (CLI), jq (optional but recommended)
#   - Writes a timestamped markdown under ./system-reports/

PROJECT_ID=""
REGION="us-central1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_ID="$2"; shift 2 ;;
    --region)
      REGION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  PROJECT_ID=$(gcloud config get-value core/project 2>/dev/null || true)
fi

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: GCP project not provided and not set in gcloud config. Use --project <ID> or 'gcloud config set project <ID>'"
  exit 1
fi

mkdir -p ./system-reports
TS=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="./system-reports/${PROJECT_ID}-full-report-${TS}.md"

section_divider() {
  echo "" >> "$REPORT_FILE"
  echo "---" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

# Header
{
  echo "# InfinityAI.Pro - Complete System Analysis Report"
  echo ""
  echo "**Generated:** $(date)"
  echo "**Project ID:** ${PROJECT_ID}"
  echo "**Region:** ${REGION}"
  echo ""
  echo "## 📊 EXECUTIVE SUMMARY"
  echo ""
} > "$REPORT_FILE"

# 1. Project overview
{
  echo "## 1️⃣ PROJECT OVERVIEW & CONFIGURATION"
  echo ""
  echo "### Project Information"
  gcloud config list 2>&1 || true
  echo ""
  echo "### Active APIs & Services"
  gcloud services list --enabled --project="${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# 2. Cloud Run services
{
  echo "## 2️⃣ CLOUD RUN SERVICES - COMPLETE ANALYSIS"
  echo ""
  echo "### All Deployed Services"
  gcloud run services list --platform managed --region "${REGION}" --project "${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# Enumerate actual services dynamically
mapfile -t SERVICES < <(gcloud run services list --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format="value(metadata.name)" 2>/dev/null || true)
for SERVICE in "${SERVICES[@]}"; do
  {
    echo "### 📦 Service: ${SERVICE}"
    echo ""
    echo "#### Service Details"
    gcloud run services describe "${SERVICE}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format=yaml 2>&1 || true
    echo ""
    echo "#### Resource Configuration"
    gcloud run services describe "${SERVICE}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format='value(spec.template.spec.containers[0].resources)' 2>&1 || true
    echo ""
    echo "#### Environment Variables"
    gcloud run services describe "${SERVICE}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format='value(spec.template.spec.containers[0].env)' 2>&1 || true
    echo ""
    echo "#### Service URL"
    gcloud run services describe "${SERVICE}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)' 2>&1 || true
    echo ""
    section_divider
  } >> "$REPORT_FILE"
done

# 3. Firebase Functions
{
  echo "## 3️⃣ FIREBASE FUNCTIONS - COMPLETE ANALYSIS"
  echo ""
  echo "### All Deployed Functions"
  firebase functions:list --project "${PROJECT_ID}" 2>&1 || echo "⚠️ firebase CLI not found or not logged in. Skipping detailed Firebase sections."
  echo ""
} >> "$REPORT_FILE"

# If firebase CLI is present, enumerate functions
if command -v firebase >/dev/null 2>&1; then
  # Attempt JSON output to enumerate
  FUNC_JSON=$(firebase functions:list --project "${PROJECT_ID}" --json 2>/dev/null || echo "[]")
  if command -v jq >/dev/null 2>&1; then
    mapfile -t FUNCS < <(echo "$FUNC_JSON" | jq -r '.[].id' 2>/dev/null || true)
  else
    # Fallback: parse names from table output
    mapfile -t FUNCS < <(firebase functions:list --project "${PROJECT_ID}" 2>/dev/null | awk '{print $1}' | tail -n +4 | sed 's/|//g' | sed 's/\r//g')
  fi
  for FUNCTION in "${FUNCS[@]}"; do
    [[ -z "$FUNCTION" ]] && continue
    {
      echo "### 🔧 Function: ${FUNCTION}"
      echo ""
      echo "#### Function Configuration (gcloud describe v1/v2 best-effort)"
      gcloud functions describe "${FUNCTION}" --region="${REGION}" --project="${PROJECT_ID}" --format=yaml 2>&1 || true
      echo ""
      echo "#### Runtime & Resources"
      gcloud functions describe "${FUNCTION}" --region="${REGION}" --project="${PROJECT_ID}" --format='value(runtime,availableMemoryMb,timeout,maxInstances)' 2>&1 || true
      echo ""
      echo "#### HTTPS Trigger (if any)"
      gcloud functions describe "${FUNCTION}" --region="${REGION}" --project="${PROJECT_ID}" --format='value(httpsTrigger.url)' 2>&1 || true
      echo ""
      section_divider
    } >> "$REPORT_FILE"
  done
fi

# 4. Firebase configuration & Firestore
{
  echo "## 4️⃣ FIREBASE CONFIGURATION & INTEGRATIONS"
  echo ""
  echo "### Firebase Project Info"
  firebase projects:list 2>&1 || true
  echo ""
  echo "### Firestore Database"
  gcloud firestore databases list --project="${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# 5. AI/ML Integrations
{
  echo "## 5️⃣ AI/ML INTEGRATIONS & SERVICES"
  echo ""
  echo "### Vertex AI Models (region ${REGION})"
  gcloud ai models list --region="${REGION}" --project="${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# 6. Secret Manager
{
  echo "## 6️⃣ SECRET MANAGER & SECURITY"
  echo ""
  echo "### All Secrets"
  gcloud secrets list --project="${PROJECT_ID}" 2>&1 || true
  echo ""
  echo "### Secret Access Permissions"
} >> "$REPORT_FILE"
for SECRET in $(gcloud secrets list --project="${PROJECT_ID}" --format="value(name)" 2>/dev/null || true); do
  {
    echo "#### Secret: ${SECRET}"
    gcloud secrets get-iam-policy "${SECRET}" --project="${PROJECT_ID}" 2>&1 || true
    echo ""
  } >> "$REPORT_FILE"
done

# 7. IAM
{
  echo "## 7️⃣ IAM ROLES & PERMISSIONS"
  echo ""
  echo "### Service Accounts"
  gcloud iam service-accounts list --project="${PROJECT_ID}" 2>&1 || true
  echo ""
  echo "### IAM Policy Bindings"
  gcloud projects get-iam-policy "${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# 8. Networking
{
  echo "## 8️⃣ NETWORKING & CONNECTIVITY"
  echo ""
  echo "### VPC Networks"
  gcloud compute networks list --project="${PROJECT_ID}" 2>&1 || true
  echo ""
  echo "### Firewall Rules"
  gcloud compute firewall-rules list --project="${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# 9. Monitoring (limited quick sample)
{
  echo "## 9️⃣ MONITORING & LOGGING"
  echo ""
  echo "(Tip: For large logs, refine filters to specific services/functions.)"
  echo ""
} >> "$REPORT_FILE"

# 10. Quotas & limits
{
  echo "## 🔟 QUOTAS & RESOURCE LIMITS"
  echo ""
  echo "### Current Quota Usage"
  gcloud compute project-info describe --project="${PROJECT_ID}" 2>&1 || true
  echo ""
} >> "$REPORT_FILE"

# Footer
{
  echo "---"
  echo ""
  echo "## 🎯 REPORT GENERATION COMPLETE"
  echo "Generated: $(date)"
  echo "Report Location: $REPORT_FILE"
} >> "$REPORT_FILE"

echo "✅ Report generation complete!"
echo "📄 Report saved to: $REPORT_FILE"
