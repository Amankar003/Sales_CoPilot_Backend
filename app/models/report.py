"""
report.py - Report model for storing generated audit reports.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Report(SQLModel, table=True):
    """Stores generated audit reports."""

    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, foreign_key="businesses.id")
    audit_id: int = Field(foreign_key="audits.id")

    title: str
    executive_summary: Optional[str] = None
    website_audit_summary: Optional[str] = None
    social_audit_summary: Optional[str] = None
    pain_points: Optional[str] = None           # JSON text
    recommended_solutions: Optional[str] = None  # JSON text
    opportunity_summary: Optional[str] = None
    overall_score: Optional[float] = None

    html_path: Optional[str] = None
    pdf_path: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
