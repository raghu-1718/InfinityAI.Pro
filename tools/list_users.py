import firebase_admin
from firebase_admin import credentials, firestore
import os

PROJECT_ID = "gen-lang-client-0779271931"

def list_users():
    try:
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
        
        db = firestore.client()
        users_ref = db.collection(u'users')
        docs = users_ref.stream()
        
        with open("users.txt", "w", encoding="utf-8") as f:
            f.write(f"Listing Users in project: {PROJECT_ID}\n")
            f.write("-" * 50 + "\n")
            found = False
            for doc in docs:
                found = True
                data = doc.to_dict()
                name = data.get('displayName') or data.get('name') or "Unknown"
                email = data.get('email', 'No Email')
                dhan_connected = data.get('dhanConnected', False)
                f.write(f"ID: {doc.id} | Name: {name} | Email: {email} | Dhan Connected: {dhan_connected}\n")
            
            if not found:
                f.write("No users found.\n")
            
    except Exception as e:
        with open("users.txt", "w", encoding="utf-8") as f:
             f.write(f"Error: {e}")

if __name__ == "__main__":
    list_users()
