# Security Group Fix for InfinityAI ECS Health Checks
# CRITICAL: This is blocking all health checks and traffic from the load balancer

Write-Host "=== SECURITY GROUP ISSUE IDENTIFIED ===" -ForegroundColor Red
Write-Host "Problem: ECS containers can't receive traffic from Application Load Balancer" -ForegroundColor Yellow
Write-Host "Root Cause: Security group sg-0bd6d3c8f36d085f1 only allows traffic from same security group" -ForegroundColor Yellow
Write-Host "Solution: Add inbound rules to allow ALB traffic" -ForegroundColor Green
Write-Host ""

Write-Host "=== REQUIRED IAM PERMISSIONS ===" -ForegroundColor Cyan
Write-Host "Add these permissions to your infinityai-deploy user:" -ForegroundColor Yellow
Write-Host ""
Write-Host @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupIngress",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSecurityGroupRules"
            ],
            "Resource": "*"
        }
    ]
}
"@ -ForegroundColor Green

Write-Host ""
Write-Host "=== MANUAL SECURITY GROUP FIX ===" -ForegroundColor Cyan
Write-Host "If you can't add IAM permissions, fix this manually in AWS Console:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to EC2 > Security Groups" -ForegroundColor White
Write-Host "2. Find security group: sg-0bd6d3c8f36d085f1" -ForegroundColor White
Write-Host "3. Click 'Edit inbound rules'" -ForegroundColor White
Write-Host "4. Add these rules:" -ForegroundColor White
Write-Host ""
Write-Host "   Rule 1:" -ForegroundColor Green
Write-Host "   - Type: Custom TCP" -ForegroundColor White
Write-Host "   - Port: 8000" -ForegroundColor White
Write-Host "   - Source: sg-06f41152cce3458eb (ALB security group)" -ForegroundColor White
Write-Host ""
Write-Host "   Rule 2:" -ForegroundColor Green
Write-Host "   - Type: Custom TCP" -ForegroundColor White
Write-Host "   - Port: 8003" -ForegroundColor White
Write-Host "   - Source: sg-06f41152cce3458eb (ALB security group)" -ForegroundColor White
Write-Host ""
Write-Host "   Rule 3:" -ForegroundColor Green
Write-Host "   - Type: Custom TCP" -ForegroundColor White
Write-Host "   - Port: 8004" -ForegroundColor White
Write-Host "   - Source: sg-06f41152cce3458eb (ALB security group)" -ForegroundColor White
Write-Host ""
Write-Host "5. Save rules" -ForegroundColor White
Write-Host ""

Write-Host "=== AUTOMATED COMMANDS (after IAM permissions) ===" -ForegroundColor Cyan
Write-Host "Once you have EC2 permissions, run these commands:" -ForegroundColor Yellow
Write-Host ""
Write-Host "aws ec2 authorize-security-group-ingress --group-id sg-0bd6d3c8f36d085f1 --protocol tcp --port 8000 --source-group sg-06f41152cce3458eb"
Write-Host "aws ec2 authorize-security-group-ingress --group-id sg-0bd6d3c8f36d085f1 --protocol tcp --port 8003 --source-group sg-06f41152cce3458eb"
Write-Host "aws ec2 authorize-security-group-ingress --group-id sg-0bd6d3c8f36d085f1 --protocol tcp --port 8004 --source-group sg-06f41152cce3458eb"
Write-Host ""

Write-Host "=== VERIFICATION COMMANDS ===" -ForegroundColor Cyan
Write-Host "After fixing security group, test health:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Wait 2-3 minutes for health checks to cycle, then check:"
Write-Host "aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-c/7085c47c34ca3683"
Write-Host "aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:us-east-1:152687308610:targetgroup/infinityai-tg-engine-d/14ba59846c070247"
Write-Host ""
Write-Host "# Test load balancer routing:"
Write-Host "curl http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-c/"
Write-Host "curl http://infinityai-alb-124143296.us-east-1.elb.amazonaws.com/engine-d/"
Write-Host ""

Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "This security group fix will resolve:" -ForegroundColor Green
Write-Host "✅ Health check timeouts" -ForegroundColor Green
Write-Host "✅ Load balancer routing issues" -ForegroundColor Green
Write-Host "✅ Target group unhealthy status" -ForegroundColor Green
Write-Host "✅ Failed task problems" -ForegroundColor Green
Write-Host ""
Write-Host "Once fixed, both engines should become healthy and accessible!" -ForegroundColor Green