"""
email_logger.py - Logs email sending attempts.
"""

from sqlmodel import Session
from app.models.email_log import EmailLog
from app.utils.helpers import timestamp_now
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)


def log_email_attempt(
    session: Session,
    business_id: int,
    outreach_id: int,
    recipient_email: str,
    subject: str,
    status: str,
    error_message: str = None,
) -> EmailLog:
    """
    Log an email sending attempt to the database.
    """
    logger.info(f"Logging email attempt to {recipient_email} - Status: {status}")

    log_entry = EmailLog(
        business_id=business_id,
        outreach_id=outreach_id,
        recipient_email=recipient_email,
        subject=subject,
        status=status,
        sent_at=datetime.utcnow() if status == "sent" else None,
        error_message=error_message,
    )

    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)

    return log_entry
