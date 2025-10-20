# DNS Configuration Verification Guide

## Current Status (as of October 21, 2025)

### ✅ Working
- **infinityai.pro** (apex) - SSL Active, endpoint accessible

### ⏳ Pending DNS Propagation
- **api.infinityai.pro** - Waiting for CNAME propagation
- **engine.infinityai.pro** - Waiting for CNAME propagation

---

## Required DNS Records in Namecheap

Please verify these exact records are configured in your Namecheap Advanced DNS settings:

### For Apex Domain (infinityai.pro) ✅
Already working - A and AAAA records are active

### For API Subdomain (api.infinityai.pro) ⏳
```
Type: CNAME Record
Host: api
Value: ghs.googlehosted.com.
TTL: Automatic (or 300)
```

### For Engine Subdomain (engine.infinityai.pro) ⏳
```
Type: CNAME Record
Host: engine
Value: ghs.googlehosted.com.
TTL: Automatic (or 300)
```

---

## How to Verify in Namecheap

1. **Login to Namecheap**
   - Go to https://www.namecheap.com
   - Sign in to your account

2. **Access Domain Management**
   - Click "Domain List" in the left sidebar
   - Find `infinityai.pro`
   - Click "Manage"

3. **Check Advanced DNS**
   - Click the "Advanced DNS" tab
   - Look for the CNAME records

4. **Expected Configuration**
   ```
   Type          Host      Value                      TTL
   ────────────────────────────────────────────────────────
   CNAME Record  api       ghs.googlehosted.com.      Automatic
   CNAME Record  engine    ghs.googlehosted.com.      Automatic
   ```

---

## Common Issues & Solutions

### Issue 1: CNAME Value Formatting
**Problem:** Namecheap might strip the trailing dot  
**Solution:** 
- Try both: `ghs.googlehosted.com.` (with dot) and `ghs.googlehosted.com` (without dot)
- Namecheap usually handles this automatically

### Issue 2: Host Field
**Problem:** Entering full domain instead of just subdomain  
**Correct:**
- ✅ Host: `api`
- ✅ Host: `engine`

**Incorrect:**
- ❌ Host: `api.infinityai.pro`
- ❌ Host: `engine.infinityai.pro`

### Issue 3: Conflicting Records
**Problem:** Existing A, AAAA, or other CNAME records for same host  
**Solution:** 
- Delete any existing `api` or `engine` records before adding CNAME
- Only ONE record type per host name

### Issue 4: TTL Settings
**Problem:** Very high TTL delays propagation  
**Solution:**
- Use "Automatic" or set to 300 seconds (5 minutes)
- Lower TTL = faster propagation

---

## DNS Propagation Timeline

| Time Frame | Expected Status |
|------------|----------------|
| 0-5 min    | Records saved in Namecheap |
| 5-15 min   | DNS starts propagating |
| 15-30 min  | Most resolvers see new records |
| 30-60 min  | Full global propagation |

---

## Testing DNS Propagation

### Option 1: Using PowerShell (Recommended)
```powershell
# Test with Google DNS
nslookup api.infinityai.pro 8.8.8.8
nslookup engine.infinityai.pro 8.8.8.8

# Test with Cloudflare DNS
nslookup api.infinityai.pro 1.1.1.1
nslookup engine.infinityai.pro 1.1.1.1
```

**What to look for:**
- ✅ Success: Shows `canonical name = ghs.googlehosted.com`
- ❌ Not ready: Shows `can't find` or `Non-existent domain`

### Option 2: Online DNS Checker
Visit: https://www.whatsmydns.net/
- Enter: `api.infinityai.pro`
- Select: `CNAME` record type
- Check multiple locations worldwide

### Option 3: Run Verification Script
```powershell
.\scripts\verify_dns_and_ssl.ps1
```

---

## Once DNS Propagates

### Automatic Process
1. ✅ DNS CNAME records become visible globally
2. ⏳ Google Cloud Run detects DNS propagation
3. ⏳ SSL certificate provisioning begins automatically
4. ⏳ SSL challenges complete (can take up to 24 hours)
5. ✅ Domain mapping becomes ACTIVE
6. ✅ HTTPS endpoints become accessible

### Manual Verification
```powershell
# Check SSL status
gcloud beta run domain-mappings describe api.infinityai.pro --region=us-central1 --project=infinity-ai-5ec7c
gcloud beta run domain-mappings describe engine.infinityai.pro --region=us-central1 --project=infinity-ai-5ec7c

# Test endpoints (once SSL is active)
curl https://api.infinityai.pro/health
curl https://engine.infinityai.pro/health
```

---

## Screenshot Checklist for Namecheap

When you check your Namecheap DNS settings, verify:

- [ ] Two CNAME records exist (api and engine)
- [ ] Host field shows just `api` (not full domain)
- [ ] Host field shows just `engine` (not full domain)
- [ ] Value is `ghs.googlehosted.com` or `ghs.googlehosted.com.`
- [ ] TTL is set to Automatic or 300
- [ ] No conflicting A or AAAA records for api/engine
- [ ] Records show a green checkmark (active status)

---

## Support Commands

### Check Current DNS Status
```powershell
# Quick check all domains
.\scripts\verify_dns_and_ssl.ps1

# Manual checks
nslookup api.infinityai.pro 8.8.8.8
nslookup engine.infinityai.pro 8.8.8.8
```

### View Domain Mapping Details
```powershell
gcloud beta run domain-mappings list --region=us-central1 --project=infinity-ai-5ec7c
```

### Force DNS Cache Clear (Windows)
```powershell
ipconfig /flushdns
```

---

## Next Steps After DNS Propagates

1. **Wait for SSL** (automatic, up to 24 hours)
2. **Verify endpoints** become accessible
3. **Update documentation** if needed
4. **Monitor** with `verify_dns_and_ssl.ps1` script

---

## Contact & Resources

- **DNS Propagation Checker:** https://www.whatsmydns.net/
- **Namecheap DNS Guide:** https://www.namecheap.com/support/knowledgebase/article.aspx/767/10/how-to-change-dns-for-a-domain/
- **Google Cloud Run Domains:** https://cloud.google.com/run/docs/mapping-custom-domains

---

**Last Updated:** October 21, 2025  
**Status:** Waiting for DNS propagation of api and engine subdomains
