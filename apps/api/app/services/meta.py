"""Meta (Facebook) OAuth + Graph API helpers.

When META_APP_ID / META_APP_SECRET are set, uses real Facebook Login + Graph API.
Otherwise provides a demo connection so the UI can be exercised without a Meta app.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import uuid
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import is_localhost_url, resolve_meta_oauth_redirect_uri, settings
from app.crypto import encrypt_secret
from app.models import MetaAdAccount, MetaConnection, MetaInstagramAccount, MetaPage, utcnow

logger = logging.getLogger(__name__)

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"
OAUTH_DIALOG = f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth"

# Facebook Login scopes for Marketing API (via facebook.com/dialog/oauth).
# Do not use instagram_business_* here — those are for Instagram Login only.
# Do not request `email` — not valid for Marketing API OAuth on many app types.
META_SCOPES = [
    "public_profile",
    "pages_show_list",
    "pages_read_engagement",
    "business_management",
    "ads_read",
    "ads_management",
]

# OAuth state: Redis in production, in-memory fallback for local dev
_oauth_states: dict[str, dict] = {}
_OAUTH_PREFIX = "adzmate:meta_oauth:"


async def store_oauth_state(state: str, payload: dict, ttl_seconds: int = 600) -> None:
    from app.redis_client import redis_set_json

    key = f"{_OAUTH_PREFIX}{state}"
    if await redis_set_json(key, payload, ttl_seconds=ttl_seconds):
        return
    _oauth_states[state] = payload


async def pop_oauth_state(state: str) -> dict | None:
    from app.redis_client import get_redis, redis_delete, redis_get_json

    key = f"{_OAUTH_PREFIX}{state}"
    client = await get_redis()
    if client:
        payload = await redis_get_json(key)
        await redis_delete(key)
        if payload:
            return payload
    return _oauth_states.pop(state, None)


async def build_oauth_url(*, business_id: str, workspace_id: str, user_id: str, redirect_uri: str) -> str:
    state = secrets.token_urlsafe(24)
    await store_oauth_state(
        state,
        {
            "business_id": business_id,
            "workspace_id": workspace_id,
            "user_id": user_id,
            "redirect_uri": redirect_uri,
        },
    )
    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "response_type": "code",
        "scope": ",".join(META_SCOPES),
    }
    return f"{OAUTH_DIALOG}?{urlencode(params)}"


def meta_oauth_configured() -> bool:
    return bool(settings.meta_app_id and settings.meta_app_secret)


def meta_oauth_env_error() -> str | None:
    """Return a user-facing config hint when OAuth cannot run."""
    if not meta_oauth_configured():
        return "Set META_APP_ID and META_APP_SECRET on the API server (Render env vars)."
    redirect = resolve_meta_oauth_redirect_uri()
    if settings.is_production() and (
        is_localhost_url(redirect) or is_localhost_url(settings.web_app_url)
    ):
        return (
            "Production Meta OAuth must use HTTPS URLs. Set PUBLIC_BASE_URL, WEB_APP_URL, and "
            "META_OAUTH_REDIRECT_URI to your Render/Vercel domains (not localhost)."
        )
    return None


def assert_meta_oauth_ready() -> None:
    err = meta_oauth_env_error()
    if err:
        raise ValueError(err)


def resolve_oauth_redirect_uri() -> str:
    return resolve_meta_oauth_redirect_uri()


def get_connection_access_token(connection: MetaConnection) -> str | None:
    from app.crypto import decrypt_secret

    return decrypt_secret(connection.access_token)


def _appsecret_proof(token: str) -> str:
    return hmac.new(
        settings.meta_app_secret.encode("utf-8"),
        msg=token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


async def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    assert_meta_oauth_ready()
    params = {
        "client_id": settings.meta_app_id,
        "client_secret": settings.meta_app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{GRAPH_BASE}/oauth/access_token", params=params)
        res.raise_for_status()
        short = res.json()
        # Upgrade to long-lived user token
        long_params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "fb_exchange_token": short["access_token"],
        }
        res2 = await client.get(f"{GRAPH_BASE}/oauth/access_token", params=long_params)
        if res2.is_success:
            return res2.json()
        return short


async def graph_get(path: str, access_token: str, params: dict | None = None) -> dict:
    q = dict(params or {})
    q["access_token"] = access_token
    if settings.meta_app_secret:
        q["appsecret_proof"] = _appsecret_proof(access_token)
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{GRAPH_BASE}/{path.lstrip('/')}", params=q)
        res.raise_for_status()
        return res.json()


def _encode_graph_form_data(data: dict | None) -> dict:
    """Meta Graph form posts require JSON-encoded strings for list/dict fields."""
    encoded: dict[str, str] = {}
    for key, value in (data or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            encoded[key] = "true" if value else "false"
        elif isinstance(value, (dict, list)):
            encoded[key] = json.dumps(value)
        else:
            encoded[key] = str(value)
    return encoded


async def graph_post(
    path: str,
    access_token: str,
    *,
    data: dict | None = None,
    params: dict | None = None,
) -> dict:
    q = dict(params or {})
    q["access_token"] = access_token
    if settings.meta_app_secret:
        q["appsecret_proof"] = _appsecret_proof(access_token)
    body = _encode_graph_form_data(data)
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(f"{GRAPH_BASE}/{path.lstrip('/')}", params=q, data=body)
        if not res.is_success:
            detail = res.text[:500]
            raise httpx.HTTPStatusError(
                f"Meta Graph API error {res.status_code}: {detail}",
                request=res.request,
                response=res,
            )
        return res.json()


async def graph_post_multipart(
    path: str,
    access_token: str,
    *,
    files: dict,
    data: dict | None = None,
) -> dict:
    q = {"access_token": access_token}
    if settings.meta_app_secret:
        q["appsecret_proof"] = _appsecret_proof(access_token)
    async with httpx.AsyncClient(timeout=120.0) as client:
        res = await client.post(
            f"{GRAPH_BASE}/{path.lstrip('/')}",
            params=q,
            files=files,
            data=_encode_graph_form_data(data),
        )
        if not res.is_success:
            detail = res.text[:500]
            raise httpx.HTTPStatusError(
                f"Meta Graph API error {res.status_code}: {detail}",
                request=res.request,
                response=res,
            )
        return res.json()


async def fetch_meta_profile(access_token: str) -> dict:
    return await graph_get("me", access_token, {"fields": "id,name"})


async def fetch_pages(access_token: str) -> list[dict]:
    data = await graph_get(
        "me/accounts",
        access_token,
        {"fields": "id,name,category,access_token,picture{url},instagram_business_account{id,username,name,profile_picture_url}"},
    )
    return data.get("data") or []


async def fetch_ad_accounts(access_token: str) -> list[dict]:
    data = await graph_get(
        "me/adaccounts",
        access_token,
        {"fields": "id,name,currency,timezone_name,account_status"},
    )
    return data.get("data") or []


async def replace_connection_assets(
    db: AsyncSession,
    connection: MetaConnection,
    *,
    pages: list[dict],
    ad_accounts: list[dict],
) -> None:
    # Clear previous assets
    for model in (MetaPage, MetaInstagramAccount, MetaAdAccount):
        rows = (
            await db.execute(select(model).where(model.connection_id == connection.id))
        ).scalars().all()
        for row in rows:
            await db.delete(row)

    ig_rows: list[MetaInstagramAccount] = []
    for page in pages:
        db.add(
            MetaPage(
                id=str(uuid.uuid4()),
                connection_id=connection.id,
                page_id=str(page["id"]),
                name=page.get("name") or "Untitled Page",
                category=page.get("category"),
                page_access_token=encrypt_secret(page.get("access_token")),
                picture_url=((page.get("picture") or {}).get("data") or {}).get("url"),
            )
        )
        ig = page.get("instagram_business_account") or {}
        if ig.get("id"):
            ig_rows.append(
                MetaInstagramAccount(
                    id=str(uuid.uuid4()),
                    connection_id=connection.id,
                    ig_user_id=str(ig["id"]),
                    username=ig.get("username") or "instagram",
                    name=ig.get("name"),
                    page_id=str(page["id"]),
                    profile_picture_url=ig.get("profile_picture_url"),
                )
            )
    for ig in ig_rows:
        db.add(ig)

    for act in ad_accounts:
        status = act.get("account_status")
        db.add(
            MetaAdAccount(
                id=str(uuid.uuid4()),
                connection_id=connection.id,
                ad_account_id=str(act["id"]),
                name=act.get("name") or str(act["id"]),
                currency=act.get("currency"),
                timezone_name=act.get("timezone_name"),
                account_status=str(status) if status is not None else None,
            )
        )


async def sync_connection_from_token(
    db: AsyncSession,
    connection: MetaConnection,
    access_token: str,
    *,
    status: str = "connected",
) -> MetaConnection:
    profile = await fetch_meta_profile(access_token)
    pages = await fetch_pages(access_token)
    ads = await fetch_ad_accounts(access_token)

    connection.access_token = encrypt_secret(access_token)
    connection.meta_user_id = str(profile.get("id") or "")
    connection.meta_user_name = profile.get("name")
    connection.scopes = ",".join(META_SCOPES)
    connection.status = status
    connection.updated_at = utcnow()

    await replace_connection_assets(db, connection, pages=pages, ad_accounts=ads)

    # Auto-select first assets if none selected
    if pages and not connection.selected_page_id:
        connection.selected_page_id = str(pages[0]["id"])
        ig = (pages[0].get("instagram_business_account") or {}).get("id")
        if ig:
            connection.selected_instagram_id = str(ig)
    if ads and not connection.selected_ad_account_id:
        connection.selected_ad_account_id = str(ads[0]["id"])

    await db.commit()
    await db.refresh(connection)
    return connection


async def upsert_demo_connection(
    db: AsyncSession,
    *,
    business_id: str,
    workspace_id: str,
) -> MetaConnection:
    existing = (
        await db.execute(select(MetaConnection).where(MetaConnection.business_id == business_id))
    ).scalar_one_or_none()
    if existing:
        connection = existing
    else:
        connection = MetaConnection(
            id=str(uuid.uuid4()),
            business_id=business_id,
            workspace_id=workspace_id,
        )
        db.add(connection)
        await db.flush()

    connection.meta_user_id = "demo-meta-user"
    connection.meta_user_name = "Demo Meta User"
    connection.access_token = "demo-token"
    connection.scopes = ",".join(META_SCOPES)
    connection.status = "demo"
    connection.updated_at = utcnow()

    demo_pages = [
        {
            "id": "page_1001",
            "name": "Aurora Lifestyle",
            "category": "Brand",
            "access_token": "demo-page-token",
            "picture": {"data": {"url": None}},
            "instagram_business_account": {
                "id": "ig_2001",
                "username": "aurora.lifestyle",
                "name": "Aurora Lifestyle",
                "profile_picture_url": None,
            },
        },
        {
            "id": "page_1002",
            "name": "Summit Outfitters",
            "category": "Retail",
            "access_token": "demo-page-token-2",
            "picture": {"data": {"url": None}},
            "instagram_business_account": {
                "id": "ig_2002",
                "username": "summit.outfitters",
                "name": "Summit Outfitters",
            },
        },
    ]
    demo_ads = [
        {
            "id": "act_3001",
            "name": "Aurora — US Growth",
            "currency": "USD",
            "timezone_name": "America/New_York",
            "account_status": 1,
        },
        {
            "id": "act_3002",
            "name": "Summit — Retargeting",
            "currency": "USD",
            "timezone_name": "America/Los_Angeles",
            "account_status": 1,
        },
        {
            "id": "act_3003",
            "name": "APAC Test Account",
            "currency": "SGD",
            "timezone_name": "Asia/Singapore",
            "account_status": 1,
        },
    ]
    await replace_connection_assets(db, connection, pages=demo_pages, ad_accounts=demo_ads)
    connection.selected_page_id = "page_1001"
    connection.selected_instagram_id = "ig_2001"
    connection.selected_ad_account_id = "act_3001"
    await db.commit()
    await db.refresh(connection)
    return connection
