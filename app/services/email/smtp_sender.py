"""
smtp_sender.py - Handles sending emails via SMTP.
"""

import aiosmtplib
from email.message import EmailMessage
from app.core.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> bool:
    """
    Send an email using configured SMTP settings.
    Returns True if successful, False otherwise.
    """
    if not settings.has_smtp_config:
        logger.warning(
            "SMTP is not fully configured. "
            f"Would have sent email to {to_email} with subject: '{subject}'"
        )
        return False

    message = EmailMessage()
    message["From"] = settings.SMTP_EMAIL
    message["To"] = to_email
    message["Subject"] = subject

    if is_html:
        message.set_content(body, subtype="html")
    else:
        message.set_content(body)

    try:
        logger.info(f"Sending email to {to_email} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            use_tls=True if settings.SMTP_PORT == 465 else False,
            start_tls=True if settings.SMTP_PORT == 587 else False,
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
