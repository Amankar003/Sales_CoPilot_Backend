"""
seo_audit.py - SEO auditing and scoring.
"""

from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_seo_score(audit_data: Dict[str, Any]) -> float:
    """
    Calculate an SEO score (0-100) based on audit data.
    
    Scoring factors:
    - Has meta title (15 points)
    - Meta title length 30-60 chars (10 points)
    - Has meta description (15 points)
    - Meta description length 120-160 chars (10 points)
    - Has exactly 1 H1 tag (10 points)
    - All images have alt text (15 points)
    - SSL enabled (10 points)
    - Mobile responsive (15 points)
    """
    score = 0.0

    # Meta title
    meta_title = audit_data.get("meta_title")
    if meta_title:
        score += 15
        title_len = len(meta_title)
        if 30 <= title_len <= 60:
            score += 10
        elif 20 <= title_len <= 70:
            score += 5

    # Meta description
    meta_desc = audit_data.get("meta_description")
    if meta_desc:
        score += 15
        desc_len = len(meta_desc)
        if 120 <= desc_len <= 160:
            score += 10
        elif 80 <= desc_len <= 200:
            score += 5

    # H1 tags
    h1_count = audit_data.get("h1_count", 0)
    if h1_count == 1:
        score += 10
    elif h1_count > 1:
        score += 5  # Has H1s but too many

    # Image alt text
    missing_alt = audit_data.get("image_alt_missing_count", 0)
    if missing_alt == 0:
        score += 15
    elif missing_alt <= 3:
        score += 10
    elif missing_alt <= 5:
        score += 5

    # SSL
    if audit_data.get("ssl_enabled"):
        score += 10

    # Mobile responsive
    if audit_data.get("mobile_responsive"):
        score += 15

    return min(score, 100.0)


def get_seo_recommendations(
    audit_data: Dict[str, Any],
    seo_score: float,
) -> list:
    """Generate SEO recommendations based on audit findings."""
    recommendations = []

    if not audit_data.get("meta_title"):
        recommendations.append("Add a descriptive meta title to improve search visibility")

    if not audit_data.get("meta_description"):
        recommendations.append("Add a meta description to improve click-through rates from search")

    if audit_data.get("h1_count", 0) == 0:
        recommendations.append("Add an H1 heading tag for better SEO structure")
    elif audit_data.get("h1_count", 0) > 1:
        recommendations.append("Use only one H1 tag per page for optimal SEO")

    if audit_data.get("image_alt_missing_count", 0) > 0:
        count = audit_data["image_alt_missing_count"]
        recommendations.append(f"Add alt text to {count} images for better accessibility and SEO")

    if not audit_data.get("ssl_enabled"):
        recommendations.append("Enable HTTPS/SSL for security and SEO ranking boost")

    if not audit_data.get("mobile_responsive"):
        recommendations.append("Make the website mobile-responsive for better rankings")

    if seo_score < 50:
        recommendations.append("Consider a comprehensive SEO overhaul to improve online visibility")

    return recommendations
