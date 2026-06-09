"""
call_notes_generator.py - Orchestrates call notes generation.
"""

from typing import List
from app.models.business import Business
from app.models.audit import Audit
from app.agents.outreach_agent import generate_call_notes
from app.utils.parser import safe_json_loads
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_call_script_notes(business: Business, audit: Audit | None) -> str:
    """
    Generate bullet points and script for a sales call.
    """
    logger.info(f"Generating call notes for {business.name}")

    pain_points = []
    if audit and audit.pain_points_json:
        pain_points = safe_json_loads(audit.pain_points_json, [])

    # Call AI agent
    notes = await generate_call_notes(
        business_name=business.name,
        category=business.category,
        pain_points=pain_points,
    )

    if not notes:
        # Fallback content
        notes = f"""Call Notes for {business.name}:
- Introduce yourself and mention you help {business.category}s.
- Ask about their current lead generation process.
- Mention 1-2 areas of improvement if they have a weak online presence.
- Propose a short discovery meeting.
"""

    return notes
