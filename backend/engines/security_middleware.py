"""
Security middleware for all InfinityAI.Pro services
Provides HSTS, CSP, and other security headers
"""
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware implementing:
    - HSTS (HTTP Strict Transport Security)
    - CSP (Content Security Policy)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    """
    
    def __init__(self, app: FastAPI, enable_hsts: bool = True):
        super().__init__(app)
        self.enable_hsts = enable_hsts
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS - Force HTTPS for 1 year
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # CSP - Restrict resource loading
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://engine-*.us-central1.run.app wss://engine-*.us-central1.run.app; "
            "frame-ancestors 'none';"
        )
        
        # Prevent embedding in frames
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


def add_security_headers(app: FastAPI, enable_hsts: bool = True):
    """
    Add security headers middleware to FastAPI app
    
    Args:
        app: FastAPI application instance
        enable_hsts: Whether to enable HSTS header
    """
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)