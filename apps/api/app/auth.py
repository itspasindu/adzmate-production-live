"""Supabase JWT auth + workspace context."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, Query
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import Workspace, WorkspaceMember


@dataclass
class AuthUser:
    id: str
    email: str | None = None


@dataclass
class WorkspaceContext:
    user: AuthUser
    workspace: Workspace
    role: str


def auth_enabled() -> bool:
    """Auth is enforced when enabled and either a JWT secret or Supabase URL is configured."""
    if not settings.auth_enabled:
        return False
    return bool(settings.supabase_jwt_secret or settings.supabase_url)


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient | None:
    if not settings.supabase_url:
        return None
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(url, cache_keys=True)


def _decode_token(token: str) -> AuthUser:
    """Verify Supabase access tokens (ES256 via JWKS, or legacy HS256 secret)."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token header: {exc}") from exc

    alg = header.get("alg", "HS256")
    audience = "authenticated"
    issuer = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
    )

    try:
        if alg in ("ES256", "RS256", "EdDSA"):
            client = _jwks_client()
            if not client:
                raise HTTPException(
                    status_code=401,
                    detail="Asymmetric JWT requires SUPABASE_URL for JWKS verification",
                )
            key = client.get_signing_key_from_jwt(token).key
            decode_kwargs: dict = {
                "algorithms": [alg],
                "audience": audience,
            }
            if issuer:
                decode_kwargs["issuer"] = issuer
            payload = jwt.decode(token, key, **decode_kwargs)
        elif alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise HTTPException(
                    status_code=401,
                    detail="HS256 JWT requires SUPABASE_JWT_SECRET",
                )
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience=audience,
            )
        else:
            raise HTTPException(status_code=401, detail=f"Unsupported JWT alg: {alg}")
    except HTTPException:
        raise
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return AuthUser(id=str(sub), email=payload.get("email"))


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Expected Bearer token")
    return parts[1].strip() or None


async def get_optional_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Query(default=None),
) -> AuthUser | None:
    if not auth_enabled():
        return AuthUser(id="local-demo", email="demo@local.dev")

    token = _extract_bearer(authorization) or access_token
    if not token:
        return None
    return _decode_token(token)


async def get_current_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Query(default=None),
) -> AuthUser:
    user = await get_optional_user(authorization=authorization, access_token=access_token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def ensure_default_workspace(db: AsyncSession, user: AuthUser) -> WorkspaceContext:
    """Return user's first workspace, creating a personal one if needed."""
    result = await db.execute(
        select(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(WorkspaceMember.created_at.asc())
        .limit(1)
    )
    row = result.first()
    if row:
        member, workspace = row
        return WorkspaceContext(user=user, workspace=workspace, role=member.role)

    # Local demo mode: reuse seeded workspace so seed campaigns remain visible
    if user.id == "local-demo":
        workspace_id = settings.demo_workspace_id
        workspace = (
            await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        ).scalar_one_or_none()
        if not workspace:
            workspace = Workspace(
                id=workspace_id,
                name="Local Demo",
                created_by=user.id,
            )
            db.add(workspace)
        else:
            existing_member = (
                await db.execute(
                    select(WorkspaceMember).where(
                        WorkspaceMember.workspace_id == workspace_id,
                        WorkspaceMember.user_id == user.id,
                    )
                )
            ).scalar_one_or_none()
            if existing_member:
                return WorkspaceContext(user=user, workspace=workspace, role=existing_member.role)

        db.add(
            WorkspaceMember(
                id=str(uuid.uuid4()),
                workspace_id=workspace.id,
                user_id=user.id,
                role="owner",
            )
        )
        await db.commit()
        await db.refresh(workspace)
        return WorkspaceContext(user=user, workspace=workspace, role="owner")

    workspace = Workspace(
        id=str(uuid.uuid4()),
        name="My Workspace",
        created_by=user.id,
    )
    db.add(workspace)
    db.add(
        WorkspaceMember(
            id=str(uuid.uuid4()),
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
    )
    await db.commit()
    await db.refresh(workspace)
    return WorkspaceContext(user=user, workspace=workspace, role="owner")


async def get_workspace_context(
    user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    workspace_id: str | None = Query(default=None),
) -> WorkspaceContext:
    selected = x_workspace_id or workspace_id
    if not selected:
        return await ensure_default_workspace(db, user)

    result = await db.execute(
        select(WorkspaceMember, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMember.workspace_id)
        .where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.workspace_id == selected,
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    member, workspace = row
    return WorkspaceContext(user=user, workspace=workspace, role=member.role)


def require_role(*allowed: str):
    async def _dep(ctx: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if ctx.role == "owner" or ctx.role in allowed:
            return ctx
        raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(allowed)}")

    return _dep


WRITER_ROLES = ("owner", "admin", "approver", "member")
APPROVER_ROLES = ("owner", "admin", "approver")
VIEWER_ROLES = ("owner", "admin", "approver", "member", "viewer")
