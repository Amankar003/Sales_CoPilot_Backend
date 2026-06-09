"""
audit_routes.py - API routes for business audits.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select

from app.database.session import get_session
from app.models.business import Business
from app.models.audit import Audit
from app.schemas.audit_schema import AuditResponse
from app.services.audit.audit_orchestrator import run_full_audit
from app.utils.parser import safe_json_loads

router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.post("/{business_id}", response_model=AuditResponse)
async def generate_audit(
    business_id: int,
    session: Session = Depends(get_session),
):
    """
    Run a full digital audit for a business.
    This may take a few seconds as it fetches the website and runs AI analysis.
    """
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    audit = await run_full_audit(business, session)
    
    # Parse JSON strings to lists for the response
    response_data = audit.model_dump()
    response_data["pain_points"] = safe_json_loads(audit.pain_points_json)
    response_data["opportunities"] = safe_json_loads(audit.opportunities_json)
    response_data["recommendations"] = safe_json_loads(audit.recommendations_json)
    
    return response_data


@router.get("/{business_id}", response_model=AuditResponse)
def get_audit(
    business_id: int,
    session: Session = Depends(get_session),
):
    """Get the latest audit for a business."""
    audit = session.exec(
        select(Audit)
        .where(Audit.business_id == business_id)
        .order_by(Audit.created_at.desc())
    ).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found for this business. Run an audit first.")
        
    # Parse JSON strings to lists for the response
    response_data = audit.model_dump()
    response_data["pain_points"] = safe_json_loads(audit.pain_points_json)
    response_data["opportunities"] = safe_json_loads(audit.opportunities_json)
    response_data["recommendations"] = safe_json_loads(audit.recommendations_json)
    
    return response_data
