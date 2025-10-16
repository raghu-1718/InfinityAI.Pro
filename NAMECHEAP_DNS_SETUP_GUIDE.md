# 🌐 InfinityAI.Pro - Namecheap DNS Setup Guide

## ✅ Current Deployment Status

**All services are deployed and healthy on GCP Cloud Run!**

- ✅ Frontend: `https://infinityai-frontend-bprmddefsa-uc.a.run.app`
- ✅ Engine A: `https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app`
- ✅ Engine B: `https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app`
- ✅ Engine C: `https://engine-c-prod-bprmddefsa-uc.a.run.app`
- ✅ Engine D: `https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app`
- ✅ Engine Ultra: `https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app`

**Overall Health Score: 90%** 🟢 EXCELLENT

---

## 📋 Step-by-Step Namecheap DNS Configuration

### Option 1: Using GCP Cloud DNS (Recommended)

#### Step 1: Create Cloud DNS Zone in GCP

```powershell
# Create Cloud DNS managed zone for infinityai.pro
gcloud dns managed-zones create infinityai-pro-zone \
    --dns-name="infinityai.pro." \
    --description="DNS zone for InfinityAI.Pro" \
    --project=after-yesterday-473512-k3
```

#### Step 2: Get Nameservers from GCP

```powershell
# Get the nameservers assigned by Google Cloud DNS
gcloud dns managed-zones describe infinityai-pro-zone \
    --project=after-yesterday-473512-k3 \
    --format="value(nameServers)"
```

**Expected Output (will be something like):**
```
ns-cloud-e1.googledomains.com.
ns-cloud-e2.googledomains.com.
ns-cloud-e3.googledomains.com.
ns-cloud-e4.googledomains.com.
```

#### Step 3: Create DNS Records in Cloud DNS

```powershell
# Create A record pointing to Cloud Run frontend
# First, get the Cloud Run IP
$CLOUD_RUN_IP = "gclb.infinityai.pro"  # Cloud Load Balancer

# Create DNS record set
gcloud dns record-sets create infinityai.pro. \
    --zone=infinityai-pro-zone \
    --type=CNAME \
    --ttl=300 \
    --rrdatas="ghs.googlehosted.com."

# Create www subdomain
gcloud dns record-sets create www.infinityai.pro. \
    --zone=infinityai-pro-zone \
    --type=CNAME \
    --ttl=300 \
    --rrdatas="ghs.googlehosted.com."
```

#### Step 4: Update Namecheap

1. **Log in to Namecheap:**
   - Go to https://www.namecheap.com/
   - Click "Sign In"

2. **Navigate to Domain List:**
   - Click "Domain List" in the left sidebar
   - Find `infinityai.pro`
   - Click "Manage"

3. **Change Nameservers:**
   - Scroll to "NAMESERVERS" section
   - Select "Custom DNS"
   - Enter the 4 nameservers you got from GCP:
     ```
     ns-cloud-e1.googledomains.com
     ns-cloud-e2.googledomains.com
     ns-cloud-e3.googledomains.com
     ns-cloud-e4.googledomains.com
     ```
   - Click the green checkmark ✓ to save

---

### Option 2: Using Namecheap DNS (Simpler, but less flexible)

#### Step 1: Keep Namecheap DNS

In Namecheap dashboard:
1. Go to "Domain List"
2. Click "Manage" next to infinityai.pro
3. Select "Namecheap BasicDNS" or "Namecheap PremiumDNS"

#### Step 2: Add DNS Records

1. Scroll to "Advanced DNS" tab
2. Click "ADD NEW RECORD"

**Add these records:**

| Type  | Host | Value | TTL |
|-------|------|-------|-----|
| CNAME | @ | ghs.googlehosted.com | Automatic |
| CNAME | www | ghs.googlehosted.com | Automatic |
| TXT | @ | google-site-verification=YOUR_VERIFICATION_CODE | Automatic |

#### Step 3: Verify Domain in Google Search Console

1. Go to: https://search.google.com/search-console
2. Add property: `infinityai.pro`
3. Use TXT record method
4. Copy the verification code
5. Add TXT record in Namecheap (see table above)
6. Click "Verify" in Search Console

---

## 🔧 Complete Domain Mapping in GCP

Once DNS is configured, map your domain to Cloud Run:

