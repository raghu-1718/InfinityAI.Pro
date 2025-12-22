#!/bin/bash
# Engine D Performance Optimization Deployment
# Implements Google Cloud's recommended latency optimization strategies

set -e

PROJECT_ID="gen-lang-client-0779271931"
REGION="us-central1"
SERVICE_NAME="engine-d-chatbot-prod"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║        🚀 Engine D Performance Optimization Deployment               ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Current Configuration:"
gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format="table(spec.template.spec.containers[0].resources.limits.cpu,
                    spec.template.spec.containers[0].resources.limits.memory,
                    spec.template.spec.containerConcurrency,
                    spec.template.metadata.annotations.'autoscaling.knative.dev/minScale',
                    spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale')"

echo ""
echo "⚡ Applying Optimizations:"
echo "  ✅ CPU: 1 → 4 (4x increase for NLP workloads)"
echo "  ✅ Memory: 1Gi → 8Gi (8x increase for model caching)"
echo "  ✅ Min Instances: 0 → 1 (eliminate cold starts)"
echo "  ✅ Concurrency: 80 (optimal for async workloads)"
echo "  ✅ Startup CPU Boost: Enabled"
echo ""

read -p "🔍 Apply these optimizations? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Optimization cancelled"
    exit 1
fi

echo ""
echo "🚀 Deploying optimized configuration..."

gcloud run services update ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --cpu=4 \
  --memory=8Gi \
  --concurrency=80 \
  --min-instances=1 \
  --max-instances=3 \
  --timeout=300 \
  --cpu-boost \
  --no-cpu-throttling \
  --execution-environment=gen2 \
  --quiet

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Optimization deployment successful!"
    echo ""
    echo "🏥 Testing performance..."
    sleep 5
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
      --region=${REGION} \
      --project=${PROJECT_ID} \
      --format="value(status.url)")
    
    echo "Testing: ${SERVICE_URL}/health"
    
    START_TIME=$(date +%s%3N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "${SERVICE_URL}/health")
    END_TIME=$(date +%s%3N)
    LATENCY=$((END_TIME - START_TIME))
    
    echo ""
    echo "📊 Performance Results:"
    echo "  Status Code: ${HTTP_CODE}"
    echo "  Latency: ${LATENCY}ms"
    
    if [ "${HTTP_CODE}" = "200" ]; then
        if [ ${LATENCY} -lt 1000 ]; then
            echo "  ✅ Target achieved! (<1000ms)"
        elif [ ${LATENCY} -lt 2000 ]; then
            echo "  ⚠️  Improved but above target (${LATENCY}ms)"
        else
            echo "  ⚠️  Still high latency (${LATENCY}ms)"
        fi
    else
        echo "  ⚠️  Health check failed (HTTP ${HTTP_CODE})"
    fi
    
    echo ""
    echo "📋 New Configuration:"
    gcloud run services describe ${SERVICE_NAME} \
      --region=${REGION} \
      --project=${PROJECT_ID} \
      --format="table(spec.template.spec.containers[0].resources.limits.cpu,
                        spec.template.spec.containers[0].resources.limits.memory,
                        spec.template.spec.containerConcurrency,
                        spec.template.metadata.annotations.'autoscaling.knative.dev/minScale',
                        spec.template.metadata.annotations.'autoscaling.knative.dev/maxScale')"
    
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                      ║"
    echo "║              ✨ Engine D Optimization Complete!                      ║"
    echo "║                                                                      ║"
    echo "╚══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🎯 Expected Improvements:"
    echo "  • 40-60% latency reduction from increased CPU"
    echo "  • Eliminated cold starts with min-instance=1"
    echo "  • Better model caching with 8Gi memory"
    echo "  • Faster startup with CPU boost"
    echo ""
    echo "📈 Next Steps:"
    echo "  1. Monitor latency over next 24 hours"
    echo "  2. Consider adding Redis caching if still >1000ms"
    echo "  3. Refactor to async/parallel engine calls"
    echo ""
else
    echo ""
    echo "❌ Deployment failed!"
    echo "Check logs: gcloud logging read --limit=20 ..."
    exit 1
fi
