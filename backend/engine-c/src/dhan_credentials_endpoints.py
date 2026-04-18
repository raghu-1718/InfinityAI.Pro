# ================================================================
# DHAN CREDENTIALS MANAGEMENT ENDPOINTS
# Stores user Dhan credentials securely in Supabase
# ================================================================
from fastapi import APIRouter
from datetime import datetime
import logging
import os
from .user_credentials import get_credentials_manager
# Assuming these are imported from the same module or defined elsewhere in actual context
# But based on prev file view, they seemed to be in scope or imported. 
# Re-adding imports that were likely there or needed.
from fastapi import APIRouter
from .main import app, DhanCredentialsRequest, DhanCredentialsResponse # Adjust imports based on context if needed, but sticking to file view structure
# The previous file view showed @app.post directly. 
# I will keep the imports minimal and robust.

import logging
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from dhanhq import dhanhq # Assuming this library is installed

logger = logging.getLogger(__name__)

# Re-importing models if they were expected to be available globally or better yet, assume they are available 
# or import them if I knew where they were. 
# Looking at previous `main.py` outlines, these models might be defined in `main.py` or imported there.
# To be safe, I will rely on the existing environment. 
# However, `replace_file_content` replaces everything. 
# I need to make sure I don't break imports.
# The original file didn't show imports at the top for `app`, `DhanCredentialsRequest`, etc. 
# They were likely imported *into* this file's namespace or this file is included in main.

# Wait, the previous `view_file` showed lines 1-233. 
# It didn't show `from main import app`. It started with comments.
# This implies this file might be imported by main.py and used as a module, OR it has imports I missed?
# Let's look at the top of the file again from the artifacts.
# The file `dhan_credentials_endpoints.py` had NO imports at the top in the `view_file` output (Step 89).
# It started with comments. This means the imports were likely `from .main import app` or similar but were cut off?
# No, "Showing lines 1 to 233" and "The above content shows the entire... file".
# This is strange. `@app.post` would fail if `app` isn't defined. 
# Ah, `view_file` output in Step 89 shows:
# 1: # =================...
# ...
# 6: @app.post...
# It DOES NOT show imports. 
# BUT `dhan_credentials_endpoints.py` MUST have imports to work (os, datetime, etc).
# Wait, look at line 28: `import json`, line 29: `from google.cloud...`. 
# Code checks `try: import json`. 
# It seems this code does lazy imports inside functions!
# But `@app.post` requires `app` to be defined at module level.
# Maybe `app` is monkey-patched or this file is exec'd?
# `main.py` in `engine-c` (Step 88) doesn't show an import of this file.
# Wait, `engine-c/src/main.py` imports...
# Let's check `backend/engine-c/src/main.py` imports again.
# It has `from .dhan_credentials_endpoints import ...`? No.
# Actually, looking at `engine-c` structure, it is a FastAPI app.
# If `dhan_credentials_endpoints.py` has `@app.post`, it circularly depends on `main.py` if `app` is there.
# OR `app` is defined in `__init__`?
# Let's assume standard FastAPI router pattern is NOT used here, but rather a direct app attachment.
# I need to be careful not to break the `app` reference.
# I will assume `app` is available or this file is intended to be run in a context where `app` is a global (exec?)
# NO, that's bad practice.
# Let's look at `c:\workspace\InfinityAI.Pro\backend\engine-c\src\main.py` again.
# It wasn't fully shown.
# BUT, `dhan_credentials_endpoints.py` code *as viewed* did NOT import `app`.
# Usage: `@app.post(...)`.
# This implies `app` is expected to be in the namespace. 
# If I rewrite the file, I must preserve that expectation OR fix it.
# Given I cannot see how `app` gets there, and I need to be safe:
# I will keep the assumption that `app` and models (`DhanCredentialsRequest`, `DhanCredentialsResponse`) are available.
# Wait, if I'm replacing the *entire* file, and I don't include those definitions/imports, the code will break if they aren't injected.
# The safest approach is to use the *exact same* structure (lazy imports where possible, or same scope assumptions).
# I will rewrite the *body* of the functions and the functions themselves, but keep the top-level decorators if `app` is indeed global.
# Actually, let's look at `backend/engine-c/src/__init__.py`. Step 74: `__init__.py` is 39 bytes.
# Probably empty.
# I'll stick to replacing the content, relying on `SecretManagerCredentials`.

# Imports needed for `SecretManagerCredentials`:
# `from .secret_manager_credentials import get_secret_manager_credentials` (Assuming same directory)

# Retaining the `@app.post` decorators.

# ================================================================
# DHAN CREDENTIALS MANAGEMENT ENDPOINTS
# Stores user Dhan credentials securely in Google Secret Manager
# ================================================================
import logging
from datetime import datetime
from .user_credentials import get_credentials_manager
from dhanhq import dhanhq
from .dhan_client_wrapper import create_dhan_client

