"""
email_generator.py - Orchestrates email content generation.
"""

from typing import Dict, Any
from app.models.business import Business
from app.models.audit import Audit
from app.agents.outreach_agent import generate_outreach_email
from app.utils.parser import safe_json_loads
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_email_content(business: Business, audit: Audit | None) -> Dict[str, str]:
    """
    Generate personalized email subject and body.
    """
    logger.info(f"Generating email for {business.name}")

    pain_points = []
    if audit and audit.pain_points_json:
        pain_points = safe_json_loads(audit.pain_points_json, [])

    # Call AI agent
    email_content = await generate_outreach_email(
        business_name=business.name,
        category=business.category,
        location=business.location,
        has_website=audit.has_website if audit else False,
        pain_points=pain_points,
    )

    if not email_content:
        # Fallback content
        email_content = {
            "subject": f"Enhancing {business.name}'s digital presence in {business.location}",
            "body": f"Hi team at {business.name},\n\nI noticed some opportunities to improve your online presence for your {business.category} in {business.location}. Let's connect to discuss how we can help you get more customers.\n\nBest regards,"
        }

    return email_content
