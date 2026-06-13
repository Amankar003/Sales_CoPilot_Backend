"""
smtp_sender.py - Handles sending emails via SMTP with multi-account pool and failover.

Flow:
1. Try SMTPPoolManager.get_available_account()
2. If no pool accounts → fallback to .env SMTP config (backward compat)
3. If pool account found → decrypt password → send via aiosmtplib
4. On success → mark_sent() → return SendResult
5. On failure → mark_failed() → retry with alternate account (max 3 attempts)
6. Return SendResult with smtp_account_id, message_id, provider, success flag
"""

from dataclasses import dataclass, field
from typing import Optional, List

import aiosmtplib
from email.message import EmailMessage

from sqlmodel import Session

from app.core.settings import settings
from app.core.constants import SMTP_MAX_RETRIES
from app.services.email.smtp_pool_manager import smtp_pool
from app.utils.crypto import decrypt_password, mask_email
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SendResult:
    """Result of an email send attempt."""
    success: bool
    smtp_account_id: Optional[int] = None
    provider: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


async def _send_via_smtp(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool,
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool = False,
    use_starttls: bool = True,
) -> str:
    """
    Low-level SMTP send. Returns the SMTP Message-ID on success.
    Raises an exception on failure.
    """
    message = EmailMessage()
    message["From"] = username
    message["To"] = to_email
    message["Subject"] = subject

    if is_html:
        message.set_content(body, subtype="html")
    else:
        message.set_content(body)

    masked_sender = mask_email(username)
    logger.info(f"Sending email to {to_email} via {masked_sender} ({host}:{port})")

    await aiosmtplib.send(
        message,
        hostname=host,
        port=port,
        username=username,
        password=password,
        use_tls=use_tls,
        start_tls=use_starttls,
    )

    # Extract message ID from sent message
    message_id = message.get("Message-ID", "")
    logger.info(f"Email sent successfully to {to_email} via {masked_sender}")
    return message_id


async def _send_via_env_fallback(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool,
) -> SendResult:
    """
    Fallback: send using the legacy .env SMTP configuration.
    Used when no SMTP accounts exist in the database pool.
    """
    if not settings.has_smtp_config:
        logger.warning(
            "SMTP is not configured (no pool accounts AND no .env SMTP config). "
            f"Would have sent email to {to_email} with subject: '{subject}'"
        )
        return SendResult(
            success=False,
            error="SMTP not configured. Add SMTP accounts in Settings or configure .env.",
        )

    try:
        use_tls = settings.SMTP_PORT == 465
        use_starttls = settings.SMTP_PORT == 587

        message_id = await _send_via_smtp(
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html,
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            use_tls=use_tls,
            use_starttls=use_starttls,
        )

        return SendResult(
            success=True,
            provider="env_fallback",
            message_id=message_id,
        )

    except Exception as e:
        logger.error(f"Failed to send email via .env SMTP to {to_email}: {e}")
        return SendResult(
            success=False,
            error=f"ENV SMTP failed: {str(e)}",
        )


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    session: Optional[Session] = None,
) -> SendResult:
    """
    Send an email using the SMTP pool with automatic failover.

    Priority:
    1. SMTP Pool (database accounts) with retry/failover
    2. Fallback to .env SMTP config (backward compatibility)

    Args:
        to_email: Recipient email address
        subject: Email subject line
        body: Email body content
        is_html: Whether the body is HTML
        session: Database session (required for pool-based sending)

    Returns:
        SendResult with success status, account info, and error details.
    """
    # If no session provided, use .env fallback directly
    if session is None:
        return await _send_via_env_fallback(to_email, subject, body, is_html)

    # Try the SMTP pool first
    excluded_ids: List[int] = []
    retry_count = 0

    for attempt in range(1, SMTP_MAX_RETRIES + 1):
        account = smtp_pool.get_available_account(
            session=session,
            exclude_ids=excluded_ids if excluded_ids else None,
        )

        if account is None:
            # No pool accounts available — fall back to .env
            if attempt == 1:
                logger.info("No SMTP pool accounts available. Falling back to .env config.")
                result = await _send_via_env_fallback(to_email, subject, body, is_html)
                result.retry_count = retry_count
                return result
            else:
                # We already tried some pool accounts and they all failed
                break

        try:
            # Decrypt the stored password
            plain_password = decrypt_password(account.password_encrypted)

            message_id = await _send_via_smtp(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                host=account.host,
                port=account.port,
                username=account.email,
                password=plain_password,
                use_tls=account.use_tls,
                use_starttls=account.use_starttls,
            )

            # Success — record it
            smtp_pool.mark_sent(session, account.id)

            return SendResult(
                success=True,
                smtp_account_id=account.id,
                provider=account.provider,
                message_id=message_id,
                retry_count=retry_count,
            )

        except Exception as e:
            error_msg = str(e)
            masked = mask_email(account.email)
            logger.warning(
                f"SMTP send failed via '{account.name}' ({masked}), "
                f"attempt {attempt}/{SMTP_MAX_RETRIES}: {error_msg}"
            )

            # Mark this account as failed
            smtp_pool.mark_failed(session, account.id, error_msg)

            # Exclude this account from the next attempt
            excluded_ids.append(account.id)
            retry_count += 1

    # All pool retries exhausted — try .env fallback as last resort
    logger.warning(
        f"All {SMTP_MAX_RETRIES} SMTP pool retries exhausted. "
        "Attempting .env fallback as last resort."
    )
    result = await _send_via_env_fallback(to_email, subject, body, is_html)
    result.retry_count = retry_count

    if not result.success:
        result.error = (
            f"All SMTP pool accounts failed after {retry_count} retries. "
            f"ENV fallback also failed: {result.error}"
        )

    return result
