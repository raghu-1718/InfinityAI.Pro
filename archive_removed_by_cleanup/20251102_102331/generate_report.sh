#!/bin/bash

# InfinityAI.Pro - Complete System Analysis Report Generator
# Date: $(date)
# Project: infinityai-pro-45818

echo "=========================================="
echo "🚀 InfinityAI.Pro - Complete System Report"
echo "=========================================="
echo ""

# Create report directory
mkdir -p ./system-reports
REPORT_FILE="./system-reports/infinityai-pro-full-report-$(date +%Y%m%d-%H%M%S).md"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
# InfinityAI.Pro - Complete System Analysis Report

**Generated:** $(date)
**Project ID:** infinityai-pro-45818
**Region:** us-central1

---

## 📊 EXECUTIVE SUMMARY

EOF

echo "📝 Generating comprehensive system report..."
echo ""

# ============================================
# SECTION 1: PROJECT OVERVIEW
# ============================================
echo "## 1️⃣ PROJECT OVERVIEW & CONFIGURATION" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "### Project Information" >> "$REPORT_FILE"
gcloud config list >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

echo "### Active APIs & Services" >> "$REPORT_FILE"
gcloud services list --enabled --project=infinityai-pro-45818 >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

# ============================================
# SECTION 2: CLOUD RUN SERVICES (ALL 20)
# ============================================
echo "## 2️⃣ CLOUD RUN SERVICES - COMPLETE ANALYSIS" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

echo "🔍 Analyzing Cloud Run Services..."

echo "### All Deployed Services" >> "$REPORT_FILE"
gcloud run services list --platform managed --region us-central1 --project=infinityai-pro-45818 >> "$REPORT_FILE" 2>&1
echo "" >> "$REPORT_FILE"

echo "✅ Report generation complete: $REPORT_FILE"
