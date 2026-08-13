"""
InfinityAI.Pro - Coupon-Based Authentication System
====================================================
Simple coupon code authentication for dashboard access.
Users enter a valid coupon code to unlock the dashboard,
then configure their Dhan credentials to access trading features.
"""
import os
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def utcnow():
    """Return timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


class CouponCode(BaseModel):
    """Coupon code model"""
    code: str
    description: Optional[str] = None
    max_uses: int = 1
    current_uses: int = 0
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = None
    features: List[str] = ["dashboard", "trading", "signals"]


class CouponSession(BaseModel):
    """User session after coupon validation"""
    session_id: str
    coupon_code: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True
    dhan_configured: bool = False


class CouponAuthManager:
    """Manages coupon-based authentication"""

    def __init__(self):
        try:
            from src.user_credentials import get_credentials_manager
            manager = get_credentials_manager()
            self.db = manager.db if manager else None
            self.coupons_collection = "coupons"
            self.sessions_collection = "coupon_sessions"
            self.users_collection = "users"
            self._memory_coupons = {}
            self._memory_sessions = {}
            self._memory_users = {}
            if self.db:
                logger.info("✅ CouponAuthManager initialized with Firestore")
            else:
                logger.info("ℹ️ CouponAuthManager using in-memory storage fallback")
        except Exception as e:
            logger.warning(f"Firestore DB client not available, using in-memory storage: {e}")
            self.db = None
            self._memory_coupons = {}
            self._memory_sessions = {}
            self._memory_users = {}


    def _hash_code(self, code: str) -> str:
        """Get coupon code ID (Plain text now)"""
        return code.upper().strip()

    def _generate_session_id(self, coupon_code: str) -> str:
        """Generate unique session ID"""
        timestamp = utcnow().isoformat()
        return hashlib.sha256(f"{coupon_code}:{timestamp}".encode()).hexdigest()[:32]

    def _generate_user_id(self, coupon_code: str, session_id: str) -> str:
        """Generate unique user ID based on coupon"""
        return f"coupon_{hashlib.sha256(coupon_code.encode()).hexdigest()[:8]}_{session_id[:8]}"

    # =========================================================================
    # Coupon Management (Admin Functions)
    # =========================================================================

    async def create_coupon(
        self,
        code: str,
        description: str = "InfinityAI Pro Access",
        max_uses: int = 1,
        valid_days: int = 365,
        features: List[str] = None,
        assigned_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new coupon code"""
        code_id = self._hash_code(code)

        coupon_data = {
            "code_id": code_id,
            "code_display": code.upper(),
            "description": description,
            "max_uses": max_uses,
            "current_uses": 0,
            "expires_at": utcnow() + timedelta(days=valid_days),
            "is_active": True,
            "created_at": utcnow(),
            "features": features or ["dashboard", "trading", "signals", "ai_analysis"],
            "assigned_email": assigned_email.lower().strip() if assigned_email else None
        }

        if self.db:
            try:
                # Add coupon string fields 
                self.db.table(self.coupons_collection).upsert({
                    "code_id": code_id,
                    "code_display": coupon_data["code_display"],
                    "description": coupon_data["description"],
                    "max_uses": coupon_data["max_uses"],
                    "current_uses": coupon_data["current_uses"],
                    "expires_at": coupon_data["expires_at"].isoformat() if coupon_data["expires_at"] else None,
                    "is_active": coupon_data["is_active"],
                    "created_at": coupon_data["created_at"].isoformat() if coupon_data["created_at"] else None,
                    "features": coupon_data["features"],
                    "assigned_email": coupon_data["assigned_email"]
                }).execute()
            except Exception as e:
                logger.error(f"Failed to save coupon to Supabase: {e}")
                self._memory_coupons[code_id] = coupon_data
        else:
            self._memory_coupons[code_id] = coupon_data

        logger.info(f"✅ Created coupon: {code_id} (assigned to: {assigned_email})")
        return {"success": True, "coupon": coupon_data}

    async def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        """Get coupon by code"""
        code_id = self._hash_code(code)

        if self.db:
            try:
                response = self.db.table(self.coupons_collection).select("*").eq("code_id", code_id).execute()
                if response.data and len(response.data) > 0:
                    data = response.data[0]
                    # Parse dates back to datetime objects if needed
                    if "expires_at" in data and isinstance(data["expires_at"], str):
                        try:
                            data["expires_at"] = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
                        except: pass
                    return data
            except Exception as e:
                logger.error(f"Error fetching coupon from Supabase: {e}")
            return None
        else:
            return self._memory_coupons.get(code_id)

    # =========================================================================
    # Authentication Functions
    # =========================================================================

    async def validate_coupon(self, code: str, link_user_id: Optional[str] = None, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a coupon code and create a session if valid.
        If link_user_id/email is provided, validate binding.
        """
        code = code.upper().strip()

        if not code or len(code) < 4:
            return {"success": False, "message": "Invalid coupon code format"}

        coupon = await self.get_coupon(code)

        if not coupon:
            logger.warning(f"Invalid coupon attempt: {code}")
            return {"success": False, "message": "Invalid coupon code"}

        # Check if active
        if not coupon.get("is_active", False):
            return {"success": False, "message": "This coupon has been deactivated"}

        # Check binding (Strict 1-to-1 Email check)
        assigned_email = coupon.get("assigned_email")
        if assigned_email and email:
            if assigned_email.lower() != email.lower():
                logger.warning(f"Coupon {code} stolen attempt by {email} (owned by {assigned_email})")
                return {"success": False, "message": "This coupon is reserved for a different user"}
        
        # If coupon has assigned email but no email provided in request
        if assigned_email and not email:
             return {"success": False, "message": "Email verification required for this coupon"}


        # Check expiry
        expires_at = coupon.get("expires_at")
        if expires_at:
            # Handle both datetime and ISO string timestamps
            try:
                if isinstance(expires_at, datetime):
                     exp = expires_at
                else:
                     exp = datetime.fromtimestamp(expires_at.timestamp(), tz=timezone.utc)
                
                if exp < utcnow():
                    return {"success": False, "message": "This coupon has expired"}
            except Exception as e:
                logger.error(f"Expiry check error: {e}")

        # Check usage limit (with Idempotency)
        max_uses = coupon.get("max_uses", 1)
        current_uses = coupon.get("current_uses", 0)
        
        # Check if this user already used this coupon (Re-entry allowed)
        is_reentry = False
        if link_user_id:
            used_by = coupon.get("used_by", [])
            if isinstance(used_by, list):
                is_reentry = link_user_id in used_by
            elif isinstance(used_by, str):
                is_reentry = used_by == link_user_id

        if max_uses > 0 and current_uses >= max_uses and not is_reentry:
            return {"success": False, "message": "This coupon has reached its usage limit"}

        # Create session
        session_id = self._generate_session_id(code)
        user_id = link_user_id if link_user_id else self._generate_user_id(code, session_id)

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "google_user_id": link_user_id,
            "google_email": email,
            "coupon_code": code, # Storing plain code now
            "created_at": utcnow(),
            "expires_at": utcnow() + timedelta(days=30),
            "is_active": True,
            "dhan_configured": False,
            "last_activity": utcnow()
        }

        # Update coupon usage
        if self.db:
            try:
                # Need to stringify dates
                session_db_data = session_data.copy()
                session_db_data["created_at"] = session_db_data["created_at"].isoformat()
                session_db_data["expires_at"] = session_db_data["expires_at"].isoformat()
                session_db_data["last_activity"] = session_db_data["last_activity"].isoformat()
                self.db.table(self.sessions_collection).upsert(session_db_data).execute()
            except Exception as e:
                logger.error(f"Failed to insert session: {e}")
            
            if not is_reentry:
                try:
                    # In Supabase, you can't easily increment via API, so we fetch and update, or use RPC.
                    # Since we already fetched the coupon earlier:
                    used_by_list = coupon.get("used_by", [])
                    if isinstance(used_by_list, str): used_by_list = [used_by_list]
                    used_by_list.append(user_id)
                    
                    self.db.table(self.coupons_collection).update({
                        "current_uses": current_uses + 1,
                        "used_by": used_by_list,
                        "used_at": utcnow().isoformat()
                    }).eq("code_id", self._hash_code(code)).execute()
                except Exception as e:
                    logger.error(f"Failed to update coupon stats: {e}")
        else:
            self._memory_sessions[session_id] = session_data
            if not is_reentry:
                self._memory_coupons[code]["current_uses"] = current_uses + 1

        logger.info(f"✅ Session created for coupon: {code} -> User: {email}")

        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "message": "Access Granted! Welcome to InfinityAI Pro.",
            "features": coupon.get("features", ["dashboard"]),
            "expires_at": session_data["expires_at"].isoformat()
        }

    async def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate an existing session"""
        if not session_id:
            return {"valid": False, "message": "No session provided"}

        if self.db:
            try:
                response = self.db.table(self.sessions_collection).select("*").eq("session_id", session_id).execute()
                if not response.data or len(response.data) == 0:
                    return {"valid": False, "message": "Session not found"}
                session = response.data[0]
            except Exception as e:
                logger.error(f"Error validating session: {e}")
                return {"valid": False, "message": "Session fetch failed"}
        else:
            session = self._memory_sessions.get(session_id)
            if not session:
                return {"valid": False, "message": "Session not found"}

        # Check if active
        if not session.get("is_active", False):
            return {"valid": False, "message": "Session has been invalidated"}

        # Check expiry
        expires_at = session.get("expires_at")
        if expires_at:
            try:
                if isinstance(expires_at, datetime):
                    if expires_at < utcnow():
                        return {"valid": False, "message": "Session has expired"}
                else:
                    if expires_at.timestamp() < utcnow().timestamp():
                        return {"valid": False, "message": "Session has expired"}
            except:
                pass

        # Update last activity
        if self.db:
            try:
                self.db.table(self.sessions_collection).update({"last_activity": utcnow().isoformat()}).eq("session_id", session_id).execute()
            except Exception as e:
                pass

        return {
            "valid": True,
            "user_id": session.get("user_id"),
            "session_id": session_id,
            "dhan_configured": session.get("dhan_configured", False),
            "created_at": session.get("created_at"),
            "expires_at": session.get("expires_at")
        }

    async def update_session_dhan_status(self, session_id: str, dhan_configured: bool) -> bool:
        """Update session when Dhan is configured"""
        if self.db:
            try:
                self.db.table(self.sessions_collection).update({
                    "dhan_configured": dhan_configured,
                    "dhan_configured_at": utcnow().isoformat() if dhan_configured else None
                }).eq("session_id", session_id).execute()
            except Exception as e:
                logger.error(f"Failed to update dhan status: {e}")
        else:
            if session_id in self._memory_sessions:
                self._memory_sessions[session_id]["dhan_configured"] = dhan_configured
        return True

    async def logout(self, session_id: str) -> Dict[str, Any]:
        """Invalidate a session (logout)"""
        if self.db:
            try:
                self.db.table(self.sessions_collection).update({"is_active": False, "logged_out_at": utcnow().isoformat()}).eq("session_id", session_id).execute()
            except Exception as e:
                logger.error(f"Logout failed: {e}")
        else:
            if session_id in self._memory_sessions:
                self._memory_sessions[session_id]["is_active"] = False

        return {"success": True, "message": "Logged out successfully"}

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details by session_id"""
        if not session_id:
            return None

        if self.db:
            try:
                response = self.db.table(self.sessions_collection).select("*").eq("session_id", session_id).execute()
                if not response.data or len(response.data) == 0:
                    return None
                session = response.data[0]
            except Exception as e:
                return None
        else:
            session = self._memory_sessions.get(session_id)
            if not session:
                return None

        # Check if active and not expired
        if not session.get("is_active", False):
            return None

        expires_at = session.get("expires_at")
        if expires_at:
            try:
                if isinstance(expires_at, datetime):
                    if expires_at < utcnow():
                        return None
                else:
                    if expires_at.timestamp() < utcnow().timestamp():
                        return None
            except:
                pass

        # Update last activity
        if self.db:
            try:
                self.db.table(self.sessions_collection).update({"last_activity": utcnow().isoformat()}).eq("session_id", session_id).execute()
            except Exception: pass

        # Get features from the coupon
        coupon_hash = session.get("coupon_code_hash")
        features = ["dashboard", "trading", "signals"]
        if coupon_hash and self.db:
            try:
                resp = self.db.table(self.coupons_collection).select("features").eq("code_id", coupon_hash).execute()
                if resp.data and len(resp.data) > 0:
                    features = resp.data[0].get("features", features)
            except Exception: pass

        return {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "features": features,
            "created_at": session.get("created_at"),
            "expires_at": session.get("expires_at"),
            "dhan_configured": session.get("dhan_configured", False)
        }

    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate/logout a session"""
        if self.db:
            try:
                self.db.table(self.sessions_collection).update({"is_active": False, "logged_out_at": utcnow().isoformat()}).eq("session_id", session_id).execute()
                return True
            except Exception:
                return False
        else:
            if session_id in self._memory_sessions:
                self._memory_sessions[session_id]["is_active"] = False
                return True
            return False

    async def list_coupons(self) -> List[Dict[str, Any]]:
        """List all coupons (admin function)"""
        coupons = []

        if self.db:
            try:
                response = self.db.table(self.coupons_collection).select("*").execute()
                if response.data:
                    for data in response.data:
                        coupons.append({
                            "code_display": data.get("code_display", "****"),
                            "description": data.get("description", ""),
                            "max_uses": data.get("max_uses", 0),
                            "current_uses": data.get("current_uses", 0),
                            "is_active": data.get("is_active", False),
                            "expires_at": data.get("expires_at"),
                            "created_at": data.get("created_at"),
                            "features": data.get("features", [])
                        })
            except Exception as e:
                logger.error(f"Error fetching coupons: {e}")
        else:
            for code_hash, data in self._memory_coupons.items():
                coupons.append({
                    "code_display": data.get("code_display", "****"),
                    "description": data.get("description", ""),
                    "max_uses": data.get("max_uses", 0),
                    "current_uses": data.get("current_uses", 0),
                    "is_active": data.get("is_active", False),
                    "expires_at": data.get("expires_at"),
                    "created_at": data.get("created_at"),
                    "features": data.get("features", [])
                })

        return coupons

    # =========================================================================
    # Default Coupons (for initial setup)
    # =========================================================================

    async def initialize_default_coupons(self):
        """Create new family coupons and cleanup old ones"""
        
        # 1. Cleanup Legacy Coupons
        legacy_codes = ["INFINITY2024", "INFINITY2025", "RAGHU-ADMIN", "DEMO-ACCESS"]
        for code in legacy_codes:
            code_hash = self._hash_code(code)
            try:
                if self.db:
                     self.db.table(self.coupons_collection).delete().eq("code_id", code_hash).execute()
                elif code_hash in self._memory_coupons:
                     del self._memory_coupons[code_hash]
                logger.info(f"🧹 Cleaned up legacy coupon: {code}")
            except Exception as e:
                logger.warning(f"Error cleaning up {code}: {e}")

        # 2. Initialize New Family Coupons
        family_coupons = [
            "INFAI-FAM-DAD", "INFAI-FAM-MOM", "INFAI-FAM-SAI", "INFAI-FAM-PRI",
            "INFAI-FAM-HARSHA", "INFAI-FAM-KAVI", "INFAI-FAM-CHOTU", "INFAI-FAM-RAJ",
            "INFAI-FAM-1718", "INFAI-FAM-0506"
        ]

        for code in family_coupons:
            # Check if exists
            existing = await self.get_coupon(code)
            if not existing:
                await self.create_coupon(
                    code=code,
                    description="InfinityAI Family Access",
                    max_uses=1,
                    valid_days=3650, # 10 years validity
                    features=["dashboard", "trading", "signals", "ai_analysis", "family_plan"]
                )
                logger.info(f"✅ Created family coupon: {code}")


# Singleton instance
_coupon_manager = None

def get_coupon_manager() -> CouponAuthManager:
    """Get or create CouponAuthManager singleton"""
    global _coupon_manager
    if _coupon_manager is None:
        _coupon_manager = CouponAuthManager()
    return _coupon_manager
