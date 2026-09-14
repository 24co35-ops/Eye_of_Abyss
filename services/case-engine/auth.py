"""JWT auth — roles: INVESTIGATOR / SUPERVISOR / ADMIN (design-doc §7)."""

import os
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

JWT_SECRET    = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 15

Role = Literal["INVESTIGATOR", "SUPERVISOR", "ADMIN"]

bearer = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str        # officer_id
    role: Role
    unit: str = ""
    exp: int | None = None


def create_access_token(sub: str, role: Role, unit: str = "", expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT token."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": sub,
        "role": role,
        "unit": unit,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**data)
    except (JWTError, Exception) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> TokenPayload:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    return decode_token(creds.credentials)


def require_role(*roles: Role):
    """Dependency factory — require one of the given roles."""
    def _check(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{user.role}' lacks required permission {roles}"
            )
        return user
    return _check
