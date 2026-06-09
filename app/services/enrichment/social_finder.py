"""
social_finder.py - Find social media profiles for businesses.
"""

from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def find_social_profiles(
    business_name: str,
    location: str,
    website_html: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Find social media profiles for a business.
    
    Strategy:
    1. Extract from website HTML if available
    2. Fall back to search-based discovery
    """
    profiles = {
        "instagram": None,
        "facebook": None,
        "linkedin": None,
    }

    # Try extracting from website HTML first
    if website_html:
        profiles = extract_social_from_html(website_html)

    logger.info(f"Social profiles for {business_name}: {profiles}")
    return profiles


def extract_social_from_html(html_content: str) -> Dict[str, Optional[str]]:
    """Extract social media links from website HTML."""
    from bs4 import BeautifulSoup

    profiles = {
        "instagram": None,
        "facebook": None,
        "linkedin": None,
    }

    try:
        soup = BeautifulSoup(html_content, "lxml")
        links = soup.find_all("a", href=True)

        for link in links:
            href = link["href"].lower()

            if "instagram.com" in href and not profiles["instagram"]:
                profiles["instagram"] = link["href"]

            elif "facebook.com" in href and not profiles["facebook"]:
                profiles["facebook"] = link["href"]

            elif "linkedin.com" in href and not profiles["linkedin"]:
                profiles["linkedin"] = link["href"]

    except Exception as e:
        logger.error(f"Error extracting social profiles from HTML: {e}")

    return profiles
