# 🌐 InfinityAI.Pro - Domain Verification and Mapping Guide

## ✅ Current Status

### Deployment Status
- **Frontend URL**: https://infinityai-frontend-bprmddefsa-uc.a.run.app
- **All Backend Engines**: ✅ HEALTHY (5/5)
- **Build Status**: ✅ SUCCESS with correct URLs

### DNS Configuration
- **Namecheap Nameservers**: ✅ Configured
  - ns-cloud-c1.googledomains.com
  - ns-cloud-c2.googledomains.com
  - ns-cloud-c3.googledomains.com
  - ns-cloud-c4.googledomains.com
- **GCP Cloud DNS Zone**: ✅ Created (infinityai-pro-zone)

---

## 🔍 Step 1: Verify Domain Ownership

### Option A: DNS TXT Record (Recommended)

1. **Get Verification Token**:
   ```powershell
   # Open Google Search Console
   Start-Process "https://search.google.com/search-console/welcome"
   ```

2. **Add Property**:
   - Select "Domain" property type
   - Enter: `infinityai.pro`
   - Click "Continue"

3. **Copy TXT Record** provided by Google (looks like):
   ```
   google-site-verification=abc123xyz456...
   ```

4. **Add to Cloud DNS**:
   ```powershell
   gcloud dns record-sets create infinityai.pro. `
     --rrdatas="google-site-verification=YOUR_TOKEN_HERE" `
     --type=TXT `
     --ttl=3600 `
     --zone=infinityai-pro-zone
   ```

5. **Verify** (after 5-10 minutes):
   ```powershell
   gcloud domains verify infinityai.pro
   ```

### Option B: HTML File Upload

1. Download verification HTML file from Google Search Console
2. Upload to Cloud Run service
3. Click "Verify" in Search Console

---

## 🗺️ Step 2: Create DNS Records

### A. Create Load Balancer IP (for Cloud Run)

Since Cloud Run doesn't provide static IPs directly, we need to use:

**Option 1: Use ghs.googlehosted.com (Recommended)**
```powershell
# Create CNAME for www
gcloud dns record-sets create www.infinityai.pro. `
  --rrdatas="ghs.googlehosted.com." `
  --type=CNAME `
  --ttl=300 `
  --zone=infinityai-pro-zone

# For root domain, we need domain mapping first
```

**Option 2: Create Global Load Balancer with Static IP**
```powershell
# Reserve static IP
gcloud compute addresses create infinityai-frontend-ip `
  --global `
  --ip-version=IPV4

# Get the IP
$STATIC_IP = gcloud compute addresses describe infinityai-frontend-ip --global --format="value(address)"

# Create A record
gcloud dns record-sets create infinityai.pro. `
  --rrdatas="$STATIC_IP" `
  --type=A `
  --ttl=300 `
  --zone=infinityai-pro-zone
```

---

## 🎯 Step 3: Create Cloud Run Domain Mapping

### After Domain Verification:

```powershell
# Map root domain
gcloud beta run domain-mappings create `
  --service=infinityai-frontend `
  --domain=infinityai.pro `
  --region=us-central1

# Map www subdomain
gcloud beta run domain-mappings create `
  --service=infinityai-frontend `
  --domain=www.infinityai.pro `
  --region=us-central1
```

### Verify Mapping:
```powershell
gcloud beta run domain-mappings list --region=us-central1
```

---

## 📋 Step 4: DNS Record Configuration

### Required DNS Records in Cloud DNS:

| Record Type | Name | Value | TTL | Purpose |
|------------|------|-------|-----|---------|
| **A** | @ | [Load Balancer IP] | 300 | Root domain |
| **CNAME** | www | ghs.googlehosted.com. | 300 | www subdomain |
| **TXT** | @ | google-site-verification=... | 3600 | Domain verification |

### Create Records:
```powershell
# After getting Cloud Run's recommended DNS records from domain mapping
gcloud dns record-sets list --zone=infinityai-pro-zone
```

---

## 🔐 Step 5: SSL Certificate (Automatic)

Google Cloud Run automatically provisions SSL certificates after:
1. ✅ Domain verification complete
2. ✅ DNS records pointing correctly
3. ⏳ DNS propagation (24-48 hours)

