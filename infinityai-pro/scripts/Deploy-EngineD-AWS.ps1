# InfinityAI.Pro - Engine D AWS Deployment Script (PowerShell)
# Deploy central backend API to AWS ECS with full DHAN integration

param(
    [string]$AWSRegion = "us-east-1",
    [string]$ClusterName = "infinityai-cluster",
    [string]$ServiceName = "infinityai-engine-d",
    [string]$TaskFamily = "infinityai-engine-d",
    [string]$ECRRepoName = "infinityai-engine-d"
)

Write-Host "🚀 Starting Engine D (AWS Central Backend) Deployment..." -ForegroundColor Cyan

# Configuration
$LogGroupName = "/ecs/infinityai-engine-d"

# Get AWS Account ID
Write-Host "Getting AWS Account ID..." -ForegroundColor Blue
$AccountId = (aws sts get-caller-identity --query Account --output text)
$ECRUri = "${AccountId}.dkr.ecr.${AWSRegion}.amazonaws.com/${ECRRepoName}"

Write-Host "✅ AWS Account ID: $AccountId" -ForegroundColor Green
Write-Host "✅ ECR Repository: $ECRUri" -ForegroundColor Green

# Step 1: Store DHAN credentials securely in AWS Secrets Manager
Write-Host "🔐 Storing DHAN credentials in AWS Secrets Manager..." -ForegroundColor Magenta

$DHANSecretJson = @{
    client_id = "63b3086e"
    client_secret = "147fc424-cd90-4bd6-a843-15c3766e2df7"
} | ConvertTo-Json -Compress

try {
    aws secretsmanager create-secret --name "infinityai/dhan-credentials" --description "DHAN API credentials for InfinityAI.Pro trading system" --secret-string $DHANSecretJson --region $AWSRegion 2>$null
    Write-Host "✅ DHAN credentials created in AWS Secrets Manager" -ForegroundColor Green
} catch {
    Write-Host "Secret exists, updating..." -ForegroundColor Yellow
    aws secretsmanager update-secret --secret-id "infinityai/dhan-credentials" --secret-string $DHANSecretJson --region $AWSRegion
    Write-Host "✅ DHAN credentials updated in AWS Secrets Manager" -ForegroundColor Green
}

# Step 2: Create ECR repository
Write-Host "📦 Creating ECR repository..." -ForegroundColor Blue
try {
    aws ecr create-repository --repository-name $ECRRepoName --region $AWSRegion 2>$null
    Write-Host "✅ ECR repository created" -ForegroundColor Green
} catch {
    Write-Host "Repository already exists" -ForegroundColor Yellow
}

# Step 3: Build and push Docker image
Write-Host "🐳 Building Docker image..." -ForegroundColor Blue
Set-Location "..\engine-d-aws"

# Login to ECR
Write-Host "Logging into ECR..." -ForegroundColor Blue
$LoginPassword = aws ecr get-login-password --region $AWSRegion
$LoginPassword | docker login --username AWS --password-stdin $ECRUri

# Build image
Write-Host "Building Docker image..." -ForegroundColor Blue
docker build -t $ECRRepoName .
docker tag "${ECRRepoName}:latest" "${ECRUri}:latest"

# Push image
Write-Host "📤 Pushing image to ECR..." -ForegroundColor Blue
docker push "${ECRUri}:latest"
Write-Host "✅ Docker image pushed successfully" -ForegroundColor Green

Set-Location "..\scripts"

# Step 4: Create CloudWatch Log Group
Write-Host "📝 Creating CloudWatch Log Group..." -ForegroundColor Blue
try {
    aws logs create-log-group --log-group-name $LogGroupName --region $AWSRegion 2>$null
    Write-Host "✅ CloudWatch Log Group created" -ForegroundColor Green
} catch {
    Write-Host "Log group already exists" -ForegroundColor Yellow
}

# Step 5: Create ECS Cluster
Write-Host "🖥️ Creating ECS Cluster..." -ForegroundColor Blue
try {
    aws ecs create-cluster --cluster-name $ClusterName --region $AWSRegion 2>$null
    Write-Host "✅ ECS Cluster created" -ForegroundColor Green
} catch {
    Write-Host "Cluster already exists" -ForegroundColor Yellow
}

# Step 6: Create IAM roles
Write-Host "👤 Creating IAM roles..." -ForegroundColor Blue

# Create task execution role trust policy
$TaskExecutionRoleTrustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                Service = "ecs-tasks.amazonaws.com"
            }
            Action = "sts:AssumeRole"
        }
    )
} | ConvertTo-Json -Depth 3

$TaskExecutionRoleTrustPolicy | Out-File -FilePath "task-execution-role-trust-policy.json" -Encoding utf8

