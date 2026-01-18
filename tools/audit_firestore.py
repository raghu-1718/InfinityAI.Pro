
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as google_firestore

# Initialize Firestore
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        "projectId": "galvanic-pulsar-482815-h0",
    })

db = google_firestore.Client()

def audit_firestore():
    print(f"\n--- Auditing Firestore Collections for {db.project} ---")
    
    # List all collections
    collections = db.collections()
    
    report = []
    
    for collection in collections:
        col_name = collection.id
        docs = list(collection.stream())
        count = len(docs)
        print(f"\nCollection: {col_name} (Count: {count})")
        
        sample_keys = []
        if count > 0:
            sample_data = docs[0].to_dict()
            sample_keys = list(sample_data.keys())
            print(f"  - Sample Dict Keys: {sample_keys}")
            print(f"  - Sample Doc ID: {docs[0].id}")
            
        report.append({
            "collection": col_name,
            "count": count,
            "keys": sample_keys
        })

    return report

if __name__ == "__main__":
    audit_firestore()
