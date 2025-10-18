"""
JWT Authentication Service for Engine D
Handles token generation, validation, and user authentication
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt  # type: ignore[import]
from jose.exceptions import ExpiredSignatureError, JWTError  # type: ignore[import]
from passlib.context import CryptContext  # type: ignore[import]
import os
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "infinity-ai-pro-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        
        # Demo users (in production, use database)
        self.users_db: Dict[str, Dict[str, Any]] = {
            "raghu@infinityai.pro": {
                "username": "raghu",
                "email": "raghu@infinityai.pro",
                "hashed_password": pwd_context.hash("infinity2025"),
                "full_name": "Raghu",
                "role": "admin",
                "is_active": True
            },
            "demo@infinityai.pro": {
                "username": "demo",
                "email": "demo@infinityai.pro",
                "hashed_password": pwd_context.hash("demo123"),
                "full_name": "Demo User",
                "role": "user",
                "is_active": True
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = self.users_db.get(email)
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        if not self.verify_password(password, user["hashed_password"]):
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        return user
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode: Dict[str, Any] = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return None
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return self.users_db.get(email)
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Complete login flow - authenticate and return token"""
        user = self.authenticate_user(email, password)
        if not user:
            return None
        
        # Create access token
        access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
        access_token = self.create_access_token(
            data={
                "sub": user["email"],
                "username": user["username"],
                "role": user["role"]
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "email": user["email"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "expires_in": self.access_token_expire_minutes * 60  # seconds
        }

# Global auth service instance
auth_service = AuthService()
