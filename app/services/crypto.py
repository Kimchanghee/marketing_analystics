"""Utilities for encrypting and decrypting sensitive channel credentials."""
from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings

logger = logging.getLogger(__name__)


class DecryptionError(Exception):
    """Raised when decryption fails due to invalid data or wrong key."""
    pass


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    settings = get_settings()
    key_material = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_material)
    return Fernet(fernet_key)


def encrypt(value: Optional[str]) -> Optional[str]:
    """Encrypt *value* using Fernet symmetric encryption."""
    if value is None:
        return None
    fernet = _get_fernet()
    token = fernet.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt(value: Optional[str]) -> Optional[str]:
    """Decrypt previously encrypted *value* using the application secret.

    Args:
        value: Encrypted string or None

    Returns:
        None if value is None (no encrypted value provided)
        Decrypted string if successful

    Raises:
        DecryptionError: If decryption fails due to invalid/corrupted data or wrong key
    """
    if value is None:
        return None
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(value.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken as e:
        # Decryption failed - could be wrong key, corrupted data, or tampered value
        logger.error(f"Decryption failed - possible data corruption or wrong key: {e}")
        raise DecryptionError(f"Failed to decrypt value: {e}") from e
