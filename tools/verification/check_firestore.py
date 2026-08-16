
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from datetime import datetime

# Initialize Firebase (using ADC or default project)
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "project-841b7f97-5ee3-4fbe-920")
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={'projectId': project_id})

db = firestore.client()

USER_ID = "B79BqvTlaTZltC8uGO3jLxJBBt93"

def check_firestore():
    print(f"🔍 Checking Firestore for User {USER_ID}...")
    
    doc_ref = db.collection("users").document(USER_ID)
    doc = doc_ref.get()

    if doc.exists:
        print("   ✅ User Document Found:")
        data = doc.to_dict()
        print(json.dumps(data, indent=2, default=str))
        
        # Check specific fields (CamelCase)
        print(f"\n   dhanConnected: {data.get('dhanConnected')}")
        print(f"   dhanClientId: {data.get('dhanClientId')}")
        print(f"   lastUpdatedAt: {data.get('lastUpdatedAt')}")
    else:
        print("   ❌ User Document NOT Found")

if __name__ == "__main__":
    check_firestore()
