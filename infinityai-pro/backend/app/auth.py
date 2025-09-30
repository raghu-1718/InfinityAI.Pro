"""
Authentication router for InfinityAI.Pro
Handles user registration, login, JWT token management, and session tracking
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import structlog

from .database import DatabaseManager, get_db_connection
from .crypto import TokenEncryption, JWTSecurity
from .schemas import (
    SignupIn, LoginIn, TokenOut, UserOut, PasswordChangeIn,
    APIResponse, UserRole
)

logger = structlog.get_logger(__name__)

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", JWTSecurity.generate_jwt_secret())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthManager:
    """Authentication manager class"""
    
    @staticmethod
    def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        }
        
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
    
    @staticmethod
    async def get_user_by_id(user_id: UUID) -> Optional[dict]:
        """Get user by ID from database"""
        query = """
            SELECT id, username, email, first_name, last_name, 
                   is_active, is_verified, created_at, last_login
            FROM users WHERE id = $1 AND is_active = true
        """
        return await DatabaseManager.execute_query(
            query, (user_id,), fetch_one=True
        )
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[dict]:
        """Get user by username or email"""
        query = """
            SELECT id, username, email, hashed_password, first_name, last_name,
                   is_active, is_verified, created_at, last_login
            FROM users WHERE (username = $1 OR email = $1) AND is_active = true
        """
        return await DatabaseManager.execute_query(
            query, (username,), fetch_one=True
        )
    
    @staticmethod
    async def create_user(user_data: SignupIn) -> dict:
        """Create new user account"""
        hashed_password = TokenEncryption.hash_password(user_data.password)
        
        query = """
            INSERT INTO users (username, email, hashed_password, first_name, last_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, username, email, first_name, last_name, is_active, is_verified, created_at
        """
        
        try:
            user = await DatabaseManager.execute_query(
                query, (
                    user_data.username,
                    user_data.email,
                    hashed_password,
                    user_data.first_name,
                    user_data.last_name
                ),
                fetch_one=True
            )
            
            if user:
                logger.info("User created successfully", user_id=user['id'], username=user['username'])
            
            return user
            
        except Exception as e:
            if "unique constraint" in str(e).lower():
                if "username" in str(e).lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
                elif "email" in str(e).lower():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered"
                    )
            
            logger.error("User creation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
    
    @staticmethod
    async def update_last_login(user_id: UUID, request: Request) -> None:
        """Update user's last login timestamp and create session record"""
        # Update last login
        await DatabaseManager.execute_query(
            "UPDATE users SET last_login = $1 WHERE id = $2",
            (datetime.utcnow(), user_id)
        )
        
        # Create session record (for token tracking)
        token_hash = JWTSecurity.create_token_hash(str(user_id))  # Placeholder hash
        
        query = """
            INSERT INTO user_sessions (user_id, token_hash, expires_at, user_agent, ip_address)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else None
        
        await DatabaseManager.execute_query(
            query, (user_id, token_hash, expires_at, user_agent, ip_address)
        )


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """Get current authenticated user"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = AuthManager.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await AuthManager.get_user_by_id(UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Get current active user"""
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return current_user


# Authentication endpoints
@router.post("/signup", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: SignupIn):
    """Register new user account"""
    try:
        user = await AuthManager.create_user(user_data)
        
        return APIResponse(
            success=True,
            message="Account created successfully. Please verify your email.",
            data={
                "user_id": str(user["id"]),
                "username": user["username"],
                "email": user["email"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Signup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=TokenOut)
async def login(login_data: LoginIn, request: Request):
    """Authenticate user and return JWT tokens"""
    try:
        # Get user
        user = await AuthManager.get_user_by_username(login_data.username)
        
        if not user or not TokenEncryption.verify_password(
            login_data.password, user["hashed_password"]
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        # Create tokens
        access_token = AuthManager.create_access_token(user["id"])
        refresh_token = AuthManager.create_refresh_token(user["id"])
        
        # Update last login
        await AuthManager.update_last_login(user["id"], request)
        
        logger.info("User logged in successfully", user_id=user["id"], username=user["username"])
        
        return TokenOut(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
            user_id=user["id"],
            username=user["username"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request
):
    """OAuth2-compatible token endpoint"""
    login_data = LoginIn(username=form_data.username, password=form_data.password)
    return await login(login_data, request)


@router.post("/refresh", response_model=TokenOut)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = AuthManager.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = payload.get("sub")
        user = await AuthManager.get_user_by_id(UUID(user_id))
        
        if not user or not user.get("is_active", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        new_access_token = AuthManager.create_access_token(user_id)
        
        return TokenOut(
            access_token=new_access_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=UUID(user_id),
            username=user["username"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh token"
        )


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Get current user profile"""
    return UserOut(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        first_name=current_user.get("first_name"),
        last_name=current_user.get("last_name"),
        is_active=current_user["is_active"],
        is_verified=current_user["is_verified"],
        created_at=current_user["created_at"],
        last_login=current_user.get("last_login")
    )


@router.put("/password", response_model=APIResponse)
async def change_password(
    password_data: PasswordChangeIn,
    current_user: Annotated[dict, Depends(get_current_active_user)]
):
    """Change user password"""
    try:
        # Get current user with password
        user = await AuthManager.get_user_by_username(current_user["username"])
        
        # Verify current password
        if not TokenEncryption.verify_password(
            password_data.current_password, user["hashed_password"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = TokenEncryption.hash_password(password_data.new_password)
        
        # Update password
        await DatabaseManager.execute_query(
            "UPDATE users SET hashed_password = $1 WHERE id = $2",
            (new_password_hash, current_user["id"])
        )
        
        logger.info("Password changed successfully", user_id=current_user["id"])
        
        return APIResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change failed", error=str(e), user_id=current_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post("/logout", response_model=APIResponse)
async def logout(
    current_user: Annotated[dict, Depends(get_current_active_user)],
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """Logout user and invalidate session"""
    try:
        # Create token hash for session invalidation
        token_hash = JWTSecurity.create_token_hash(token)
        
        # Revoke session
        await DatabaseManager.execute_query(
            "UPDATE user_sessions SET is_revoked = true WHERE user_id = $1 AND token_hash = $2",
            (current_user["id"], token_hash)
        )
        
        logger.info("User logged out successfully", user_id=current_user["id"])
        
        return APIResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        return APIResponse(
            success=True,
            message="Logged out successfully"  # Always return success for logout
        )


# Health check for authentication service
@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    try:
        # Test JWT functionality
        test_token = AuthManager.create_access_token("test-user-id")
        payload = AuthManager.verify_token(test_token)
        
        if payload and payload.get("sub") == "test-user-id":
            return {
                "status": "healthy",
                "service": "authentication",
                "jwt_functional": True,
                "timestamp": datetime.utcnow()
            }
        else:
            return {
                "status": "degraded",
                "service": "authentication",
                "jwt_functional": False,
                "error": "JWT token validation failed"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "authentication",
            "error": str(e)
        }