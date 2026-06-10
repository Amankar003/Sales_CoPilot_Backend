"""
campaign.py - Campaign model for grouping discovered leads.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Campaign(SQLModel, table=True):
    """Represents a lead generation campaign in the system."""

    __tablename__ = "campaigns"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sector: str = Field(index=True)
    location: str = Field(index=True)
    status: str = Field(default="draft")  # draft, discovering, enriching, auditing, generating_reports, generating_outreach, completed, completed_with_errors, failed
    leads_count: int = Field(default=0)
    enriched_count: int = Field(default=0)
    audited_count: int = Field(default=0)
    reports_count: int = Field(default=0)
    outreach_count: int = Field(default=0)
    emails_sent_count: int = Field(default=0)
    pipeline_error: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