# Create execution role
try {
    aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file://task-execution-role-trust-policy.json --region $AWSRegion 2>$null
    Write-Host "✅ Task execution role created" -ForegroundColor Green
} catch {
    Write-Host "Execution role already exists" -ForegroundColor Yellow
}

aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>$null

# Task role with additional permissions
$TaskRolePolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @(
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            )
            Resource = "arn:aws:secretsmanager:${AWSRegion}:${AccountId}:secret:infinityai/*"
        },
        @{
            Effect = "Allow"
            Action = @(
                "elasticache:DescribeCacheClusters",
                "elasticache:DescribeReplicationGroups"
            )
            Resource = "*"
        }
    )
} | ConvertTo-Json -Depth 3

$TaskRolePolicy | Out-File -FilePath "task-role-policy.json" -Encoding utf8

try {
    aws iam create-role --role-name infinityai-engine-d-task-role --assume-role-policy-document file://task-execution-role-trust-policy.json --region $AWSRegion 2>$null
    Write-Host "✅ Task role created" -ForegroundColor Green
} catch {
    Write-Host "Task role already exists" -ForegroundColor Yellow
}

aws iam put-role-policy --role-name infinityai-engine-d-task-role --policy-name InfinityAI-Engine-D-Policy --policy-document file://task-role-policy.json 2>$null

# Step 7: Create Redis cluster (ElastiCache)
Write-Host "📚 Creating Redis cluster..." -ForegroundColor Blue
try {
    aws elasticache create-replication-group --replication-group-id infinityai-redis --description "Redis cluster for InfinityAI.Pro" --num-cache-clusters 1 --cache-node-type cache.t3.micro --engine redis --region $AWSRegion 2>$null
    Write-Host "✅ Redis cluster creation initiated" -ForegroundColor Green
} catch {
    Write-Host "Redis cluster creation in progress or already exists" -ForegroundColor Yellow
}

# Step 8: Get default VPC and subnets
Write-Host "🔍 Getting default VPC and subnets..." -ForegroundColor Blue
$DefaultVPCId = aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region $AWSRegion
$SubnetIds = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$DefaultVPCId" --query "Subnets[0:2].SubnetId" --output text --region $AWSRegion
$SubnetArray = $SubnetIds -split "`t"
$Subnet1 = $SubnetArray[0]
$Subnet2 = if ($SubnetArray.Length -gt 1) { $SubnetArray[1] } else { $SubnetArray[0] }

Write-Host "✅ Default VPC: $DefaultVPCId" -ForegroundColor Green
Write-Host "✅ Using subnets: $Subnet1, $Subnet2" -ForegroundColor Green

# Create security group
Write-Host "🛡️ Creating security group..." -ForegroundColor Blue
try {
    $SecurityGroupId = aws ec2 create-security-group --group-name infinityai-sg --description "Security group for InfinityAI.Pro" --vpc-id $DefaultVPCId --region $AWSRegion --query "GroupId" --output text
    Write-Host "✅ Security group created: $SecurityGroupId" -ForegroundColor Green
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress --group-id $SecurityGroupId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWSRegion 2>$null
    aws ec2 authorize-security-group-ingress --group-id $SecurityGroupId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWSRegion 2>$null
    aws ec2 authorize-security-group-ingress --group-id $SecurityGroupId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $AWSRegion 2>$null
} catch {
    $SecurityGroupId = aws ec2 describe-security-groups --filters "Name=group-name,Values=infinityai-sg" --query "SecurityGroups[0].GroupId" --output text --region $AWSRegion
    Write-Host "Security group already exists: $SecurityGroupId" -ForegroundColor Yellow
}

