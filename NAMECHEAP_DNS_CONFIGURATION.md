# INFINITYAI.PRO NAMECHEAP DNS CONFIGURATION
## Complete DNS Records to Add/Update

**Domain:** infinityai.pro  
**Registrar:** Namecheap  
**Update Method:** Namecheap Dashboard → Domain Management → Advanced DNS  
**Generated:** 2026-01-21T10:40:00Z

---

## 📋 DNS RECORDS TO ADD IN NAMECHEAP

### Record 1: Root Domain A Record (Firebase Hosting)
```
Type:       A
Host:       @
Value:      199.36.158.100
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 2: WWW Subdomain A Record (Firebase Hosting)
```
Type:       A
Host:       www
Value:      199.36.158.100
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 3: Firebase Domain Verification TXT Record
```
Type:       TXT
Host:       @
Value:      firebase=galvanic-pulsar-482815-h0
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 4: CNAME for Cloud Run Engine-C (API)
```
Type:       CNAME
Host:       api
Value:      engine-c-228557716858.us-central1.run.app.c.appspot.com
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 5: CNAME for Cloud Run Engine-A (Orchestrator)
```
Type:       CNAME
Host:       orchestrator
Value:      engine-a-3acobgd3qa-uc.a.run.app.c.appspot.com
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 6: CNAME for Cloud Run Engine-B (Signals)
```
Type:       CNAME
Host:       signals
Value:      engine-b-3acobgd3qa-uc.a.run.app.c.appspot.com
TTL:        3600 (1 hour)
Priority:   (leave blank)
```

### Record 7: MX Records (Email - Optional, if needed)
```
Type:       MX
Host:       @
Value:      aspmx.l.google.com
Priority:   10
TTL:        3600

Type:       MX
Host:       @
Value:      alt1.aspmx.l.google.com
Priority:   20
TTL:        3600

Type:       MX
Host:       @
Value:      alt2.aspmx.l.google.com
Priority:   30
TTL:        3600

Type:       MX
Host:       @
Value:      aspmx2.googlemail.com
Priority:   40
TTL:        3600

Type:       MX
Host:       @
Value:      aspmx3.googlemail.com
Priority:   50
TTL:        3600
```

---

## 🔍 DNS PROPAGATION & VERIFICATION

**After adding records, DNS should propagate within:**
- Immediate (some regions): < 5 minutes
- Standard: 15-30 minutes
- Full propagation: 24-48 hours

**Verify Records Using:**

```bash
# Check A records
nslookup infinityai.pro

# Check CNAME records
nslookup api.infinityai.pro

# Check TXT records
nslookup -type=TXT infinityai.pro

# Full DNS check (Linux/Mac)
dig infinityai.pro
dig api.infinityai.pro
dig www.infinityai.pro
```

---

## 📊 DNS RECORD SUMMARY TABLE

| Record Type | Host | Value | TTL | Purpose |
|-------------|------|-------|-----|---------|
| A | @ | 199.36.158.100 | 3600 | Firebase Hosting root domain |
| A | www | 199.36.158.100 | 3600 | Firebase Hosting www subdomain |
| TXT | @ | firebase=galvanic-pulsar-482815-h0 | 3600 | Firebase domain verification |
| CNAME | api | engine-c-228557716858.us-central1.run.app.c.appspot.com | 3600 | Cloud Run Engine-C (LIVE trading) |
| CNAME | orchestrator | engine-a-3acobgd3qa-uc.a.run.app.c.appspot.com | 3600 | Cloud Run Engine-A (Orchestrator) |
| CNAME | signals | engine-b-3acobgd3qa-uc.a.run.app.c.appspot.com | 3600 | Cloud Run Engine-B (ML Signals) |
| MX | @ | aspmx.l.google.com (priority 10) | 3600 | Google Workspace email (optional) |

---

## 🚀 WHAT EACH RECORD DOES

### A Records (Root + WWW)
- Route all traffic to `infinityai.pro` and `www.infinityai.pro` to Firebase Hosting
- Firebase serves Next.js frontend from Firebase Hosting
- SSL automatically provisioned and managed by Firebase

### CNAME Records (API Subdomains)
- `api.infinityai.pro` → Engine-C (Live Trading API, DhanHQ broker integration)
- `orchestrator.infinityai.pro` → Engine-A (AI risk scoring and orchestration)
- `signals.infinityai.pro` → Engine-B (ML signal generation)
- Each CNAME routes to respective Cloud Run service

### TXT Record (Firebase Verification)
- Required by Firebase to verify domain ownership
- Firebase checks for this record before issuing SSL certificate

### MX Records (Email - Optional)
- Only needed if using Google Workspace for email at infinityai.pro
- Skip if not using email service

---

## ✅ STEP-BY-STEP NAMECHEAP SETUP

1. **Login to Namecheap Dashboard**
   - Go to https://www.namecheap.com/dashboard/
   - Navigate to "Manage Domains"

2. **Select Domain: infinityai.pro**
   - Click on infinityai.pro
   - Scroll to "Nameservers" section

3. **Verify Nameserver Configuration** (do NOT change unless needed)
   - Should be pointing to Namecheap's nameservers (default)
   - If custom, keep current settings

4. **Go to Advanced DNS Tab**
   - Click "Advanced DNS" tab (next to "Domain" tab)

5. **Add/Update DNS Records**
   - Click "Add New Record" for each record above
   - Enter Type, Host, Value, TTL exactly as shown
   - Save each record

6. **Record Addition Order (Recommended)**
   - First: TXT record (firebase verification)
   - Then: A records (root + www)
   - Then: CNAME records (subdomains)
   - Last: MX records (if using email)

7. **Verify After Addition**
   - Wait 5-15 minutes for propagation
   - Use `nslookup` or online DNS checker to verify

---

## 🔗 INTEGRATION ARCHITECTURE

```
User Browser (infinityai.pro)
    ↓
