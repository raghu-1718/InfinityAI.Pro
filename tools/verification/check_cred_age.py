import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize with implicit certs
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.client()

def check_creds(field, value):
    print(f"\nSearching for {field} = {value}...")
    try:
        # Check modern nested path
        query = db.collection('dhan_credentials').where(f'credentials.{field}', '==', value)
        docs = list(query.stream())
        
        if not docs:
            # Check legacy flat path
            query = db.collection('dhan_credentials').where(field, '==', value)
            docs = list(query.stream())

        if docs:
            for doc in docs:
                data = doc.to_dict()
                updated = data.get('updated_at')
                created = data.get('created_at')
                print(f"✅ Found Document ID: {doc.id}")
                print(f"   Connection Status: {data.get('connection_status')}")
                print(f"   Last Updated: {updated} ({(datetime.now().astimezone() - updated).total_seconds()/3600:.1f} hours ago)" if updated else "   Last Updated: Unknown")
        else:
            print(f"❌ No credentials found for {value}")
    except Exception as e:
        print(f"Error: {e}")

check_creds('client_id', '1101302170')
check_creds('clientId', '1101302170')
