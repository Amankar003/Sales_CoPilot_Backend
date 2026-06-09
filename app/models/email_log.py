"""
email_log.py - EmailLog model for tracking sent emails.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class EmailLog(SQLModel, table=True):
    """Tracks all email sending attempts."""

    __tablename__ = "email_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, foreign_key="businesses.id")
    outreach_id: int = Field(foreign_key="outreach.id")

    recipient_email: str
    subject: str
    status: str = Field(default="pending")  # pending, sent, failed
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
