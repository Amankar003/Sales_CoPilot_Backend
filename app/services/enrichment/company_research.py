"""
company_research.py - Deep company research using available data.
"""

from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def research_company(
    business_name: str,
    location: str,
    website: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Research a company and gather additional information.
    Returns structured research data.
    """
    logger.info(f"Researching company: {business_name} in {location}")

    research = {
        "business_name": business_name,
        "location": location,
        "category": category,
        "has_website": bool(website),
        "website": website,
        "research_notes": [],
    }

    # Add basic research notes based on available data
    if not website:
        research["research_notes"].append(
            "No website found - major opportunity for website development"
        )
    else:
        research["research_notes"].append(f"Website found: {website}")

    if category:
        research["research_notes"].append(
            f"Business operates in the {category} sector in {location}"
        )

    return research
