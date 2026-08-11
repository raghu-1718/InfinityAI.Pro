import firebase_admin
from firebase_admin import credentials, firestore

project_id = 'project-841b7f97-5ee3-4fbe-920'
cred = credentials.ApplicationDefault()
try:
    firebase_admin.initialize_app(cred, {'projectId': project_id})
except Exception:
    pass

db = firestore.client()

print('=== USER_CREDENTIALS COLLECTION ===')
uc_docs = list(db.collection('user_credentials').stream())
print(f'Total user_credentials docs: {len(uc_docs)}')
for doc in uc_docs:
    d = doc.to_dict()
    cid = d.get("dhan_client_id") or d.get("client_id")
    print(f'Doc ID: {doc.id} | client_id: {cid} | keys: {list(d.keys())}')

print('\n=== USERS COLLECTION ===')
u_docs = list(db.collection('users').stream())
print(f'Total users docs: {len(u_docs)}')
for doc in u_docs:
    d = doc.to_dict()
    print(f'Doc ID: {doc.id} | keys: {list(d.keys())}')
