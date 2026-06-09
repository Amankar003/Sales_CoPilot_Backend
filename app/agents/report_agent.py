"""
report_agent.py - AI agent for generating report content.
"""

import json
from typing import Dict, Any, List
from app.services.llm.llm_client import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Mock fallback response
MOCK_REPORT_CONTENT = {
    "executive_summary": "This digital audit reveals that the business has a baseline online presence but misses key opportunities for lead generation. Addressing the technical and strategic gaps identified will significantly improve customer acquisition.",
    "website_audit_summary": "The website requires structural improvements. While it serves as a basic digital brochure, it lacks optimization for search engines and conversion rate optimization (CRO) elements necessary to capture leads effectively.",
    "social_audit_summary": "Social media presence is currently underutilized. A consistent strategy across relevant platforms would help build brand awareness and engage with the local community.",
    "opportunity_summary": "By implementing a targeted digital strategy focusing on website optimization and active social engagement, the business can capture a larger share of the local market."
}

REPORT_SYSTEM_PROMPT = """
You are a top-tier digital strategy consultant writing an audit report for a client.
Write professional, persuasive, and encouraging summaries for the audit report. The tone should be authoritative but helpful - showing them what's wrong, but emphasizing that we can fix it and grow their revenue.

Respond ONLY with a valid JSON object in this exact format:
{
  "executive_summary": "A 3-4 sentence high-level summary of the business's current digital state and the growth opportunity.",
  "website_audit_summary": "A 2-3 sentence summary of the website's technical and UX performance.",
  "social_audit_summary": "A 2-3 sentence summary of their social media presence.",
  "opportunity_summary": "A 2-3 sentence concluding summary of what they stand to gain by implementing the recommendations."
}
"""

REPORT_USER_PROMPT = """
Business Context:
- Name: {business_name}
- Category: {category}
- Location: {location}
- Has Website: {has_website}

Scores (0-100):
- Overall: {audit_score}
- SEO: {seo_score}
- Social: {social_score}
- UX: {ux_score}

Pain Points Identified:
{pain_points}

Recommendations:
{recommendations}
"""


async def generate_report_content_with_ai(
    business_name: str,
    category: str,
    location: str,
    audit_score: float,
    seo_score: float,
    social_score: float,
    ux_score: float,
    pain_points: List[str],
    recommendations: List[str],
    has_website: bool,
) -> Dict[str, str]:
    """
    Use AI to write professional summaries for the audit report.
    Returns structured JSON or mock data if AI is disabled.
    """
    logger.info(f"Calling AI to generate report content for {business_name}")
    
    # Use HEAVY model for long-form generation and professional report writing
    return await llm_client.generate_json(
        task_type="heavy",
        system_prompt=REPORT_SYSTEM_PROMPT,
        user_prompt=REPORT_USER_PROMPT,
        fallback=MOCK_REPORT_CONTENT,
        variables={
            "business_name": business_name,
            "category": category,
            "location": location,
            "has_website": "Yes" if has_website else "No",
            "audit_score": audit_score or 0,
            "seo_score": seo_score or 0,
            "social_score": social_score or 0,
            "ux_score": ux_score or 0,
            "pain_points": json.dumps(pain_points),
            "recommendations": json.dumps(recommendations),
        },
        temperature=0.4
    )
