#!/bin/bash
# Automated health check for InfinityAI.Pro services
# Run this via Cloud Scheduler every 5 minutes

SERVICES=(
    "engine-a-market-data-prod"
    "engine-b-ai-ml-prod"
    "engine-c-execution-prod"
    "engine-d-chatbot-prod"
    "engine-ultra-aggressive-prod"
    "infinityai-frontend"
)

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
RESULTS_FILE="/tmp/health_check_${TIMESTAMP}.json"

echo "{" > $RESULTS_FILE
echo '  "timestamp": "'$TIMESTAMP'",' >> $RESULTS_FILE
echo '  "checks": [' >> $RESULTS_FILE

for i in "${!SERVICES[@]}"; do
    SERVICE="${SERVICES[$i]}"
    URL="https://${SERVICE}-bprmddefsa-uc.a.run.app/health"
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$URL")
    LATENCY=$(curl -s -o /dev/null -w "%{time_total}" -m 10 "$URL")
    
    if [ "$i" -gt 0 ]; then
        echo "," >> $RESULTS_FILE
    fi
    
    echo '    {' >> $RESULTS_FILE
    echo '      "service": "'$SERVICE'",' >> $RESULTS_FILE
    echo '      "http_code": '$HTTP_CODE',' >> $RESULTS_FILE
    echo '      "latency": '$LATENCY',' >> $RESULTS_FILE
    echo '      "healthy": '$( [ "$HTTP_CODE" -eq 200 ] && echo "true" || echo "false" ) >> $RESULTS_FILE
    echo '    }' >> $RESULTS_FILE
done

echo '  ]' >> $RESULTS_FILE
echo '}' >> $RESULTS_FILE

cat $RESULTS_FILE
