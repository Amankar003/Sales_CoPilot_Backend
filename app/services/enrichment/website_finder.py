"""
website_finder.py - Find and validate business websites.
"""

import httpx
from typing import Optional
from app.services.discovery.serp_search import search_business_website
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def find_website(business_name: str, location: str) -> Optional[str]:
    """
    Find the official website for a business.
    Uses DuckDuckGo search and validates the URL.
    """
    try:
        url = await search_business_website(business_name, location)
        if url:
            # Validate the URL is accessible
            is_valid = await validate_url(url)
            if is_valid:
                return url
        return None
    except Exception as e:
        logger.error(f"Website finder error for {business_name}: {e}")
        return None


async def validate_url(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL is accessible."""
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=timeout,
            verify=False,  # Some Indian sites have SSL issues
        ) as client:
            response = await client.head(url)
            return response.status_code < 400
    except Exception:
        return False


async def check_ssl(url: str) -> bool:
    """Check if a website has valid SSL."""
    try:
        if not url.startswith("https"):
            return False
        async with httpx.AsyncClient(
            timeout=10.0,
            verify=True,  # Strict SSL check
        ) as client:
            response = await client.head(url)
            return response.status_code < 400
    except Exception:
        return False
