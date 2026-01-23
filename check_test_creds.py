import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()
uid = 'B79BqvTlaTZltC8uGO3jLxJBBt93'

# Check dhan_credentials collection
doc = db.collection('dhan_credentials').document(uid).get()
print(f'User UID: {uid}')
print(f'Has dhan_credentials doc: {doc.exists}')
if doc.exists:
    data = doc.to_dict()
    print(f'Fields: {list(data.keys())}')
    print(f'client_id present: {"client_id" in data}')
    print(f'accessToken present: {"accessToken" in data}')
    if 'client_id' in data:
        print(f'client_id: {data["client_id"]}')
    if 'credentials' in data:
        print(f'credentials field type: {type(data["credentials"])}')
