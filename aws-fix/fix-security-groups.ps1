# Fix Security Groups for Engine C and D
$sgId = "sg-0bd6d3c8f36d085f1"
$region = "us-east-1"

Write-Host "🔧 Fixing Security Group Rules..." -ForegroundColor Yellow

# Add inbound rules for Engine C (port 8000) and Engine D (port 8004)
aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $region
aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 8004 --cidr 0.0.0.0/0 --region $region
aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $region
aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $region

Write-Host "✅ Security group rules added!" -ForegroundColor Green