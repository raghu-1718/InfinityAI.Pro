"""
Lightweight Auth service for Engine C.
NOTE: This service requires real credentials to be provided via environment
or Secret Manager. It intentionally does NOT ship demo users or credentials.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from passlib.context import CryptContext
import os
import json
import logging

logger = logging.getLogger(__name__)

# JWT Configuration - MUST be provided via env or Secret Manager
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

        # Load users from environment-provided JSON. Production should provide
        # a secure user store (DB or Secret Manager). If absent, login is disabled.
        users_json = os.getenv("USERS_JSON", "")
        try:
            self.users_db: Dict[str, Dict[str, Any]] = json.loads(users_json) if users_json else {}
        except Exception:
            self.users_db = {}

    def _require_secret(self) -> None:
        if not self.secret_key:
            raise RuntimeError("JWT secret not configured. Set JWT_SECRET_KEY in environment or Secret Manager.")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.users_db.get(email)
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        if not self.verify_password(password, user.get("hashed_password", "")):
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        return user

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        self._require_secret()
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            self._require_secret()
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return None
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.authenticate_user(email, password)
        if not user:
            return None
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user["email"], "username": user.get("username"), "role": user.get("role", "user")},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer", "user": {"email": user["email"], "username": user.get("username")}, "expires_in": self.access_token_expire_minutes * 60}

# Global instance
auth_service = AuthService()
