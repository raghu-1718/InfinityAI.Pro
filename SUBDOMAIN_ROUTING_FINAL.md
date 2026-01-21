# INFINITYAI.PRO SUBDOMAIN ROUTING - FINAL DNS CONFIGURATION
## Complete Cloud Run Integration via Direct CNAME Routing

**Status:** ✅ Ready for Namecheap Update  
**Generated:** 2026-01-21T11:00:00Z  
**Project:** galvanic-pulsar-482815-h0  
**Method:** Direct Cloud Run CNAME routing with SSL auto-provisioning

---

## 📋 CURRENT NAMECHEAP DNS STATE

### ✅ Already Configured (Keep As-Is)
```
A Record     @         199.36.158.100       3600    (Firebase Hosting)
A Record     www       199.36.158.100       3600    (Firebase Hosting)
TXT Record   @         firebase=gen-lang-client-0779271931
TXT Record   @         hosting-site=galvanic-pulsar-482815-h0
TXT Record   @         v=spf1 include:spf.privateemail.com ~all
TXT Record   default._domainkey  (DKIM - keep as-is)
TXT Record   @         google-site-verification=... (Google - keep)
```

### ❌ Remove These (Old Cloud Run entries)
```
CNAME engine-a → ghs.googlehosted.com
CNAME engine-b → ghs.googlehosted.com
CNAME engine-c → ghs.googlehosted.com
```

---

## ✅ ADD THESE 3 CNAME RECORDS (NEW - Cloud Run Subdomains)

### Record 1: Engine-C (LIVE Trading API)
```
Type:   CNAME
Host:   api
Value:  engine-c-3acobgd3qa-uc.a.run.app
TTL:    3600
```

### Record 2: Engine-A (Risk Orchestrator)
```
Type:   CNAME
Host:   orchestrator
Value:  engine-a-3acobgd3qa-uc.a.run.app
TTL:    3600
```

### Record 3: Engine-B (ML Signals)
```
Type:   CNAME
Host:   signals
Value:  engine-b-3acobgd3qa-uc.a.run.app
TTL:    3600
```

---

## 🌐 RESULTING DOMAIN STRUCTURE

After adding the 3 CNAME records above, you'll have:

| Domain | Destination | Purpose | Status |
|--------|-------------|---------|--------|
| https://infinityai.pro | Firebase Hosting (199.36.158.100) | Frontend (Next.js) | ✅ LIVE |
| https://www.infinityai.pro | Firebase Hosting (199.36.158.100) | Frontend www | ✅ LIVE |
| https://api.infinityai.pro | Cloud Run Engine-C | Live Trading API | ⏳ After CNAME propagates |
| https://orchestrator.infinityai.pro | Cloud Run Engine-A | Risk Orchestration | ⏳ After CNAME propagates |
| https://signals.infinityai.pro | Cloud Run Engine-B | ML Signals | ⏳ After CNAME propagates |

---

## 📊 PROPAGATION & SSL TIMELINE

**Phase 1: Add CNAME Records to Namecheap (5 min)**
- Navigate to infinityai.pro Advanced DNS
- Remove old engine-a/b/c entries
- Add 3 new CNAME records
- Save

**Phase 2: DNS Propagation (5-30 min)**
- Verify: `nslookup api.infinityai.pro 8.8.8.8`
- Expected: resolves to `engine-c-3acobgd3qa-uc.a.run.app`

**Phase 3: Cloud Run SSL Auto-Provisioning (Automatic)**
- Once DNS resolves, Cloud Run automatically issues SSL cert
- Takes 5-15 minutes
- No manual action needed

**Phase 4: Full Production Ready (40-50 min total)**
- All 5 domains (apex, www, api, orchestrator, signals) accessible over HTTPS
- SSL certificates active on all subdomains
- Live trading, orchestration, and signals fully routed

---

## 🎯 VERIFICATION CHECKLIST

### After Adding CNAME Records (Wait 5-30 min for propagation)

- [ ] **DNS Propagation Check**
  ```bash
  nslookup api.infinityai.pro 8.8.8.8
  # Expected: engine-c-3acobgd3qa-uc.a.run.app
  
  nslookup orchestrator.infinityai.pro 8.8.8.8
  # Expected: engine-a-3acobgd3qa-uc.a.run.app
  
  nslookup signals.infinityai.pro 8.8.8.8
  # Expected: engine-b-3acobgd3qa-uc.a.run.app
  ```

- [ ] **HTTPS Access Verification**
  ```bash
  curl -I https://api.infinityai.pro
  # Expected: 200 or 301 (not 404 or cert error)
  
  curl -I https://orchestrator.infinityai.pro
  # Expected: 200 or 301
  
  curl -I https://signals.infinityai.pro
  # Expected: 200 or 301
  ```

- [ ] **SSL Certificate Status**
  ```bash
  # Check certificate issuer
  echo | openssl s_client -servername api.infinityai.pro \
    -connect api.infinityai.pro:443 2>/dev/null | grep -A3 "subject="
  # Expected: Certificate issued by Google
  ```