**Check Certificate Status**:
```powershell
gcloud beta run domain-mappings describe infinityai.pro --region=us-central1
```

---

## ✅ Step 6: Update OAuth Redirect URIs

### Update Dhan OAuth Configuration:

Once domain is live, update redirect URIs in:

1. **Dhan Developer Portal**:
   - Login: https://myaccount.dhan.co/developers
   - Update Redirect URI: `https://infinityai.pro/broker-integration`
   - Update Postback URL: `https://engine-c-prod-bprmddefsa-uc.a.run.app/dhan/postback`

2. **Update Frontend Code** (if needed):
   ```javascript
   // frontend/web/src/hooks/useDhanIntegration.js
   const FRONTEND_URL = 'https://infinityai.pro';
   ```

---

## 🧪 Step 7: Verification Commands

### Test DNS Propagation:
```powershell
# Check nameservers
Resolve-DnsName -Name infinityai.pro -Type NS

# Check A record
Resolve-DnsName -Name infinityai.pro -Type A

# Check CNAME
Resolve-DnsName -Name www.infinityai.pro -Type CNAME

# Check TXT
Resolve-DnsName -Name infinityai.pro -Type TXT
```

### Test HTTPS Access:
```powershell
# Test Cloud Run URL (current working URL)
curl https://infinityai-frontend-bprmddefsa-uc.a.run.app/health

# Test custom domain (after DNS propagation)
curl https://infinityai.pro/health
curl https://www.infinityai.pro/health
```

### Test Backend Connectivity:
```powershell
python verify_gcp_deployment.py
```

---

## 📊 Expected Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Domain Verification | 5-30 minutes | ⏳ Pending |
| DNS Propagation | 1-48 hours | ⏳ Pending |
| SSL Certificate | 15-60 minutes | ⏳ After DNS |
| Full Availability | 24-48 hours | ⏳ In Progress |

---

## 🚨 Troubleshooting

### Issue: Domain Not Verified
```powershell
# Re-check verification status
gcloud domains list-user-verified

# Verify TXT record exists
Resolve-DnsName -Name infinityai.pro -Type TXT

# Wait 10-15 minutes after adding TXT record
```

### Issue: SSL Certificate Pending
```powershell
# Check domain mapping status
gcloud beta run domain-mappings describe infinityai.pro --region=us-central1

# Verify DNS records
gcloud dns record-sets list --zone=infinityai-pro-zone
```

### Issue: 404 on Custom Domain
- Wait for DNS propagation
- Verify CNAME/A records point correctly
- Check domain mapping is active

---

## 🎯 Quick Start Commands

### Complete Setup Script:
```powershell
# 1. Verify domain (after adding TXT record in Google Search Console)
gcloud domains verify infinityai.pro

# 2. Get domain mapping DNS requirements
gcloud beta run domain-mappings create `
  --service=infinityai-frontend `
  --domain=infinityai.pro `
  --region=us-central1

# 3. Follow the DNS record instructions from output

# 4. Test after 24-48 hours
curl https://infinityai.pro
```

---

## 📞 Support Resources

- **Google Cloud DNS**: https://cloud.google.com/dns/docs
- **Cloud Run Custom Domains**: https://cloud.google.com/run/docs/mapping-custom-domains
- **Namecheap DNS**: https://www.namecheap.com/support/knowledgebase/article.aspx/767/10/how-to-change-dns-for-a-domain/
- **Google Search Console**: https://search.google.com/search-console

---

## ✅ Current Access

**Working URLs** (use these while DNS propagates):
- Frontend: https://infinityai-frontend-bprmddefsa-uc.a.run.app
- Engine A: https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app/health
- Engine B: https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app/health
- Engine C: https://engine-c-prod-bprmddefsa-uc.a.run.app/health
- Engine D: https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app/health
- Engine Ultra: https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app/health

**Target URLs** (after domain mapping):
- Production: https://infinityai.pro
- WWW: https://www.infinityai.pro

---

*Last Updated: January 2025*
*Frontend Build: ✅ Fixed with correct URLs*
*Deployment Status: ✅ All engines healthy*
