# 🚨 EXTERNAL SETUP REQUIRED - Action Items Before Deployment

**Date:** November 2, 2025  
**Status:** ⏳ AWAITING USER ACTION  
**Critical:** These steps MUST be completed before pushing to trigger deployment

---

## ✅ Completed Automated Setup

The following has been configured automatically:

- ✅ All 7 GitHub Actions secrets set
- ✅ Vercel domains added: `infinityai.pro` and `api.infinityai.pro`
- ✅ DHAN_WEBHOOK_SECRET environment variable set in Vercel api-webhooks project
- ✅ Workflow file updated with production values
- ✅ API-webhooks CORS configured with production URLs
- ✅ Northflank CLI authenticated and project verified

---

## 🔴 STEP 1: Configure DNS Records (CRITICAL)

You must configure DNS records with your domain registrar (where you purchased infinityai.pro).

### Required DNS Records:

#### A. For Vercel (Frontend and API Webhooks)

**Record 1: Frontend Domain**
```
Type: A
Host: @
Value: 76.76.21.21
TTL: 3600 (or Auto)
```

**Record 2: API Subdomain**
```
Type: A
Host: api
Value: 76.76.21.21
TTL: 3600 (or Auto)
```

#### B. For Northflank (Engines Gateway) - OPTIONAL FOR NOW

**Record 3: Engines Subdomain**
```
Type: CNAME
Host: engines
Value: <YOUR_NORTHFLANK_GATEWAY_URL> (e.g., infinity-ai-gateway-xyz.northflank.app)
TTL: 3600 (or Auto)
```

**Note:** The Northflank gateway URL will be provided after you create an API Gateway in Northflank. For now, you can skip this and use Northflank's default URLs.

---

### 📍 Where to Add DNS Records

**Option 1: Use your current registrar DNS**
1. Log in to your domain registrar (e.g., GoDaddy, Namecheap, Google Domains, Cloudflare)
2. Navigate to DNS Management for `infinityai.pro`
3. Add the A records above
4. Wait 5-15 minutes for propagation

**Option 2: Use Vercel DNS (Recommended for simplicity)**
1. Update your domain's nameservers to:
   - `ns1.vercel-dns.com`
   - `ns2.vercel-dns.com`
2. Vercel will automatically configure all required DNS records
3. Wait 24-48 hours for nameserver propagation (can be faster)

---

## 🔴 STEP 2: Configure Dhan Webhook (CRITICAL)

You must configure the webhook endpoint in your Dhan API Console.

### Instructions:

1. **Log in to Dhan Developer Console**
   - URL: https://api.dhan.co (or your Dhan developer portal)
   - Use your Dhan API credentials

2. **Navigate to Webhooks Section**
   - Look for "Webhooks", "Notifications", or "Event Subscriptions"

3. **Add New Webhook Endpoint**
   - **Webhook URL:** `https://api.infinityai.pro/api/webhook/dhan`
   - **Secret Key:** `kMDXOZHGS04K25eRQYbwTWhILCAutzmBiaoJ38cE7r1qxpd9UnfPljyvgN6sVF`
   - **Events to Subscribe:** Select all order-related events (order placed, executed, cancelled, etc.)

4. **Test the Webhook**
   - Use Dhan's "Test Webhook" feature (if available)
   - Or place a test order to verify webhook delivery

---

## 🔴 STEP 3: Verify Vercel Domain Configuration

After configuring DNS, verify the domains are working:

### Check Domain Status:

```powershell
# Check frontend domain
vercel domains ls --project prj_DZGuGnAqA3ntefoQZ8b53xOjwaBf

# Check webhooks domain
vercel domains ls --project prj_EHBU9CqlyO8zaN7mwLe7r8MpL2bW
```

### Expected Output:
Both domains should show as **"Valid"** or **"Verified"** once DNS propagates.

---

## 🟡 OPTIONAL: Create Northflank API Gateway

For clean, permanent engine URLs (recommended for production):

### Option A: Use Northflank CLI

```powershell
# Create an API Gateway named "engines"
northflank create gateway engines --project infinity-ai --region asia-southeast

# Add domain to the gateway
northflank add domain engines.infinityai.pro --gateway engines --project infinity-ai
```

