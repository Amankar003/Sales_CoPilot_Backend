"""
email_logger.py - Logs email sending attempts with SMTP pool attribution.
"""

from sqlmodel import Session
from app.models.email_log import EmailLog
from datetime import datetime
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


def log_email_attempt(
    session: Session,
    business_id: int,
    outreach_id: int,
    recipient_email: str,
    subject: str,
    status: str,
    error_message: Optional[str] = None,
    smtp_account_id: Optional[int] = None,
    provider: Optional[str] = None,
    message_id: Optional[str] = None,
    delivery_status: Optional[str] = None,
    bounce_reason: Optional[str] = None,
    retry_count: int = 0,
) -> EmailLog:
    """
    Log an email sending attempt to the database.

    Args:
        session: Database session
        business_id: Associated business ID
        outreach_id: Associated outreach content ID
        recipient_email: Recipient email address
        subject: Email subject line
        status: Legacy status field (pending, sent, failed)
        error_message: Error details if failed
        smtp_account_id: ID of the SMTP account used (from pool)
        provider: SMTP provider name (gmail, ses, etc.)
        message_id: SMTP Message-ID header for tracking
        delivery_status: Extended delivery lifecycle status
        bounce_reason: Bounce classification if applicable
        retry_count: Number of retry attempts made

    Returns:
        The created EmailLog entry.
    """
    logger.info(f"Logging email attempt to {recipient_email} - Status: {status}")

    # Default delivery_status to match legacy status if not explicitly provided
    if delivery_status is None:
        delivery_status = status

    log_entry = EmailLog(
        business_id=business_id,
        outreach_id=outreach_id,
        recipient_email=recipient_email,
        subject=subject,
        status=status,
        sent_at=datetime.utcnow() if status == "sent" else None,
        error_message=error_message,
        smtp_account_id=smtp_account_id,
        provider=provider,
        message_id=message_id,
        delivery_status=delivery_status,
        bounce_reason=bounce_reason,
        retry_count=retry_count,
    )

    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)

    return log_entry
