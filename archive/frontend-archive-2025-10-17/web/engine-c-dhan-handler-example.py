# Mock Engine C Backend - Dhan OAuth Handler Example
# This demonstrates the backend endpoints needed for Dhan integration

from flask import Flask, request, jsonify
import os
import jwt
import requests
from datetime import datetime, timedelta
import secrets
import hashlib

app = Flask(__name__)

# Configuration
DHAN_API_BASE = "https://api.dhan.co"
DHAN_CLIENT_ID = os.getenv('DHAN_CLIENT_ID', 'demo_client_id')
DHAN_CLIENT_SECRET = os.getenv('DHAN_CLIENT_SECRET', 'demo_client_secret')
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))

# In-memory storage (use proper database in production)
user_tokens = {}
connection_status = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "engine-c-trading",
        "dhan_integration": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/dhan/status', methods=['GET'])
def get_dhan_status():
    """Get current Dhan connection status for user"""
    try:
        # Get user from authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Invalid authorization"}), 401
        
        token = auth_header.replace('Bearer ', '')
        user_id = extract_user_from_token(token)
        
        if user_id in connection_status:
            status = connection_status[user_id]
            return jsonify({
                "connected": status['connected'],
                "account_details": status.get('account_details'),
                "last_validated": status.get('last_validated'),
                "expires_at": status.get('expires_at')
            })
        else:
            return jsonify({
                "connected": False,
                "account_details": None,
                "last_validated": None,
                "expires_at": None
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dhan/callback', methods=['POST'])
def handle_oauth_callback():
    """Handle OAuth callback and exchange code for tokens"""
    try:
        data = request.get_json()
        code = data.get('code')
        state = data.get('state')
        redirect_uri = data.get('redirect_uri')
        
        print(f"🔄 Processing Dhan OAuth callback: code={code[:10]}..., state={state}")
        
        # Exchange authorization code for access token
        token_response = exchange_code_for_token(code, redirect_uri)
        
        if not token_response:
            return jsonify({"error": "Failed to exchange code for token"}), 400
        
        # Get user from authorization header
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        user_id = extract_user_from_token(token)
        
        # Store tokens securely (encrypt in production)
        user_tokens[user_id] = {
            "access_token": encrypt_token(token_response['access_token']),
            "refresh_token": encrypt_token(token_response.get('refresh_token')),
            "expires_at": datetime.utcnow() + timedelta(seconds=token_response.get('expires_in', 3600)),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Get account details from Dhan API
        account_details = get_dhan_account_details(token_response['access_token'])
        
        # Update connection status
        connection_status[user_id] = {
            "connected": True,
            "account_details": account_details,
            "last_validated": datetime.utcnow().isoformat(),
            "expires_at": user_tokens[user_id]["expires_at"].isoformat()
        }
        
        print(f"✅ Dhan account connected for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Dhan account connected successfully",
            "account_details": account_details
        })
        
    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dhan/postback', methods=['POST'])
def handle_dhan_postback():
    """Handle postback notifications from Dhan"""
    try:
        data = request.get_json()
        print(f"📨 Received Dhan postback: {data}")
        
        # Validate postback signature (implement signature verification)
        if not validate_postback_signature(data):
            return jsonify({"error": "Invalid signature"}), 401
        
        # Process different types of postback events
        event_type = data.get('event_type')
        user_account = data.get('user_account')
        
        if event_type == 'order_update':
            # Handle order status updates
            handle_order_update(data)
        elif event_type == 'position_update':
            # Handle position updates
            handle_position_update(data)
        elif event_type == 'funds_update':
            # Handle funds/margin updates
            handle_funds_update(data)
        
        return jsonify({"status": "processed"})
        
    except Exception as e:
        print(f"❌ Postback error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/dhan/disconnect', methods=['POST'])
def disconnect_dhan():
    """Disconnect Dhan account"""
    try:
        # Get user from authorization header
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        user_id = extract_user_from_token(token)
        
        # Revoke tokens with Dhan API (if supported)
        if user_id in user_tokens:
            access_token = decrypt_token(user_tokens[user_id]['access_token'])
            revoke_dhan_token(access_token)
            del user_tokens[user_id]
        
        # Update connection status
        if user_id in connection_status:
            del connection_status[user_id]
        
        print(f"🔌 Dhan account disconnected for user {user_id}")
        
        return jsonify({
            "success": True,
            "message": "Dhan account disconnected successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper functions

def extract_user_from_token(token):
    """Extract user ID from JWT token"""
    try:
        # For demo, just use the token as user ID
        # In production, decode JWT properly
        return token if token else "demo-user"
    except:
        return "demo-user"

def exchange_code_for_token(code, redirect_uri):
    """Exchange authorization code for access token"""
    try:
        # Mock response - in production, make actual API call to Dhan
        return {
            "access_token": f"dhan_access_{secrets.token_urlsafe(32)}",
            "refresh_token": f"dhan_refresh_{secrets.token_urlsafe(32)}",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Actual implementation would be:
        # response = requests.post(f"{DHAN_API_BASE}/oauth/token", {
        #     "grant_type": "authorization_code",
        #     "code": code,
        #     "redirect_uri": redirect_uri,
        #     "client_id": DHAN_CLIENT_ID,
        #     "client_secret": DHAN_CLIENT_SECRET
        # })
        # return response.json() if response.ok else None
        
    except Exception as e:
        print(f"❌ Token exchange error: {e}")
        return None

def get_dhan_account_details(access_token):
    """Get account details from Dhan API"""
    try:
        # Mock response - in production, make actual API call
        return {
            "account_id": "DH12345",
            "account_type": "TRADING",
            "client_name": "Demo User",
            "status": "ACTIVE",
            "connected_at": datetime.utcnow().isoformat()
        }
        
        # Actual implementation:
        # headers = {"Authorization": f"Bearer {access_token}"}
        # response = requests.get(f"{DHAN_API_BASE}/user/profile", headers=headers)
        # return response.json() if response.ok else None
        
    except Exception as e:
        print(f"❌ Account details error: {e}")
        return None

def encrypt_token(token):
    """Encrypt token for storage (implement proper encryption)"""
    # Use proper encryption in production (AES, etc.)
    return hashlib.sha256(token.encode()).hexdigest()

def decrypt_token(encrypted_token):
    """Decrypt token from storage"""
    # In production, implement proper decryption
    return encrypted_token

def validate_postback_signature(data):
    """Validate postback signature from Dhan"""
    # Implement HMAC signature verification
    return True

def handle_order_update(data):
    """Handle order status updates"""
    print(f"📋 Order update: {data}")

def handle_position_update(data):
    """Handle position updates"""
    print(f"📊 Position update: {data}")

def handle_funds_update(data):
    """Handle funds/margin updates"""
    print(f"💰 Funds update: {data}")

def revoke_dhan_token(access_token):
    """Revoke token with Dhan API"""
    try:
        # Implementation for token revocation
        print(f"🔒 Revoking Dhan token: {access_token[:10]}...")
    except Exception as e:
        print(f"❌ Token revocation error: {e}")

if __name__ == '__main__':
    print("🚀 Engine C - Dhan Integration Handler")
    print("📋 Available endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /api/dhan/status - Get connection status")
    print("  POST /api/dhan/callback - OAuth callback handler")
    print("  POST /api/dhan/postback - Postback notifications")
    print("  POST /api/dhan/disconnect - Disconnect account")
    
    app.run(host='0.0.0.0', port=8003, debug=True)