# Configure environment variables and secrets across clouds for InfinityAI.Pro
# This script writes a .env template locally and prints commands to store secrets in AWS, Azure, and GCP.

param(
    [string]$AwsRegion = "us-east-1",
    [string]$AzureKeyVault = "",
    [string]$GcpProject = ""
)

$envTemplate = @"
# InfinityAI.Pro Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Core services
KAFKA_BOOTSTRAP_SERVERS=broker:9092
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@db:5432/infinityai
JWT_SECRET_KEY=replace_me
ENCRYPTION_KEY=replace_me

# External APIs
ALPHA_VANTAGE_API_KEY=replace_me
YAHOO_FINANCE_API_KEY=replace_me
OPENAI_API_KEY=replace_me
DHAN_CLIENT_ID=replace_me
DHAN_API_KEY=replace_me
DHAN_API_SECRET=replace_me
DHAN_ACCESS_TOKEN=replace_me

# Ultra Aggressive
ULTRA_AGGRESSIVE_MODE=false
RISK_PER_TRADE=0.25
"@

$envPath = Join-Path (Get-Location) ".env.template"
$envTemplate | Out-File -FilePath $envPath -Encoding UTF8
Write-Host "✅ Wrote .env template to $envPath" -ForegroundColor Green

Write-Host "\nAWS Secrets Manager commands (update values before running):" -ForegroundColor Cyan
$awsDhanJson = '{"""client_id""":"""...""","""api_key""":"""...""","""api_secret""":"""...""","""access_token""":"""..."""}'
@(
    "aws secretsmanager create-secret --name infinityai/JWT_SECRET_KEY --secret-string 'replace_me' --region $AwsRegion",
    "aws secretsmanager create-secret --name infinityai/ENCRYPTION_KEY --secret-string 'replace_me' --region $AwsRegion",
    "aws secretsmanager create-secret --name infinityai/DATABASE_URL --secret-string 'postgresql://...' --region $AwsRegion",
    "aws secretsmanager create-secret --name infinityai/OPENAI_API_KEY --secret-string 'sk-...' --region $AwsRegion",
    "aws secretsmanager create-secret --name infinityai/DHAN --secret-string '$awsDhanJson' --region $AwsRegion"
) | ForEach-Object { Write-Host $_ }

if ($AzureKeyVault) {
    Write-Host "\nAzure Key Vault commands:" -ForegroundColor Cyan
    $azDhanJson = '{"""client_id""":"""...""","""api_key""":"""...""","""api_secret""":"""...""","""access_token""":"""..."""}'
    @(
        "az keyvault secret set --vault-name $AzureKeyVault --name JWT-SECRET-KEY --value 'replace_me'",
        "az keyvault secret set --vault-name $AzureKeyVault --name ENCRYPTION-KEY --value 'replace_me'",
        "az keyvault secret set --vault-name $AzureKeyVault --name DATABASE-URL --value 'postgresql://...'",
