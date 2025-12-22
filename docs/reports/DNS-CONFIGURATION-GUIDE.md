# DNS Configuration Guide for Custom Domains

**Issue:** Custom domains (*.infinityai.pro) return `ERR_NAME_NOT_RESOLVED`  
**Root Cause:** DNS records not configured in domain registrar  
**Status:** Domain mappings exist in GCP but DNS doesn't point to them

---

## Current Situation

### ✅ What's Working
- All 3 Cloud Run services are deployed and operational
- Services accessible via Cloud Run URLs:
  - `infinityai-engine-a-429140669077.us-central1.run.app`
  - `infinityai-engine-b-429140669077.us-central1.run.app`
  - `infinityai-engine-c-execution-429140669077.us-central1.run.app`
- Frontend deployed to Firebase Hosting
- Domain mappings created in GCP Cloud Run

### ❌ What's Not Working
- `engine-a.infinityai.pro` - ERR_NAME_NOT_RESOLVED
- `engine-b.infinityai.pro` - ERR_NAME_NOT_RESOLVED
- `engine-c.infinityai.pro` - ERR_NAME_NOT_RESOLVED
- `infinityai.pro` - May or may not resolve depending on DNS setup

---

## Why Custom Domains Don't Work

When you create a domain mapping in Google Cloud Run:
1. ✅ GCP creates the mapping configuration
2. ✅ GCP generates SSL certificates
3. ✅ GCP provides DNS record requirements
4. ❌ **YOU** must add DNS records to your domain registrar
5. ❌ DNS propagation must complete (24-48 hours)

**Current Problem:** Step 4 is not done. Your domain registrar doesn't know to point `engine-a.infinityai.pro` to Google's servers.

---

## Solution Options

### Option 1: Use Cloud Run URLs (CURRENT - WORKING)

**Status:** ✅ Implemented  
**Pros:** Works immediately, no DNS configuration needed  
**Cons:** Long ugly URLs

Frontend is currently configured to use:
```
https://infinityai-engine-a-429140669077.us-central1.run.app
https://infinityai-engine-b-429140669077.us-central1.run.app
https://infinityai-engine-c-execution-429140669077.us-central1.run.app
https://gen-lang-client-0779271931.web.app
```

These URLs work right now and your application is accessible.

### Option 2: Configure DNS Records (REQUIRES DOMAIN ACCESS)

**Status:** ⏳ Pending DNS configuration  
**Pros:** Clean custom domains  
**Cons:** Requires domain registrar access, 24-48 hours propagation

---

## How to Configure DNS (Option 2)

### Step 1: Get Required DNS Records from GCP

Run these commands to get the exact DNS records GCP requires:

```powershell
# For Engine A
gcloud beta run domain-mappings describe engine-a.infinityai.pro `
  --region=us-central1 `
  --project=gen-lang-client-0779271931 `
  --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)"

# For Engine B
gcloud beta run domain-mappings describe engine-b.infinityai.pro `
  --region=us-central1 `
  --project=gen-lang-client-0779271931 `
  --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)"

# For Engine C
gcloud beta run domain-mappings describe engine-c.infinityai.pro `
  --region=us-central1 `
  --project=gen-lang-client-0779271931 `
  --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)"

# For main domain (if mapped)
gcloud beta run domain-mappings describe infinityai.pro `
  --region=us-central1 `
  --project=gen-lang-client-0779271931 `
  --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)"
```

### Step 2: Expected DNS Record Format

GCP will typically provide records like:

```
Type: A
Name: engine-a
Value: 216.239.32.21 (example IP - use actual from GCP)

Type: AAAA
Name: engine-a
Value: 2001:4860:4802:32::15 (example IPv6 - use actual from GCP)

Type: CNAME
Name: engine-a
Value: ghs.googlehosted.com.
```

### Step 3: Add Records to Your Domain Registrar

**Where you bought infinityai.pro**, go to DNS management and add:

#### For GoDaddy:
1. Login to GoDaddy
2. Go to "My Products"
3. Click "DNS" next to infinityai.pro
4. Click "Add" for each record
5. Enter Type, Name, Value from GCP output
6. Save all records

#### For Cloudflare:
1. Login to Cloudflare
2. Select infinityai.pro domain
3. Go to "DNS" tab
4. Click "Add record"
5. Enter Type, Name, Value from GCP output
6. Set Proxy status to "DNS only" (gray cloud)
7. Save all records

#### For Namecheap:
1. Login to Namecheap
2. Go to Domain List
3. Click "Manage" next to infinityai.pro
4. Go to "Advanced DNS" tab
5. Add each record from GCP output
6. Save changes

#### For Google Domains:
1. Login to Google Domains
2. Select infinityai.pro
3. Click "DNS" in left menu
4. Scroll to "Custom resource records"
5. Add each record from GCP output
6. Click "Add"

