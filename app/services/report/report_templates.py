"""
report_templates.py - HTML templates for audit reports.
"""

from typing import List, Optional
from app.models.business import Business
from app.models.audit import Audit
from app.utils.helpers import format_score


def render_report_html(
    business: Business,
    audit: Audit,
    executive_summary: str,
    website_audit_summary: str,
    social_audit_summary: str,
    pain_points: List[str],
    recommended_solutions: List[str],
    opportunity_summary: str,
) -> str:
    """Render a professional HTML audit report."""

    # Score color helper
    def score_color(score: Optional[float]) -> str:
        if score is None:
            return "#6b7280"
        if score >= 70:
            return "#10b981"
        if score >= 40:
            return "#f59e0b"
        return "#ef4444"

    pain_points_html = "".join(
        f'<li class="pain-point">{point}</li>' for point in pain_points
    )
    solutions_html = "".join(
        f'<li class="solution">{sol}</li>' for sol in recommended_solutions
    )

    overall_score = audit.audit_score or 0
    overall_color = score_color(audit.audit_score)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Audit Report - {business.name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f9fafb;
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        .header {{
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 16px; opacity: 0.9; }}
        .header .date {{ font-size: 14px; opacity: 0.7; margin-top: 12px; }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            font-size: 20px;
            color: #4f46e5;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .section p {{ margin-bottom: 12px; color: #4b5563; }}
        .score-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .score-card {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }}
        .score-card .score {{
            font-size: 32px;
            font-weight: 700;
        }}
        .score-card .label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }}
        .overall-score {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #f0f0ff, #faf5ff);
            border-radius: 12px;
            margin: 20px 0;
        }}
        .overall-score .big-score {{
            font-size: 64px;
            font-weight: 800;
            color: {overall_color};
        }}
        .overall-score .score-label {{
            font-size: 16px;
            color: #6b7280;
            margin-top: 8px;
        }}
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 8px; color: #4b5563; }}
        .pain-point {{ color: #dc2626; }}
        .solution {{ color: #059669; }}
        .check {{ color: #10b981; }}
        .cross {{ color: #ef4444; }}
        .business-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .info-item {{
            padding: 8px 0;
            border-bottom: 1px solid #f3f4f6;
        }}
        .info-label {{ font-size: 12px; color: #9ca3af; text-transform: uppercase; }}
        .info-value {{ font-size: 14px; color: #1f2937; font-weight: 500; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #9ca3af;
            font-size: 12px;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ padding: 0; }}
            .section {{ box-shadow: none; border: 1px solid #e5e7eb; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Digital Audit Report</h1>
            <div class="subtitle">{business.name} — {business.category}</div>
            <div class="date">Location: {business.location} | Generated by LeadPilot AI</div>
        </div>

        <div class="section">
            <h2>Overall Score</h2>
            <div class="overall-score">
                <div class="big-score">{overall_score:.0f}</div>
                <div class="score-label">out of 100</div>
            </div>
            <div class="score-grid">
                <div class="score-card">
                    <div class="score" style="color: {score_color(audit.seo_score)}">{format_score(audit.seo_score)}</div>
                    <div class="label">SEO Score</div>
                </div>
                <div class="score-card">
                    <div class="score" style="color: {score_color(audit.ux_score)}">{format_score(audit.ux_score)}</div>
                    <div class="label">UX Score</div>
                </div>
                <div class="score-card">
                    <div class="score" style="color: {score_color(audit.social_score)}">{format_score(audit.social_score)}</div>
                    <div class="label">Social Score</div>
                </div>
                <div class="score-card">
                    <div class="score" style="color: {score_color(audit.loading_speed_score)}">{format_score(audit.loading_speed_score)}</div>
                    <div class="label">Speed Score</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Executive Summary</h2>
            <p>{executive_summary}</p>
        </div>

        <div class="section">
            <h2>Business Overview</h2>
            <div class="business-info">
                <div class="info-item">
                    <div class="info-label">Business Name</div>
                    <div class="info-value">{business.name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Category</div>
                    <div class="info-value">{business.category}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Location</div>
                    <div class="info-value">{business.location}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Website</div>
                    <div class="info-value">{business.website or 'Not available'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Phone</div>
                    <div class="info-value">{business.phone or 'Not available'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email</div>
                    <div class="info-value">{business.email or 'Not available'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Google Rating</div>
                    <div class="info-value">{f'{business.google_rating}/5' if business.google_rating else 'Not available'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Reviews</div>
                    <div class="info-value">{business.reviews_count or 'Not available'}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Website Audit</h2>
            <p>{website_audit_summary}</p>
            <div style="margin-top: 16px;">
                <p><span class="{'check' if audit.has_website else 'cross'}">{'✓' if audit.has_website else '✗'}</span> Has Website</p>
                <p><span class="{'check' if audit.ssl_enabled else 'cross'}">{'✓' if audit.ssl_enabled else '✗'}</span> SSL/HTTPS Enabled</p>
                <p><span class="{'check' if audit.mobile_responsive else 'cross'}">{'✓' if audit.mobile_responsive else '✗'}</span> Mobile Responsive</p>
                <p><span class="{'check' if audit.has_contact_form else 'cross'}">{'✓' if audit.has_contact_form else '✗'}</span> Contact Form</p>
                <p><span class="{'check' if audit.has_whatsapp else 'cross'}">{'✓' if audit.has_whatsapp else '✗'}</span> WhatsApp Integration</p>
                <p><span class="{'check' if audit.has_booking_system else 'cross'}">{'✓' if audit.has_booking_system else '✗'}</span> Booking System</p>
            </div>
        </div>

        <div class="section">
            <h2>Social Media Audit</h2>
            <p>{social_audit_summary}</p>
        </div>

        <div class="section">
            <h2>Pain Points Identified</h2>
            <ul>{pain_points_html or '<li>No major pain points identified</li>'}</ul>
        </div>

        <div class="section">
            <h2>Recommended Solutions</h2>
            <ul>{solutions_html or '<li>No specific recommendations at this time</li>'}</ul>
        </div>

        <div class="section">
            <h2>Opportunity Summary</h2>
            <p>{opportunity_summary}</p>
        </div>

        <div class="footer">
            <p>Generated by LeadPilot AI | Confidential Report</p>
        </div>
    </div>
</body>
</html>"""
