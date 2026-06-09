"""
dashboard_routes.py - API routes for dashboard statistics.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from typing import Dict, Any, List

from app.database.session import get_session
from app.models.business import Business
from app.models.audit import Audit
from app.models.report import Report
from app.models.email_log import EmailLog
from app.schemas.business_schema import BusinessResponse
from app.schemas.audit_schema import AuditSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """Get high-level statistics for the dashboard."""
    
    total_leads = session.exec(select(func.count(Business.id))).one()
    total_audits = session.exec(select(func.count(Audit.id))).one()
    total_reports = session.exec(select(func.count(Report.id))).one()
    emails_sent = session.exec(
        select(func.count(EmailLog.id)).where(EmailLog.status == "sent")
    ).one()
    
    # Calculate average audit score
    avg_score_result = session.exec(
        select(func.avg(Audit.audit_score)).where(Audit.audit_score.is_not(None))
    ).one()
    avg_audit_score = round(avg_score_result, 1) if avg_score_result else 0
    
    return {
        "total_leads": total_leads,
        "audits_completed": total_audits,
        "reports_generated": total_reports,
        "emails_sent": emails_sent,
        "average_audit_score": avg_audit_score,
    }


@router.get("/recent-leads", response_model=List[BusinessResponse])
def get_recent_leads(
    limit: int = 5,
    session: Session = Depends(get_session)
):
    """Get the most recently added leads."""
    leads = session.exec(
        select(Business)
        .order_by(Business.created_at.desc())
        .limit(limit)
    ).all()
    return leads


@router.get("/recent-audits", response_model=List[AuditSummary])
def get_recent_audits(
    limit: int = 5,
    session: Session = Depends(get_session)
):
    """Get the most recent audits with business names."""
    query = (
        select(Audit, Business.name.label("business_name"))
        .join(Business, Audit.business_id == Business.id)
        .order_by(Audit.created_at.desc())
        .limit(limit)
    )
    
    results = session.exec(query).all()
    
    summaries = []
    for audit, business_name in results:
        summaries.append({
            "id": audit.id,
            "business_id": audit.business_id,
            "business_name": business_name,
            "audit_score": audit.audit_score,
            "has_website": audit.has_website,
            "seo_score": audit.seo_score,
            "social_score": audit.social_score,
            "created_at": audit.created_at,
        })
        
    return summaries