---

## 🔧 TROUBLESHOOTING

### CNAME Not Resolving?
1. Verify you saved the changes in Namecheap
2. Wait 5-15 minutes (DNS TTL is 3600 seconds = 1 hour)
3. Try: `nslookup api.infinityai.pro 8.8.8.8` (Google's DNS bypasses local cache)
4. Check Namecheap dashboard—confirm records are saved

### 404 Error on Subdomain?
1. Ensure CNAME points to exact URL: `engine-c-3acobgd3qa-uc.a.run.app` (NO https://)
2. Wait for DNS propagation if just added
3. Cloud Run service must be deployed and running (check `gcloud run services list`)

### SSL Certificate Not Issued?
1. Wait 10-15 minutes after DNS propagation
2. Cloud Run auto-issues SSL for domains mapping to services
3. Check certificate: `echo | openssl s_client -servername api.infinityai.pro -connect api.infinityai.pro:443`

### Service Returns 403/404?
1. Service may not have public endpoint enabled
2. Run: `gcloud run services describe engine-c --region=us-central1 --project=galvanic-pulsar-482815-h0`
3. Confirm `--allow-unauthenticated` is set
4. If not, run: `gcloud run services update engine-c --allow-unauthenticated --region=us-central1 --project=galvanic-pulsar-482815-h0`

---

## 📞 NEXT STEPS (USER ACTION)

### Step 1: Update Namecheap (5 minutes)
1. Go to https://www.namecheap.com/dashboard/
2. Select **infinityai.pro**
3. Click **Advanced DNS**
4. **Remove** (3 records):
   - CNAME engine-a → ghs.googlehosted.com
   - CNAME engine-b → ghs.googlehosted.com
   - CNAME engine-c → ghs.googlehosted.com

5. **Add** (3 new records):
   ```
   CNAME  api            engine-c-3acobgd3qa-uc.a.run.app
   CNAME  orchestrator   engine-a-3acobgd3qa-uc.a.run.app
   CNAME  signals        engine-b-3acobgd3qa-uc.a.run.app
   ```
6. **Save**

### Step 2: Verify DNS (5-30 minutes)
```bash
nslookup api.infinityai.pro 8.8.8.8
nslookup orchestrator.infinityai.pro 8.8.8.8
nslookup signals.infinityai.pro 8.8.8.8
```

### Step 3: Test HTTPS Endpoints (5 minutes)
```bash
curl -I https://infinityai.pro
curl -I https://www.infinityai.pro
curl -I https://api.infinityai.pro
curl -I https://orchestrator.infinityai.pro
curl -I https://signals.infinityai.pro
```

### Step 4: Confirm SSL & Full Production Ready
All endpoints respond with HTTPS (200/301/302, no SSL warnings).

---

## 📊 INFRASTRUCTURE SUMMARY

### Frontend (Firebase Hosting)
- **Domain:** infinityai.pro, www.infinityai.pro
- **IP:** 199.36.158.100 (Firebase anycast)
- **Status:** ✅ LIVE (200 OK verified)
- **SSL:** Managed by Firebase

### APIs (Cloud Run)
| Service | Subdomain | Cloud Run URL | Status |
|---------|-----------|---------------|--------|
| Engine-C | api.infinityai.pro | engine-c-3acobgd3qa-uc.a.run.app | ⏳ After CNAME |
| Engine-A | orchestrator.infinityai.pro | engine-a-3acobgd3qa-uc.a.run.app | ⏳ After CNAME |
| Engine-B | signals.infinityai.pro | engine-b-3acobgd3qa-uc.a.run.app | ⏳ After CNAME |

### SSL/TLS
- **Type:** Cloud Run auto-provisioned SSL
- **Domains:** api.infinityai.pro, orchestrator.infinityai.pro, signals.infinityai.pro
- **Validation:** Automatic (no manual DNS records needed)
- **Auto-Renewal:** Enabled

---

## ✅ FINAL CHECKLIST

- [x] Firebase Hosting (apex + www) live with SSL
- [x] Cloud Run services identified and URLs extracted
- [x] CNAME records generated for 3 subdomains
- [x] Namecheap DNS update plan documented
- [x] Propagation timeline provided
- [x] Verification commands included
- [x] Troubleshooting guide provided
- [ ] User adds CNAME records to Namecheap
- [ ] DNS propagates (5-30 min)
- [ ] SSL auto-provisions on Cloud Run subdomains (5-15 min after DNS)
- [ ] Full production launch complete (40-50 min total)

---

**Status:** Ready for Namecheap CNAME Update  
**Generated:** 2026-01-21T11:00:00Z  
**Project:** galvanic-pulsar-482815-h0  
**Domain:** infinityai.pro

---

# 🚀 READY FOR PRODUCTION

All three Cloud Run engines (Engine-C, Engine-A, Engine-B) are now routable via custom subdomains with automatic SSL provisioning. Frontend (Firebase) is already live. Add the 3 CNAME records to Namecheap and full production will be ready in ~40-50 minutes.
