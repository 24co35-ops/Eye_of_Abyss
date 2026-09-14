"""Auth router for Case Engine — /auth/* endpoints + FastAPI dependencies.

Delegates crypto to shared.auth; stores users in PostgreSQL via db.User.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# shared is on PYTHONPATH in all containers
from shared.auth import (
    Role,
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
    verify_wallet_sig,
)
from shared.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
    WalletLoginRequest,
)

from db import AuditLog, User, get_db

DB          = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE  = "refresh_token"
COOKIE_MAX_AGE  = 7 * 24 * 3600   # 7 days in seconds


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT", "dev") == "prod",
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )


def _user_response(u: User) -> UserResponse:
    return UserResponse(
        user_id=u.user_id,
        email=u.email,
        role=u.role,
        wallet_address=u.wallet_address,
        is_active=u.is_active,
        created_at=u.created_at,
    )


async def _log(db: AsyncSession, actor: str, action: str, detail: dict = None, case_id=None):
    db.add(AuditLog(actor=actor, action=action, detail=detail or {}, case_id=case_id))
    await db.commit()


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response, db: DB):
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")

    # Only OWNER can create OWNER/SUPERVISOR accounts without an existing OWNER auth
    # ponytail: skip complex invite flow — first user auto-becomes OWNER
    owner_count = await db.scalar(select(User).where(User.role == Role.OWNER.value))
    role = Role.OWNER.value if owner_count is None else body.role

    user = User(email=body.email, hashed_password=hash_password(body.password), role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access  = create_access_token(str(user.user_id), user.role, user.email)
    refresh = create_refresh_token(str(user.user_id))
    _set_refresh_cookie(response, refresh)
    await _log(db, user.email, "REGISTER", {"role": role})
    return TokenResponse(access_token=access)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: DB):
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    access  = create_access_token(str(user.user_id), user.role, user.email)
    refresh = create_refresh_token(str(user.user_id))
    _set_refresh_cookie(response, refresh)
    await _log(db, user.email, "LOGIN")
    return TokenResponse(access_token=access)


# ── Wallet Login ──────────────────────────────────────────────────────────────

@router.post("/wallet-login", response_model=TokenResponse)
async def wallet_login(body: WalletLoginRequest, response: Response, db: DB):
    if not verify_wallet_sig(body.wallet_address, body.message, body.signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid wallet signature")

    user = await db.scalar(select(User).where(User.wallet_address == body.wallet_address.lower()))
    if not user:
        # Auto-create wallet-only account as INVESTIGATOR
        user = User(
            email=f"{body.wallet_address.lower()}@wallet.local",
            wallet_address=body.wallet_address.lower(),
            role=Role.INVESTIGATOR.value,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    access  = create_access_token(str(user.user_id), user.role, user.email)
    refresh = create_refresh_token(str(user.user_id))
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(response: Response, db: DB, refresh: str | None = Cookie(default=None, alias=REFRESH_COOKIE)):
    if not refresh:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    user_id = decode_refresh_token(refresh)
    user = await db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found or deactivated")

    access      = create_access_token(str(user.user_id), user.role, user.email)
    new_refresh = create_refresh_token(str(user.user_id))
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=access)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(REFRESH_COOKIE)
    return {"detail": "Logged out"}


# ── User management (OWNER only) ──────────────────────────────────────────────

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("", response_model=List[UserResponse])
async def list_users(db: DB, _: Annotated[TokenPayload, Depends(require_role(Role.OWNER))]):
    result = await db.execute(select(User))
    return [_user_response(u) for u in result.scalars().all()]


@users_router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: UUID, db: DB, _: Annotated[TokenPayload, Depends(require_role(Role.OWNER))]):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return _user_response(user)


@users_router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    body: UpdateUserRequest,
    db: DB,
    caller: Annotated[TokenPayload, Depends(require_role(Role.OWNER))],
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    await db.commit()
    await db.refresh(user)
    await _log(db, caller.email, "UPDATE_USER", {"target": str(user_id), "changes": body.dict(exclude_none=True)})
    return _user_response(user)


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DB,
    caller: Annotated[TokenPayload, Depends(require_role(Role.OWNER))],
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
    await _log(db, caller.email, "DELETE_USER", {"target": str(user_id)})
