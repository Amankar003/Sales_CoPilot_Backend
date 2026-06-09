"""
report_generator.py - Generate audit report content.
"""

import json
from typing import Optional
from sqlmodel import Session, select
from app.models.business import Business
from app.models.audit import Audit
from app.models.report import Report
from app.services.report.report_templates import render_report_html
from app.services.report.pdf_generator import generate_pdf
from app.agents.report_agent import generate_report_content_with_ai
from app.utils.parser import safe_json_loads
from app.utils.file_manager import get_report_path, save_file
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def generate_report(
    business: Business,
    audit: Audit,
    session: Session,
) -> Report:
    """
    Generate a comprehensive audit report for a business.
    
    Steps:
    1. Gather audit data
    2. Generate report content (AI-enhanced)
    3. Render HTML report
    4. Generate PDF
    5. Save report to database
    """
    logger.info(f"Generating report for: {business.name} (ID: {business.id})")

    # Check for existing report and remove it
    existing_report = session.exec(
        select(Report).where(Report.business_id == business.id)
    ).first()
    if existing_report:
        session.delete(existing_report)
        session.commit()

    # Parse audit JSON data
    pain_points = safe_json_loads(audit.pain_points_json, [])
    opportunities = safe_json_loads(audit.opportunities_json, [])
    recommendations = safe_json_loads(audit.recommendations_json, [])

    # Generate AI-enhanced content
    ai_content = await generate_report_content_with_ai(
        business_name=business.name,
        category=business.category,
        location=business.location,
        audit_score=audit.audit_score,
        seo_score=audit.seo_score,
        social_score=audit.social_score,
        ux_score=audit.ux_score,
        pain_points=pain_points,
        recommendations=recommendations,
        has_website=audit.has_website,
    )

    # Build report data
    executive_summary = ai_content.get("executive_summary", _default_executive_summary(
        business, audit, pain_points
    ))
    website_audit_summary = ai_content.get("website_audit_summary", _default_website_summary(audit))
    social_audit_summary = ai_content.get("social_audit_summary", _default_social_summary(audit))
    opportunity_summary = ai_content.get("opportunity_summary", _default_opportunity_summary(
        opportunities
    ))
    recommended_solutions = ai_content.get("recommended_solutions", recommendations)

    # Render HTML report
    html_content = render_report_html(
        business=business,
        audit=audit,
        executive_summary=executive_summary,
        website_audit_summary=website_audit_summary,
        social_audit_summary=social_audit_summary,
        pain_points=pain_points,
        recommended_solutions=recommended_solutions,
        opportunity_summary=opportunity_summary,
    )

    # Save HTML file
    html_path = get_report_path(business.id, "html")
    save_file(html_path, html_content)

    # Generate PDF
    pdf_path = get_report_path(business.id, "pdf")
    pdf_success = generate_pdf(html_content, pdf_path)
    if not pdf_success:
        pdf_path = None

    # Save report to database
    report = Report(
        business_id=business.id,
        audit_id=audit.id,
        title=f"Digital Audit Report - {business.name}",
        executive_summary=executive_summary,
        website_audit_summary=website_audit_summary,
        social_audit_summary=social_audit_summary,
        pain_points=json.dumps(pain_points, ensure_ascii=False),
        recommended_solutions=json.dumps(recommended_solutions, ensure_ascii=False),
        opportunity_summary=opportunity_summary,
        overall_score=audit.audit_score,
        html_path=html_path,
        pdf_path=pdf_path,
    )

    session.add(report)
    session.commit()
    session.refresh(report)

    logger.info(f"Report generated for {business.name}. ID: {report.id}")
    return report


def _default_executive_summary(business: Business, audit: Audit, pain_points: list) -> str:
    """Generate a default executive summary without AI."""
    score_text = f"{audit.audit_score:.0f}/100" if audit.audit_score else "N/A"
    website_text = "has a website" if audit.has_website else "does not have a website"

    return (
        f"{business.name} is a {business.category.lower()} based in {business.location}. "
        f"The business {website_text} and received an overall digital audit score of {score_text}. "
        f"Our analysis identified {len(pain_points)} key areas for improvement. "
        f"Addressing these gaps can significantly improve online visibility, "
        f"customer engagement, and revenue generation."
    )


def _default_website_summary(audit: Audit) -> str:
    """Generate default website audit summary."""
    if not audit.has_website:
        return (
            "The business does not have a website. This is a critical gap in today's "
            "digital-first world. A professional website is essential for credibility, "
            "customer acquisition, and online presence."
        )

    parts = []
    if audit.ssl_enabled:
        parts.append("SSL is enabled")
    else:
        parts.append("SSL is NOT enabled (security risk)")

    if audit.mobile_responsive:
        parts.append("mobile responsive")
    else:
        parts.append("not mobile responsive")

    seo_text = f"SEO score: {audit.seo_score:.0f}/100" if audit.seo_score else "SEO: not scored"
    parts.append(seo_text)

    return f"The website is {'secure' if audit.ssl_enabled else 'not secure'}, " + \
           ", ".join(parts) + "."


def _default_social_summary(audit: Audit) -> str:
    """Generate default social audit summary."""
    score = audit.social_score or 0
    if score >= 70:
        return "Strong social media presence with good engagement potential."
    elif score >= 40:
        return "Moderate social media presence. Several platforms are missing or underutilized."
    else:
        return "Weak social media presence. Significant opportunity for growth through social channels."


def _default_opportunity_summary(opportunities: list) -> str:
    """Generate default opportunity summary."""
    if not opportunities:
        return "Limited opportunities identified based on current analysis."

    return (
        f"We identified {len(opportunities)} key opportunities for growth: "
        + "; ".join(opportunities[:5])
        + "."
    )
