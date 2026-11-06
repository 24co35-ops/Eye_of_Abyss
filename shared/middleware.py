"""Hardened security, rate limiting, body size enforcement, and request logging middleware."""

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

# Hard limit for file uploads and JSON payloads: 100 MB
MAX_BODY_SIZE_BYTES = int(os.getenv("MAX_BODY_SIZE_MB", "100")) * 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects industry-standard security headers (OWASP recommended) on every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss: http: https:; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Strict Transport Security when in production or HTTPS
        if os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") or request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            
        return response


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    """Enforces hard request body size limit to prevent memory exhaustion and DoS attacks."""

    def __init__(self, app, max_bytes: int = MAX_BODY_SIZE_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "detail": f"Request body exceeds maximum size limit of {self.max_bytes // (1024 * 1024)} MB.",
                        },
                    )
            except ValueError:
                pass

        # Wrap receive stream to defend against chunked transfers without content-length
        bytes_received = 0
        original_receive = request._receive

        async def _bounded_receive():
            nonlocal bytes_received
            message = await original_receive()
            if message["type"] == "http.request":
                bytes_received += len(message.get("body", b""))
                if bytes_received > self.max_bytes:
                    raise RuntimeError("Request body exceeded maximum size limit")
            return message

        request._receive = _bounded_receive
        try:
            return await call_next(request)
        except RuntimeError as exc:
            if "maximum size limit" in str(exc):
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "payload_too_large",
                        "detail": f"Request body exceeds maximum size limit of {self.max_bytes // (1024 * 1024)} MB.",
                    },
                )
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter across replicas using Redis, with in-memory fallback.
    
    # ponytail: Redis ZSET pipeline for multi-worker sync; in-memory fallback for local tests.
    """

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.rpm = requests_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
        self.history: dict[str, list[float]] = defaultdict(list)
        self.exempt_paths = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}
        self._redis = None
        self._init_redis()

    def _init_redis(self):
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self._redis = redis.from_url(redis_url, socket_timeout=1.0, socket_connect_timeout=1.0)
            except Exception:
                self._redis = None

    def _check_redis(self, client_id: str, now: float) -> tuple[bool, int, int]:
        """Returns (is_allowed, remaining, retry_after) using Redis Sorted Sets."""
        if not self._redis:
            return False, 0, 0
        try:
            key = f"eob:ratelimit:{client_id}"
            window_start = now - 60.0
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}": now})
            pipe.expire(key, 65)
            _, count, _, _ = pipe.execute()
            
            if count > self.rpm:
                return False, 0, 60
            remaining = max(0, self.rpm - count)
            return True, remaining, 0
        except Exception:
            # Fall back to in-memory on any Redis failure
            self._redis = None
            return False, 0, 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in self.exempt_paths:
            return await call_next(request)

        # Identify client by Bearer token or client IP
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            client_id = auth_header.split(" ")[1][:32]
        elif os.getenv("TRUST_PROXY", "0") == "1":
            forwarded = request.headers.get("x-forwarded-for", "")
            client_id = forwarded.split(",")[0].strip() or (
                request.client.host if request.client else "unknown"
            )
        else:
            client_id = request.client.host if request.client else "unknown"

        now = time.time()
        window_start = now - 60.0

        # Try Redis first
        if self._redis is not None:
            allowed, remaining, retry_after = self._check_redis(client_id, now)
            if self._redis is not None:
                if not allowed:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "rate_limit_exceeded",
                            "detail": f"Rate limit of {self.rpm} requests/minute exceeded. Try again in {retry_after}s.",
                        },
                        headers={"Retry-After": str(max(1, retry_after))},
                    )
                response = await call_next(request)
                response.headers["X-RateLimit-Limit"] = str(self.rpm)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                return response

        # In-memory fallback
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
