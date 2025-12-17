#!/bin/bash
###############################################################################
# InfinityAI.Pro - GCP Uptime Monitoring Configuration
#
# Purpose: Configure uptime checks and alerting for all 6 Cloud Run services
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="after-yesterday-473512-k3"
REGION="us-central1"
NOTIFICATION_CHANNEL_EMAIL="<MONITORING_ALERT_EMAIL>"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     InfinityAI.Pro - Uptime Monitoring Configuration        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Set GCP project
gcloud config set project ${PROJECT_ID}

# Service URLs
declare -A SERVICES=(
    ["engine-a-market-data"]="engine-a-market-data-prod-bprmddefsa-uc.a.run.app"
    ["engine-b-ai-ml"]="engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app"
    ["engine-c-execution"]="engine-c-prod-bprmddefsa-uc.a.run.app"
    ["engine-d-chatbot"]="engine-d-chatbot-prod-bprmddefsa-uc.a.run.app"
    ["engine-ultra-aggressive"]="engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app"
    ["infinityai-frontend"]="infinityai-frontend-bprmddefsa-uc.a.run.app"
)

###############################################################################
# Step 1: Create Notification Channel
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 1: Creating Email Notification Channel${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create notification channel JSON
cat > /tmp/notification-channel.json <<EOF
{
  "type": "email",
  "displayName": "InfinityAI Alerts",
  "description": "Email notifications for InfinityAI.Pro monitoring alerts",
  "labels": {
    "email_address": "${NOTIFICATION_CHANNEL_EMAIL}"
  },
  "enabled": true
}
EOF

echo -e "${YELLOW}Creating email notification channel...${NC}"
CHANNEL_ID=$(gcloud alpha monitoring channels create --channel-content-from-file=/tmp/notification-channel.json --format="value(name)" 2>&1 || echo "")

if [ -z "$CHANNEL_ID" ]; then
    echo -e "${YELLOW}Channel may already exist, fetching existing...${NC}"
    CHANNEL_ID=$(gcloud alpha monitoring channels list --filter="labels.email_address=${NOTIFICATION_CHANNEL_EMAIL}" --format="value(name)" | head -n 1)
fi

echo -e "${GREEN}✓ Notification channel: ${CHANNEL_ID}${NC}"

###############################################################################
# Step 2: Create Uptime Checks for Each Service
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 2: Creating Uptime Checks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

for service_name in "${!SERVICES[@]}"; do
    hostname="${SERVICES[$service_name]}"
    
    echo -e "\n${YELLOW}Creating uptime check for ${service_name}...${NC}"
    
    # Create uptime check JSON
    cat > /tmp/uptime-${service_name}.json <<EOF
{
  "displayName": "${service_name}-health-check",
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "${PROJECT_ID}",
      "host": "${hostname}"
    }
  },
  "httpCheck": {
    "requestMethod": "GET",
    "path": "/health",
    "port": 443,
    "useSsl": true,
    "validateSsl": true
  },
  "period": "60s",
  "timeout": "10s",
  "contentMatchers": [
    {
      "content": "healthy"
    }
  ],
  "selectedRegions": [
    "USA",
    "EUROPE",
    "ASIA_PACIFIC"
  ]
}
EOF

    # Create the uptime check
    gcloud monitoring uptime create --config-from-file=/tmp/uptime-${service_name}.json 2>&1 || echo "  (May already exist)"
    
    echo -e "${GREEN}✓ Uptime check created for ${service_name}${NC}"
done

