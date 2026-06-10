"""
outreach_schema.py - Pydantic schemas for outreach endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OutreachResponse(BaseModel):
    """Schema for outreach response."""
    id: int
    business_id: int
    business_name: Optional[str] = None
    audit_id: Optional[int] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    whatsapp_message: Optional[str] = None
    call_notes: Optional[str] = None
    meeting_pitch: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
