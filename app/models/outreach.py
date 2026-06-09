"""
outreach.py - Outreach model for storing generated outreach content.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Outreach(SQLModel, table=True):
    """Stores generated outreach content for a business."""

    __tablename__ = "outreach"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, foreign_key="businesses.id")
    audit_id: Optional[int] = Field(default=None, foreign_key="audits.id")

    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    whatsapp_message: Optional[str] = None
    call_notes: Optional[str] = None
    meeting_pitch: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
