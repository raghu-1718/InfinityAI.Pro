# Domain Integration Plan: infinityai.pro

## Complete DNS & Custom Domain Setup for GCP + Firebase

**Date:** 2026-01-20T18:00:00Z
**Domain:** infinityai.pro
**Registrar:** Namecheap
**Project:** galvanic-pulsar-482815-h0

---

## 📋 CURRENT INFRASTRUCTURE

### Firebase Hosting

- **Default Domain:** galvanic-pulsar-482815-h0.web.app
- **Region:** us-central1
- **Primary Service:** Frontend (Next.js)
- **Public Directory:** frontend/web-app/out

### Cloud Run Services (us-central1)

- **engine-a:** https://engine-a-3acobgd3qa-uc.a.run.app (Orchestrator)
- **engine-b:** https://engine-b-3acobgd3qa-uc.a.run.app (AI/ML Signals)
- **engine-c:** https://engine-c-3acobgd3qa-uc.a.run.app (Execution - LIVE MODE)
- **20+ Cloud Functions:** market-data-ingestion, detect-momentum-signals, etc.

### Load Balancer (Optional)

- None currently (Cloud Run services have individual URLs)

---

## 🎯 DNS STRATEGY

### Option A: Firebase + Cloud Run Routing (RECOMMENDED)

```
infinityai.pro              → Firebase Hosting (Frontend)
www.infinityai.pro          → Firebase Hosting (Frontend)
api.infinityai.pro          → engine-c (Main Execution)
orchestrator.infinityai.pro → engine-a (Orchestrator)
signals.infinityai.pro      → engine-b (AI/ML Signals)
```

### Option B: Single Load Balancer (Advanced)

- Would require Google Cloud Load Balancer (additional cost)
- Centralizes all routing through single IP
- Not recommended for current architecture

**Proceeding with Option A (Firebase + Cloud Run).**

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Add Custom Domain to Firebase Hosting

**Firebase Hosting needs verification:**

```bash
firebase hosting:sites:create infinityai-pro --project=galvanic-pulsar-482815-h0
```

This creates:

- New Firebase Hosting site: `infinityai-pro`
- Default domain: infinityai-pro.firebaseapp.com
- Ready to link custom domain

### Step 2: Verify Domain Ownership

Firebase will provide a TXT record for domain verification:

**Record Name:** `_acme-challenge.infinityai.pro`
**Type:** TXT
**Value:** (Firebase will provide - we'll get this after adding domain)

### Step 3: Add Cloud Run Custom Domain Mappings

For each Cloud Run service, add custom domain:

```bash
# engine-c (Main API)
gcloud run domain-mappings create \
  --service=engine-c \
  --domain=api.infinityai.pro \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0

# engine-a (Orchestrator)
gcloud run domain-mappings create \
  --service=engine-a \
  --domain=orchestrator.infinityai.pro \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0

# engine-b (Signals)
gcloud run domain-mappings create \
  --service=engine-b \
  --domain=signals.infinityai.pro \
  --region=us-central1 \
  --project=galvanic-pulsar-482815-h0
```

Each command returns an IP address to use in DNS.

---

## 🔐 SSL/TLS CERTIFICATES

- **Firebase Hosting:** Auto-provisions SSL certificate (free, automatic renewal)
- **Cloud Run:** Google-managed SSL certificate (auto-provisioned)
- **Time to issue:** ~15-30 minutes after DNS records propagate
- **Renewal:** Automatic (no action needed)

---

## 📝 NAMECHEAP DNS RECORDS (TO BE UPDATED)

After completing Steps 1-3 above, you'll have specific IPs to add. Here's the template:

### Template (You'll fill in actual IPs from gcloud output)

| Type  | Name             | Value                     | TTL  | Notes                 |
| ----- | ---------------- | ------------------------- | ---- | --------------------- |
| A     | infinityai.pro   | `[FIREBASE_IP]`           | 3600 | Firebase Hosting root |
| CNAME | www              | infinityai.pro            | 3600 | Redirect to root      |
| CNAME | api              | engine-c-ip.c.run.app     | 3600 | Cloud Run engine-c    |
| CNAME | orchestrator     | engine-a-ip.c.run.app     | 3600 | Cloud Run engine-a    |
| CNAME | signals          | engine-b-ip.c.run.app     | 3600 | Cloud Run engine-b    |
| TXT   | \_acme-challenge | `[FIREBASE_VERIFICATION]` | 3600 | SSL verification      |

---

## 📊 DOMAIN ROUTING AFTER DNS UPDATE

```
User Request                  DNS Resolution               Service
─────────────────────────────────────────────────────────────────

infinityai.pro               → Firebase Hosting           Frontend (Next.js)
www.infinityai.pro           → Firebase Hosting           Frontend (Next.js)

api.infinityai.pro           → engine-c Cloud Run         Live Trading Execution
orchestrator.infinityai.pro  → engine-a Cloud Run         AI Orchestration
signals.infinityai.pro       → engine-b Cloud Run         ML Signal Generation

Firebase Rewrites            (via firebase.json)
/api/**                      → engine-a Cloud Run         API endpoints
/trading/**                  → engine-c Cloud Run         Trading operations
```

---

## ✅ VERIFICATION CHECKLIST

After updating DNS in Namecheap:

```bash
# Test DNS propagation
nslookup infinityai.pro
nslookup api.infinityai.pro
nslookup www.infinityai.pro

# Test HTTPS (should be green checkmark)
curl -I https://infinityai.pro
curl -I https://api.infinityai.pro

# Test Firebase Hosting
curl https://infinityai.pro/health

# Test Cloud Run endpoints
curl https://api.infinityai.pro/health
curl https://orchestrator.infinityai.pro/health
curl https://signals.infinityai.pro/health
```

---

## ⏱️ TIMELINE

| Step | Action                                | Time      | Status    |
| ---- | ------------------------------------- | --------- | --------- |
| 1    | Create Firebase custom domain         | ~2 min    | ⏳ Ready  |
| 2    | Get Firebase TXT verification record  | ~1 min    | ⏳ Ready  |
| 3    | Create Cloud Run domain mappings      | ~5 min    | ⏳ Ready  |
| 4    | Get Cloud Run IPs                     | Immediate | ⏳ Ready  |
| 5    | Update Namecheap DNS records          | Immediate | 👤 Manual |
| 6    | Wait for DNS propagation              | 15-30 min | ⏳ Auto   |
| 7    | Wait for SSL certificate provisioning | 15-30 min | ⏳ Auto   |
| 8    | Verify HTTPS working                  | ~5 min    | ⏳ Ready  |

**Total Time:** ~1 hour from start to full deployment

---

## 🚀 NEXT ACTIONS

1. **Review this plan** - Confirm routing strategy
2. **Execute GCP configuration** (Steps 1-3 above)
3. **Collect all DNS records** from command outputs
4. **Fill in Namecheap** with exact records provided
5. **Verify** after DNS propagates

---

**Ready to proceed?** Reply with confirmation and I'll execute all GCP configuration steps and provide exact Namecheap records.
