# Firebase Service Account Setup

## Overview
This document describes how the Firebase service account credentials are securely stored and accessed in the InfinityAI.Pro platform.

## Secret Manager Configuration

### Secret Details
- **Secret Name**: `firebase-service-account`
- **Project**: `gen-lang-client-0779271931` (Project ID: 429140669077)
- **Firebase Project**: `infinity-ai-5ec7c`
- **Service Account Email**: `firebase-adminsdk-fbsvc@infinity-ai-5ec7c.iam.gserviceaccount.com`
- **Replication**: Automatic (multi-region)
- **Created**: October 19, 2025

### Access Secret from Cloud Run Services

To access the Firebase service account from your Cloud Run services:

#### Option 1: Environment Variable (Recommended)
Add the secret as an environment variable in your Cloud Run service:

**Bash/Linux:**
```bash
gcloud run services update SERVICE_NAME \
  --update-secrets=FIREBASE_SERVICE_ACCOUNT=firebase-service-account:latest \
  --region=us-central1
```

**PowerShell:**
```powershell
gcloud run services update SERVICE_NAME --update-secrets=FIREBASE_SERVICE_ACCOUNT=firebase-service-account:latest --region=us-central1
```

Then in your code:
```python
import os
import json

# Read from environment variable
firebase_creds = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
```

#### Option 2: Volume Mount
Mount the secret as a file:

**Bash/Linux:**
```bash
gcloud run services update SERVICE_NAME \
  --update-secrets=/secrets/firebase-sa.json=firebase-service-account:latest \
  --region=us-central1
```

**PowerShell:**
```powershell
gcloud run services update SERVICE_NAME --update-secrets=/secrets/firebase-sa.json=firebase-service-account:latest --region=us-central1
```

Then in your code:
```python
import firebase_admin
from firebase_admin import credentials

# Initialize with service account file
cred = credentials.Certificate('/secrets/firebase-sa.json')
firebase_admin.initialize_app(cred)
```

#### Option 3: Secret Manager API
Access programmatically using Secret Manager client:

```python
from google.cloud import secretmanager

def get_firebase_credentials():
    """Fetch Firebase credentials from Secret Manager"""
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/429140669077/secrets/firebase-service-account/versions/latest"
    
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### Grant Access to Service Accounts

To allow a Cloud Run service to access the secret:

**Bash/Linux:**
```bash
# Get the service account email for your Cloud Run service
SERVICE_ACCOUNT=$(gcloud run services describe SERVICE_NAME --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')

# Grant Secret Manager Secret Accessor role
gcloud secrets add-iam-policy-binding firebase-service-account \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

**PowerShell:**
```powershell
# Get the service account email for your Cloud Run service
$SERVICE_ACCOUNT = gcloud run services describe SERVICE_NAME --region=us-central1 --format='value(spec.template.spec.serviceAccountName)'

# Grant Secret Manager Secret Accessor role
gcloud secrets add-iam-policy-binding firebase-service-account --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"
```

### Verify Access

Test that the secret is accessible:

```bash
# View secret metadata
gcloud secrets describe firebase-service-account

# List versions
gcloud secrets versions list firebase-service-account

# Access the secret value (be careful with this in production)
gcloud secrets versions access latest --secret="firebase-service-account"
```

## Security Best Practices

1. **Never commit credentials to git** - Always use Secret Manager
2. **Use least privilege** - Only grant access to services that need it
3. **Rotate credentials** - Periodically create new versions of the secret
4. **Audit access** - Monitor who accesses the secret via Cloud Logging
5. **Use latest version** - Reference `latest` version in production for automatic updates

## Rotation Procedure

To rotate the Firebase service account key:

1. Create a new service account key in Firebase Console
2. Create a new version of the secret:
   ```bash
   echo 'NEW_JSON_CONTENT' | gcloud secrets versions add firebase-service-account --data-file=-
   ```
3. Test with new version
4. Delete old Firebase key in Firebase Console
5. Optionally disable old secret version:
   ```bash
   gcloud secrets versions disable VERSION_NUMBER --secret=firebase-service-account
   ```

## Troubleshooting

### Permission Denied
If you get permission denied errors:
- Ensure the service account has `roles/secretmanager.secretAccessor`
- Check that Secret Manager API is enabled: `gcloud services enable secretmanager.googleapis.com`

### Secret Not Found
Verify the secret exists:
```bash
gcloud secrets list | grep firebase-service-account
```

### Invalid Credentials
If Firebase initialization fails:
- Verify the secret content is valid JSON
- Check that the Firebase project ID matches
- Ensure the service account hasn't been deleted in Firebase Console

## Related Documentation
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
