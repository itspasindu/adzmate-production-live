from __future__ import annotations

from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Object storage abstraction (local disk or Cloudflare R2)."""

    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Persist bytes at key; return the key."""

    @abstractmethod
    async def read_bytes(self, key: str) -> bytes:
        """Read object bytes."""

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        """Public HTTPS URL for browsers (CDN or API proxy)."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True when the object exists."""

    def upload_key(self, campaign_id: str, filename: str = "product.png") -> str:
        return f"uploads/{campaign_id}/{filename}"

    def generated_key(self, campaign_id: str, *parts: str) -> str:
        return f"generated/{campaign_id}/{'/'.join(parts)}"

    def preview_key(self, campaign_id: str, filename: str = "index.html") -> str:
        return f"previews/{campaign_id}/{filename}"
