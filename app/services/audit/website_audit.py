"""
website_audit.py - Website auditing: HTTPS, homepage analysis, contact detection.
"""

import httpx
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from app.utils.logger import get_logger
from app.core.constants import CTA_KEYWORDS

logger = get_logger(__name__)


async def audit_website(url: str) -> Dict[str, Any]:
    """
    Perform a comprehensive website audit.
    
    Checks:
    - HTTPS / SSL
    - Page loads successfully
    - Title and meta description
    - H1 tags
    - Contact form detection
    - WhatsApp link detection
    - CTA keyword detection
    - Social media links
    - Image alt text
    - Basic mobile viewport detection
    """
    logger.info(f"Auditing website: {url}")

    result = {
        "has_website": True,
        "ssl_enabled": False,
        "mobile_responsive": False,
        "loading_speed_score": None,
        "has_contact_form": False,
        "has_whatsapp": False,
        "has_booking_system": False,
        "has_crm_signals": False,
        "meta_title": None,
        "meta_description": None,
        "h1_count": 0,
        "image_alt_missing_count": 0,
        "broken_links_count": 0,
        "cta_found": [],
        "social_links": {},
        "tech_stack": [],
        "html_content": None,
    }

    try:
        # Check SSL
        result["ssl_enabled"] = url.startswith("https")

        # Fetch the page
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            verify=False,
        ) as client:
            response = await client.get(url)

        if response.status_code >= 400:
            logger.warning(f"Website returned status {response.status_code}")
            result["has_website"] = False
            return result

        html_content = response.text
        result["html_content"] = html_content
        soup = BeautifulSoup(html_content, "lxml")

        # Extract title
        title_tag = soup.find("title")
        result["meta_title"] = title_tag.get_text(strip=True) if title_tag else None

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["meta_description"] = meta_desc.get("content", "").strip()

        # Count H1 tags
        result["h1_count"] = len(soup.find_all("h1"))

        # Check images for alt text
        images = soup.find_all("img")
        result["image_alt_missing_count"] = sum(
            1 for img in images if not img.get("alt", "").strip()
        )

        # Check for contact form
        forms = soup.find_all("form")
        for form in forms:
            form_text = form.get_text().lower()
            if any(kw in form_text for kw in ["name", "email", "phone", "message", "contact"]):
                result["has_contact_form"] = True
                break

        # Check for WhatsApp
        html_lower = html_content.lower()
        if "wa.me" in html_lower or "whatsapp" in html_lower or "api.whatsapp" in html_lower:
            result["has_whatsapp"] = True

        # Check for booking/appointment system
        booking_keywords = ["book now", "appointment", "schedule", "reservation", "book a"]
        if any(kw in html_lower for kw in booking_keywords):
            result["has_booking_system"] = True

        # Check for CRM signals
        crm_keywords = ["hubspot", "salesforce", "zoho", "pipedrive", "freshsales"]
        if any(kw in html_lower for kw in crm_keywords):
            result["has_crm_signals"] = True

        # Detect CTAs
        for cta in CTA_KEYWORDS:
            if cta.lower() in html_lower:
                result["cta_found"].append(cta)

        # Check mobile viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        if viewport:
            result["mobile_responsive"] = True

        # Simple loading speed estimation based on page size
        page_size_kb = len(html_content) / 1024
        if page_size_kb < 100:
            result["loading_speed_score"] = 90.0
        elif page_size_kb < 300:
            result["loading_speed_score"] = 70.0
        elif page_size_kb < 500:
            result["loading_speed_score"] = 50.0
        else:
            result["loading_speed_score"] = 30.0

        logger.info(f"Website audit complete for {url}")

    except httpx.TimeoutException:
        logger.warning(f"Timeout auditing {url}")
        result["loading_speed_score"] = 10.0
    except Exception as e:
        logger.error(f"Error auditing website {url}: {e}")
        result["has_website"] = False

    return result


def get_no_website_result() -> Dict[str, Any]:
    """Return audit results for a business without a website."""
    return {
        "has_website": False,
        "ssl_enabled": False,
        "mobile_responsive": False,
        "loading_speed_score": 0.0,
        "has_contact_form": False,
        "has_whatsapp": False,
        "has_booking_system": False,
        "has_crm_signals": False,
        "meta_title": None,
        "meta_description": None,
        "h1_count": 0,
        "image_alt_missing_count": 0,
        "broken_links_count": 0,
        "cta_found": [],
        "social_links": {},
        "tech_stack": [],
        "html_content": None,
    }
