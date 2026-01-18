# 🔐 KMS Credential Encryption Setup Guide

**Priority**: MEDIUM (Fix #4 from security audit)
**Timeline**: 3-4 hours
**Status**: Ready to implement after engine deployments complete

---

## Overview

This guide implements end-to-end encryption for DhanHQ broker credentials using Google Cloud KMS (Key Management Service). Currently, credentials are stored in plaintext in Firestore (user-isolated but unencrypted).

**Security Improvement**:

- ✅ Credentials encrypted at rest with AES-256
- ✅ Key rotation supported
- ✅ Audit logs for all encryption/decryption operations
- ✅ Separation of duties (Cloud Functions encrypt, Engine C decrypts)

---

## Architecture

```
User → Frontend → Cloud Function (saveDhanCredentials)
                       ↓ Encrypt with KMS
                   Firestore (encrypted ciphertext)
                       ↓ Read encrypted
                   Engine C → Decrypt with KMS
                       ↓ Use plaintext credentials
                   DhanHQ API
```

**Key Points**:

- Encryption happens in Cloud Functions (server-side)
- Ciphertext stored in Firestore (never plaintext)
- Engine C decrypts on-demand (credentials never cached)
- KMS key never leaves Google infrastructure

---

## Step 1: Create KMS Key Ring and Key

### 1.1 Create Key Ring

```powershell
# Key ring is a logical grouping of keys (one-time setup)
gcloud kms keyrings create infinityai-credentials `
  --location=us-central1 `
  --project=galvanic-pulsar-482815-h0

# Verify creation
gcloud kms keyrings describe infinityai-credentials `
  --location=us-central1 `
  --project=galvanic-pulsar-482815-h0
```

**Expected Output**:

```yaml
createTime: "2026-01-19T..."
name: projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai-credentials
```

### 1.2 Create Encryption Key

```powershell
# Create symmetric encryption key for credentials
gcloud kms keys create dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --purpose=encryption `
  --rotation-period=90d `
  --next-rotation-time=2026-04-19T00:00:00Z `
  --project=galvanic-pulsar-482815-h0

# Verify creation
gcloud kms keys describe dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --project=galvanic-pulsar-482815-h0
```

**Expected Output**:

```yaml
createTime: "2026-01-19T..."
name: projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai-credentials/cryptoKeys/dhan-credentials
purpose: ENCRYPT_DECRYPT
versionTemplate:
  algorithm: GOOGLE_SYMMETRIC_ENCRYPTION
  protectionLevel: SOFTWARE
rotationPeriod: 7776000s # 90 days
nextRotationTime: "2026-04-19T00:00:00Z"
```

**Key Details**:

- **Algorithm**: AES-256-GCM (Google default)
- **Rotation**: Automatic every 90 days
- **Protection**: SOFTWARE (HSM available but more expensive)

---

## Step 2: Grant IAM Permissions

### 2.1 Identify Service Accounts

```powershell
# Cloud Functions default service account
$FUNCTIONS_SA = "galvanic-pulsar-482815-h0@appspot.gserviceaccount.com"

# Engine C service account
$ENGINE_C_SA = gcloud run services describe engine-c `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --format="value(spec.template.spec.serviceAccountName)"

Write-Host "Cloud Functions SA: $FUNCTIONS_SA"
Write-Host "Engine C SA: $ENGINE_C_SA"
```

### 2.2 Grant Cloud Functions Encrypter Permission

```powershell
# Cloud Functions needs to ENCRYPT credentials before storing
gcloud kms keys add-iam-policy-binding dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --member="serviceAccount:galvanic-pulsar-482815-h0@appspot.gserviceaccount.com" `
  --role="roles/cloudkms.cryptoKeyEncrypter" `
  --project=galvanic-pulsar-482815-h0

# Verify
gcloud kms keys get-iam-policy dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --project=galvanic-pulsar-482815-h0
```

### 2.3 Grant Engine C Decrypter Permission

```powershell
# Engine C needs to DECRYPT credentials when executing trades
gcloud kms keys add-iam-policy-binding dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --member="serviceAccount:$ENGINE_C_SA" `
  --role="roles/cloudkms.cryptoKeyDecrypter" `
  --project=galvanic-pulsar-482815-h0

# Verify
gcloud kms keys get-iam-policy dhan-credentials `
  --location=us-central1 `
  --keyring=infinityai-credentials `
  --project=galvanic-pulsar-482815-h0
```

**Expected IAM Policy**:

```yaml
bindings:
  - members:
      - serviceAccount:galvanic-pulsar-482815-h0@appspot.gserviceaccount.com
    role: roles/cloudkms.cryptoKeyEncrypter
  - members:
      - serviceAccount:[ENGINE-C-SA]
    role: roles/cloudkms.cryptoKeyDecrypter
```

---

## Step 3: Update Cloud Functions (Encryption)

### 3.1 Install KMS Client Library

**Location**: `infra/firebase/functions/package.json`

```json
{
  "dependencies": {
    "@google-cloud/kms": "^4.0.0",
    "firebase-admin": "^12.0.0",
    "firebase-functions": "^5.0.0"
  }
}
```

Run:

```powershell
cd infra/firebase/functions
npm install @google-cloud/kms --save
```

### 3.2 Create KMS Helper Module

**Location**: `infra/firebase/functions/src/kms.ts` (NEW FILE)

```typescript
import { KeyManagementServiceClient } from "@google-cloud/kms";

const kmsClient = new KeyManagementServiceClient();

const KEY_NAME =
  "projects/galvanic-pulsar-482815-h0/locations/us-central1/keyRings/infinityai-credentials/cryptoKeys/dhan-credentials";

export async function encryptCredential(plaintext: string): Promise<string> {
  const [encryptResponse] = await kmsClient.encrypt({
    name: KEY_NAME,
    plaintext: Buffer.from(plaintext, "utf8"),
  });

  if (!encryptResponse.ciphertext) {
    throw new Error("KMS encryption failed: no ciphertext returned");
  }

  // Return base64-encoded ciphertext for Firestore storage
  return Buffer.from(encryptResponse.ciphertext).toString("base64");
}

export async function testKMSConnection(): Promise<boolean> {
  try {
    const testPlaintext = "test-connection";
    const ciphertext = await encryptCredential(testPlaintext);
    return ciphertext.length > 0;
  } catch (error) {
    console.error("KMS connection test failed:", error);
    return false;
  }
}
```

### 3.3 Update saveDhanCredentials Function

**Location**: `infra/firebase/functions/src/storeCredentials.ts`

**BEFORE** (current plaintext storage):

```typescript
export const saveDhanCredentials = onCall(async (request) => {
  const { client_id, access_token } = request.data;
  const uid = request.auth?.uid;

  if (!uid) throw new HttpsError("unauthenticated", "User must be logged in");

  await db.collection("user_broker_credentials").doc(uid).set({
    dhan_client_id: client_id, // ❌ PLAINTEXT
    dhan_access_token: access_token, // ❌ PLAINTEXT
    last_updated: admin.firestore.FieldValue.serverTimestamp(),
  });

  return { success: true };
});
```

**AFTER** (KMS-encrypted storage):

```typescript
import { encryptCredential } from "./kms";

export const saveDhanCredentials = onCall(async (request) => {
  const { client_id, access_token } = request.data;
  const uid = request.auth?.uid;

  if (!uid) throw new HttpsError("unauthenticated", "User must be logged in");

  // ✅ Encrypt sensitive fields with KMS
  const encryptedClientId = await encryptCredential(client_id);
  const encryptedAccessToken = await encryptCredential(access_token);

  await db.collection("user_broker_credentials").doc(uid).set({
    dhan_client_id_encrypted: encryptedClientId, // ✅ ENCRYPTED
    dhan_access_token_encrypted: encryptedAccessToken, // ✅ ENCRYPTED
    encryption_key_version: KEY_NAME,
    last_updated: admin.firestore.FieldValue.serverTimestamp(),
  });

  return { success: true };
});
```

### 3.4 Deploy Updated Cloud Functions

```powershell
cd infra/firebase/functions
npm run build
firebase deploy --only functions --project=galvanic-pulsar-482815-h0
```

---

## Step 4: Update Engine C (Decryption)

### 4.1 Install KMS Client Library

**Location**: `backend/engine-c/requirements.txt`

Add:

```txt
google-cloud-kms>=2.16.0
```

Rebuild:

```powershell
cd backend/engine-c
pip install -r requirements.txt
```

### 4.2 Create KMS Helper Module

**Location**: `backend/engine-c/src/kms_helper.py` (NEW FILE)

```python
from google.cloud import kms
import base64
import os
from typing import Optional

# KMS client (initialized once)
_kms_client: Optional[kms.KeyManagementServiceClient] = None

KEY_NAME = (
    "projects/galvanic-pulsar-482815-h0/locations/us-central1/"
    "keyRings/infinityai-credentials/cryptoKeys/dhan-credentials"
)

def get_kms_client() -> kms.KeyManagementServiceClient:
    """Get or create KMS client (singleton pattern)."""
    global _kms_client
    if _kms_client is None:
        _kms_client = kms.KeyManagementServiceClient()
    return _kms_client

def decrypt_credential(ciphertext_base64: str) -> str:
    """Decrypt KMS-encrypted credential.

    Args:
        ciphertext_base64: Base64-encoded ciphertext from Firestore

    Returns:
        Decrypted plaintext credential

    Raises:
        Exception: If decryption fails
    """
    client = get_kms_client()

    # Decode base64 ciphertext
    ciphertext = base64.b64decode(ciphertext_base64)

    # Decrypt with KMS
    response = client.decrypt(
        request={
            "name": KEY_NAME,
            "ciphertext": ciphertext,
        }
    )

    # Return plaintext as string
    return response.plaintext.decode('utf-8')

def test_kms_connection() -> bool:
    """Test KMS connection and permissions."""
    try:
        client = get_kms_client()
        # Test encryption (requires cryptoKeyEncrypter permission)
        test_plaintext = b"test-connection"
        response = client.encrypt(
            request={
                "name": KEY_NAME,
                "plaintext": test_plaintext,
            }
        )
        return len(response.ciphertext) > 0
    except Exception as e:
        print(f"KMS connection test failed: {e}")
        return False
```

### 4.3 Update Credential Loading Logic

**Location**: `backend/engine-c/src/dhan_client_wrapper.py`

**BEFORE** (reads plaintext):

```python
def load_user_credentials(uid: str) -> dict:
    cred_doc = db.collection('user_broker_credentials').document(uid).get()

    if not cred_doc.exists:
        raise ValueError(f"No credentials found for user {uid}")

    cred_data = cred_doc.to_dict()
    return {
        'client_id': cred_data['dhan_client_id'],      # ❌ PLAINTEXT
        'access_token': cred_data['dhan_access_token'], # ❌ PLAINTEXT
    }
```

**AFTER** (decrypts with KMS):

```python
from .kms_helper import decrypt_credential

def load_user_credentials(uid: str) -> dict:
    cred_doc = db.collection('user_broker_credentials').document(uid).get()

    if not cred_doc.exists:
        raise ValueError(f"No credentials found for user {uid}")

    cred_data = cred_doc.to_dict()

    # ✅ Decrypt credentials with KMS
    client_id = decrypt_credential(cred_data['dhan_client_id_encrypted'])
    access_token = decrypt_credential(cred_data['dhan_access_token_encrypted'])

    return {
        'client_id': client_id,
        'access_token': access_token,
    }
```

### 4.4 Rebuild and Deploy Engine C

```powershell
# Rebuild Docker image
gcloud builds submit `
  --config=backend/engine-c/cloudbuild.yaml `
  --project=galvanic-pulsar-482815-h0 `
  --region=us-central1

# Deploy to Cloud Run
gcloud run deploy engine-c `
  --image=us-central1-docker.pkg.dev/galvanic-pulsar-482815-h0/infinityai/engine-c:latest `
  --region=us-central1 `
  --project=galvanic-pulsar-482815-h0 `
  --set-env-vars="ENVIRONMENT=production,GOOGLE_CLOUD_PROJECT=galvanic-pulsar-482815-h0" `
  --allow-unauthenticated
```

---

## Step 5: Migrate Existing Credentials

### 5.1 Create Migration Script

**Location**: `tools/migrate_credentials_to_kms.py` (NEW FILE)

```python
#!/usr/bin/env python3
"""
Migrate existing plaintext credentials to KMS-encrypted format.

This script:
1. Reads all plaintext credentials from Firestore
2. Encrypts them with KMS
3. Writes encrypted versions back to Firestore
4. Verifies decryption works
5. Optionally deletes plaintext fields
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google.cloud import firestore, kms
import base64
from typing import Dict, List

# Initialize clients
db = firestore.Client(project='galvanic-pulsar-482815-h0')
kms_client = kms.KeyManagementServiceClient()

KEY_NAME = (
    "projects/galvanic-pulsar-482815-h0/locations/us-central1/"
    "keyRings/infinityai-credentials/cryptoKeys/dhan-credentials"
)

def encrypt_credential(plaintext: str) -> str:
    """Encrypt credential with KMS."""
    response = kms_client.encrypt(
        request={
            "name": KEY_NAME,
            "plaintext": plaintext.encode('utf-8'),
        }
    )
    return base64.b64encode(response.ciphertext).decode('utf-8')

def decrypt_credential(ciphertext_base64: str) -> str:
    """Decrypt credential with KMS (for verification)."""
    ciphertext = base64.b64decode(ciphertext_base64)
    response = kms_client.decrypt(
        request={
            "name": KEY_NAME,
            "ciphertext": ciphertext,
        }
    )
    return response.plaintext.decode('utf-8')

def migrate_user_credentials(uid: str, cred_data: Dict, dry_run: bool = True) -> bool:
    """Migrate a single user's credentials."""
    print(f"\n🔄 Migrating user: {uid}")

    # Check if already migrated
    if 'dhan_client_id_encrypted' in cred_data:
        print(f"  ✓ Already encrypted, skipping")
        return True

    # Check for plaintext fields
    if 'dhan_client_id' not in cred_data or 'dhan_access_token' not in cred_data:
        print(f"  ⚠ Missing plaintext credentials, skipping")
        return False

    try:
        # Encrypt credentials
        plaintext_client_id = cred_data['dhan_client_id']
        plaintext_access_token = cred_data['dhan_access_token']

        print(f"  🔐 Encrypting client_id...")
        encrypted_client_id = encrypt_credential(plaintext_client_id)

        print(f"  🔐 Encrypting access_token...")
        encrypted_access_token = encrypt_credential(plaintext_access_token)

        # Verify decryption works
        print(f"  🔍 Verifying decryption...")
        decrypted_client_id = decrypt_credential(encrypted_client_id)
        decrypted_access_token = decrypt_credential(encrypted_access_token)

        if decrypted_client_id != plaintext_client_id:
            raise ValueError("Client ID decryption verification failed!")
        if decrypted_access_token != plaintext_access_token:
            raise ValueError("Access token decryption verification failed!")

        print(f"  ✓ Encryption/decryption verified")

        # Write to Firestore
        if not dry_run:
            print(f"  💾 Writing encrypted credentials to Firestore...")
            db.collection('user_broker_credentials').document(uid).update({
                'dhan_client_id_encrypted': encrypted_client_id,
                'dhan_access_token_encrypted': encrypted_access_token,
                'encryption_key_version': KEY_NAME,
                'migrated_at': firestore.SERVER_TIMESTAMP,
            })

            # Delete plaintext fields (optional - keep for rollback)
            # db.collection('user_broker_credentials').document(uid).update({
            #     'dhan_client_id': firestore.DELETE_FIELD,
            #     'dhan_access_token': firestore.DELETE_FIELD,
            # })

            print(f"  ✅ Migration complete")
        else:
            print(f"  [DRY RUN] Would write encrypted credentials")

        return True

    except Exception as e:
        print(f"  ❌ Migration failed: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Migrate credentials to KMS encryption')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without writing')
    parser.add_argument('--uid', help='Migrate specific user only')
    args = parser.parse_args()

    print("=" * 60)
    print("Credential Migration to KMS Encryption")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"KMS Key: {KEY_NAME}")
    print("=" * 60)

    # Get all credentials
    if args.uid:
        print(f"\nMigrating single user: {args.uid}")
        doc = db.collection('user_broker_credentials').document(args.uid).get()
        if not doc.exists:
            print(f"❌ User {args.uid} not found")
            sys.exit(1)
        credentials = [(args.uid, doc.to_dict())]
    else:
        print("\nFetching all user credentials...")
        docs = db.collection('user_broker_credentials').stream()
        credentials = [(doc.id, doc.to_dict()) for doc in docs]
        print(f"Found {len(credentials)} users")

    # Migrate each user
    success_count = 0
    skip_count = 0
    fail_count = 0

    for uid, cred_data in credentials:
        result = migrate_user_credentials(uid, cred_data, dry_run=args.dry_run)
        if result is True:
            success_count += 1
        elif result is None:
            skip_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {success_count}")
    print(f"⏭  Skipped: {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print("=" * 60)

    if args.dry_run:
        print("\n⚠ DRY RUN COMPLETE - No changes written to Firestore")
        print("Run without --dry-run to perform actual migration")
    else:
        print("\n✅ MIGRATION COMPLETE")

if __name__ == '__main__':
    main()
```

### 5.2 Run Migration

```powershell
# TEST FIRST (dry run)
cd c:\workspace\InfinityAI.Pro
python tools/migrate_credentials_to_kms.py --dry-run

# MIGRATE ONE USER (test)
python tools/migrate_credentials_to_kms.py --uid=<TEST_USER_UID>

# MIGRATE ALL USERS (production)
python tools/migrate_credentials_to_kms.py
```

---

## Step 6: Verification & Testing

### 6.1 Test KMS Encryption/Decryption

```powershell
# Test Cloud Functions encryption
curl -X POST https://us-central1-galvanic-pulsar-482815-h0.cloudfunctions.net/saveDhanCredentials `
  -H "Authorization: Bearer <FIREBASE_ID_TOKEN>" `
  -H "Content-Type: application/json" `
  -d '{"client_id":"test-client-id","access_token":"test-access-token"}'

# Verify in Firestore (should see encrypted fields)
gcloud firestore collections documents list user_broker_credentials `
  --project=galvanic-pulsar-482815-h0 `
  --limit=1
```

### 6.2 Test Engine C Decryption

```powershell
# Test Engine C can load and decrypt credentials
curl -X POST https://engine-c-228557716858.us-central1.run.app/api/dhan/test-credentials `
  -H "Content-Type: application/json" `
  -d '{"uid":"<TEST_USER_UID>"}'

# Expected: {"status":"success","credentials_loaded":true}
```

### 6.3 End-to-End Trading Test

```powershell
# Place test order (will use decrypted credentials internally)
curl -X POST https://engine-c-228557716858.us-central1.run.app/api/execute-order `
  -H "Content-Type: application/json" `
  -d '{
    "uid":"<USER_UID>",
    "symbol":"NIFTY2602520000CE",
    "quantity":1,
    "side":"BUY",
    "order_type":"LIMIT",
    "price":100
  }'

# Verify order placed with DhanHQ
```

---

## Security Checklist

Before marking this complete, verify:

- [ ] KMS key created with 90-day rotation
- [ ] Cloud Functions has `cryptoKeyEncrypter` permission
- [ ] Engine C has `cryptoKeyDecrypter` permission
- [ ] Cloud Functions code encrypts before Firestore write
- [ ] Engine C code decrypts after Firestore read
- [ ] Migration script tested on one user successfully
- [ ] All existing users migrated
- [ ] End-to-end trading test successful with encrypted credentials
- [ ] Firestore shows no plaintext `dhan_client_id` or `dhan_access_token` fields
- [ ] Cloud Logging shows KMS decrypt operations (audit trail)

---

## Rollback Plan

If issues occur:

1. **Keep plaintext fields temporarily** (don't delete during migration)
2. **Revert Cloud Functions** to read plaintext fields
3. **Revert Engine C** to read plaintext fields
4. **Redeploy** both services
5. **Debug** KMS permissions or code issues
6. **Re-migrate** once fixed

**Plaintext Cleanup** (only after 1 week of successful production use):

```python
# Delete plaintext fields from all users
for doc in db.collection('user_broker_credentials').stream():
    db.collection('user_broker_credentials').document(doc.id).update({
        'dhan_client_id': firestore.DELETE_FIELD,
        'dhan_access_token': firestore.DELETE_FIELD,
    })
```

---

## Cost Estimate

**KMS Pricing** (us-central1):

- Key versions: $0.06/month per active version
- Encrypt operations: $0.03 per 10,000 operations
- Decrypt operations: $0.03 per 10,000 operations

**Estimated Monthly Cost**:

- 1 active key version: $0.06
- 1,000 users × 2 credentials × 1 save/month = 2,000 encrypts: $0.01
- 1,000 users × 2 credentials × 30 trades/month = 60,000 decrypts: $0.18
- **Total: ~$0.25/month** (negligible)

---

## Timeline

| Task                        | Duration      | Dependencies           |
| --------------------------- | ------------- | ---------------------- |
| Create KMS key ring and key | 5 min         | GCP CLI access         |
| Grant IAM permissions       | 5 min         | Service accounts exist |
| Update Cloud Functions code | 45 min        | KMS module, testing    |
| Deploy Cloud Functions      | 5 min         | Code tested            |
| Update Engine C code        | 45 min        | KMS module, testing    |
| Rebuild & deploy Engine C   | 10 min        | Build system working   |
| Create migration script     | 60 min        | Testing, verification  |
| Test migration (1 user)     | 15 min        | KMS permissions        |
| Migrate all users           | 15 min        | Script tested          |
| End-to-end verification     | 30 min        | Test trading account   |
| **TOTAL**                   | **3-4 hours** | -                      |

---

## Next Steps

After engine deployments complete:

1. Create KMS key ring and key (5 min)
2. Grant IAM permissions (5 min)
3. Update and deploy Cloud Functions (1 hour)
4. Update and deploy Engine C (1 hour)
5. Run migration script (30 min)
6. Verify end-to-end (30 min)

**Status**: ✅ Ready to implement
**Blocker**: None (can start immediately after current deployments finish)
