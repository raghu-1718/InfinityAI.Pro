# AWS Load Balancer Fix Commands
# Run these commands AFTER adding the IAM permissions

# 1. Create listener rule for Engine C (path /engine-c/*)
aws elbv2 create-rule `
  --listener-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:listener/app/infinityai-alb/3ba082317288d222/eaab4cd54c1a90eb" `
  --priority 1 `
  --conditions Field=path-pattern,Values="/engine-c/*" `
  --actions Type=forward,TargetGroupArn="arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683"

# 2. Create listener rule for Engine D (path /engine-d/*)  
aws elbv2 create-rule `
  --listener-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:listener/app/infinityai-alb/3ba082317288d222/eaab4cd54c1a90eb" `
  --priority 2 `
  --conditions Field=path-pattern,Values="/engine-d/*" `
  --actions Type=forward,TargetGroupArn="arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-d/14ba59846c070247"

# 3. Fix Engine C target group port (from 8000 to 8003)
aws elbv2 modify-target-group `
  --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683" `
  --port 8003

# 4. Verify the fixes
aws elbv2 describe-rules --listener-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:listener/app/infinityai-alb/3ba082317288d222/eaab4cd54c1a90eb"
aws elbv2 describe-target-health --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683"
aws elbv2 describe-target-health --target-group-arn "arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-d/14ba59846c070247"