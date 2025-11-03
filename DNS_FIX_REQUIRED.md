# DNS Configuration Fix for infinityai.pro

## ⚠️ CRITICAL: A Record Update Required

### Current Issue
- **infinityai.pro** A record points to: `199.36.158.100` (Vercel IP)
- **Required** A record should point to: `216.239.32.21` (Google Cloud Run)

### Namecheap Update Required

**Login to Namecheap → Domain List → infinityai.pro → Advanced DNS**

#### Update THIS Record:
```
Type: A Record
Host: @
Value: 199.36.158.100 ❌ DELETE THIS
TTL: Automatic
```

#### Replace WITH:
```
Type: A Record
Host: @
Value: 216.39.32.21 ✅ UPDATE TO THIS
TTL: Automatic
```

### All Required DNS Records (Complete List)

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A Record | @ | **216.239.32.21** | Automatic |
| CNAME | www | ghs.googlehosted.com | Automatic |
| CNAME | engine-a | ghs.googlehosted.com | Automatic |
| CNAME | engine-b | ghs.googlehosted.com | Automatic |
| CNAME | engine-c | ghs.googlehosted.com | Automatic |
| CNAME | engine-d | ghs.googlehosted.com | Automatic |

### Verification After Update

Wait 5-15 minutes for DNS propagation, then test:

```powershell
# Should return 216.239.32.21
nslookup infinityai.pro 8.8.8.8

# Should work with HTTPS
curl -I https://infinityai.pro

# Test all subdomains
curl -I https://engine-a.infinityai.pro/health
curl -I https://engine-b.infinityai.pro/health
curl -I https://engine-c.infinityai.pro/health
curl -I https://engine-d.infinityai.pro/health
```

### What This Fixes

- ✅ Main domain (infinityai.pro) points to Firebase Hosting
- ✅ Subdomains (engine-*.infinityai.pro) point to Cloud Run engines
- ✅ SSL certificates can provision correctly
- ✅ No more Vercel 404 errors
- ✅ Complete platform accessibility

### Technical Details

**Firebase Hosting** serves `infinityai.pro` and `www.infinityai.pro`
- Uses Cloud Run domain mapping with A record `216.239.32.21`
- SSL certificate auto-provisioned by Google

**Cloud Run Engines** serve engine subdomains
- Use CNAME records pointing to `ghs.googlehosted.com`
- Each engine has dedicated custom domain mapping

## Summary

**ONE CHANGE NEEDED:** Update A record from `199.36.158.100` → `216.239.32.21`

All other DNS records (www + 4 engine CNAMEs) are already correct.
