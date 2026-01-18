from google.cloud import firestore
import os

# Implicit auth using ADC
db = firestore.Client()

def check_creds():
    print("Checking 'dhan_credentials' collection...")
    try:
        docs = db.collection('dhan_credentials').stream()
        found = False
        for doc in docs:
            found = True
            data = doc.to_dict()
            print(f"Document ID: {doc.id}")
            print(f"  -> All Data: {data}")
        
        if not found:
            print("No documents found in 'dhan_credentials'.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_creds()
