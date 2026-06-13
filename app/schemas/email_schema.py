"""
email_schema.py - Pydantic schemas for email endpoints.
Extended with SMTP pool attribution fields.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmailSendRequest(BaseModel):
    """Schema for sending an email."""
    recipient_email: Optional[str] = None  # If not provided, uses business email


class EmailLogResponse(BaseModel):
    """Schema for email log response with SMTP pool attribution."""
    id: int
    business_id: int
    outreach_id: int
    recipient_email: str
    subject: str
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    business_name: Optional[str] = None

    # SMTP Pool tracking
    smtp_account_id: Optional[int] = None
    provider: Optional[str] = None
    message_id: Optional[str] = None
    delivery_status: Optional[str] = None
    bounce_reason: Optional[str] = None
    retry_count: int = 0

    class Config:
        from_attributes = True
