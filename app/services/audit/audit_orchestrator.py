"""
audit_orchestrator.py - Orchestrates the full audit process for a business.
"""

import json
from typing import Optional
from sqlmodel import Session, select
from app.models.business import Business
from app.models.audit import Audit
from app.services.audit.website_audit import audit_website, get_no_website_result
from app.services.audit.seo_audit import calculate_seo_score, get_seo_recommendations
from app.services.audit.social_audit import (
    calculate_social_score,
    get_social_recommendations,
)
from app.services.enrichment.social_finder import find_social_profiles
from app.services.enrichment.techstack_detector import detect_tech_stack
from app.agents.audit_agent import analyze_audit_with_ai
from app.core.constants import AUDIT_WEIGHTS
from app.utils.helpers import calculate_weighted_score
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_full_audit(business: Business, session: Session) -> Audit:
    """
    Run a comprehensive audit for a business.
    
    Steps:
    1. Audit website (if exists)
    2. Calculate SEO score
    3. Calculate social score
    4. Calculate UX score
    5. Detect pain points via AI
    6. Generate recommendations
    7. Save audit to database
    """
    logger.info(f"Starting full audit for: {business.name} (ID: {business.id})")

    # Check for existing audit and remove it
    existing_audit = session.exec(
        select(Audit).where(Audit.business_id == business.id)
    ).first()
    if existing_audit:
        session.delete(existing_audit)
        session.commit()

    # Step 1: Website audit
    website_data = {}
    html_content = None
    if business.website:
        website_data = await audit_website(business.website)
        html_content = website_data.pop("html_content", None)
    else:
        website_data = get_no_website_result()

    # Step 2: Enrich social data from website
    if html_content:
        social_profiles = await find_social_profiles(
            business.name, business.location, html_content
        )
        # Update business social links if found and not already set
        if social_profiles.get("instagram") and not business.instagram:
            business.instagram = social_profiles["instagram"]
        if social_profiles.get("facebook") and not business.facebook:
            business.facebook = social_profiles["facebook"]
        if social_profiles.get("linkedin") and not business.linkedin:
            business.linkedin = social_profiles["linkedin"]
        session.add(business)
        session.commit()

    # Step 3: Calculate SEO score
    seo_score = calculate_seo_score(website_data) if website_data.get("has_website") else 0.0

    # Step 4: Calculate social score
    social_score = calculate_social_score(
        instagram=business.instagram,
        facebook=business.facebook,
        linkedin=business.linkedin,
        has_whatsapp=website_data.get("has_whatsapp", False),
        google_rating=business.google_rating,
        reviews_count=business.reviews_count,
    )

    # Step 5: Calculate UX score
    ux_score = calculate_ux_score(website_data)

    # Step 6: Calculate overall audit score
    scores = {
        "website": website_data.get("loading_speed_score", 0.0) if website_data.get("has_website") else 0.0,
        "seo": seo_score,
        "social": social_score,
        "ux": ux_score,
    }
    overall_score = calculate_weighted_score(scores, AUDIT_WEIGHTS)

    # Step 7: Generate pain points and recommendations
    pain_points = generate_pain_points(business, website_data, seo_score, social_score)
    seo_recs = get_seo_recommendations(website_data, seo_score)
    social_recs = get_social_recommendations(
        instagram=business.instagram,
        facebook=business.facebook,
        linkedin=business.linkedin,
        has_whatsapp=website_data.get("has_whatsapp", False),
        google_rating=business.google_rating,
        reviews_count=business.reviews_count,
    )
    all_recommendations = seo_recs + social_recs

    # Step 8: Try AI analysis for enhanced insights
    ai_insights = await analyze_audit_with_ai(
        business_name=business.name,
        category=business.category,
        location=business.location,
        audit_data=website_data,
        seo_score=seo_score,
        social_score=social_score,
    )
    if ai_insights:
        if ai_insights.get("pain_points"):
            pain_points.extend(ai_insights["pain_points"])
        if ai_insights.get("recommendations"):
            all_recommendations.extend(ai_insights["recommendations"])

    # Deduplicate
    pain_points = list(dict.fromkeys(pain_points))
    all_recommendations = list(dict.fromkeys(all_recommendations))

    # Generate opportunities
    opportunities = generate_opportunities(pain_points, business.category)

    # Step 9: Save audit to database
    audit = Audit(
        business_id=business.id,
        has_website=website_data.get("has_website", False),
        ssl_enabled=website_data.get("ssl_enabled", False),
        mobile_responsive=website_data.get("mobile_responsive", False),
        loading_speed_score=website_data.get("loading_speed_score"),
        seo_score=seo_score,
        ux_score=ux_score,
        social_score=social_score,
        has_contact_form=website_data.get("has_contact_form", False),
        has_whatsapp=website_data.get("has_whatsapp", False),
        has_booking_system=website_data.get("has_booking_system", False),
        has_crm_signals=website_data.get("has_crm_signals", False),
        broken_links_count=website_data.get("broken_links_count", 0),
        meta_title=website_data.get("meta_title"),
        meta_description=website_data.get("meta_description"),
        h1_count=website_data.get("h1_count", 0),
        image_alt_missing_count=website_data.get("image_alt_missing_count", 0),
        audit_score=overall_score,
        pain_points_json=json.dumps(pain_points, ensure_ascii=False),
        opportunities_json=json.dumps(opportunities, ensure_ascii=False),
        recommendations_json=json.dumps(all_recommendations, ensure_ascii=False),
    )

    session.add(audit)
    session.commit()
    session.refresh(audit)

    logger.info(f"Audit complete for {business.name}. Score: {overall_score}")
    return audit


