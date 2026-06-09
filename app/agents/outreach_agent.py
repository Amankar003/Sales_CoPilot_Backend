"""
outreach_agent.py - AI agent for generating outreach content (Email, WhatsApp, Calls, Pitches).
"""

import json
from typing import Dict, Any, List
from app.services.llm.llm_client import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

# --- Mock Fallbacks ---

MOCK_EMAIL = {
    "subject": "Quick question about your lead generation in {location}",
    "body": "Hi {business_name} team,\n\nI was looking for a good {category} in {location} and came across your business. I noticed you have great potential but might be missing out on customers because of a few online visibility issues.\n\nWe recently helped a similar business increase their local inquiries by 40% in just two months.\n\nWould you be open to a brief 10-minute chat next week to see if we can do the same for you?\n\nBest regards,\n[Your Name]"
}

MOCK_WHATSAPP = "Hi {business_name} team! 👋 I noticed your {category} business in {location} is doing great, but your online presence has a few gaps costing you customers. We specialize in fixing this. Open to a quick 5-min chat this week to discuss?"

MOCK_CALL_NOTES = """Call Prep for {business_name}:
1. Building Rapport: Compliment them on being a top {category} in {location}.
2. The Hook: Mention that despite their reputation, they are losing online traffic to competitors.
3. The Proof: Bring up specific pain points (e.g., poor mobile experience, missing SEO).
4. The Ask: Propose a 15-min discovery call to show the full audit report."""

MOCK_PITCH = "Based on our audit, fixing these specific digital gaps will immediately increase your local search visibility. Let's schedule a 15-minute strategy session where I'll walk you through the exact blueprint to capture the {location} market."


# --- Prompts ---

EMAIL_SYSTEM_PROMPT = """
Write a cold outreach email to a business owner.
Rules:
1. Make the subject line catchy and personalized, but not clickbaity.
2. Keep the email under 150 words.
3. Highlight 1-2 specific pain points so they know this isn't a generic blast.
4. Focus on the value (more customers, better reputation) rather than the technical fix.
5. End with a low-friction call to action (a quick chat).

Respond ONLY with a valid JSON object:
{
  "subject": "Email subject line here",
  "body": "Full email body here"
}
"""

EMAIL_USER_PROMPT = """
Target: {business_name} (A {category} in {location})
Has Website: {has_website}
Key Pain Points Found: {pain_points}
"""

WHATSAPP_SYSTEM_PROMPT = """
Write a cold outreach WhatsApp message to a business owner.
Rules:
1. Keep it very short (under 50 words).
2. Be polite, friendly, and use 1-2 emojis.
3. Hook them with a specific local insight or compliment.
4. End with a simple question to get a reply.

Return ONLY the text of the message, no JSON or extra commentary.
"""

WHATSAPP_USER_PROMPT = """
Target: {business_name} (A {category} in {location})
"""

CALL_NOTES_SYSTEM_PROMPT = """
Write preparation notes for a cold call to a business.
Create a structured bulleted list covering:
- Intro/Hook
- The Problem (based on their pain points)
- The Value Proposition
- Handling common objections
- The Close (booking a meeting)

Return ONLY the text of the notes, no JSON or extra commentary.
"""

CALL_NOTES_USER_PROMPT = """
Target: {business_name} (A {category} in {location})
Key Pain Points: {pain_points}
"""

PITCH_SYSTEM_PROMPT = """
Write a short, punchy meeting booking pitch (elevator pitch) that our sales rep can use at the end of an initial conversation.
The pitch should be 2-3 sentences and focus purely on the ROI and getting them to agree to a longer strategy meeting.

Return ONLY the text of the pitch, no JSON or extra commentary.
"""

PITCH_USER_PROMPT = """
Target: {business_name} (A {category} in {location})
Key Opportunities: {opportunities}
"""

# --- Functions ---

async def generate_outreach_email(
    business_name: str, category: str, location: str, 
    has_website: bool, pain_points: List[str]
) -> Dict[str, str]:
    mock = MOCK_EMAIL.copy()
    mock["subject"] = mock["subject"].format(location=location)
    mock["body"] = mock["body"].format(business_name=business_name, category=category, location=location)
    
    # Use HEAVY model for highly personalized and nuanced email generation
    return await llm_client.generate_json(
        task_type="heavy",
        system_prompt=EMAIL_SYSTEM_PROMPT,
        user_prompt=EMAIL_USER_PROMPT,
        fallback=mock,
        variables={
            "business_name": business_name, 
            "category": category, 
            "location": location,
            "has_website": "Yes" if has_website else "No", 
            "pain_points": json.dumps(pain_points[:3])
        },
        temperature=0.7
    )


async def generate_whatsapp_message(business_name: str, category: str, location: str) -> str:
    mock = MOCK_WHATSAPP.format(business_name=business_name, category=category, location=location)
    
    # Use LIGHT model for short, simple WhatsApp messages
    return await llm_client.generate_text(
        task_type="light",
        system_prompt=WHATSAPP_SYSTEM_PROMPT,
        user_prompt=WHATSAPP_USER_PROMPT,
        fallback=mock,
        variables={
            "business_name": business_name, 
            "category": category, 
            "location": location
        },
        temperature=0.7
    )


async def generate_call_notes(business_name: str, category: str, pain_points: List[str]) -> str:
    mock = MOCK_CALL_NOTES.format(business_name=business_name, category=category, location="your area")
    
    # Use HEAVY model for structured call strategy and objection handling
    return await llm_client.generate_text(
        task_type="heavy",
        system_prompt=CALL_NOTES_SYSTEM_PROMPT,
        user_prompt=CALL_NOTES_USER_PROMPT,
        fallback=mock,
        variables={
            "business_name": business_name, 
            "category": category, 
            "location": "your area",
            "pain_points": json.dumps(pain_points[:3])
        },
        temperature=0.5
    )


async def generate_meeting_pitch(business_name: str, category: str, opportunities: List[str]) -> str:
    mock = MOCK_PITCH.format(location="your area")
    
    # Use LIGHT model for a simple short pitch
    return await llm_client.generate_text(
        task_type="light",
        system_prompt=PITCH_SYSTEM_PROMPT,
        user_prompt=PITCH_USER_PROMPT,
        fallback=mock,
        variables={
            "business_name": business_name, 
            "category": category, 
            "location": "your area",
            "opportunities": json.dumps(opportunities[:3])
        },
        temperature=0.7
    )
