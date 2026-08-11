"""Script to clear user_credentials collection in Firestore."""
import firebase_admin
from firebase_admin import credentials, firestore
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
cred = credentials.ApplicationDefault()
try:
    firebase_admin.initialize_app(cred, {'projectId': project_id})
except Exception:
    pass

db = firestore.client()

print("=" * 70)
print(f"CLEARING 'user_credentials' COLLECTION IN PROJECT: {project_id}")
print("=" * 70)

uc_ref = db.collection("user_credentials")
docs = list(uc_ref.stream())

deleted_count = 0
for doc in docs:
    print(f"Deleting document ID: {doc.id}")
    doc.reference.delete()
    deleted_count += 1

print("-" * 70)
print(f"✅ Successfully deleted {deleted_count} document(s) from 'user_credentials' collection.")
print("The collection is now clean and ready for fresh setup from the frontend Settings page.")
print("=" * 70)
