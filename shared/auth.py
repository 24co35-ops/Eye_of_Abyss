"""Shared auth module — used by all Eye of Abyss services.

Roles: OWNER > SUPERVISOR > INVESTIGATOR > VIEWER
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Optional
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# ── JWT Provider (python-jose -> PyJWT -> pure Python stdlib HMAC-SHA256) ──
try:
    from jose import JWTError, jwt as _jwt_mod
    def _encode_jwt(claims: dict, secret: str, algorithm: str) -> str:
        return _jwt_mod.encode(claims, secret, algorithm=algorithm)
    def _decode_jwt(token: str, secret: str, algorithms: list[str]) -> dict:
        return _jwt_mod.decode(token, secret, algorithms=algorithms)
except ImportError:
    try:
        import jwt as _pyjwt  # type: ignore[import-not-found]
        class JWTError(Exception):
            pass
        def _encode_jwt(claims: dict, secret: str, algorithm: str) -> str:
            return _pyjwt.encode(claims, secret, algorithm=algorithm)
        def _decode_jwt(token: str, secret: str, algorithms: list[str]) -> dict:
            try:
                return _pyjwt.decode(token, secret, algorithms=algorithms)
            except Exception as e:
                raise JWTError(str(e))
    except ImportError:
        import base64
        import hashlib
        import hmac
        import json
        import time

        class JWTError(Exception):
            pass

        def _b64url_encode(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        def _b64url_decode(s: str) -> bytes:
            padding = 4 - (len(s) % 4)
            if padding != 4:
                s += "=" * padding
            return base64.urlsafe_b64decode(s.encode("ascii"))

        def _encode_jwt(claims: dict, secret: str, algorithm: str = "HS256") -> str:
            header = {"alg": "HS256", "typ": "JWT"}
            h_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
            c_copy = dict(claims)
            if "exp" in c_copy and isinstance(c_copy["exp"], datetime):
                c_copy["exp"] = int(c_copy["exp"].timestamp())
            p_b64 = _b64url_encode(json.dumps(c_copy, separators=(",", ":"), default=str).encode("utf-8"))
            sig = hmac.new(secret.encode("utf-8"), f"{h_b64}.{p_b64}".encode("utf-8"), hashlib.sha256).digest()
            s_b64 = _b64url_encode(sig)
            return f"{h_b64}.{p_b64}.{s_b64}"

        def _decode_jwt(token: str, secret: str, algorithms: list[str] = None) -> dict:
            parts = token.split(".")
            if len(parts) != 3:
                raise JWTError("Invalid JWT token format")
            h_b64, p_b64, s_b64 = parts
            expected_sig = hmac.new(secret.encode("utf-8"), f"{h_b64}.{p_b64}".encode("utf-8"), hashlib.sha256).digest()
            actual_sig = _b64url_decode(s_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise JWTError("Signature verification failed")
            payload = json.loads(_b64url_decode(p_b64).decode("utf-8"))
            if "exp" in payload:
                now_ts = int(time.time())
                exp_val = payload["exp"]
                exp_ts = int(exp_val) if isinstance(exp_val, (int, float, str)) else 0
                if exp_ts and now_ts > exp_ts:
                    raise JWTError("Token expired")
            return payload

# ── Config ────────────────────────────────────────────────────────────────────

JWT_SECRET         = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_REFRESH_SECRET = os.getenv("JWT_REFRESH_SECRET", JWT_SECRET + "-refresh")
JWT_ALGORITHM      = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_EXPIRE_MIN  = 15
REFRESH_EXPIRE_DAYS = 7
REFRESH_COOKIE     = "refresh_token"

bearer  = HTTPBearer(auto_error=False)

# ── Password hashing provider (passlib -> bcrypt -> stdlib pbkdf2) ───────────
try:
    from passlib.context import CryptContext  # type: ignore[import-not-found]
    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def hash_password(plain: str) -> str:
        return _pwd_ctx.hash(plain)
    def verify_password(plain: str, hashed: str) -> bool:
        return _pwd_ctx.verify(plain, hashed)
except Exception:
    try:
        import bcrypt  # type: ignore[import-not-found]
        def hash_password(plain: str) -> str:
            return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        def verify_password(plain: str, hashed: str) -> bool:
            try:
                return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
            except Exception:
                return False
    except Exception:
        import hashlib, hmac
        def hash_password(plain: str) -> str:
            salt = os.urandom(16).hex()
            dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), 100000)
            return f"pbkdf2:{salt}:{dk.hex()}"
        def verify_password(plain: str, hashed: str) -> bool:
            if not hashed or not hashed.startswith("pbkdf2:"):
                return False
            try:
                _, salt, dk_hex = hashed.split(":", 2)
                check = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), 100000)
                return hmac.compare_digest(check.hex(), dk_hex)
            except Exception:
                return False


# ── Role ─────────────────────────────────────────────────────────────────────

class Role(str, Enum):
    OWNER        = "OWNER"
    SUPERVISOR   = "SUPERVISOR"
    INVESTIGATOR = "INVESTIGATOR"
    VIEWER       = "VIEWER"

# Role hierarchy — higher index = more privilege
_RANK = {Role.VIEWER: 0, Role.INVESTIGATOR: 1, Role.SUPERVISOR: 2, Role.OWNER: 3}


# ── SQLAlchemy User model (optional, used by case-engine) ──────────────────────
try:
    from sqlalchemy import Boolean, Column, DateTime, String
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.orm import DeclarativeBase

    class AuthBase(DeclarativeBase):
        """Separate declarative base so services that only need auth don't inherit case tables."""
        pass

    class User(AuthBase):
        __tablename__ = "users"

        user_id         = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
        email           = Column(String(255), unique=True, nullable=False, index=True)
        hashed_password = Column(String(255), nullable=True)   # NULL for wallet-only users
        role            = Column(String(20), nullable=False, default=Role.VIEWER.value)
        wallet_address  = Column(String(42), unique=True, nullable=True)  # 0x... ETH address
        is_active       = Column(Boolean, default=True, nullable=False)
        created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
