from fastapi import FastAPI, Request, Response

# Security middleware for Engine A

def add_security_headers(app: FastAPI) -> None:
    # Decorator type: (str) -> Callable[[Request, Callable], Awaitable[Response]]
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next: callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

# Usage: add_security_headers(app)
