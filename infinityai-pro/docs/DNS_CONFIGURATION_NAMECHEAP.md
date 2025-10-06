# 🌐 Namecheap DNS Configuration for InfinityAI.Pro

## Current Frontend URLs  
- **Azure Container App**: `https://infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io`
- **Target Custom Domain**: `infinityai.pro` and `www.infinityai.pro`
- **Status**: ✅ Frontend is WORKING and serving React app correctly!

## 📋 DNS Records to Add in Namecheap

### 1. Root Domain Configuration (Frontend)
```
Type: CNAME
Host: @
Value: infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io
TTL: 3600 (or Automatic)
```

### 2. WWW Subdomain Configuration (Frontend)
```
Type: CNAME  
Host: www
Value: infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io
TTL: 3600 (or Automatic)
```

### 3. API Subdomain Configuration (Backend API)
```
Type: CNAME
Host: api
Value: infinityai-app.agreeablemeadow-7375b1f7.eastus.azurecontainerapps.io
TTL: 3600 (or Automatic)
```

## 🛠️ Step-by-Step Instructions

### Step 1: Login to Namecheap
1. Go to https://namecheap.com
2. Login to your account
3. Navigate to **Domain List**
4. Click **Manage** next to your domain

### Step 2: Configure DNS
1. Go to **Advanced DNS** tab
2. **Delete** any existing A or CNAME records for `@` and `www`
3. **Add** the three CNAME records above

### Step 3: Azure Static Web App Configuration
1. Go to Azure Portal
2. Navigate to your Static Web App: `brave-ocean-09e85cd10-preview`
3. Go to **Custom domains**
4. Click **+ Add**
5. Add both:
   - `infinityai.pro`
   - `www.infinityai.pro`
6. Follow validation steps

### Step 4: SSL Certificate
Azure will automatically provision Let's Encrypt SSL certificates for your custom domains.

## ⏱️ Propagation Time
- DNS changes take **5-30 minutes** to propagate
- SSL certificate provisioning takes **2-24 hours**

## 🔍 Verification Commands
```bash
# Check DNS propagation
nslookup infinityai.pro
nslookup www.infinityai.pro

# Test connectivity
curl -I https://infinityai.pro
curl -I https://www.infinityai.pro
```

## 📋 Final URLs After Configuration
- **Frontend**: `https://infinityai.pro`
- **API**: `https://api.infinityai.pro`
- **Dashboard**: `https://infinityai.pro/dashboard`
- **Trading**: `https://infinityai.pro/trading`

## ⚠️ Important Notes
1. **Root Domain CNAME**: Some DNS providers don't support CNAME for root domain. If this fails, use A record with Azure Static Web App IP
2. **Backup Plan**: Keep Azure URL as backup until custom domain is fully working
3. **Update Frontend**: Update API configuration to use new custom domain