except ImportError:
    AuthBase = None  # type: ignore
    User = None  # type: ignore


# ── Token helpers ─────────────────────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str        # user_id as string
    role: str
    email: str = ""
    exp: Optional[int] = None


def create_access_token(sub: str, role: str, email: str = "") -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE_MIN)
    return _encode_jwt(
        {"sub": sub, "role": role, "email": email, "exp": int(expire.timestamp())},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def create_refresh_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
    return _encode_jwt(
        {"sub": sub, "exp": int(expire.timestamp())},
        JWT_REFRESH_SECRET, algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> TokenPayload:
    try:
        data = _decode_jwt(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**data)
    except (JWTError, Exception) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def decode_refresh_token(token: str) -> str:
    """Returns sub (user_id) from a valid refresh token."""
    try:
        data = _decode_jwt(token, JWT_REFRESH_SECRET, algorithms=[JWT_ALGORITHM])
        return data["sub"]
    except (JWTError, Exception) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=f"Invalid refresh token: {e}")




# ── MetaMask / wallet sig verify ──────────────────────────────────────────────

def verify_wallet_sig(address: str, message: str, signature: str) -> bool:
    """Return True if `signature` is a valid eth_sign over `message` by `address`."""
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        msg = encode_defunct(text=message)
        recovered = Account.recover_message(msg, signature=signature)
        return recovered.lower() == address.lower()
    except Exception:
        return False


# ── FastAPI dependencies ───────────────────────────────────────────────────────

def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> TokenPayload:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    return decode_access_token(creds.credentials)


def require_role(*roles: Role):
    """Dependency factory: require one of the given roles (or higher rank)."""
    min_rank = min(_RANK[r] for r in roles)

    def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        user_rank = _RANK.get(Role(user.role), -1)
        if user_rank < min_rank:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' insufficient. Required: {[r.value for r in roles]}"
            )
        return user
    return _check


CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
