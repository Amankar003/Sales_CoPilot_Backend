"""
whatsapp_generator.py - Orchestrates WhatsApp message generation.
"""

from app.models.business import Business
from app.agents.outreach_agent import generate_whatsapp_message
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_whatsapp_content(business: Business) -> str:
    """
    Generate a short, punchy WhatsApp message.
    """
    logger.info(f"Generating WhatsApp message for {business.name}")

    # Call AI agent
    message = await generate_whatsapp_message(
        business_name=business.name,
        category=business.category,
        location=business.location,
    )

    if not message:
        # Fallback content
        message = f"Hi {business.name} team! 👋 We help {business.category}s in {business.location} get more customers online. Would you be open to a quick 5-min chat about improving your digital presence?"

    return message
