from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import models
from app.db.base import get_async_session


@dataclass
class AuthenticatedUser:
    user_id: str
    email: Optional[str] = None
    raw_claims: dict[str, Any] | None = None


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer token.",
        )

    token = authorization[len(prefix):].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is empty.",
        )

    return token


def _build_authenticated_user(payload: dict[str, Any]) -> AuthenticatedUser:
    user_id = payload.get("sub") or payload.get("id")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user subject.",
        )

    return AuthenticatedUser(
        user_id=str(user_id),
        email=email,
        raw_claims=payload,
    )


def _verify_with_jwt_secret(token: str, jwt_secret: str) -> AuthenticatedUser:
    payload = jwt.decode(
        token,
        jwt_secret,
        algorithms=["HS256"],
        options={"verify_aud": False},
    )
    return _build_authenticated_user(payload)


async def _verify_with_supabase_auth_server(token: str) -> AuthenticatedUser:
    settings = get_settings()

    if not settings.SUPABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured.",
        )

    if not settings.SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_ANON_KEY is not configured.",
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "apikey": settings.SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {token}",
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to verify token with Supabase Auth server.",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
        )

    payload = response.json()
    return _build_authenticated_user(payload)


async def verify_supabase_jwt(
    authorization: Optional[str] = Header(default=None),
) -> AuthenticatedUser:
    settings = get_settings()
    token = _extract_bearer_token(authorization)

    if settings.SUPABASE_JWT_SECRET:
        try:
            return _verify_with_jwt_secret(token, settings.SUPABASE_JWT_SECRET)
        except ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Expired access token.",
            ) from exc
        except InvalidTokenError:
            # Fall through to Supabase Auth API verification if configured.
            pass

    return await _verify_with_supabase_auth_server(token)


async def _ensure_local_user_row(
    user: AuthenticatedUser,
    db: AsyncSession,
) -> None:
    try:
        existing = await db.get(models.User, user.user_id)

        if existing is None:
            db.add(
                models.User(
                    id=user.user_id,
                    email=user.email,
                    llm_config=None,
                )
            )
            await db.commit()
            return

        updated = False
        if user.email and existing.email != user.email:
            existing.email = user.email
            updated = True

        if updated:
            await db.commit()

    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to synchronize authenticated user with local database.",
        ) from exc


async def get_current_user(
    user: AuthenticatedUser = Depends(verify_supabase_jwt),
    db: AsyncSession = Depends(get_async_session),
) -> AuthenticatedUser:
    await _ensure_local_user_row(user, db)
    return user