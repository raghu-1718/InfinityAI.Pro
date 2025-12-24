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
from google.cloud import firestore
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
            self.db = firestore.Client()
            self.coupons_collection = "coupons"
            self.sessions_collection = "coupon_sessions"
            self.users_collection = "coupon_users"
            logger.info("✅ CouponAuthManager initialized with Firestore")
        except Exception as e:
            logger.warning(f"Firestore not available, using in-memory storage: {e}")
            self.db = None
            self._memory_coupons = {}
            self._memory_sessions = {}
            self._memory_users = {}

    def _hash_code(self, code: str) -> str:
        """Hash coupon code for secure comparison"""
        return hashlib.sha256(code.upper().strip().encode()).hexdigest()

    def _generate_session_id(self, coupon_code: str) -> str:
        """Generate unique session ID"""
        timestamp = utcnow().isoformat()
        return hashlib.sha256(f"{coupon_code}:{timestamp}".encode()).hexdigest()[:32]

    def _generate_user_id(self, coupon_code: str, session_id: str) -> str:
        """Generate unique user ID based on coupon"""
        return f"coupon_{self._hash_code(coupon_code)[:16]}_{session_id[:8]}"

    # =========================================================================
    # Coupon Management (Admin Functions)
    # =========================================================================

    async def create_coupon(
        self,
        code: str,
        description: str = "InfinityAI Pro Access",
        max_uses: int = 1,
        valid_days: int = 365,
        features: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new coupon code"""
        code_hash = self._hash_code(code)

        coupon_data = {
            "code_hash": code_hash,
            "code_display": code.upper()[:4] + "****",  # Masked display
            "description": description,
            "max_uses": max_uses,
            "current_uses": 0,
            "expires_at": utcnow() + timedelta(days=valid_days),
            "is_active": True,
            "created_at": utcnow(),
            "features": features or ["dashboard", "trading", "signals", "ai_analysis"]
        }

        if self.db:
            doc_ref = self.db.collection(self.coupons_collection).document(code_hash)
            doc_ref.set(coupon_data)
        else:
            self._memory_coupons[code_hash] = coupon_data

        logger.info(f"✅ Created coupon: {coupon_data['code_display']}")
        return {"success": True, "coupon": coupon_data}

    async def get_coupon(self, code: str) -> Optional[Dict[str, Any]]:
        """Get coupon by code"""
        code_hash = self._hash_code(code)

        if self.db:
            doc_ref = self.db.collection(self.coupons_collection).document(code_hash)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        else:
            return self._memory_coupons.get(code_hash)

    # =========================================================================
    # Authentication Functions
    # =========================================================================

    async def validate_coupon(self, code: str, link_user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a coupon code and create a session if valid.
        If link_user_id is provided (e.g. Firebase UID), use it.

        Returns:
            success: bool
            session_id: str (if successful)
            user_id: str (if successful)
            message: str
            features: list (if successful)
        """
        code = code.upper().strip()

        if not code or len(code) < 4:
            return {
                "success": False,
                "message": "Invalid coupon code format"
            }

        coupon = await self.get_coupon(code)

        if not coupon:
            logger.warning(f"Invalid coupon attempt: {code[:4]}****")
            return {
                "success": False,
                "message": "Invalid coupon code"
            }

        # Check if active
        if not coupon.get("is_active", False):
            return {
                "success": False,
                "message": "This coupon has been deactivated"
            }

        # Check expiry
        expires_at = coupon.get("expires_at")
        if expires_at:
            if isinstance(expires_at, datetime):
                if expires_at < utcnow():
                    return {
                        "success": False,
                        "message": "This coupon has expired"
                    }
            else:
                # Handle Firestore timestamp
                try:
                    if expires_at.timestamp() < utcnow().timestamp():
                        return {
                            "success": False,
                            "message": "This coupon has expired"
                        }
                except:
                    pass

        # Check usage limit
        max_uses = coupon.get("max_uses", 1)
        current_uses = coupon.get("current_uses", 0)
        if max_uses > 0 and current_uses >= max_uses:
            return {
                "success": False,
                "message": "This coupon has reached its usage limit"
            }

        # Create session
        session_id = self._generate_session_id(code)
        
        # Use provided user ID (Firebase UID) if available, otherwise generate one
        user_id = link_user_id if link_user_id else self._generate_user_id(code, session_id)

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "google_user_id": link_user_id, # explicit field
            "coupon_code_hash": self._hash_code(code),
            "created_at": utcnow(),
            "expires_at": utcnow() + timedelta(days=30),  # Session valid for 30 days
            "is_active": True,
            "dhan_configured": False,
            "last_activity": utcnow()
        }

        # Update coupon usage
        code_hash = self._hash_code(code)
        if self.db:
            # Save session
            self.db.collection(self.sessions_collection).document(session_id).set(session_data)
            # Increment coupon usage and set used_by
            coupon_ref = self.db.collection(self.coupons_collection).document(code_hash)
            coupon_ref.update({
                "current_uses": firestore.Increment(1),
                "used_by": user_id,
                "used_at": utcnow()
            })
        else:
            self._memory_sessions[session_id] = session_data
            self._memory_coupons[code_hash]["current_uses"] = current_uses + 1
            self._memory_coupons[code_hash]["used_by"] = user_id

        logger.info(f"✅ Session created for coupon: {code[:4]}**** -> User: {user_id[:16]}...")

        return {
            "success": True,
            "session_id": session_id,
            "user_id": user_id,
            "message": "Coupon validated successfully! Welcome to InfinityAI Pro.",
            "features": coupon.get("features", ["dashboard"]),
            "expires_at": session_data["expires_at"].isoformat()
        }

    async def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate an existing session"""
        if not session_id:
            return {"valid": False, "message": "No session provided"}

        if self.db:
            doc_ref = self.db.collection(self.sessions_collection).document(session_id)
            doc = doc_ref.get()
            if not doc.exists:
                return {"valid": False, "message": "Session not found"}
            session = doc.to_dict()
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
            doc_ref.update({"last_activity": utcnow()})

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
            doc_ref = self.db.collection(self.sessions_collection).document(session_id)
            doc_ref.update({
                "dhan_configured": dhan_configured,
                "dhan_configured_at": utcnow() if dhan_configured else None
            })
        else:
            if session_id in self._memory_sessions:
                self._memory_sessions[session_id]["dhan_configured"] = dhan_configured
        return True

    async def logout(self, session_id: str) -> Dict[str, Any]:
        """Invalidate a session (logout)"""
        if self.db:
            doc_ref = self.db.collection(self.sessions_collection).document(session_id)
            doc_ref.update({"is_active": False, "logged_out_at": utcnow()})
        else:
            if session_id in self._memory_sessions:
                self._memory_sessions[session_id]["is_active"] = False

        return {"success": True, "message": "Logged out successfully"}

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details by session_id"""
        if not session_id:
            return None

        if self.db:
            doc_ref = self.db.collection(self.sessions_collection).document(session_id)
            doc = doc_ref.get()
            if not doc.exists:
                return None
            session = doc.to_dict()
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
            doc_ref.update({"last_activity": utcnow()})

        # Get features from the coupon
        coupon_hash = session.get("coupon_code_hash")
        features = ["dashboard", "trading", "signals"]
        if coupon_hash and self.db:
            coupon_doc = self.db.collection(self.coupons_collection).document(coupon_hash).get()
            if coupon_doc.exists:
                features = coupon_doc.to_dict().get("features", features)

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
                doc_ref = self.db.collection(self.sessions_collection).document(session_id)
                doc_ref.update({"is_active": False, "logged_out_at": utcnow()})
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
            docs = self.db.collection(self.coupons_collection).stream()
            for doc in docs:
                data = doc.to_dict()
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
                     self.db.collection(self.coupons_collection).document(code_hash).delete()
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
