# InfinityAI.Pro Azure Static Web App Deployment Fix
# Run these commands to redeploy your frontend

# 1. Check current Static Web Apps
az staticwebapp list --output table

# 2. Delete the broken Static Web App (if exists)
az staticwebapp delete --name brave-ocean-09e85cd10 --resource-group infinityai-rg --yes

# 3. Create new Static Web App
az staticwebapp create \
  --name infinityai-frontend-prod \
  --resource-group infinityai-rg \
  --source ./infinityai-pro/frontend \
  --location centralus \
  --branch main \
  --app-location "/" \
  --output-location "build"

# 4. Get the new URL
az staticwebapp show --name infinityai-frontend-prod --resource-group infinityai-rg --query "defaultHostname" --output tsv

# 5. Update custom domain (if you have one)
# az staticwebapp hostname set --hostname infinityai.pro --name infinityai-frontend-prod --resource-group infinityai-rg

echo "✅ Azure Static Web App deployment commands ready"
echo "Run these commands in order to fix your frontend deployment"