# Namecheap DNS Configuration for InfinityAI.Pro

**Domain:** infinityai.pro  
**Registrar:** Namecheap  
**Date:** November 28, 2025

---

## How to Add DNS Records in Namecheap

1. Login to Namecheap: https://www.namecheap.com
2. Go to **Domain List**
3. Click **Manage** next to `infinityai.pro`
4. Click **Advanced DNS** tab
5. Add each record below

---

## DNS Records to Add

### For engine-a.infinityai.pro

**Record Type:** CNAME  
**Host:** engine-a  
**Value:** ghs.googlehosted.com.  
**TTL:** Automatic (or 300)

---

### For engine-b.infinityai.pro

**Record Type:** CNAME  
**Host:** engine-b  
**Value:** ghs.googlehosted.com.  
**TTL:** Automatic (or 300)

---

### For engine-c.infinityai.pro

**Record Type:** CNAME  
**Host:** engine-c  
**Value:** ghs.googlehosted.com.  
**TTL:** Automatic (or 300)

---

### For www.infinityai.pro (Frontend - Optional)

**Record Type:** CNAME  
**Host:** www  
**Value:** after-yesterday-473512-k3.web.app.  
**TTL:** Automatic (or 300)

---

### For infinityai.pro (Root Domain - Optional)

**Record Type:** A  
**Host:** @  
**Value:** 151.101.1.195 (or Firebase IP)  
**TTL:** Automatic (or 300)

Or use CNAME flattening if Namecheap supports it:
**Record Type:** ALIAS or CNAME  
**Host:** @  
**Value:** after-yesterday-473512-k3.web.app.

---

## Summary Table

| Record Type | Host | Value | Purpose |
|------------|------|-------|---------|
| CNAME | engine-a | ghs.googlehosted.com. | Engine A API |
| CNAME | engine-b | ghs.googlehosted.com. | Engine B API |
| CNAME | engine-c | ghs.googlehosted.com. | Engine C API |
| CNAME | www | after-yesterday-473512-k3.web.app. | Frontend |
| A or ALIAS | @ | 151.101.1.195 | Root domain |

---

## Important Notes

1. **Trailing Dot:** For CNAME values, include the trailing dot (`.`) - `ghs.googlehosted.com.`
2. **TTL:** Use Automatic or 300 seconds for faster propagation during setup
3. **Propagation:** DNS changes take 15 minutes to 48 hours to propagate globally
4. **SSL Certificates:** GCP auto-provisions SSL certificates after DNS propagates (up to 24 hours)

---

## After Adding DNS Records

### Wait for Propagation

Check DNS propagation status:
```powershell
# Check each subdomain
nslookup engine-a.infinityai.pro 8.8.8.8
nslookup engine-b.infinityai.pro 8.8.8.8
nslookup engine-c.infinityai.pro 8.8.8.8

# Or use online tool
# https://dnschecker.org
```

### Verify Domain Mapping Status

```powershell
# Check Cloud Run domain mapping status
gcloud beta run domain-mappings describe engine-a.infinityai.pro `
  --region=us-central1 `
  --project=after-yesterday-473512-k3 `
  --format="get(status.conditions[0].status)"

# Should return: True
```

### Update Frontend

Once DNS propagates and shows "True", update frontend to use custom domains:
```powershell
cd C:\workspace\InfinityAI.Pro
# Run deployment script with custom domains enabled
.\scripts\deploy-with-custom-domains.ps1
```

---

## Troubleshooting

### DNS Not Resolving After 48 Hours

1. Check records are exactly as specified (including trailing dots)
2. Verify TTL is not too high (use 300 for testing)
3. Clear DNS cache: `ipconfig /flushdns`
4. Test with different DNS: `nslookup engine-a.infinityai.pro 1.1.1.1`

### SSL Certificate Issues

- Certificates provision automatically after DNS propagates
- Can take up to 24 hours
- Check status in GCP Console → Cloud Run → Domain Mappings

### CNAME Already Exists Error

- Remove any existing CNAME records for engine-a, engine-b, engine-c
- Namecheap only allows one record per host name

---

## Quick Copy-Paste for Namecheap

```
Record 1:
Type: CNAME Record
Host: engine-a
Value: ghs.googlehosted.com.
TTL: Automatic

Record 2:
Type: CNAME Record
Host: engine-b
Value: ghs.googlehosted.com.
TTL: Automatic

Record 3:
Type: CNAME Record
Host: engine-c
Value: ghs.googlehosted.com.
TTL: Automatic
```

---

## Status Tracking

- [ ] DNS records added to Namecheap
- [ ] DNS propagation complete (15 min - 48 hrs)
- [ ] Domain mappings show Ready: True in GCP
- [ ] SSL certificates provisioned
- [ ] Frontend updated to use custom domains
- [ ] End-to-end testing complete

---

**Current Status:** DNS records provided, awaiting configuration in Namecheap

**Next Step:** Add the 3 CNAME records above to Namecheap Advanced DNS
