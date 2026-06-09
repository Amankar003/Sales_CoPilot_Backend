"""
validators.py - Input validation helpers.
"""

import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """Check if an email address is valid."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """Check if a URL is valid."""
    pattern = r"^https?://[^\s<>\"{}|\\^`\[\]]+$"
    return bool(re.match(pattern, url))


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalize a URL by adding https:// if missing."""
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def sanitize_string(text: Optional[str], max_length: int = 500) -> Optional[str]:
    """Sanitize and truncate a string."""
    if not text:
        return None
    # Remove excess whitespace
    text = " ".join(text.split())
    # Truncate
    if len(text) > max_length:
        text = text[:max_length] + "..."
    return text


def is_valid_phone(phone: str) -> bool:
    """Basic phone number validation for Indian numbers."""
    # Remove common separators
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)
    # Indian numbers: 10 digits, optionally prefixed with 91
    return bool(re.match(r"^(91)?[6-9]\d{9}$", cleaned))
