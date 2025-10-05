# InfinityAI.Pro AWS ECS Infrastructure Fix Commands
# Configure AWS CLI first: aws configure

echo "🟠 Checking AWS ECS Infrastructure..."

# 1. Check if cluster exists and is active
echo "Checking ECS Cluster..."
aws ecs describe-clusters --clusters infinityai-pro-cluster --region us-east-1

# 2. List services in the cluster
echo "Listing ECS Services..."
aws ecs list-services --cluster infinityai-pro-cluster --region us-east-1

# 3. Check service status
echo "Checking Service Status..."
aws ecs describe-services \
  --cluster infinityai-pro-cluster \
  --services engine-c-service engine-d-service \
  --region us-east-1

# 4. Check task definitions
echo "Checking Task Definitions..."
aws ecs list-task-definitions --family-prefix infinityai-engine --region us-east-1

# 5. Check Load Balancer
echo "Checking Application Load Balancer..."
aws elbv2 describe-load-balancers \
  --names infinityai-pro-alb \
  --region us-east-1

# 6. Check Target Groups
echo "Checking Target Groups..."
aws elbv2 describe-target-groups \
  --region us-east-1 \
  --query "TargetGroups[?contains(TargetGroupName, 'infinityai')]"

# 7. If services are stopped, restart them
echo "Restarting ECS Services..."
aws ecs update-service \
  --cluster infinityai-pro-cluster \
  --service engine-c-service \
  --force-new-deployment \
  --region us-east-1

aws ecs update-service \
  --cluster infinityai-pro-cluster \
  --service engine-d-service \
  --force-new-deployment \
  --region us-east-1

# 8. Check security groups
echo "Checking Security Groups..."
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=infinityai-*" \
  --region us-east-1

# 9. Check if Load Balancer is healthy
echo "Testing Load Balancer Health..."
curl -f http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com/health || echo "Load Balancer not responding"

echo "✅ AWS ECS fix commands completed"
echo "If services don't exist, you'll need to redeploy them using ECS task definitions"