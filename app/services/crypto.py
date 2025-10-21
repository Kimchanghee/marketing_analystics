"""Utilities for encrypting and decrypting sensitive channel credentials."""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


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
    """Decrypt previously encrypted *value* using the application secret."""
    if value is None:
        return None
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(value.encode("utf-8"))
    except InvalidToken:
        return None
    return decrypted.decode("utf-8")
