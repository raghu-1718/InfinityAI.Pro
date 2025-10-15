#!/usr/bin/env python3
"""
InfinityAI.Pro - Security Hardening Implementation
Token validation, input sanitization, CSRF protection, and secure session management
"""

import hashlib
import hmac
import jwt
import os
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import bleach  # Optional dependency for HTML sanitization
import html
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    'JWT_SECRET': os.getenv('JWT_SECRET', secrets.token_urlsafe(32)),
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRY_HOURS': 24,
    'CSRF_SECRET': os.getenv('CSRF_SECRET', secrets.token_urlsafe(32)),
    'SESSION_TIMEOUT_MINUTES': 30,
    'MAX_REQUEST_SIZE': 10 * 1024 * 1024,  # 10MB
    'RATE_LIMIT_REQUESTS': 1000,
    'RATE_LIMIT_WINDOW': 3600  # 1 hour
}

@dataclass
class SecurityContext:
    user_id: str
    permissions: List[str]
    session_id: str
    csrf_token: str
    issued_at: datetime
    expires_at: datetime

class TokenValidator:
    """JWT Token validation and management"""
    
    def __init__(self):
        self.secret = SECURITY_CONFIG['JWT_SECRET']
        self.algorithm = SECURITY_CONFIG['JWT_ALGORITHM']
        self.expiry_hours = SECURITY_CONFIG['JWT_EXPIRY_HOURS']
    
    def generate_token(self, user_id: str, permissions: List[str] = None) -> str:
        """Generate a JWT token for user"""
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'permissions': permissions or ['read'],
            'iat': now,
            'exp': now + timedelta(hours=self.expiry_hours),
            'jti': secrets.token_urlsafe(16)  # JWT ID for token revocation
        }
        
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> SecurityContext:
        """Validate and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            
            return SecurityContext(
                user_id=payload['user_id'],
                permissions=payload.get('permissions', ['read']),
                session_id=payload.get('jti'),
                csrf_token=self.generate_csrf_token(payload['user_id']),
                issued_at=datetime.fromtimestamp(payload['iat']),
                expires_at=datetime.fromtimestamp(payload['exp'])
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def generate_csrf_token(self, user_id: str) -> str:
        """Generate CSRF token for user"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f"{user_id}:{timestamp}"
        csrf_token = hmac.new(
            SECURITY_CONFIG['CSRF_SECRET'].encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}:{csrf_token}"
    
    def validate_csrf_token(self, user_id: str, token: str) -> bool:
        """Validate CSRF token"""
        try:
            timestamp, csrf_hash = token.split(':', 1)
            
            # Check if token is not too old (1 hour)
            token_age = datetime.utcnow().timestamp() - float(timestamp)
            if token_age > 3600:
                return False
            
            # Regenerate and compare
            expected_message = f"{user_id}:{timestamp}"
            expected_hash = hmac.new(
                SECURITY_CONFIG['CSRF_SECRET'].encode(),
                expected_message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(csrf_hash, expected_hash)
        except (ValueError, TypeError):
            return False

class InputSanitizer:
    """Input sanitization and validation"""
    
    @staticmethod
    def sanitize_html(input_text: str) -> str:
        """Sanitize HTML input to prevent XSS"""
        if not input_text:
            return ""
        
        # Escape HTML characters to prevent XSS
        sanitized = html.escape(input_text, quote=True)
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick='
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_sql_input(input_text: str) -> str:
        """Sanitize input to prevent SQL injection"""
        if not input_text:
            return ""
        
        # Escape single quotes and remove dangerous keywords
        dangerous_patterns = [
            r'\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|EXEC|UNION|SELECT)\b',
            r'[;\'"\\]'
        ]
        
        sanitized = input_text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_trading_symbol(symbol: str) -> str:
        """Validate and sanitize trading symbol"""
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        # Allow only alphanumeric characters and limited special chars
        sanitized = re.sub(r'[^A-Za-z0-9\-_&]', '', symbol.upper())
        
        if not sanitized or len(sanitized) > 20:
            raise HTTPException(status_code=400, detail="Invalid trading symbol")
        
        return sanitized
    
    @staticmethod
    def validate_numeric_input(value: Any, min_val: float = None, max_val: float = None) -> float:
        """Validate numeric input with range checking"""
        try:
            num_value = float(value)
            
            if min_val is not None and num_value < min_val:
                raise HTTPException(status_code=400, detail=f"Value must be >= {min_val}")
            
            if max_val is not None and num_value > max_val:
                raise HTTPException(status_code=400, detail=f"Value must be <= {max_val}")
            
            return num_value
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid numeric value")
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        return email.lower().strip()

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis or database
        self.max_requests = SECURITY_CONFIG['RATE_LIMIT_REQUESTS']
        self.window_seconds = SECURITY_CONFIG['RATE_LIMIT_WINDOW']
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True

class SecurityMiddleware:
    """Security middleware for FastAPI applications"""
    
    def __init__(self):
        self.token_validator = TokenValidator()
        self.input_sanitizer = InputSanitizer()
        self.rate_limiter = RateLimiter()
        self.security = HTTPBearer()
    
    async def validate_request_security(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> SecurityContext:
        """Complete request security validation"""
        
        # Rate limiting
        client_ip = request.client.host
        if not self.rate_limiter.is_allowed(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Token validation
        security_context = self.token_validator.validate_token(credentials.credentials)
        
        # Request size validation
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > SECURITY_CONFIG['MAX_REQUEST_SIZE']:
            raise HTTPException(status_code=413, detail="Request too large")
        
        return security_context
    
    async def validate_csrf_token(self, request: Request, security_context: SecurityContext):
        """Validate CSRF token for state-changing operations"""
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            raise HTTPException(status_code=403, detail="CSRF token required")
        
        if not self.token_validator.validate_csrf_token(security_context.user_id, csrf_token):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    def sanitize_trading_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize trading request data"""
        sanitized = {}
        
        if 'symbol' in request_data:
            sanitized['symbol'] = self.input_sanitizer.validate_trading_symbol(request_data['symbol'])
        
        if 'quantity' in request_data:
            sanitized['quantity'] = int(self.input_sanitizer.validate_numeric_input(
                request_data['quantity'], min_val=1, max_val=10000
            ))
        
        if 'price' in request_data:
            sanitized['price'] = self.input_sanitizer.validate_numeric_input(
                request_data['price'], min_val=0.01, max_val=100000
            )
        
        if 'order_type' in request_data:
            allowed_types = ['MARKET', 'LIMIT', 'STOP_LOSS']
            if request_data['order_type'].upper() not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid order type")
            sanitized['order_type'] = request_data['order_type'].upper()
        
        if 'transaction_type' in request_data:
            allowed_transactions = ['BUY', 'SELL']
            if request_data['transaction_type'].upper() not in allowed_transactions:
                raise HTTPException(status_code=400, detail="Invalid transaction type")
            sanitized['transaction_type'] = request_data['transaction_type'].upper()
        
        return sanitized

class SessionManager:
    """Secure session management"""
    
    def __init__(self):
        self.active_sessions = {}  # In production, use Redis
        self.session_timeout = timedelta(minutes=SECURITY_CONFIG['SESSION_TIMEOUT_MINUTES'])
    
    def create_session(self, user_id: str) -> str:
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'csrf_token': secrets.token_urlsafe(32)
        }
        
        return session_id
    
    def validate_session(self, session_id: str) -> bool:
        """Validate and refresh session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        now = datetime.utcnow()
        
        # Check if session has expired
        if now - session['last_activity'] > self.session_timeout:
            del self.active_sessions[session_id]
            return False
        
        # Refresh session activity
        session['last_activity'] = now
        return True
    
    def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if now - session['last_activity'] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global security instances
security_middleware = SecurityMiddleware()
session_manager = SessionManager()

# Security dependencies for FastAPI
async def get_security_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> SecurityContext:
    """FastAPI dependency for security validation"""
    return await security_middleware.validate_request_security(request, credentials)

async def validate_csrf(
    request: Request,
    security_context: SecurityContext = Depends(get_security_context)
):
    """FastAPI dependency for CSRF validation"""
    await security_middleware.validate_csrf_token(request, security_context)

def sanitize_trading_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Function to sanitize trading request data"""
    return security_middleware.sanitize_trading_request(request_data)

# Security headers middleware
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY" 
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Logging security events
def log_security_event(event_type: str, details: Dict[str, Any], user_id: str = None):
    """Log security events for monitoring"""
    logger.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | Details: {details}")

if __name__ == "__main__":
    print("🛡️ InfinityAI.Pro Security Hardening Module")
    print("✅ Token validation implemented")
    print("✅ Input sanitization implemented") 
    print("✅ CSRF protection implemented")
    print("✅ Rate limiting implemented")
    print("✅ Session management implemented")
    print("✅ Security headers implemented")
    print("🔐 Security hardening complete!")