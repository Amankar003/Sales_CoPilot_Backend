"""
pitch_generator.py - Orchestrates meeting pitch generation.
"""

from app.models.business import Business
from app.models.audit import Audit
from app.agents.outreach_agent import generate_meeting_pitch
from app.utils.parser import safe_json_loads
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_pitch_content(business: Business, audit: Audit | None) -> str:
    """
    Generate a meeting booking pitch.
    """
    logger.info(f"Generating meeting pitch for {business.name}")

    opportunities = []
    if audit and audit.opportunities_json:
        opportunities = safe_json_loads(audit.opportunities_json, [])

    # Call AI agent
    pitch = await generate_meeting_pitch(
        business_name=business.name,
        category=business.category,
        opportunities=opportunities,
    )

    if not pitch:
        # Fallback content
        pitch = f"Let's schedule a 15-minute discovery call to show you exactly how we can implement these solutions for {business.name} and increase your revenue."

    return pitch
