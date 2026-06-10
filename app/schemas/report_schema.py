"""
report_schema.py - Pydantic schemas for report endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReportResponse(BaseModel):
    """Schema for report response."""
    id: int
    business_id: int
    business_name: Optional[str] = None
    audit_id: int
    title: str
    executive_summary: Optional[str] = None
    website_audit_summary: Optional[str] = None
    social_audit_summary: Optional[str] = None
    pain_points: Optional[List[str]] = None
    recommended_solutions: Optional[List[str]] = None
    opportunity_summary: Optional[str] = None
    overall_score: Optional[float] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportSummary(BaseModel):
    """Compact report summary for listing."""
    id: int
    business_id: int
    business_name: Optional[str] = None
    title: str
    overall_score: Optional[float] = None
    has_pdf: bool = False
    created_at: datetime
