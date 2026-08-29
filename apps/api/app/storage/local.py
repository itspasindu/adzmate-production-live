from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Filesystem storage under apps/api/{uploads,generated,previews}."""

    def _path(self, key: str) -> Path:
        root = key.split("/", 1)[0]
        if root == "uploads":
            base = settings.uploads_dir
            rel = key[len("uploads/") :]
        elif root == "generated":
            base = settings.generated_dir
            rel = key[len("generated/") :]
        elif root == "previews":
            base = settings.previews_dir
            rel = key[len("previews/") :]
        else:
            raise ValueError(f"Unknown storage key prefix: {key}")
        return base / rel

    async def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    async def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def get_public_url(self, key: str) -> str:
        return f"{settings.public_base_url.rstrip('/')}/{key}"

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()
