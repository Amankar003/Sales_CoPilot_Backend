"""
report_routes.py - API routes for report generation.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlmodel import Session, select
import os

from app.database.session import get_session
from app.models.business import Business
from app.models.audit import Audit
from app.models.report import Report
from app.schemas.report_schema import ReportResponse
from app.services.report.report_generator import generate_report
from app.utils.parser import safe_json_loads

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.post("/generate/{business_id}", response_model=ReportResponse)
async def create_report(
    business_id: int,
    session: Session = Depends(get_session),
):
    """
    Generate a professional audit report for a business.
    Requires an audit to be run first.
    """
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    audit = session.exec(
        select(Audit)
        .where(Audit.business_id == business_id)
        .order_by(Audit.created_at.desc())
    ).first()
    
    if not audit:
        raise HTTPException(
            status_code=400, 
            detail="Cannot generate report. Please run an audit for this business first."
        )
        
    report = await generate_report(business, audit, session)
    
    # Parse JSON strings to lists for the response
    response_data = report.model_dump()
    response_data["pain_points"] = safe_json_loads(report.pain_points)
    response_data["recommended_solutions"] = safe_json_loads(report.recommended_solutions)
    
    return response_data


@router.get("/{business_id}", response_model=ReportResponse)
def get_report(
    business_id: int,
    session: Session = Depends(get_session),
):
    """Get the latest report for a business."""
    report = session.exec(
        select(Report)
        .where(Report.business_id == business_id)
        .order_by(Report.created_at.desc())
    ).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    # Parse JSON strings to lists for the response
    response_data = report.model_dump()
    response_data["pain_points"] = safe_json_loads(report.pain_points)
    response_data["recommended_solutions"] = safe_json_loads(report.recommended_solutions)
    
    return response_data


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    session: Session = Depends(get_session),
):
    """Download the PDF version of the report."""
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if not report.pdf_path or not os.path.exists(report.pdf_path):
        # Fallback to HTML if PDF isn't available
        if report.html_path and os.path.exists(report.html_path):
            return FileResponse(
                path=report.html_path,
                filename=f"Audit_Report_{report.business_id}.html",
                media_type="text/html"
            )
        raise HTTPException(status_code=404, detail="Report file not found on disk")
        
    return FileResponse(
        path=report.pdf_path,
        filename=f"Audit_Report_{report.business_id}.pdf",
        media_type="application/pdf"
    )