Namecheap DNS Resolution
    ↓ (A Record 199.36.158.100)
Firebase Hosting
    ↓
Frontend (Next.js, Ably channels)
    ↓
API Calls to:
    → api.infinityai.pro/api/dhan/place-order → Engine-C (LIVE Trading)
    → orchestrator.infinityai.pro/api/orchestrate → Engine-A (Risk/Execution)
    → signals.infinityai.pro/api/signals → Engine-B (ML Models)
    ↓
DhanHQ Broker API
    ↓
Real-Time Orders & Trades
```

---

## 📧 HTTPS/SSL STATUS

**Certificate:** infinityai-pro-ssl (GCP Managed Certificate)  
**Status:** PROVISIONING (will complete after DNS records added)  
**Domains:** infinityai.pro, www.infinityai.pro  
**Auto-Renewal:** Enabled  
**Certificate Provider:** Google Cloud SSL  

**Current URL Status:**
- ❌ https://infinityai.pro → Will work after DNS propagation
- ❌ https://www.infinityai.pro → Will work after DNS propagation
- ✅ https://galvanic-pulsar-482815-h0-web-app.web.app → Works now (Firebase default)

---

## ⚠️ IMPORTANT NOTES

1. **DNS Propagation Time**
   - Changes may take 5 minutes to 48 hours to fully propagate
   - Check multiple DNS checkers to confirm propagation
   - If issues persist after 48h, contact Namecheap support

2. **SSL Certificate Provisioning**
   - After DNS records added, Google Cloud will validate domains
   - SSL certificate provisioning may take 5-30 minutes
   - Check GCP console for certificate status

3. **Firestore Security Rules**
   - Already configured to enforce per-user isolation
   - LIVE trading mode active (paper trading eliminated)
   - Guardrails enforced (market hours, symbol whitelist, order caps)

4. **Backend Services**
   - Engine-C: LIVE TRADING (💰 badge confirmed)
   - Engine-A: Risk Scoring & Orchestration
   - Engine-B: ML Signal Generation (XGBoost, LightGBM, CatBoost)
   - All services use Secret Manager for credential encryption

5. **Email/MX Configuration**
   - MX records are optional
   - Only add if using Google Workspace for email at infinityai.pro
   - Skip if not needed

---

## 🔧 TROUBLESHOOTING

**DNS Not Resolving?**
```bash
# Flush DNS cache (Windows)
ipconfig /flushdns

# Flush DNS cache (Mac)
sudo dscacheutil -flushcache

# Check DNS on Linux
dig infinityai.pro @8.8.8.8
```

**SSL Certificate Not Provisioning?**
- Wait 5-10 minutes after DNS records added
- Check GCP Console → Compute → SSL Certificates
- Verify TXT record is correctly added to Namecheap

**CNAME Records Not Working?**
- Ensure no A records exist for the same host (CNAME conflict)
- Use `nslookup -type=CNAME` to verify CNAME records

**Subdomain Redirects Not Working?**
- Update firebase.json with rewrites for api.*, orchestrator.*, signals.*
- Deploy updated firebase.json: `firebase deploy --only hosting`

---

## 📞 SUPPORT

**GCP Support:** https://cloud.google.com/support  
**Firebase Support:** https://firebase.google.com/support  
**Namecheap Support:** https://www.namecheap.com/support/  

**Project Details:**
- GCP Project ID: galvanic-pulsar-482815-h0
- Firebase Project: galvanic-pulsar-482815-h0
- Domain: infinityai.pro
- Region: us-central1

---

**Configuration Date:** 2026-01-21  
**Last Updated:** 2026-01-21T10:40:00Z  
**Status:** ✅ Ready for Namecheap DNS Update
