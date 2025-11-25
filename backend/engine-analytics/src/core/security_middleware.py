from fastapi import FastAPI, Request, Response

# Security middleware for Engine A (augmented to include CSP)

def add_security_headers(app: FastAPI) -> None:
    # Decorator type: (str) -> Callable[[Request, Callable], Awaitable[Response]]
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: callable) -> Response:
        response: Response = await call_next(request)
        # Core protections
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Add Content Security Policy (CSP) to align with platform standard
        # Keep conservative defaults; extend connect-src to allow inter-engine calls and websockets
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://*.run.app wss://*.run.app; "
            "frame-ancestors 'none';"
        )

        # Permissions Policy (Feature Policy) - keep locked down
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), "
            "microphone=(), payment=(), usb=()"
        )

        return response

# Usage: add_security_headers(app)