### Option B: Use Northflank Web Console

1. Go to https://app.northflank.com
2. Select project: **Infinity AI**
3. Navigate to **API Gateways**
4. Click **Create Gateway**
   - Name: `engines`
   - Region: Asia - Southeast
5. After creation, note the gateway URL (e.g., `infinity-ai-engines-xyz.northflank.app`)
6. Add CNAME record in DNS:
   ```
   Type: CNAME
   Host: engines
   Value: <gateway-url-from-step-5>
   ```

---

## ✅ Verification Checklist

Before proceeding to deployment, confirm:

- [ ] DNS A record added for `infinityai.pro` → `76.76.21.21`
- [ ] DNS A record added for `api.infinityai.pro` → `76.76.21.21`
- [ ] DNS propagation verified (use https://dnschecker.org)
- [ ] Dhan webhook configured with URL: `https://api.infinityai.pro/api/webhook/dhan`
- [ ] Dhan webhook secret matches: `kMDXOZHGS04K25eRQYbwTWhILCAutzmBiaoJ38cE7r1qxpd9UnfPljyvgN6sVF`
- [ ] Vercel domains show as "Valid" or "Verified"
- [ ] (Optional) Northflank gateway created and `engines.infinityai.pro` CNAME added

---

## 🚀 Ready to Deploy?

Once you've completed the steps above and verified the checklist, you're ready to deploy!

### Final Deployment Commands:

```powershell
# Navigate to project root
cd C:\Users\Raghu\Projects\InfinityAI.Pro

# Review all changes
git status

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: production deployment - multi-cloud CI/CD with Vercel, Firebase, Northflank

- Updated monorepo-deploy.yml with production project IDs and domains
- Configured Vercel domains: infinityai.pro and api.infinityai.pro
- Set DHAN_WEBHOOK_SECRET in Vercel environment
- Updated api-webhooks CORS with production URLs
- Refactored Engine C with multi-broker architecture
- Added pytest unit tests for OrderManager
- Created api-webhooks service for Dhan webhooks
- All 7 GitHub Actions secrets configured and verified"

# Push to trigger deployment
git push origin recovery/v4.6-stabilization
```

### Monitor Deployment:

1. **GitHub Actions**: https://github.com/raghu-1718/InfinityAI.Pro/actions
2. **Vercel Dashboard**: https://vercel.com/infinityaipro/frontend and https://vercel.com/infinityaipro/api-webhooks
3. **Firebase Console**: https://console.firebase.google.com/project/infinitygt-b2287
4. **Northflank Dashboard**: https://app.northflank.com/projects/infinity-ai

---

## 🆘 Troubleshooting

### DNS Not Propagating?
- Use https://dnschecker.org to check propagation status globally
- Typical propagation: 5-15 minutes (A records), up to 48 hours (nameserver changes)
- Clear your local DNS cache: `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (Mac)

### Vercel Domain Not Verifying?
- Run: `vercel domains verify infinityai.pro` and `vercel domains verify api.infinityai.pro`
- Check TTL settings (should be 3600 or lower for faster updates)
- Ensure no conflicting records (delete old A/CNAME records first)

### Dhan Webhook Not Working?
- Test locally first: Use ngrok to expose local api-webhooks and test with Dhan
- Verify signature secret matches exactly (case-sensitive, no extra spaces)
- Check Dhan console for webhook delivery logs/errors

### Northflank Gateway Issues?
- For now, you can skip the gateway and use direct service URLs
- Update frontend config to point to individual engine URLs instead
- Create the gateway later for cleaner architecture

---

## 📞 Support

- **Documentation**: See `config/SECRETS_SETUP_COMPLETE.md` for full configuration details
- **Logs**: Check GitHub Actions logs, Vercel deployment logs, and Northflank service logs
- **Secrets Reference**: `config/secrets-mapping.md`

---

**Generated:** 2025-11-02 15:00 UTC  
**Next Action:** Complete external setup steps above, then run deployment commands  
**Status After Deployment:** Full production multi-cloud deployment across Vercel, Firebase, and Northflank 🚀