# Step 9: Update task definition with actual values
Write-Host "📋 Creating ECS task definition..." -ForegroundColor Blue
$TaskDefinition = @{
    family = $TaskFamily
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "512"
    memory = "1024"
    executionRoleArn = "arn:aws:iam::${AccountId}:role/ecsTaskExecutionRole"
    taskRoleArn = "arn:aws:iam::${AccountId}:role/infinityai-engine-d-task-role"
    containerDefinitions = @(
        @{
            name = "infinityai-engine-d"
            image = "${ECRUri}:latest"
            portMappings = @(
                @{
                    containerPort = 8000
                    protocol = "tcp"
                }
            )
            essential = $true
            environment = @(
                @{
                    name = "AWS_DEFAULT_REGION"
                    value = $AWSRegion
                },
                @{
                    name = "REDIS_HOST"
                    value = "infinityai-redis.cache.amazonaws.com"
                }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = $LogGroupName
                    "awslogs-region" = $AWSRegion
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

$TaskDefinition | Out-File -FilePath "task-definition.json" -Encoding utf8

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWSRegion

# Step 10: Create Application Load Balancer
Write-Host "⚖️ Creating Application Load Balancer..." -ForegroundColor Blue
try {
    $ALBArn = aws elbv2 create-load-balancer --name infinityai-engine-d-alb --subnets $Subnet1 $Subnet2 --security-groups $SecurityGroupId --scheme internet-facing --type application --ip-address-type ipv4 --region $AWSRegion --query "LoadBalancers[0].LoadBalancerArn" --output text
    Write-Host "✅ Application Load Balancer created: $ALBArn" -ForegroundColor Green
} catch {
    $ALBArn = aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query "LoadBalancers[0].LoadBalancerArn" --output text --region $AWSRegion
    Write-Host "Load balancer already exists: $ALBArn" -ForegroundColor Yellow
}

# Step 11: Create target group
Write-Host "🎯 Creating target group..." -ForegroundColor Blue
try {
    $TGArn = aws elbv2 create-target-group --name infinityai-engine-d-tg --protocol HTTP --port 8000 --vpc-id $DefaultVPCId --target-type ip --health-check-path "/health" --health-check-protocol HTTP --region $AWSRegion --query "TargetGroups[0].TargetGroupArn" --output text
    Write-Host "✅ Target group created: $TGArn" -ForegroundColor Green
} catch {
    $TGArn = aws elbv2 describe-target-groups --names infinityai-engine-d-tg --query "TargetGroups[0].TargetGroupArn" --output text --region $AWSRegion
    Write-Host "Target group already exists: $TGArn" -ForegroundColor Yellow
}

# Step 12: Create listener
Write-Host "👂 Creating load balancer listener..." -ForegroundColor Blue
try {
    aws elbv2 create-listener --load-balancer-arn $ALBArn --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TGArn --region $AWSRegion 2>$null
    Write-Host "✅ Load balancer listener created" -ForegroundColor Green
} catch {
    Write-Host "Listener already exists" -ForegroundColor Yellow
}

# Step 13: Create ECS service
Write-Host "🚀 Creating ECS service..." -ForegroundColor Blue
$NetworkConfig = @{
    awsvpcConfiguration = @{
        subnets = @($Subnet1, $Subnet2)
        securityGroups = @($SecurityGroupId)
        assignPublicIp = "ENABLED"
    }
} | ConvertTo-Json -Depth 3

$LoadBalancerConfig = @(
    @{
        targetGroupArn = $TGArn
        containerName = "infinityai-engine-d"
        containerPort = 8000
    }
) | ConvertTo-Json -Depth 2

try {
    aws ecs create-service --cluster $ClusterName --service-name $ServiceName --task-definition $TaskFamily --desired-count 2 --launch-type FARGATE --network-configuration $NetworkConfig --load-balancers $LoadBalancerConfig --region $AWSRegion 2>$null
    Write-Host "✅ ECS service created successfully" -ForegroundColor Green
} catch {
    Write-Host "Service creation in progress or updating existing service" -ForegroundColor Yellow
}

# Get ALB DNS name for output
$ALBDNSName = aws elbv2 describe-load-balancers --names infinityai-engine-d-alb --query "LoadBalancers[0].DNSName" --output text --region $AWSRegion

# Clean up temporary files
Remove-Item -Path "task-execution-role-trust-policy.json" -ErrorAction SilentlyContinue
Remove-Item -Path "task-role-policy.json" -ErrorAction SilentlyContinue
Remove-Item -Path "task-definition.json" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🎉 Engine D AWS Deployment Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host "✅ DHAN Credentials: Securely stored in AWS Secrets Manager" -ForegroundColor Green
Write-Host "✅ Docker Image: ${ECRUri}:latest" -ForegroundColor Green
Write-Host "✅ ECS Cluster: $ClusterName" -ForegroundColor Green
Write-Host "✅ ECS Service: $ServiceName" -ForegroundColor Green
Write-Host "✅ Redis Cluster: infinityai-redis" -ForegroundColor Green
Write-Host "✅ Load Balancer: infinityai-engine-d-alb" -ForegroundColor Green
Write-Host "✅ Load Balancer DNS: $ALBDNSName" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Configure DNS: api.infinityai.pro -> $ALBDNSName" -ForegroundColor White
Write-Host "2. Set up SSL certificate" -ForegroundColor White
Write-Host "3. Deploy Azure frontend" -ForegroundColor White
Write-Host ""
Write-Host "📍 Engine D will be available at: http://$ALBDNSName" -ForegroundColor Cyan
Write-Host "🔐 DHAN API Integration: Ready with your credentials" -ForegroundColor Green

return @{
    Status = "Success"
    AccountId = $AccountId
    ECRUri = $ECRUri
    ALBDNSName = $ALBDNSName
    ClusterName = $ClusterName
    ServiceName = $ServiceName
}