### Step 4: Verify DNS Propagation

After adding records, wait 15 minutes to 48 hours for propagation.

Check status with:
```powershell
# Check if DNS resolves
nslookup engine-a.infinityai.pro 8.8.8.8
nslookup engine-b.infinityai.pro 8.8.8.8
nslookup engine-c.infinityai.pro 8.8.8.8

# Check domain mapping status
gcloud beta run domain-mappings describe engine-a.infinityai.pro `
  --region=us-central1 `
  --project=gen-lang-client-0779271931
```

Look for `status.conditions[0].status: True` which means it's ready.

### Step 5: Update Frontend to Use Custom Domains

Once DNS propagates (Status shows True), update frontend:

```powershell
cd C:\workspace\InfinityAI.Pro

# Update URLs in frontend
$content = Get-Content "frontend/web/index.html" -Raw
$content = $content -replace 'https://infinityai-engine-a-429140669077\.us-central1\.run\.app', 'https://engine-a.infinityai.pro'
$content = $content -replace 'https://infinityai-engine-b-429140669077\.us-central1\.run\.app', 'https://engine-b.infinityai.pro'
$content = $content -replace 'https://infinityai-engine-c-execution-429140669077\.us-central1\.run\.app', 'https://engine-c.infinityai.pro'
Set-Content "frontend/web/index.html" -Value $content -NoNewline

# Deploy
cd frontend/web
firebase deploy --only hosting --project gen-lang-client-0779271931

# Commit
cd ../..
git add frontend/web/index.html
git commit -m "feat: Update frontend to use custom domains (DNS configured)"
git push origin feature/3-engine-architecture
```

---

## Troubleshooting

### Custom domains still don't work after 48 hours?

1. **Check DNS records are correct:**
   ```powershell
   nslookup engine-a.infinityai.pro
   ```
   Should return an IP address, not "can't find"

2. **Verify domain ownership in GCP:**
   ```powershell
   gcloud domains list-user-verified --project=gen-lang-client-0779271931
   ```
   infinityai.pro should be listed

3. **Check Cloud Run domain mapping status:**
   ```powershell
   gcloud beta run domain-mappings list --region=us-central1 --project=gen-lang-client-0779271931
   ```
   Look for "Ready: True"

4. **Check SSL certificate status:**
   Certificates can take up to 24 hours to provision after DNS propagates

### ERR_SSL_VERSION_OR_CIPHER_MISMATCH?

- Certificate is provisioning (wait 1-24 hours after DNS propagates)
- Try accessing via http:// first, then https://

### Certificate errors?

- GCP auto-provisions certificates
- Takes 15 minutes to 24 hours after DNS propagates
- Check status in GCP Console → Cloud Run → Domain Mappings

---

## Current DNS Configuration Status

**Last Checked:** November 27, 2025

| Domain | DNS Configured? | Status |
|--------|----------------|--------|
| engine-a.infinityai.pro | ❌ No | ERR_NAME_NOT_RESOLVED |
| engine-b.infinityai.pro | ❌ No | ERR_NAME_NOT_RESOLVED |
| engine-c.infinityai.pro | ❌ No | ERR_NAME_NOT_RESOLVED |
| infinityai.pro | ❓ Unknown | Not tested |

---

## Quick Reference

### Working URLs (Use These Now)
```
Engine A: https://infinityai-engine-a-429140669077.us-central1.run.app/docs
Engine B: https://infinityai-engine-b-429140669077.us-central1.run.app/docs
Engine C: https://infinityai-engine-c-execution-429140669077.us-central1.run.app/docs
Frontend: https://gen-lang-client-0779271931.web.app
```

### Target URLs (After DNS Configuration)
```
Engine A: https://engine-a.infinityai.pro/docs
Engine B: https://engine-b.infinityai.pro/docs
Engine C: https://engine-c.infinityai.pro/docs
Frontend: https://infinityai.pro (requires additional mapping)
```

---

## Next Steps

1. **Immediate (DONE):** Use Cloud Run URLs - Application is accessible now
2. **When ready:** Add DNS records in domain registrar
3. **After DNS propagates:** Update frontend to use custom domains
4. **Optional:** Set up infinityai.pro for frontend (requires Firebase custom domain setup)

---

## Support

- GCP Cloud Run DNS Configuration: https://cloud.google.com/run/docs/mapping-custom-domains
- Firebase Custom Domain: https://firebase.google.com/docs/hosting/custom-domain
- DNS Propagation Check: https://dnschecker.org

---

**Summary:** Your application works perfectly with Cloud Run URLs. Custom domains require DNS configuration in your domain registrar, which you can do whenever you have access to the domain's DNS management panel.
