# InfinityAI.Pro API Keys Setup Script
# Run this after getting each API key

Write-Host "🚀 InfinityAI.Pro API Keys Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Function to set Railway variable
function Set-RailwayVar {
    param($Name, $Value)
    if ($Value -and $Value -ne "your_key_here") {
        Write-Host "Setting $Name..." -ForegroundColor Green
        railway variables --set "${Name}=${Value}"
    } else {
        Write-Host "Skipping $Name (no value provided)" -ForegroundColor Yellow
    }
}

# Add your API keys here as you get them:
$ALPHA_VANTAGE_KEY = "your_key_here"
$PINECONE_API_KEY = "your_key_here"
$AZURE_OPENAI_KEY = "your_key_here"
$AZURE_OPENAI_ENDPOINT = "your_endpoint_here"
$AWS_ACCESS_KEY_ID = "your_key_here"
$AWS_SECRET_ACCESS_KEY = "your_key_here"
$AZURE_STORAGE_CONNECTION_STRING = "your_connection_string_here"

# Set the variables
Set-RailwayVar "ALPHA_VANTAGE_API_KEY" $ALPHA_VANTAGE_KEY
Set-RailwayVar "PINECONE_API_KEY" $PINECONE_API_KEY
Set-RailwayVar "AZURE_OPENAI_KEY" $AZURE_OPENAI_KEY
Set-RailwayVar "AZURE_OPENAI_ENDPOINT" $AZURE_OPENAI_ENDPOINT
Set-RailwayVar "AWS_ACCESS_KEY_ID" $AWS_ACCESS_KEY_ID
Set-RailwayVar "AWS_SECRET_ACCESS_KEY" $AWS_SECRET_ACCESS_KEY
Set-RailwayVar "AZURE_STORAGE_CONNECTION_STRING" $AZURE_STORAGE_CONNECTION_STRING

Write-Host "✅ Setup complete! Run 'railway up' to deploy with new keys." -ForegroundColor Green