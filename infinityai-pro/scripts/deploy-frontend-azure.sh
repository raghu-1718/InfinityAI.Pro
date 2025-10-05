#!/bin/bash

# InfinityAI.Pro - Azure Frontend Deployment Script
# Deploy React frontend to Azure App Service with DHAN integration

set -e

echo "🚀 Starting Frontend (Azure React App) Deployment..."

# Configuration
RESOURCE_GROUP="infinityai-rg"
APP_NAME="infinityai-pro"
APP_SERVICE_PLAN="infinityai-plan"
LOCATION="eastus"
NODE_VERSION="18.x"
CUSTOM_DOMAIN="infinityai.pro"

echo "✅ Resource Group: $RESOURCE_GROUP"
echo "✅ App Name: $APP_NAME"
echo "✅ Location: $LOCATION"

# Step 1: Create Resource Group
echo "📦 Creating Azure Resource Group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION || echo "Resource group already exists"

# Step 2: Create App Service Plan
echo "💰 Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku S1 \
    --is-linux || echo "App service plan already exists"

# Step 3: Create Web App
echo "🌐 Creating Web App..."
az webapp create \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --runtime "NODE|${NODE_VERSION}" || echo "Web app already exists"

# Step 4: Configure app settings
echo "⚙️ Configuring app settings..."
az webapp config appsettings set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        NODE_VERSION="${NODE_VERSION}" \
        WEBSITE_NODE_DEFAULT_VERSION="${NODE_VERSION}" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        REACT_APP_API_BASE_URL="https://api.infinityai.pro" \
        REACT_APP_DHAN_REDIRECT_URI="https://infinityai.pro/auth/callback" \
        REACT_APP_DHAN_POSTBACK_URL="https://api.infinityai.pro/auth/dhan/postback" \
        REACT_APP_ENVIRONMENT="production"

# Step 5: Configure startup command
echo "🚀 Configuring startup command..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --startup-file "pm2 serve build --spa --port 8080"

# Step 6: Build and prepare frontend
echo "🔨 Building React frontend..."
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build

echo "✅ Frontend build completed"

# Step 7: Create deployment package
echo "📦 Creating deployment package..."
zip -r ../scripts/frontend-deployment.zip build/ package.json

cd ../scripts

# Step 8: Deploy to Azure
echo "🚀 Deploying to Azure App Service..."
az webapp deployment source config-zip \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --src frontend-deployment.zip

# Step 9: Configure custom domain (requires domain verification)
echo "🌍 Setting up custom domain..."
az webapp config hostname add \
    --webapp-name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --hostname $CUSTOM_DOMAIN || echo "Custom domain setup requires DNS verification - configure manually"

# Step 10: Enable HTTPS redirect
echo "🔐 Enabling HTTPS redirect..."
az webapp update \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --https-only true

# Step 11: Configure CORS for API calls
echo "🌐 Configuring CORS..."
az webapp cors add \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --allowed-origins "https://api.infinityai.pro" "https://localhost:3000"

# Step 12: Configure health check
echo "❤️ Setting up health check..."
az webapp config set \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --health-check-path "/"

# Clean up deployment files
rm -f frontend-deployment.zip

echo ""
echo "🎉 Frontend Azure Deployment Complete!"
echo "====================================="
echo "✅ Resource Group: $RESOURCE_GROUP"
echo "✅ Web App: $APP_NAME"
echo "✅ App Service Plan: $APP_SERVICE_PLAN"
echo "✅ Runtime: Node.js ${NODE_VERSION}"
echo "✅ HTTPS Redirect: Enabled"
echo ""
echo "🌐 App URLs:"
echo "Default: https://${APP_NAME}.azurewebsites.net"
echo "Custom: https://${CUSTOM_DOMAIN} (after DNS setup)"
echo ""
echo "🔗 Environment Variables Configured:"
echo "- REACT_APP_API_BASE_URL: https://api.infinityai.pro"
echo "- REACT_APP_DHAN_REDIRECT_URI: https://infinityai.pro/auth/callback"
echo "- REACT_APP_DHAN_POSTBACK_URL: https://api.infinityai.pro/auth/dhan/postback"
echo ""
echo "📋 Next Steps:"
echo "1. Configure DNS records in Namecheap:"
echo "   - A Record: infinityai.pro -> Azure App Service IP"
echo "   - CNAME: www.infinityai.pro -> ${APP_NAME}.azurewebsites.net"
echo "2. Verify custom domain in Azure Portal"
echo "3. Configure SSL certificate"
echo "4. Test DHAN OAuth integration"
echo ""
echo "🔐 DHAN API URLs (configured in frontend):"
echo "- Redirect URI: https://infinityai.pro/auth/callback"
echo "- Postback URL: https://api.infinityai.pro/auth/dhan/postback"