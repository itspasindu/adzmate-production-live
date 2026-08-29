from __future__ import annotations

import asyncio

import boto3
from botocore.config import Config

from app.config import settings
from app.storage.base import StorageBackend


class R2StorageBackend(StorageBackend):
    """Cloudflare R2 via S3-compatible API."""

    def __init__(self) -> None:
        if not settings.r2_bucket:
            raise ValueError("R2_BUCKET is required for R2 storage")
        endpoint = settings.r2_endpoint or (
            f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
            if settings.r2_account_id
            else None
        )
        if not endpoint:
            raise ValueError("R2_ENDPOINT or R2_ACCOUNT_ID is required")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )
        self._bucket = settings.r2_bucket
        self._public_base = (settings.r2_public_url or "").rstrip("/")

    async def save(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    async def read_bytes(self, key: str) -> bytes:
        def _read() -> bytes:
            obj = self._client.get_object(Bucket=self._bucket, Key=key)
            return obj["Body"].read()

        return await asyncio.to_thread(_read)

    def get_public_url(self, key: str) -> str:
        if self._public_base:
            return f"{self._public_base}/{key.lstrip('/')}"
        return f"{settings.public_base_url.rstrip('/')}/assets/{key.lstrip('/')}"

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False
