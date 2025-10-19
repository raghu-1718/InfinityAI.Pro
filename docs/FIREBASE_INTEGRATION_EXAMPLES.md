# Firebase Integration Example

## Python Example - Using Firebase Admin SDK

### Install Dependencies
```bash
pip install firebase-admin google-cloud-secret-manager
```

### Option 1: Direct Secret Manager Access
```python
# backend/engines/engine-d/firebase_service.py
from google.cloud import secretmanager
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import os

class FirebaseService:
    def __init__(self):
        self.project_id = "after-yesterday-473512-k3"
        self.secret_name = "firebase-service-account"
        self.db = None
        self.app = None
        self._initialize()
    
    def _get_credentials_from_secret_manager(self):
        """Fetch Firebase credentials from Google Secret Manager"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{self.project_id}/secrets/{self.secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": secret_path})
            secret_data = response.payload.data.decode("UTF-8")
            
            return json.loads(secret_data)
        except Exception as e:
            print(f"Error fetching Firebase credentials: {e}")
            raise
    
    def _initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                creds_dict = self._get_credentials_from_secret_manager()
                cred = credentials.Certificate(creds_dict)
                
                self.app = firebase_admin.initialize_app(cred, {
                    'projectId': 'infinity-ai-5ec7c',
                })
                
                self.db = firestore.client()
                print("✅ Firebase initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                self.db = firestore.client()
                print("✅ Firebase already initialized")
                
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise
    
    def save_trade(self, trade_data: dict) -> str:
        """Save trade to Firestore"""
        try:
            doc_ref = self.db.collection('trades').document()
            doc_ref.set(trade_data)
            return doc_ref.id
        except Exception as e:
            print(f"Error saving trade: {e}")
            raise
    
    def get_user_trades(self, user_id: str, limit: int = 100):
        """Get trades for a user"""
        try:
            trades_ref = self.db.collection('trades')
            query = trades_ref.where('user_id', '==', user_id).limit(limit)
            docs = query.stream()
            
            return [{'id': doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            print(f"Error fetching trades: {e}")
            raise
    
    def verify_user_token(self, id_token: str):
        """Verify Firebase Auth token"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

# Usage example
firebase_service = FirebaseService()

# Save a trade
trade_data = {
    "user_id": "user123",
    "symbol": "NIFTY",
    "quantity": 100,
    "price": 18500,
    "timestamp": firestore.SERVER_TIMESTAMP
}
trade_id = firebase_service.save_trade(trade_data)
print(f"Trade saved with ID: {trade_id}")

# Get user trades
trades = firebase_service.get_user_trades("user123")
print(f"Found {len(trades)} trades")
```

### Option 2: Using Environment Variable in Cloud Run
```python
# Simpler approach when secret is mounted as env var
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

def initialize_firebase():
    """Initialize Firebase from environment variable"""
    try:
        # Read credentials from environment variable set by Cloud Run
        creds_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if not creds_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT environment variable not set")
        
        creds_dict = json.loads(creds_json)
        cred = credentials.Certificate(creds_dict)
        
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        return db
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        raise

# Initialize once at module level
db = initialize_firebase()
```

## FastAPI Integration Example

```python
# backend/engines/engine-d/main.py
from fastapi import FastAPI, HTTPException, Depends
from firebase_service import FirebaseService
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()
firebase = FirebaseService()

class TradeCreate(BaseModel):
    user_id: str
    symbol: str
    quantity: int
    price: float
    side: str  # "BUY" or "SELL"

@app.post("/api/trades")
async def create_trade(trade: TradeCreate):
    """Save a trade to Firebase"""
    try:
        trade_data = {
            **trade.dict(),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "executed"
        }
        
        trade_id = firebase.save_trade(trade_data)
        
        return {
            "status": "success",
            "trade_id": trade_id,
            "message": "Trade saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trades/{user_id}")
async def get_trades(user_id: str, limit: int = 100):
    """Get trades for a user"""
    try:
        trades = firebase.get_user_trades(user_id, limit)
        return {
            "status": "success",
            "count": len(trades),
            "trades": trades
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/verify")
async def verify_token(token: str):
    """Verify Firebase Auth token"""
    try:
        decoded = firebase.verify_user_token(token)
        if not decoded:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "status": "success",
            "user_id": decoded['uid'],
            "email": decoded.get('email')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token verification failed")
```

## Cloud Run Deployment with Firebase Secret

### Deploy with Secret as Environment Variable
```bash
#!/bin/bash
# deploy-with-firebase.sh

SERVICE_NAME="engine-d-orchestration-prod"
IMAGE="gcr.io/after-yesterday-473512-k3/engine-d:latest"
REGION="us-central1"

gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-secrets=FIREBASE_SERVICE_ACCOUNT=firebase-service-account:latest \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=10
```

### Deploy with Secret as Volume Mount
```bash
gcloud run deploy engine-d-orchestration-prod \
  --image=gcr.io/after-yesterday-473512-k3/engine-d:latest \
  --region=us-central1 \
  --set-secrets=/secrets/firebase-sa.json=firebase-service-account:latest
```

## Dockerfile Example with Firebase
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# The secret will be injected by Cloud Run at runtime
# No need to COPY or include credentials in the image

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### requirements.txt
```
firebase-admin==6.2.0
google-cloud-secret-manager==2.16.4
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

## Testing Locally

For local development, you can use Application Default Credentials:

```bash
# Authenticate with gcloud
gcloud auth application-default login

# Run your app - it will automatically use your credentials
python main.py
```

Or download the secret for local testing:
```bash
gcloud secrets versions access latest --secret="firebase-service-account" > firebase-sa.json

# Export environment variable
export GOOGLE_APPLICATION_CREDENTIALS="./firebase-sa.json"

# Run your app
python main.py

# Don't forget to add firebase-sa.json to .gitignore!
```

## Security Notes

1. ✅ **DO**: Use Secret Manager to store credentials
2. ✅ **DO**: Grant minimal IAM permissions
3. ✅ **DO**: Use environment variables or volume mounts in Cloud Run
4. ❌ **DON'T**: Commit credentials to git
5. ❌ **DON'T**: Include credentials in Docker images
6. ❌ **DON'T**: Log credential values
7. ❌ **DON'T**: Expose secret endpoints publicly
