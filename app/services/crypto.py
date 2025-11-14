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

    Returns:
        - None if value is None (no encrypted value provided)
        - None if decryption fails due to invalid token (logs warning)
        - Decrypted string if successful
    """
    if value is None:
        return None
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(value.encode("utf-8"))
    except InvalidToken as e:
        # Decryption failed - could be wrong key, corrupted data, or tampered value
        logger.warning(f"Failed to decrypt value (invalid token): {e}")
        return None
    return decrypted.decode("utf-8")
