# 🔄 REMOVING SANDBOX & SETTING UP PRODUCTION CREDENTIALS

## 📋 **STEP 1: Remove Sandbox Configuration**

### **Azure Container App - Remove Sandbox Variables:**
```bash
# Remove sandbox-specific environment variables
az containerapp update \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --remove-env-vars \
    "DHAN_SANDBOX_MODE" \
    "DHAN_ENVIRONMENT" \
    "DHAN_SANDBOX_API_URL"
```

### **Update with Production Settings:**
```bash
# Set production Dhan configuration
az containerapp update \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --set-env-vars \
    "DHAN_API_BASE_URL=https://api.dhan.co" \
    "DHAN_ENVIRONMENT=production" \
    "DHAN_PRODUCTION_MODE=true"
```

---

## 🔑 **STEP 2: Production Credentials Setup**

### **Replace These Environment Variables:**
```bash
# You'll need to provide your REAL Dhan credentials:

DHAN_CLIENT_ID=YOUR_REAL_CLIENT_ID
DHAN_ACCESS_TOKEN=YOUR_REAL_ACCESS_TOKEN  
DHAN_API_BASE_URL=https://api.dhan.co
DHAN_ENVIRONMENT=production
```

### **Commands to Update Azure:**
```bash
# Run this with YOUR real credentials:
az containerapp update \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --set-env-vars \
    "DHAN_CLIENT_ID=YOUR_REAL_CLIENT_ID" \
    "DHAN_ACCESS_TOKEN=YOUR_REAL_ACCESS_TOKEN" \
    "DHAN_API_BASE_URL=https://api.dhan.co" \
    "DHAN_ENVIRONMENT=production" \
    "DHAN_PRODUCTION_MODE=true"
```

---

## 🛠️ **STEP 3: Fix Static Files Issue (White Screen)**

### **The Problem:**
- JS Bundle: `/static/js/main.1f9e330d.js` returns 404
- CSS Bundle: `/static/css/main.14addf7b.css` returns 404
- This causes the white screen in your browser

### **Solutions:**

#### **Option A: Update Container Image**
```bash
# If you have a newer image with static files:
az containerapp update \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --image infinityaiacr.azurecr.io/infinityai-app:latest
```

#### **Option B: Add Static File Mounting**
```bash
# If static files need to be mounted differently:
az containerapp update \
  --name infinityai-app \
  --resource-group infinityai-pro-rg \
  --set-env-vars "SERVE_STATIC_FILES=true" "STATIC_FILE_PATH=/app/static"
```

---

## 🌐 **STEP 4: Production URLs Configuration**

### **Update Webhook URLs for Production:**
```yaml
Production Postback URL:
https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/api/webhooks/dhan

Production Redirect URL:
https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/auth/dhan/callback
```

### **Update Dhan Developer Portal:**
1. Go to: https://web.dhan.co/developer/app
2. Switch from Sandbox to Production mode
3. Update URLs with production webhook/redirect URLs above
4. Get your production Client ID and Access Token

---

## 🧪 **STEP 5: Test Production Setup**

### **Test Commands:**
```bash
# Test production Dhan API (use YOUR real token):
curl -X GET "https://api.dhan.co/v2/holdings" \
  -H "access-token: YOUR_REAL_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Test your application:
curl "https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io/health"
```

---

## ✅ **WHAT YOU NEED TO PROVIDE:**

### **From Dhan Production Portal:**
1. **Production Client ID**: (instead of sandbox 2508215064)
2. **Production Access Token**: (instead of sandbox token)
3. **Confirm webhook URLs**: Are set to your Azure app URLs

### **Your Real Credentials Format:**
```
Production Client ID: [YOUR_REAL_ID]
Production Access Token: [YOUR_REAL_TOKEN]
```

---

## 🎯 **IMMEDIATE NEXT STEPS:**

1. **Provide your real Dhan production credentials**
2. **I'll update Azure Container App with production settings**
3. **We'll test the production Dhan API connection**
4. **Fix the static files issue to resolve white screen**
5. **Your app will be ready for live trading**

**Please share your production Dhan Client ID and Access Token, and I'll complete the setup!** 🚀