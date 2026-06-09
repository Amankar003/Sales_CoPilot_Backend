"""
research_agent.py - AI agent for deep business research.
"""

from typing import Dict, Any, Optional
from app.services.llm.llm_client import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Mock fallback response
MOCK_RESEARCH_DATA = {
    "target_audience": "Local customers, typically within a 5-10 mile radius",
    "key_services": ["Primary Service 1", "Primary Service 2", "Consultation"],
    "competitor_analysis": "Highly competitive local market. Differentiation typically based on reviews and service quality.",
    "growth_opportunities": [
        "Implement a referral program",
        "Run localized Google Ads",
        "Build a robust Google My Business profile"
    ]
}

RESEARCH_SYSTEM_PROMPT = """
You are a top-tier business research analyst. Based on the limited information provided, generate strategic insights about this business.

Respond ONLY with a valid JSON object in this exact format:
{
  "target_audience": "description of target audience",
  "key_services": ["service 1", "service 2"],
  "competitor_analysis": "brief analysis of local competition",
  "growth_opportunities": ["opportunity 1", "opportunity 2"]
}
"""

RESEARCH_USER_PROMPT = """
Business Details:
- Name: {business_name}
- Category: {category}
- Location: {location}
- Description/Notes: {description}

Provide an analysis of their likely target audience, key services, local competition, and high-level growth opportunities.
"""


async def run_business_research(
    business_name: str,
    category: str,
    location: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Use AI to research a business and generate strategic insights.
    Returns structured JSON or mock data if AI is disabled.
    """
    logger.info(f"Calling AI to research {business_name}")
    
    # Use LIGHT model for simple summaries and classification
    return await llm_client.generate_json(
        task_type="light",
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        user_prompt=RESEARCH_USER_PROMPT,
        fallback=MOCK_RESEARCH_DATA,
        variables={
            "business_name": business_name,
            "category": category,
            "location": location,
            "description": description or "No additional information provided.",
        },
        temperature=0.5
    )
