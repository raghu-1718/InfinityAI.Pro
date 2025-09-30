"""
Pydantic schemas for InfinityAI.Pro
Data models for API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles enumeration"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class BrokerStatus(str, Enum):
    """Broker connection status enumeration"""
    PENDING = "pending"
    CONNECTED = "connected"
    EXPIRED = "expired"
    INVALID = "invalid"
    DISABLED = "disabled"


class AccountType(str, Enum):
    """Trading account types"""
    EQUITY = "equity"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    DERIVATIVES = "derivatives"


# Authentication Schemas
class SignupIn(BaseModel):
    """User signup request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=100, description="Secure password")
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class LoginIn(BaseModel):
    """User login request schema"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Remember login session")


class TokenOut(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user_id: UUID
    username: str


class UserOut(BaseModel):
    """User profile response schema"""
    id: UUID
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_verified: bool
    role: UserRole = UserRole.USER
    created_at: datetime
    last_login: Optional[datetime]


class PasswordChangeIn(BaseModel):
    """Password change request schema"""
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# Broker Connection Schemas
class BrokerIn(BaseModel):
    """Add broker connection request schema"""
    broker_name: str = Field(..., description="Broker name (dhan, zerodha, upstox, etc.)")
    token: str = Field(..., description="Broker API token or credentials")
    expiry_timestamp: Optional[datetime] = Field(None, description="Token expiry timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional broker data")
    
    @validator('broker_name')
    def validate_broker_name(cls, v):
        allowed_brokers = ['dhan', 'zerodha', 'upstox', 'angel', 'fyers', 'aliceblue']
        if v.lower() not in allowed_brokers:
            raise ValueError(f'Broker must be one of: {", ".join(allowed_brokers)}')
        return v.lower()


class BrokerOut(BaseModel):
    """Broker connection response schema"""
    id: UUID
    broker_name: str
    status: BrokerStatus
    expiry_timestamp: Optional[datetime]
    last_validated_at: Optional[datetime]
    validation_attempts: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class BrokerUpdateIn(BaseModel):
    """Update broker connection request schema"""
    token: Optional[str] = Field(None, description="New broker token")
    expiry_timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# Trading Account Schemas
class TradingAccountOut(BaseModel):
    """Trading account response schema"""
    id: UUID
    broker_connection_id: UUID
    account_id: str
    account_name: Optional[str]
    account_type: AccountType
    balance: float
    available_margin: float
    used_margin: float
    is_active: bool
    last_synced_at: Optional[datetime]


# Validation and Health Schemas
class BrokerValidationResult(BaseModel):
    """Broker validation result schema"""
    broker_id: UUID
    status: BrokerStatus
    message: str
    validated_at: datetime
    account_info: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any]


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime


class NotificationMessage(BaseModel):
    """Notification message schema"""
    id: UUID
    user_id: UUID
    title: str
    message: str
    type: str  # info, warning, error, success
    is_read: bool = False
    created_at: datetime


# Market Data Schemas (for integration with existing system)
class MarketDataRequest(BaseModel):
    """Market data request schema"""
    symbol: str
    interval: str = "1m"
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None


class TradeSignal(BaseModel):
    """AI trading signal schema"""
    symbol: str
    signal_type: str  # buy, sell, hold
    confidence: float = Field(..., ge=0.0, le=1.0)
    price: Optional[float] = None
    quantity: Optional[int] = None
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    reasoning: Optional[str] = None


# API Response Wrapper
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Pagination Schemas
class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


# Error Schemas
class ErrorDetail(BaseModel):
    """Error detail schema"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error response"""
    detail: List[ErrorDetail]


# Settings and Configuration
class AppSettings(BaseModel):
    """Application settings schema"""
    app_name: str = "InfinityAI.Pro"
    version: str = "2.0.0"
    debug: bool = False
    database_url: str
    redis_url: Optional[str] = None
    jwt_secret: str
    jwt_expiry_minutes: int = 60
    fernet_key: str
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"