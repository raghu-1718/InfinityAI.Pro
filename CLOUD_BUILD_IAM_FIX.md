# Cloud Build IAM Permission Fix - October 20, 2025

## Problem
Cloud Run deployment via GitHub Actions was failing with:
`
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Build failed because 
the default service account is missing required IAM permissions.
`

## Root Cause
The Cloud Build service account (26140490557@cloudbuild.gserviceaccount.com) 
lacked the necessary IAM permissions to:
1. Deploy to Cloud Run
2. Impersonate service accounts
3. Create/manage Cloud Storage buckets for source uploads

## Solution Implemented

### IAM Roles Granted to Cloud Build Service Account

1. **Cloud Run Admin** (oles/run.admin)
   - Allows deployment and management of Cloud Run services

2. **Service Account User** (oles/iam.serviceAccountUser)
   - Enables impersonation of service accounts during deployment

3. **Storage Admin** (oles/storage.admin)
   - Permits creation of buckets and upload of source code

### Commands Executed
```powershell
# Get project number
gcloud projects describe infinity-ai-5ec7c --format='value(projectNumber)'
# Result: 26140490557

# Grant Cloud Run Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member='serviceAccount:26140490557@cloudbuild.gserviceaccount.com' \
  --role='roles/run.admin'

# Grant Service Account User
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member='serviceAccount:26140490557@cloudbuild.gserviceaccount.com' \
  --role='roles/iam.serviceAccountUser'

# Grant Storage Admin
gcloud projects add-iam-policy-binding infinity-ai-5ec7c \
  --member='serviceAccount:26140490557@cloudbuild.gserviceaccount.com' \
  --role='roles/storage.admin'
```

## Verification

### IAM Roles Check
```bash
gcloud projects get-iam-policy infinity-ai-5ec7c \
  --flatten='bindings[].members' \
  --format='table(bindings.role)' \
  --filter='bindings.members:26140490557@cloudbuild.gserviceaccount.com'
```

**Result:**
- ✅ roles/cloudbuild.builds.builder
- ✅ roles/iam.serviceAccountUser
- ✅ roles/run.admin
- ✅ roles/serviceusage.serviceUsageConsumer
- ✅ roles/storage.admin

### Pipeline Test Results

**Workflow Run #18638381161:**
- ✅ Frontend Build (34s)
- ✅ Engine A Build (36s)
- ✅ CI Summary (3s)

**Workflow Run #18638376329 (triggered by commit):**
- ✅ All jobs completed successfully

## Documentation Updated

Created comprehensive IAM documentation:
- File: GCP_IAM_CONFIGURATION.md
- Documents both GitHub Actions deployer and Cloud Build service accounts
- Includes troubleshooting guide for common IAM errors
- Provides verification commands

## Commit Details

**Commit:** 42e38ccd4
**Message:** docs(iam): add comprehensive GCP IAM configuration documentation

## Status: ✅ RESOLVED

The Cloud Build permission issue is completely resolved. All CI/CD pipelines 
are now functioning correctly with proper IAM permissions in place.
