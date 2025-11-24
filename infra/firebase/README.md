# infra/firebase/README.md

## Firebase Configuration for InfinityAI.Pro

This directory contains Firestore security rules, indexes, and storage configurations for the InfinityAI.Pro platform.

### Files

- **firestore.rules**: Firestore security rules for read/write access control
- **firestore.indexes.json**: Composite indexes for optimal query performance
- **storage.rules**: Firebase Storage security rules (if using Cloud Storage)
- **firebase.json.template**: Base template for firebase.json configuration
- **.firebaserc.template**: Template for .firebaserc project configuration

### How to Deploy

```bash
# Deploy Firestore rules
firebase deploy --only firestore:rules --project=after-yesterday-473512-k3

# Deploy Firestore indexes
firebase deploy --only firestore:indexes --project=after-yesterday-473512-k3

# Deploy Storage rules
firebase deploy --only storage --project=after-yesterday-473512-k3
```

### Environment-Specific Configs

Sync these files with `frontend/web` before deployment:
- Copy `firestore.indexes.json` to `frontend/web/firestore.indexes.json`
- Copy rules to `frontend/web` directory as needed

### Security Best Practices

- Rules enforce authentication checks (JWT tokens)
- Read/write access limited to authenticated users with proper roles
- Sensitive data (API keys, credentials) stored in Secret Manager, not Firestore
