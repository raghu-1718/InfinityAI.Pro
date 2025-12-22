# Firestore Backup Configuration

## Automated Daily Backups

### Using gcloud firestore export

Create a Cloud Scheduler job to run daily backups:

```bash
# Create GCS bucket for backups
gsutil mb -p gen-lang-client-0779271931 -c STANDARD -l us-central1 gs://infinityai-firestore-backups

# Create service account for backups
gcloud iam service-accounts create firestore-backup-sa \
  --display-name="Firestore Backup Service Account" \
  --project=gen-lang-client-0779271931

# Grant necessary permissions
gcloud projects add-iam-policy-binding gen-lang-client-0779271931 \
  --member="serviceAccount:firestore-backup-sa@gen-lang-client-0779271931.iam.gserviceaccount.com" \
  --role="roles/datastore.importExportAdmin"

gsutil iam ch serviceAccount:firestore-backup-sa@gen-lang-client-0779271931.iam.gserviceaccount.com:objectAdmin \
  gs://infinityai-firestore-backups

# Create Cloud Scheduler job (runs daily at 2 AM UTC)
gcloud scheduler jobs create http firestore-daily-backup \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/gen-lang-client-0779271931/databases/(default):exportDocuments" \
  --message-body='{"outputUriPrefix":"gs://infinityai-firestore-backups"}' \
  --oauth-service-account-email="firestore-backup-sa@gen-lang-client-0779271931.iam.gserviceaccount.com" \
  --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
  --location="us-central1" \
  --project=gen-lang-client-0779271931
```

### Manual Backup

```bash
gcloud firestore export gs://infinityai-firestore-backups \
  --project=gen-lang-client-0779271931
```

### Restore from Backup

```bash
gcloud firestore import gs://infinityai-firestore-backups/[EXPORT_PREFIX] \
  --project=gen-lang-client-0779271931
```

## Backup Retention Policy

- **Daily backups:** Retained for 30 days
- **Weekly backups:** Retained for 90 days  
- **Monthly backups:** Retained for 1 year

### Lifecycle Policy

```bash
# Create lifecycle.json
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

# Apply lifecycle policy
gsutil lifecycle set lifecycle.json gs://infinityai-firestore-backups
```

## Monitoring

View backup status in Cloud Scheduler:
https://console.cloud.google.com/cloudscheduler?project=gen-lang-client-0779271931

## Notes

- Backups are incremental and include all collections
- Export/import operations don't affect database availability
- Backups can be used for disaster recovery or data migration
- Consider enabling Point-in-Time Recovery (PITR) for additional protection
