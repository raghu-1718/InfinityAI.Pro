# ✅ PRE-DEPLOYMENT CHECKLIST

**Review this checklist before running deployment commands**

---

## 🟢 AUTOMATED SETUP - COMPLETE ✅

- [x] All 7 GitHub Actions secrets configured
- [x] Vercel projects created and linked
- [x] Vercel domains added (infinityai.pro, api.infinityai.pro)
- [x] DHAN_WEBHOOK_SECRET set in Vercel environment
- [x] Workflow file updated with production values
- [x] API-webhooks CORS configured
- [x] Northflank CLI authenticated
- [x] Code files updated (no demo placeholders)

---

## 🔴 EXTERNAL SETUP - YOUR ACTION REQUIRED ⏳

### DNS Configuration (CRITICAL - Do this first!)

- [ ] Add A record: `infinityai.pro` → `76.76.21.21`
- [ ] Add A record: `api.infinityai.pro` → `76.76.21.21`
- [ ] Wait 5-15 minutes for DNS propagation
- [ ] Verify with: https://dnschecker.org/

### Vercel Domain Verification

- [ ] Run: `vercel domains ls --project prj_DZGuGnAqA3ntefoQZ8b53xOjwaBf`
- [ ] Confirm status shows "Valid" or "Verified"
- [ ] Run: `vercel domains ls --project prj_EHBU9CqlyO8zaN7mwLe7r8MpL2bW`
- [ ] Confirm status shows "Valid" or "Verified"

### Dhan Webhook Configuration (CRITICAL)

- [ ] Log in to Dhan API Console
- [ ] Add webhook endpoint: `https://api.infinityai.pro/api/webhook/dhan`
- [ ] Set secret: `kMDXOZHGS04K25eRQYbwTWhILCAutzmBiaoJ38cE7r1qxpd9UnfPljyvgN6sVF`
- [ ] Subscribe to all order events
- [ ] Test webhook delivery (if available)

---

## 🟡 OPTIONAL SETUP - Can Do Later

- [ ] Create Northflank API Gateway named "engines"
- [ ] Add CNAME: `engines.infinityai.pro` → gateway URL
- [ ] Update workflow to use gateway URL instead of placeholder

---

## 📋 MODIFIED FILES READY FOR COMMIT

```
New Files:
✅ .github/workflows/monorepo-deploy.yml
✅ .github/workflows/engine-c-tests.yml
✅ api-webhooks/ (entire directory)
✅ InfinityGT-Project/engines/engine-c-execution/core/broker/
✅ InfinityGT-Project/engines/engine-c-execution/core/execution/
✅ InfinityGT-Project/engines/engine-c-execution/tests/
✅ config/ (firebase-config.json, secrets-mapping.md, SECRETS_SETUP_COMPLETE.md)
✅ EXTERNAL_SETUP_REQUIRED.md
✅ GO_LIVE_DEPLOYMENT_SUMMARY.md
✅ scripts/northflank-login.ps1

Modified Files:
✅ InfinityGT-Project/engines/engine-c-execution/main.py
✅ InfinityGT-Project/engines/engine-c-execution/requirements.txt
✅ InfinityGT-Project/frontend/.gitignore
```

---

## 🚀 DEPLOYMENT COMMANDS (Run when external setup is complete)

```powershell
# 1. Navigate to project root
cd C:\Users\Raghu\Projects\InfinityAI.Pro

# 2. Review all changes
git status
git diff

# 3. Stage all changes
git add .

# 4. Commit with descriptive message
git commit -m "feat: production deployment - multi-cloud CI/CD with Vercel, Firebase, Northflank

Major Features:
- Refactored Engine C with multi-broker architecture (Dhan + Angel One adapters)
- Added OrderManager, RiskManager, PositionManager with clean separation of concerns
- Implemented pytest unit tests for OrderManager with risk management validation
- Created api-webhooks FastAPI service for secure Dhan webhook handling with HMAC-SHA256

Infrastructure:
- Updated monorepo-deploy.yml with production project IDs and domains
- Configured Vercel domains: infinityai.pro and api.infinityai.pro
- Set DHAN_WEBHOOK_SECRET in Vercel environment variables
- Updated CORS and API endpoints with production URLs (no demo data)

Security & Configuration:
- All 7 GitHub Actions secrets configured and verified
- Northflank CLI authenticated with deployment-role token
- Firebase project configured: infinitygt-b2287
- HMAC signature verification for webhook security

Testing:
- Added pytest test suite for Engine C OrderManager
- Validates happy path order execution and risk rejection scenarios

Breaking Changes: None (new deployment)
Deployment Target: recovery/v4.6-stabilization branch"

# 5. Push to trigger deployment
git push origin recovery/v4.6-stabilization

# 6. Monitor deployment
# GitHub Actions: https://github.com/raghu-1718/InfinityAI.Pro/actions
# Vercel Frontend: https://vercel.com/infinityaipro/frontend
# Vercel Webhooks: https://vercel.com/infinityaipro/api-webhooks
# Firebase: https://console.firebase.google.com/project/infinitygt-b2287
# Northflank: https://app.northflank.com/projects/infinity-ai
```

