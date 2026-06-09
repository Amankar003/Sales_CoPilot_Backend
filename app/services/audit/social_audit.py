"""
social_audit.py - Social media presence auditing and scoring.
"""

from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def calculate_social_score(
    instagram: Optional[str] = None,
    facebook: Optional[str] = None,
    linkedin: Optional[str] = None,
    has_whatsapp: bool = False,
    google_rating: Optional[float] = None,
    reviews_count: Optional[int] = None,
) -> float:
    """
    Calculate a social media presence score (0-100).
    
    Scoring factors:
    - Has Instagram (20 points)
    - Has Facebook (20 points)
    - Has LinkedIn (15 points)
    - Has WhatsApp (15 points)
    - Google rating >= 4.0 (15 points)
    - Google reviews > 100 (15 points)
    """
    score = 0.0

    if instagram:
        score += 20
    if facebook:
        score += 20
    if linkedin:
        score += 15
    if has_whatsapp:
        score += 15
    if google_rating and google_rating >= 4.0:
        score += 15
    elif google_rating and google_rating >= 3.0:
        score += 8
    if reviews_count and reviews_count > 100:
        score += 15
    elif reviews_count and reviews_count > 50:
        score += 8

    return min(score, 100.0)


def get_social_recommendations(
    instagram: Optional[str] = None,
    facebook: Optional[str] = None,
    linkedin: Optional[str] = None,
    has_whatsapp: bool = False,
    google_rating: Optional[float] = None,
    reviews_count: Optional[int] = None,
) -> list:
    """Generate social media recommendations."""
    recommendations = []

    if not instagram:
        recommendations.append(
            "Create an Instagram business profile to reach younger audiences"
        )
    if not facebook:
        recommendations.append(
            "Set up a Facebook Business Page for broader reach and reviews"
        )
    if not linkedin:
        recommendations.append(
            "Create a LinkedIn company page for B2B visibility"
        )
    if not has_whatsapp:
        recommendations.append(
            "Add WhatsApp Business for instant customer communication"
        )
    if not google_rating or google_rating < 4.0:
        recommendations.append(
            "Improve Google ratings through better service and review management"
        )
    if not reviews_count or reviews_count < 50:
        recommendations.append(
            "Encourage customers to leave Google reviews to build trust"
        )

    return recommendations


def get_social_summary(
    instagram: Optional[str] = None,
    facebook: Optional[str] = None,
    linkedin: Optional[str] = None,
    has_whatsapp: bool = False,
) -> str:
    """Generate a summary of social media presence."""
    platforms = []
    if instagram:
        platforms.append("Instagram")
    if facebook:
        platforms.append("Facebook")
    if linkedin:
        platforms.append("LinkedIn")
    if has_whatsapp:
        platforms.append("WhatsApp")

    if not platforms:
        return "No social media presence detected. This represents a significant growth opportunity."

    return f"Active on {', '.join(platforms)}. " + (
        "Good social presence." if len(platforms) >= 3
        else "Social presence could be expanded."
    )
