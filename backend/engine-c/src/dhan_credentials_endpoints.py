# ================================================================
# DHAN CREDENTIALS MANAGEMENT ENDPOINTS
# Stores user Dhan credentials securely in Google Secret Manager
# ================================================================

@app.post("/api/dhan/credentials", response_model=DhanCredentialsResponse)
async def save_dhan_credentials(request: DhanCredentialsRequest):
    """
    Save user's Dhan credentials to Secret Manager and verify connection
    """
    try:
        logger.info(f"💾 Saving Dhan credentials for user: {request.user_id}")
        
        # Create secret name
        secret_id = f"dhan_credentials_{request.user_id.replace('@', '_at_').replace('.', '_')}"
        
        # Prepare credentials payload
        credentials_data = {
            "client_id": request.client_id,
            "api_key": request.api_key,
            "api_secret": request.api_secret,
            "access_token": request.access_token,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to Secret Manager
        try:
            import json
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id: raise ValueError("GOOGLE_CLOUD_PROJECT env var missing")
            parent = f"projects/{project_id}"
            
            # Try to create secret or add version if exists
            try:
                secret = client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
                logger.info(f"✅ Created new secret: {secret_id}")
            except Exception as e:
                # Secret already exists, will add new version below
                logger.debug(f"Secret exists, adding new version: {str(e)[:100]}")
            
            # Add secret version
            secret_name = f"{parent}/secrets/{secret_id}"
            payload = json.dumps(credentials_data).encode("UTF-8")
            
            version = client.add_secret_version(
                request={
                    "parent": secret_name,
                    "payload": {"data": payload},
                }
            )
            logger.info(f"✅ Saved credentials version: {version.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Secret Manager: {e}")
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message=f"Failed to save credentials: {str(e)}"
            )
        
        # Verify connection with DhanHQ
        verified = False
        verification_message = "Credentials saved but not verified"
        
        try:
            dhan = dhanhq(request.client_id, request.access_token)
            # Test API call
            funds = dhan.get_fund_limits()
            if funds:
                verified = True
                verification_message = "Credentials verified successfully"
                logger.info(f"✅ Dhan connection verified for user: {request.user_id}")
        except Exception as e:
            logger.warning(f"⚠️ Credential verification failed: {e}")
            verification_message = f"Saved but verification failed: {str(e)[:100]}"
        
        return DhanCredentialsResponse(
            success=True,
            verified=verified,
            message=verification_message
        )
        
    except Exception as e:
        logger.error(f"❌ Error in save_dhan_credentials: {e}")
        return DhanCredentialsResponse(
            success=False,
            verified=False,
            message=f"Internal error: {str(e)}"
        )


@app.get("/api/dhan/credentials/{user_id}", response_model=DhanCredentialsResponse)
async def get_dhan_credentials(user_id: str):
    """
    Retrieve user's Dhan credentials (masked for security)
    """
    try:
        logger.info(f"📥 Loading Dhan credentials for user: {user_id}")
        
        secret_id = f"dhan_credentials_{user_id.replace('@', '_at_').replace('.', '_')}"
        
        try:
            import json
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id: raise ValueError("GOOGLE_CLOUD_PROJECT env var missing")
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            credentials_data = json.loads(response.payload.data.decode("UTF-8"))
            
            # Mask sensitive data
            masked_credentials = {
                "client_id": credentials_data.get("client_id", ""),
                "api_key": "***" + credentials_data.get("api_key", "")[-4:] if credentials_data.get("api_key") else "",
                "api_secret": "***" + credentials_data.get("api_secret", "")[-4:] if credentials_data.get("api_secret") else "",
                "access_token": "***" + credentials_data.get("access_token", "")[-4:] if credentials_data.get("access_token") else "",
                "is_verified": True,
                "updated_at": credentials_data.get("updated_at", "")
            }
            
            return DhanCredentialsResponse(
                success=True,
                verified=True,
                message="Credentials loaded successfully",
                credentials=masked_credentials
            )
            
        except Exception as e:
            logger.warning(f"⚠️ No credentials found for user: {user_id}")
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message="No credentials found",
                credentials=None
            )
            
    except Exception as e:
        logger.error(f"❌ Error loading credentials: {e}")
        return DhanCredentialsResponse(
            success=False,
            verified=False,
            message=f"Error: {str(e)}"
        )


@app.post("/api/dhan/verify", response_model=DhanCredentialsResponse)
async def verify_dhan_connection(request: DhanCredentialsRequest):
    """
    Verify Dhan connection without saving credentials
    """
    try:
        logger.info(f"🔍 Verifying Dhan connection for user: {request.user_id}")
        
        dhan = dhanhq(request.client_id, request.access_token)
        
        # Test connection
        funds = dhan.get_fund_limits()
        
        if funds:
            return DhanCredentialsResponse(
                success=True,
                verified=True,
                message="Connection verified successfully"
            )
        else:
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message="Connection failed - invalid response"
            )
            
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        return DhanCredentialsResponse(
            success=False,
            verified=False,
            message=f"Verification failed: {str(e)}"
        )


@app.delete("/api/dhan/credentials/{user_id}", response_model=DhanCredentialsResponse)
async def disconnect_dhan(user_id: str):
    """
    Delete user's Dhan credentials from Secret Manager
    """
    try:
        logger.info(f"🗑️ Deleting Dhan credentials for user: {user_id}")
        
        secret_id = f"dhan_credentials_{user_id.replace('@', '_at_').replace('.', '_')}"
        
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not project_id: raise ValueError("GOOGLE_CLOUD_PROJECT env var missing")
            name = f"projects/{project_id}/secrets/{secret_id}"
            
            # Delete the secret
            client.delete_secret(request={"name": name})
            
            logger.info(f"✅ Deleted credentials for user: {user_id}")
            return DhanCredentialsResponse(
                success=True,
                verified=False,
                message="Credentials deleted successfully"
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Delete failed: {e}")
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message=f"Delete failed: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"❌ Error deleting credentials: {e}")
        return DhanCredentialsResponse(
            success=False,
            verified=False,
            message=f"Error: {str(e)}"
        )
