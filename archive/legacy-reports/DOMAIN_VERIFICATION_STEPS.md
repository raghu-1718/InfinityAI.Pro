# 🔐 Domain Verification for Cloud Run - Complete Guide

## ✅ Current Status
- **Domain**: infinityai.pro
- **Google Search Console**: ✅ VERIFIED
- **GCP Cloud Run**: ❌ NOT VERIFIED (blocking domain mapping)
- **Google Account**: raghu42620@gmail.com

---

## 🎯 Problem
Google Search Console verification is **separate** from GCP Webmaster Central verification. Cloud Run requires the domain to be verified in **GCP Webmaster Central** (legacy system).

---

## 📋 Solution: Verify Domain in GCP Webmaster Central

### Step 1: Visit GCP Webmaster Central
Open this URL in your browser (make sure you're logged in as `raghu42620@gmail.com`):

```
https://www.google.com/webmasters/verification/home?hl=en
```

Or run this command:
```powershell
Start-Process "https://www.google.com/webmasters/verification/home?hl=en"
```

### Step 2: Add Your Domain
1. Click **"Add a property"** or **"Add a site"**
2. Enter: `infinityai.pro`
3. Click **"Continue"**

### Step 3: Verify Using DNS TXT Record
The verification should use the **SAME TXT record** you already added:
```
google-site-verification=sK-PGV-ADsn6B4m5FrWAVa6qhz4zp1C8Tw1fWZpCS9c
```

✅ **This record is ALREADY in your GCP Cloud DNS**, so verification should be instant!

### Step 4: Confirm Verification
After verifying, run this command to check:
```powershell
gcloud domains list-user-verified
```

You should see `infinityai.pro` in the list.

---

## 🔄 Alternative Method: Use Load Balancer with SSL

If Webmaster Central verification doesn't work, we can use an alternative approach with a Global Load Balancer:

### Option A: Cloud Load Balancer (More Complex, Full SSL Control)
1. Create a global static IP
2. Create a load balancer pointing to Cloud Run
3. Add SSL certificate
4. Point DNS A record to the static IP

### Option B: Firebase Hosting (Easiest)
1. Set up Firebase Hosting
2. Rewrite rules to Cloud Run
3. Firebase handles domain verification automatically
4. Free SSL certificate included

---

## 🚀 Quick Commands

### Check if domain is verified in GCP:
```powershell
gcloud domains list-user-verified
```

### After verification, create domain mapping:
```powershell
# For root domain
gcloud beta run domain-mappings create `
  --service=infinityai-frontend `
  --domain=infinityai.pro `
  --region=us-central1

# For www subdomain
gcloud beta run domain-mappings create `
  --service=infinityai-frontend `
  --domain=www.infinityai.pro `
  --region=us-central1
```

### List existing domain mappings:
```powershell
gcloud beta run domain-mappings list --region=us-central1
```

---

## 📊 Verification Checklist

- [x] ✅ Domain purchased and owned (Namecheap)
- [x] ✅ Nameservers updated to GCP Cloud DNS
- [x] ✅ TXT record added to DNS
- [x] ✅ Google Search Console verified
- [ ] ⏳ GCP Webmaster Central verified
- [ ] ⏳ Domain mapping created
- [ ] ⏳ DNS A/CNAME records configured
- [ ] ⏳ SSL certificate provisioned (automatic)

---

## 🆘 Troubleshooting

### Issue: "Domain not verified for current account"
**Solution**: Verify domain in GCP Webmaster Central (not just Search Console)
- URL: https://www.google.com/webmasters/verification/home

### Issue: TXT record not found
**Solution**: The record exists, just wait 5-10 minutes for propagation
```powershell
# Check if TXT record is visible
Resolve-DnsName -Name infinityai.pro -Type TXT
```

### Issue: Different Google account
**Solution**: Make sure you're using `raghu42620@gmail.com` everywhere:
- GCP Console
- Google Search Console  
- GCP Webmaster Central

---

## 📞 Next Steps

1. **Immediate**: Visit Webmaster Central and verify domain
   - https://www.google.com/webmasters/verification/home
   
2. **After verification**: Run domain mapping command
   
3. **After mapping**: Add DNS records provided by Cloud Run

4. **Wait**: 15-60 minutes for SSL certificate provisioning

5. **Test**: Visit https://infinityai.pro

---

## 🎯 Expected Timeline

| Step | Duration | Status |
|------|----------|--------|
| Webmaster Central Verification | 5 minutes | ⏳ Pending |
| Domain Mapping Creation | 2 minutes | ⏳ Pending |
| DNS Record Configuration | 5 minutes | ⏳ Pending |
| SSL Certificate Provisioning | 15-60 minutes | ⏳ Pending |
| Full DNS Propagation | 4-8 hours | ⏳ Pending |

---

*Last Updated: October 16, 2025*
*Account: raghu42620@gmail.com*
*Project: after-yesterday-473512-k3*
