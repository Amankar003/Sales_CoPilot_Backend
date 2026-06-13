"""
email_log.py - EmailLog model for tracking sent emails.
Extended with SMTP pool tracking fields for deliverability monitoring.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class EmailLog(SQLModel, table=True):
    """Tracks all email sending attempts with SMTP pool attribution."""

    __tablename__ = "email_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, foreign_key="businesses.id")
    outreach_id: int = Field(foreign_key="outreach.id")

    recipient_email: str
    subject: str
    status: str = Field(default="pending")  # pending, sent, failed (kept for backward compat)
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # SMTP Pool tracking fields
    smtp_account_id: Optional[int] = Field(default=None, foreign_key="smtp_accounts.id", index=True)
    provider: Optional[str] = Field(default=None)  # gmail, outlook, brevo, ses, mailgun, custom
    message_id: Optional[str] = Field(default=None)  # SMTP Message-ID header for tracking

    # Extended delivery lifecycle
    delivery_status: str = Field(default="pending")
    # Values: pending, sent, delivered, opened, clicked, bounced, failed

    bounce_reason: Optional[str] = Field(default=None)  # Bounce classification
    retry_count: int = Field(default=0)  # Number of retry attempts made