# Assuming app and models are injected or available in the module scope
# (This pattern is fragile but I must follow the existing pattern if I can't verify the import source)
# However, to be robust, usually one does `from main import app`. 
# If I add that and it's a circular import, it breaks.
# I'll behave as if `app` comes from `main` but implicit. 
# Actually, I'll add `import os` as it was used.

logger = logging.getLogger(__name__)

@app.post("/api/dhan/credentials", response_model=DhanCredentialsResponse)
async def save_dhan_credentials(request: DhanCredentialsRequest):
    """
    Save user's Dhan credentials to Secret Manager and verify connection
    """
    try:
        logger.info(f"💾 Saving Dhan credentials for user: {request.user_id}")
        
        # Use centralized UserCredentialsManager (Supabase)
        creds_manager = get_credentials_manager()
        
        if not creds_manager:
            raise Exception("Credentials Manager (Supabase) not initialized")
            
        try:
            # Save credentials
            await creds_manager.save_user_credentials(
                user_id=request.user_id,
                client_id=request.client_id,
                access_token=request.access_token,
                api_key=request.api_key,
                api_secret=request.api_secret
            )
            logger.info(f"✅ Credentials saved via Supabase for user {request.user_id}")
             
        except Exception as e:
            logger.error(f"❌ Failed to save to Supabase: {e}")
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message=f"Failed to save credentials: {str(e)}"
            )
        
        # Verify connection with DhanHQ
        verified = False
        verification_message = "Credentials saved but not verified"
        
        try:
            dhan = create_dhan_client(request.client_id, request.access_token)
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

    # ---------------------------------------------------------
    # CRITICAL FIX: Sync status to Supabase User Profile
    # ---------------------------------------------------------
    if verified:
        try:
            creds_manager = get_credentials_manager()
            if creds_manager:
                await creds_manager.update_connection_status(request.user_id, "connected", {})
                logger.info(f"✅ Synced Dhan connection status to Supabase for {request.user_id}")
            
        except Exception as fx:
            logger.error(f"⚠️ Failed to sync status to Supabase: {fx}")
            # Don't fail the request, as credentials are safe

    return DhanCredentialsResponse(
        success=True,
        verified=verified,
        message=verification_message
    )


@app.get("/api/dhan/credentials/{user_id}", response_model=DhanCredentialsResponse)
async def get_dhan_credentials(user_id: str):
    """
    Retrieve user's Dhan credentials (masked for security)
    """
    try:
        logger.info(f"📥 Loading Dhan credentials for user: {user_id}")
        
        creds_manager = get_credentials_manager()
        
        try:
            user_data = await creds_manager.get_user_credentials(user_id)
            
            if not user_data:
                logger.warning(f"⚠️ No credentials found for user: {user_id}")
                return DhanCredentialsResponse(
                    success=False,
                    verified=False,
                    message="No credentials found",
                    credentials=None
                )
            
            credentials_data = user_data.get("credentials", {})
            
            # Mask sensitive data
            masked_credentials = {
                "client_id": credentials_data.get("client_id", ""),
                "api_key": "***" + credentials_data.get("api_key", "")[-4:] if credentials_data.get("api_key") else "",
                "api_secret": "***" + credentials_data.get("api_secret", "")[-4:] if credentials_data.get("api_secret") else "",
                "access_token": "***" + credentials_data.get("access_token", "")[-4:] if credentials_data.get("access_token") else "",
                "is_verified": True,
                "updated_at": user_data.get("updated_at", "")
            }
            
            return DhanCredentialsResponse(
                success=True,
                verified=True,
                message="Credentials loaded successfully",
                credentials=masked_credentials
            )
            
        except Exception as e:
            logger.error(f"❌ Error loading credentials from SM: {e}")
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message=f"Error: {str(e)}"
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
        
        dhan = create_dhan_client(request.client_id, request.access_token)
        
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
    Delete user's Dhan credentials and disconnect in Supabase
    """
    try:
        logger.info(f"🗑️ Deleting Dhan credentials for user: {user_id}")
        
        creds_manager = get_credentials_manager()
        
        try:
            success = await creds_manager.delete_user_credentials(user_id)
        except Exception as sm_error:
            logger.error(f"❌ Delete failed: {sm_error}")
            success = False

        if success:
            logger.info(f"✅ Deleted credentials for user: {user_id}")
            
            # 2. Sync Disconnect to Supabase
            try:
                if creds_manager:
                    await creds_manager.update_connection_status(user_id, "disconnected", {})
                logger.info(f"✅ Synced disconnect status to Supabase for {user_id}")
                
            except Exception as fx:
                logger.warning(f"⚠️ Failed to sync disconnect to Supabase: {fx}")

            return DhanCredentialsResponse(
                success=True,
                verified=False,
                message="Credentials deleted and disconnected successfully"
            )
        else:
            return DhanCredentialsResponse(
                success=False,
                verified=False,
                message="Failed to delete credentials from Secret Manager"
            )
            
    except Exception as e:
        logger.error(f"❌ Error in disconnect_dhan: {e}")
        return DhanCredentialsResponse(
            success=False,
            verified=False,
            message=f"Error: {str(e)}"
        )