def calculate_ux_score(website_data: dict) -> float:
    """
    Calculate a UX score (0-100) based on website features.
    
    Scoring factors:
    - Has contact form (25 points)
    - Has WhatsApp (20 points)
    - Has booking system (20 points)
    - Mobile responsive (20 points)
    - Fast loading (15 points)
    """
    if not website_data.get("has_website"):
        return 0.0

    score = 0.0
    if website_data.get("has_contact_form"):
        score += 25
    if website_data.get("has_whatsapp"):
        score += 20
    if website_data.get("has_booking_system"):
        score += 20
    if website_data.get("mobile_responsive"):
        score += 20
    loading_speed = website_data.get("loading_speed_score", 0)
    if loading_speed >= 70:
        score += 15
    elif loading_speed >= 50:
        score += 10

    return min(score, 100.0)


def generate_pain_points(
    business: Business,
    website_data: dict,
    seo_score: float,
    social_score: float,
) -> list:
    """Generate pain points based on audit findings."""
    pain_points = []

    if not website_data.get("has_website"):
        pain_points.append("No website - losing potential customers who search online")

    if not website_data.get("ssl_enabled") and website_data.get("has_website"):
        pain_points.append("No SSL/HTTPS - website marked as 'Not Secure' by browsers")

    if not website_data.get("mobile_responsive") and website_data.get("has_website"):
        pain_points.append("Not mobile-friendly - poor experience for mobile users (60%+ traffic)")

    if not website_data.get("has_contact_form") and website_data.get("has_website"):
        pain_points.append("No contact form - missing lead capture opportunities")

    if not website_data.get("has_whatsapp"):
        pain_points.append("No WhatsApp integration - missing instant communication channel")

    if not website_data.get("has_booking_system"):
        pain_points.append("No online booking system - customers can't self-schedule")

    if seo_score < 40:
        pain_points.append("Poor SEO - low visibility in search engine results")

    if social_score < 30:
        pain_points.append("Weak social media presence - limited brand visibility")

    if not business.email:
        pain_points.append("No public business email - difficult for customers to reach out")

    return pain_points


def generate_opportunities(pain_points: list, category: str) -> list:
    """Generate business opportunities from pain points."""
    opportunities = []

    for point in pain_points:
        point_lower = point.lower()
        if "no website" in point_lower:
            opportunities.append(f"Website development for {category} - high ROI opportunity")
        elif "ssl" in point_lower:
            opportunities.append("SSL certificate setup and security hardening")
        elif "mobile" in point_lower:
            opportunities.append("Mobile-responsive website redesign")
        elif "seo" in point_lower:
            opportunities.append("SEO optimization package to improve search rankings")
        elif "social" in point_lower:
            opportunities.append("Social media management and content strategy")
        elif "whatsapp" in point_lower:
            opportunities.append("WhatsApp Business API integration for customer engagement")
        elif "booking" in point_lower:
            opportunities.append("Online booking/appointment system integration")
        elif "contact form" in point_lower:
            opportunities.append("Lead capture form and CRM integration")

    return opportunities