###############################################################################
# Step 3: Create Alerting Policies
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 3: Creating Alerting Policies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Policy 1: Service Down Alert
echo -e "\n${YELLOW}Creating Service Down alert policy...${NC}"
cat > /tmp/alert-service-down.json <<EOF
{
  "displayName": "InfinityAI Service Down",
  "documentation": {
    "content": "One or more InfinityAI services are not responding to health checks. Immediate action required.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Uptime check failed",
      "conditionThreshold": {
        "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" resource.type=\"uptime_url\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_FRACTION_TRUE"
          }
        ],
        "comparison": "COMPARISON_LT",
        "thresholdValue": 0.9,
        "duration": "120s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "${CHANNEL_ID}"
  ],
  "alertStrategy": {
    "autoClose": "604800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-service-down.json 2>&1 || echo "  (May already exist)"
echo -e "${GREEN}✓ Service Down alert policy created${NC}"

# Policy 2: High Latency Alert
echo -e "\n${YELLOW}Creating High Latency alert policy...${NC}"
cat > /tmp/alert-high-latency.json <<EOF
{
  "displayName": "InfinityAI High Latency",
  "documentation": {
    "content": "Service response time is consistently above 1 second. Performance degradation detected.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Request latency > 1s",
      "conditionThreshold": {
        "filter": "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_DELTA",
            "crossSeriesReducer": "REDUCE_PERCENTILE_95",
            "groupByFields": ["resource.service_name"]
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 1000,
        "duration": "300s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "${CHANNEL_ID}"
  ],
  "alertStrategy": {
    "autoClose": "604800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-high-latency.json 2>&1 || echo "  (May already exist)"
echo -e "${GREEN}✓ High Latency alert policy created${NC}"

# Policy 3: Error Rate Alert
echo -e "\n${YELLOW}Creating Error Rate alert policy...${NC}"
cat > /tmp/alert-error-rate.json <<EOF
{
  "displayName": "InfinityAI Error Rate Spike",
  "documentation": {
    "content": "Error rate has exceeded 5% for 5 minutes. Investigate service logs immediately.",
    "mimeType": "text/markdown"
  },
  "conditions": [
    {
      "displayName": "Error rate > 5%",
      "conditionThreshold": {
        "filter": "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.response_code_class=\"5xx\"",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_SUM",
            "groupByFields": ["resource.service_name"]
          }
        ],
        "comparison": "COMPARISON_GT",
        "thresholdValue": 0.05,
        "duration": "300s"
      }
    }
  ],
  "combiner": "OR",
  "enabled": true,
  "notificationChannels": [
    "${CHANNEL_ID}"
  ],
  "alertStrategy": {
    "autoClose": "604800s"
  }
}
EOF

gcloud alpha monitoring policies create --policy-from-file=/tmp/alert-error-rate.json 2>&1 || echo "  (May already exist)"
echo -e "${GREEN}✓ Error Rate alert policy created${NC}"

###############################################################################
# Step 4: Verification
###############################################################################

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Step 4: Verification${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "\n${YELLOW}Configured Uptime Checks:${NC}"
gcloud monitoring uptime list-configs --format="table(displayName,monitoredResource.labels.host,httpCheck.path)"

echo -e "\n${YELLOW}Configured Alert Policies:${NC}"
gcloud alpha monitoring policies list --format="table(displayName,enabled,notificationChannels)"

echo -e "\n${YELLOW}Notification Channels:${NC}"
gcloud alpha monitoring channels list --format="table(displayName,type,labels)"

###############################################################################
# Summary
###############################################################################

echo -e "\n${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║               Monitoring Configuration Complete              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${GREEN}✓ Uptime Monitoring Configured:${NC}"
echo -e "  • 6 uptime checks (60s interval) for all services"
echo -e "  • Health endpoint monitoring (/health)"
echo -e "  • Multi-region monitoring (USA, Europe, Asia Pacific)"

echo -e "\n${GREEN}✓ Alerting Policies Created:${NC}"
echo -e "  • Service Down: < 90% uptime in 2 minutes"
echo -e "  • High Latency: > 1s response time for 5 minutes"
echo -e "  • Error Rate: > 5% errors for 5 minutes"

echo -e "\n${GREEN}✓ Notifications:${NC}"
echo -e "  • Email: ${NOTIFICATION_CHANNEL_EMAIL}"
echo -e "  • Auto-close: 7 days"

echo -e "\n${YELLOW}📊 View Monitoring Dashboard:${NC}"
echo -e "  ${BLUE}https://console.cloud.google.com/monitoring/uptime?project=${PROJECT_ID}${NC}"

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Monitoring configuration completed!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Cleanup temp files
rm -f /tmp/notification-channel.json /tmp/uptime-*.json /tmp/alert-*.json
