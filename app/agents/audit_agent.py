"""
audit_agent.py - AI agent for analyzing audit data.
"""

import json
from typing import Dict, Any, Optional
from app.services.llm.llm_client import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Mock fallback response
MOCK_AUDIT_INSIGHTS = {
    "pain_points": [
        "Website lacks a clear call-to-action above the fold",
        "No clear unique value proposition presented to visitors",
        "Missing social proof and customer testimonials"
    ],
    "recommendations": [
        "Add a prominent 'Book Consultation' button on the hero section",
        "Include a section highlighting customer reviews and case studies",
        "Implement a lead capture popup for exit intent"
    ]
}

AUDIT_SYSTEM_PROMPT = """
You are an expert digital marketing consultant analyzing a website audit for a local business.

Respond ONLY with a valid JSON object in this exact format:
{
  "pain_points": ["point 1", "point 2", "point 3"],
  "recommendations": ["rec 1", "rec 2", "rec 3"]
}
"""

AUDIT_USER_PROMPT = """
Business Details:
- Name: {business_name}
- Category: {category}
- Location: {location}

Audit Scores:
- SEO Score: {seo_score}/100
- Social Media Score: {social_score}/100

Raw Audit Data (JSON):
{audit_data}

Based on this information, provide strategic insights. Identify 3 critical pain points that are hurting their lead generation, and 3 actionable recommendations to fix them.
"""


async def analyze_audit_with_ai(
    business_name: str,
    category: str,
    location: str,
    audit_data: Dict[str, Any],
    seo_score: float,
    social_score: float,
) -> Optional[Dict[str, Any]]:
    """
    Use AI to analyze audit data and generate pain points and recommendations.
    Returns structured JSON or mock data if AI is disabled.
    """
    logger.info(f"Calling AI to analyze audit for {business_name}")
    
    # Clean up audit data for prompt to save tokens
    clean_audit = {k: v for k, v in audit_data.items() if k not in ["html_content"]}

    # Use HEAVY model for complex reasoning and detecting pain points/recommendations
    return await llm_client.generate_json(
        task_type="heavy",
        system_prompt=AUDIT_SYSTEM_PROMPT,
        user_prompt=AUDIT_USER_PROMPT,
        fallback=MOCK_AUDIT_INSIGHTS,
        variables={
            "business_name": business_name,
            "category": category,
            "location": location,
            "seo_score": seo_score,
            "social_score": social_score,
            "audit_data": json.dumps(clean_audit),
        },
        temperature=0.3
    )
