"""Environment flags and configuration validation shared by every Eye of Abyss service."""

from __future__ import annotations

import os
import re

_PROD = {"prod", "production"}
_DEV_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

_KNOWN_WEAK_SECRETS = {
    "",
    "changeme",
    "changeme123",
    "password",
    "password123",
    "admin",
    "admin123",
    "secret",
    "dev-secret",
    "dev-refresh-secret",
    "dev-secret-change-in-production",
    "your_jwt_secret_change_in_production",
    "your_jwt_refresh_secret_change_in_production",
    "minioadmin",
    "postgres",
    "neo4j",
    "root",
    "123456",
    "12345678",
    "1234567890",
    "test",
}


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "dev").lower() in _PROD


def cors_origins() -> list[str]:
    """Explicit browser origins. Wildcard + credentials is rejected."""
    raw = os.getenv("CORS_ORIGINS", "").strip()
    origins = [o.strip() for o in raw.split(",") if o.strip() and o.strip() != "*"]
    if origins:
        return origins
    if is_production():
        raise RuntimeError(
            "CORS_ORIGINS must list explicit origins in production (wildcard is not allowed)"
        )
    return list(_DEV_ORIGINS)


def docs_kwargs() -> dict:
    """Hide OpenAPI surfaces when ENVIRONMENT is production."""
    if is_production():
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {}


def validate_secret(name: str, value: str | None, min_length: int = 16, required: bool = True) -> str:
    """Reject missing, weak, low-entropy, or default secrets.
    
    # ponytail: stdlib validation; fail-fast at startup before any network listener binds.
    """
    raw = (value or "").strip()
    if not raw:
        if required:
            raise RuntimeError(f"Required secret '{name}' is missing or empty. Set it in .env")
        return ""

    lowered = raw.lower()
    if lowered in _KNOWN_WEAK_SECRETS or "changeme" in lowered or "default" in lowered:
        raise RuntimeError(
            f"Secret '{name}' uses a known weak or placeholder default value. Choose a strong, unique secret."
        )

    if len(raw) < min_length:
        raise RuntimeError(
            f"Secret '{name}' is too short: got {len(raw)} chars, minimum required is {min_length} chars."
        )

    # Entropy check: at least 4 distinct characters to reject simple repetitions like "aaaaaaaaaaaaaaaa"
    if len(set(raw)) < 4:
        raise RuntimeError(
            f"Secret '{name}' has insufficient character diversity/entropy."
        )

    return raw


def require_secret(name: str, min_length: int = 16) -> str:
    """Read an environment variable secret and enforce security requirements."""
    val = os.getenv(name)
    return validate_secret(name, val, min_length=min_length, required=True)
