"""
techstack_detector.py - Detect technology stack from website HTML.
"""

import re
from typing import List, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Technology patterns to detect in HTML
TECH_PATTERNS = {
    "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
    "Wix": [r"wix\.com", r"wixsite\.com", r"_wix_"],
    "Shopify": [r"shopify", r"cdn\.shopify"],
    "React": [r"react", r"__next", r"_next/static"],
    "Angular": [r"ng-version", r"angular"],
    "Vue.js": [r"vue\.js", r"__vue__"],
    "jQuery": [r"jquery"],
    "Bootstrap": [r"bootstrap"],
    "Google Analytics": [r"google-analytics", r"gtag", r"UA-\d+"],
    "Google Tag Manager": [r"googletagmanager"],
    "Facebook Pixel": [r"facebook.*pixel", r"fbq\("],
    "WhatsApp Widget": [r"wa\.me", r"whatsapp", r"api\.whatsapp"],
    "Tawk.to": [r"tawk\.to"],
    "Crisp Chat": [r"crisp\.chat"],
    "Intercom": [r"intercom"],
    "Razorpay": [r"razorpay"],
    "PayTM": [r"paytm"],
    "Cloudflare": [r"cloudflare"],
}


def detect_tech_stack(html_content: Optional[str]) -> List[str]:
    """
    Detect technologies used on a website from its HTML content.
    
    Returns a list of detected technology names.
    """
    if not html_content:
        return []

    detected = []
    html_lower = html_content.lower()

    for tech, patterns in TECH_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, html_lower, re.IGNORECASE):
                if tech not in detected:
                    detected.append(tech)
                break

    logger.info(f"Detected tech stack: {detected}")
    return detected