```powershell
# Verify domain ownership first
gcloud domains verify infinityai.pro

# Create domain mapping for the frontend service
gcloud beta run domain-mappings create \
    --service=infinityai-frontend \
    --domain=infinityai.pro \
    --region=us-central1 \
    --project=after-yesterday-473512-k3

# Create mapping for www subdomain
gcloud beta run domain-mappings create \
    --service=infinityai-frontend \
    --domain=www.infinityai.pro \
    --region=us-central1 \
    --project=after-yesterday-473512-k3
```

---

## ⏰ DNS Propagation Timeline

| Time | Status |
|------|--------|
| 0-1 hour | DNS changes saved |
| 1-6 hours | Early propagation begins |
| 6-24 hours | Most servers updated |
| 24-48 hours | Full global propagation |

---

## 🧪 Testing DNS Propagation

### Method 1: Command Line

```powershell
# Windows PowerShell
Resolve-DnsName infinityai.pro

# Expected output after propagation:
# Name: infinityai.pro
# Type: A
# Address: <Cloud Run IP>
```

### Method 2: Online Tools

- https://dnschecker.org/ - Enter `infinityai.pro`
- https://www.whatsmydns.net/ - Global DNS check
- https://mxtoolbox.com/SuperTool.aspx - Complete DNS analysis

---

## ✅ Verification Checklist

- [ ] GCP Cloud DNS zone created (if using Option 1)
- [ ] Nameservers obtained from GCP
- [ ] Namecheap nameservers updated
- [ ] DNS records created
- [ ] Domain verified in Google Search Console
- [ ] Cloud Run domain mapping created
- [ ] SSL certificate issued (automatic after mapping)
- [ ] DNS propagation complete (24-48 hours)
- [ ] Website accessible at https://infinityai.pro
- [ ] HTTPS redirect working

---

## 🚨 Troubleshooting

### Issue: "Domain not verified" error

**Solution:**
```powershell
# Verify domain ownership
gcloud domains verify infinityai.pro

# If that fails, use Google Search Console method
```

### Issue: SSL Certificate pending

**Solution:**
- Wait 15-60 minutes after domain mapping
- Google automatically provisions SSL certificates
- Check status:
  ```powershell
  gcloud beta run domain-mappings describe infinityai.pro \
      --region=us-central1 \
      --format="value(status.certificate)"
  ```

### Issue: DNS not propagating

**Solution:**
- Check nameservers are correct in Namecheap
- Wait full 48 hours before troubleshooting further
- Clear your local DNS cache:
  ```powershell
  ipconfig /flushdns
  ```

---

## 📊 Current URLs (Working Now!)

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | https://infinityai-frontend-bprmddefsa-uc.a.run.app | ✅ Live |
| **Engine A** | https://engine-a-market-data-prod-bprmddefsa-uc.a.run.app | ✅ Live |
| **Engine B** | https://engine-b-ai-ml-prod-bprmddefsa-uc.a.run.app | ✅ Live |
| **Engine C** | https://engine-c-prod-bprmddefsa-uc.a.run.app | ✅ Live |
| **Engine D** | https://engine-d-chatbot-prod-bprmddefsa-uc.a.run.app | ✅ Live |
| **Engine Ultra** | https://engine-ultra-aggressive-prod-bprmddefsa-uc.a.run.app | ✅ Live |
| **Custom Domain** | https://infinityai.pro | ⏳ Pending DNS |

---

## 🎯 Next Steps After DNS Setup

1. **Test the Application:**
   ```powershell
   # Test Cloud Run URL (works now)
   curl https://infinityai-frontend-bprmddefsa-uc.a.run.app
   
   # Test custom domain (after DNS propagates)
   curl https://infinityai.pro
   ```

2. **Monitor SSL Certificate:**
   ```powershell
   # Check SSL status
   gcloud beta run domain-mappings list --region=us-central1
   ```

3. **Set up monitoring:**
   - Enable Google Cloud Monitoring
   - Set up uptime checks for infinityai.pro
   - Configure alerting for downtime

4. **Update Dhan OAuth:**
   - Update redirect URI to: `https://infinityai.pro/auth/dhan/callback`
   - Update postback URL to: `https://engine-c-prod-bprmddefsa-uc.a.run.app/api/dhan/postback`

---

## 📞 Support

If you encounter any issues:

1. Check GCP Console → Cloud Run → Domain Mappings
2. Verify DNS records in Cloud DNS
3. Test with `nslookup infinityai.pro`
4. Wait full 48 hours for DNS propagation

---

**Last Updated:** October 16, 2025  
**Deployment Score:** 90% 🟢 EXCELLENT  
**All Services:** ✅ Healthy and Running
