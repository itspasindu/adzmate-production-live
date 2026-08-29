from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


def _load_r2_backend() -> StorageBackend:
    from app.storage.r2 import R2StorageBackend

    return R2StorageBackend()


@lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    if settings.storage_backend == "r2" and settings.r2_configured():
        return _load_r2_backend()
    return LocalStorageBackend()


def is_storage_key(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith(("uploads/", "generated/", "previews/"))


def resolve_asset_url(path_or_key: str | None) -> str | None:
    """Turn a storage key or legacy local path into a public URL."""
    if not path_or_key:
        return None
    if path_or_key.startswith("http://") or path_or_key.startswith("https://"):
        return path_or_key
    if is_storage_key(path_or_key):
        return get_storage().get_public_url(path_or_key)
    # Legacy absolute/relative filesystem path from seed or older rows
    p = Path(path_or_key)
    name = p.name
    parts = p.parts
    if "uploads" in parts:
        idx = parts.index("uploads")
        key = "/".join(parts[idx:])
        return get_storage().get_public_url(key)
    if "previews" in parts:
        idx = parts.index("previews")
        key = "/".join(parts[idx:])
        return get_storage().get_public_url(key)
    if "generated" in parts:
        idx = parts.index("generated")
        key = "/".join(parts[idx:])
        return get_storage().get_public_url(key)
    if name == "product.png" and len(parts) >= 2:
        campaign_id = parts[-2]
        return get_storage().get_public_url(f"uploads/{campaign_id}/{name}")
    return None


async def read_image_bytes(path_or_key: str | None) -> bytes | None:
    if not path_or_key:
        return None
    storage = get_storage()
    if is_storage_key(path_or_key):
        if storage.exists(path_or_key):
            return await storage.read_bytes(path_or_key)
        return None
    p = Path(path_or_key)
    if p.is_file():
        return p.read_bytes()
    return None
