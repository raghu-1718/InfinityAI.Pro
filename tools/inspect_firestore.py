
import os
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

def inspect_user_credentials(user_id):
    print(f"\n--- Inspecting Credentials for {user_id} ---")
    doc_ref = db.collection("dhan_credentials").document(user_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        print(f"Document ID: {doc.id}")
        
        # Print Keys (avoid printing full secrets if possible, but we need to debug)
        print("Keys present:", list(data.keys()))
        
        if "credentials" in data:
            print("Nested 'credentials' keys:", list(data["credentials"].keys()))
            print("Client ID (Unknown):", data["credentials"].get("client_id"))
            
        if "clientId" in data:
            print("Flat 'clientId':", data.get("clientId"))
            
        print("Updated At:", data.get("updated_at") or data.get("lastUpdatedAt"))
        print("Connection Status:", data.get("connection_status"))
    else:
        print(f"❌ Document {user_id} NOT FOUND in 'dhan_credentials'")

def list_all_credentials():
    print("\n--- Listing ALL Credential Documents ---")
    docs = db.collection("dhan_credentials").stream()
    for doc in docs:
        print(f"- {doc.id}")

if __name__ == "__main__":
    USER_ID = "znyNtT2lW3MKHqFrVA6E0A2Iv3N2"
    inspect_user_credentials(USER_ID)
    list_all_credentials()
