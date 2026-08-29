from __future__ import annotations

import logging

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)
_PREFIX = "enc:"


def _fernet() -> Fernet | None:
    key = settings.token_encryption_key
    if not key:
        return None
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except Exception as exc:
        logger.error("Invalid TOKEN_ENCRYPTION_KEY (use Fernet.generate_key()): %s", exc)
        return None


def encrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if not value or value == "demo-token":
        return value
    f = _fernet()
    if not f:
        return value
    if value.startswith(_PREFIX):
        return value
    token = f.encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{_PREFIX}{token}"


def decrypt_secret(value: str | None) -> str | None:
    if value is None:
        return None
    if not value.startswith(_PREFIX):
        return value
    f = _fernet()
    if not f:
        logger.warning("Encrypted token present but TOKEN_ENCRYPTION_KEY not configured")
        return None
    try:
        return f.decrypt(value[len(_PREFIX) :].encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt stored token")
        return None