---

## 🔍 POST-DEPLOYMENT VERIFICATION

### Step 1: Check GitHub Actions
- [ ] Navigate to: https://github.com/raghu-1718/InfinityAI.Pro/actions
- [ ] Confirm all 5 jobs passed (test-engine-c, deploy-frontend, deploy-webhooks, deploy-functions, deploy-engine-c)
- [ ] Check logs for any warnings or errors

### Step 2: Test Frontend
```powershell
# Check if site is live
curl -I https://infinityai.pro

# Expected: HTTP/2 200 OK
```
- [ ] Open https://infinityai.pro in browser
- [ ] Verify no CORS errors in browser console (F12)
- [ ] Test user login/authentication

### Step 3: Test API Webhooks
```powershell
# Health check
curl https://api.infinityai.pro/api/health

# Expected: {"status":"ok"}
```
- [ ] Health endpoint returns 200 OK
- [ ] Trigger test webhook from Dhan console
- [ ] Verify webhook received and processed

### Step 4: Check Northflank
- [ ] Navigate to: https://app.northflank.com/projects/infinity-ai
- [ ] Confirm engine-c-execution service shows "Running"
- [ ] Check service logs for startup errors
- [ ] Test engine endpoints (if accessible)

### Step 5: Check Firebase
- [ ] Navigate to: https://console.firebase.google.com/project/infinitygt-b2287
- [ ] Verify Functions deployed successfully
- [ ] Check Functions logs for errors
- [ ] Test authentication flow

---

## 🆘 TROUBLESHOOTING

### If DNS not propagating:
```powershell
# Check propagation status globally
# Visit: https://dnschecker.org/
# Enter: infinityai.pro and api.infinityai.pro

# Clear local DNS cache
ipconfig /flushdns

# Check current DNS resolution
nslookup infinityai.pro
nslookup api.infinityai.pro
```

### If Vercel domain not verifying:
```powershell
# Manually trigger verification
vercel domains verify infinityai.pro
vercel domains verify api.infinityai.pro

# Check domain status
vercel domains ls --project prj_DZGuGnAqA3ntefoQZ8b53xOjwaBf
vercel domains ls --project prj_EHBU9CqlyO8zaN7mwLe7r8MpL2bW
```

### If GitHub Actions deployment fails:
1. Check the specific job that failed
2. Review the job logs for error messages
3. Common issues:
   - Missing secrets: Verify all 7 secrets are set correctly
   - Path errors: Check cwd paths in workflow match repository structure
   - Build errors: Review requirements.txt and package.json dependencies

### If Dhan webhook fails:
1. Verify signature secret matches exactly (case-sensitive)
2. Check api.infinityai.pro is accessible publicly
3. Review Dhan console for webhook delivery logs
4. Test locally first with ngrok if needed

---

## 📊 SUCCESS INDICATORS

All green when:
- ✅ GitHub Actions shows all jobs passed
- ✅ https://infinityai.pro loads without errors
- ✅ https://api.infinityai.pro/api/health returns {"status":"ok"}
- ✅ Vercel domains show "Verified" status
- ✅ Northflank engine-c-execution shows "Running"
- ✅ Firebase functions deployed (no errors in console)
- ✅ Dhan test webhook delivers successfully
- ✅ No CORS errors in browser console

---

## 🎯 ROLLBACK PROCEDURE (If Needed)

```powershell
# Option 1: Revert the last commit
git revert HEAD
git push origin recovery/v4.6-stabilization

# Option 2: Hard reset (use with caution)
git reset --hard HEAD~1
git push origin recovery/v4.6-stabilization --force

# Option 3: Create a new branch and cherry-pick good commits
git checkout -b rollback-safe
git cherry-pick <good-commit-hash>
git push origin rollback-safe
```

---

## 📞 NEED HELP?

**Documentation:**
- Full setup: `GO_LIVE_DEPLOYMENT_SUMMARY.md`
- External steps: `EXTERNAL_SETUP_REQUIRED.md`
- Secrets reference: `config/SECRETS_SETUP_COMPLETE.md`

**Logs to Check:**
- GitHub Actions: Workflow run logs
- Vercel: Deployment logs and function logs
- Northflank: Service logs and build logs
- Firebase: Functions logs in console

**Common Commands:**
```powershell
# View GitHub Actions status
gh run list --limit 5

# View Vercel deployments
vercel ls

# View Northflank services
northflank list services --project infinity-ai

# Check git status
git status
git log --oneline -5
```

---

**Status:** ⏳ **AWAITING EXTERNAL SETUP COMPLETION**  
**Next:** Complete DNS + Dhan webhook → Verify → Commit → Push → Monitor  
**Estimated Time:** 20-30 minutes (including DNS propagation)

---

**Generated:** 2025-11-02 15:10 UTC  
**All automated setup complete - Ready when you are!** 🚀
