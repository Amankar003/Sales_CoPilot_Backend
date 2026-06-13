"""
crypto.py - Encryption utilities for SMTP password storage.
Uses Fernet symmetric encryption from the cryptography library.
"""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from app.core.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Module-level cipher instance (initialized lazily)
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """
    Get or create the Fernet cipher instance.
    Uses SMTP_ENCRYPTION_KEY from settings; auto-generates if missing.
    """
    global _fernet
    if _fernet is not None:
        return _fernet

    key = getattr(settings, "SMTP_ENCRYPTION_KEY", None)

    if key and key.strip():
        try:
            _fernet = Fernet(key.strip().encode())
            logger.info("SMTP encryption key loaded from settings.")
            return _fernet
        except Exception as e:
            logger.error(f"Invalid SMTP_ENCRYPTION_KEY: {e}. Generating a new one.")

    # Auto-generate a key if none is configured
    generated_key = Fernet.generate_key().decode()
    logger.warning(
        "SMTP_ENCRYPTION_KEY not set or invalid. Auto-generated a key. "
        "Add this to your .env to persist across restarts:\n"
        f"SMTP_ENCRYPTION_KEY={generated_key}"
    )
    _fernet = Fernet(generated_key.encode())
    return _fernet


def encrypt_password(plain_text: str) -> str:
    """
    Encrypt a plain-text SMTP password.

    Args:
        plain_text: The raw password string.

    Returns:
        Base64-encoded encrypted string.
    """
    if not plain_text:
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_text.encode())
    return encrypted.decode()


def decrypt_password(encrypted_text: str) -> str:
    """
    Decrypt an encrypted SMTP password.

    Args:
        encrypted_text: The Fernet-encrypted password string.

    Returns:
        The original plain-text password.
    """
    if not encrypted_text:
        return ""
    fernet = _get_fernet()
    try:
        decrypted = fernet.decrypt(encrypted_text.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt SMTP password: {e}")
        raise ValueError("Unable to decrypt SMTP password. Check SMTP_ENCRYPTION_KEY.") from e


def mask_email(email: str) -> str:
    """
    Mask an email address for safe display in logs and API responses.

    Example:
        user.name@gmail.com -> us*****@gmail.com
    """
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * 5
    else:
        masked_local = local[:2] + "*" * 5
    return f"{masked_local}@{domain}"


def mask_password(password: str) -> str:
    """Return a fixed masked placeholder for password display."""
    return "••••••••" if password else ""
