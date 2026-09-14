"""Hardened security, rate limiting, and request logging middleware for FastAPI."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from shared.logging_config import setup_logger

logger = setup_logger("eob.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects industry-standard security headers on every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # Strict Transport Security when in production or HTTPS
        if os.getenv("ENVIRONMENT", "").lower() == "production" or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter.
    
    # ponytail: in-memory sliding window per IP/token is zero-dependency and fast.
    """

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.rpm = requests_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
        self.history: dict[str, list[float]] = defaultdict(list)
        self.exempt_paths = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in self.exempt_paths:
            return await call_next(request)

        # Identify client by Bearer token or client IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            client_id = auth_header.split(" ")[1][:32]
        else:
            client_id = request.client.host if request.client else "unknown"

        now = time.time()
        window_start = now - 60.0

        # Purge entries older than 60 seconds
        recent = [t for t in self.history[client_id] if t > window_start]
        
        if len(recent) >= self.rpm:
            retry_after = int(60.0 - (now - recent[0])) + 1
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit of {self.rpm} requests/minute exceeded. Try again in {retry_after}s.",
                },
                headers={"Retry-After": str(max(1, retry_after))},
            )

        recent.append(now)
        self.history[client_id] = recent

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rpm)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.rpm - len(recent)))
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs structured incoming request and duration."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            if path not in {"/health", "/ready"}:
                logger.info(
                    f"{method} {path} -> {response.status_code} ({duration_ms}ms)",
                    extra={
                        "http_method": method,
                        "path": path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
            return response
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled error in {method} {path}: {exc} ({duration_ms}ms)",
                exc_info=True,
                extra={"http_method": method, "path": path, "duration_ms": duration_ms},
            )
            return JSONResponse(
                status_code=500,
                content={"error": "internal_server_error", "detail": "An internal server error occurred."},
            )
