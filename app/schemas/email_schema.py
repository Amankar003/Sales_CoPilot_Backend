"""
email_schema.py - Pydantic schemas for email endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmailSendRequest(BaseModel):
    """Schema for sending an email."""
    recipient_email: Optional[str] = None  # If not provided, uses business email


class EmailLogResponse(BaseModel):
    """Schema for email log response."""
    id: int
    business_id: int
    outreach_id: int
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    business_name: Optional[str] = None

    class Config:
        from_attributes = True
