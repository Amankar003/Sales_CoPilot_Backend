"""
smtp_routes.py - API routes for SMTP pool account management.
"""

import time
from datetime import datetime, date
from typing import List

import aiosmtplib
from email.message import EmailMessage
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database.session import get_session
from app.models.smtp_account import SMTPAccount
from app.schemas.smtp_schema import (
    SMTPAccountCreate,
    SMTPAccountUpdate,
    SMTPAccountResponse,
    SMTPAccountStats,
    SMTPTestRequest,
    SMTPTestResponse,
)
from app.services.email.smtp_pool_manager import smtp_pool
from app.utils.crypto import encrypt_password, decrypt_password, mask_email
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/smtp", tags=["SMTP Pool"])


def _account_to_response(account: SMTPAccount) -> SMTPAccountResponse:
    """Convert an SMTPAccount model to a response schema with computed fields."""
    total_attempts = account.total_sent + account.total_failed
    success_rate = (account.total_sent / total_attempts * 100) if total_attempts > 0 else 0.0

    effective_daily_limit = smtp_pool.get_warmup_limit(account)

    return SMTPAccountResponse(
        id=account.id,
        name=account.name,
        email=account.email,
        host=account.host,
        port=account.port,
        use_tls=account.use_tls,
        use_starttls=account.use_starttls,
        daily_limit=account.daily_limit,
        hourly_limit=account.hourly_limit,
        sent_today=account.sent_today,
        sent_this_hour=account.sent_this_hour,
        last_sent_at=account.last_sent_at,
        status=account.status,
        priority=account.priority,
        failure_count=account.failure_count,
        total_sent=account.total_sent,
        total_failed=account.total_failed,
        warmup_enabled=account.warmup_enabled,
        warmup_start_date=account.warmup_start_date,
        warmup_daily_increment=account.warmup_daily_increment,
        provider=account.provider,
        remaining_daily=max(0, effective_daily_limit - account.sent_today),
        remaining_hourly=max(0, account.hourly_limit - account.sent_this_hour),
        success_rate=round(success_rate, 1),
        password="••••••••",
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("/accounts", response_model=List[SMTPAccountResponse])
def list_smtp_accounts(session: Session = Depends(get_session)):
    """List all SMTP accounts. Passwords are never returned."""
    accounts = session.exec(
        select(SMTPAccount).order_by(SMTPAccount.priority.desc(), SMTPAccount.created_at)
    ).all()
    return [_account_to_response(a) for a in accounts]


@router.post("/accounts", response_model=SMTPAccountResponse)
def create_smtp_account(
    request: SMTPAccountCreate,
    session: Session = Depends(get_session),
):
    """Add a new SMTP account to the pool."""
    # Check for duplicate email
    existing = session.exec(
        select(SMTPAccount).where(SMTPAccount.email == request.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"SMTP account with email '{request.email}' already exists.",
        )

    # Encrypt password before storing
    encrypted_password = encrypt_password(request.password)

    account = SMTPAccount(
        name=request.name,
        email=request.email,
        password_encrypted=encrypted_password,
        host=request.host,
        port=request.port,
        use_tls=request.use_tls,
        use_starttls=request.use_starttls,
        daily_limit=request.daily_limit,
        hourly_limit=request.hourly_limit,
        priority=request.priority,
        warmup_enabled=request.warmup_enabled,
        warmup_daily_increment=request.warmup_daily_increment,
        warmup_start_date=date.today() if request.warmup_enabled else None,
        provider=request.provider,
        status="active",
        last_reset_date=date.today(),
        last_hour_reset=datetime.utcnow(),
    )

    session.add(account)
    session.commit()
    session.refresh(account)

    masked = mask_email(account.email)
    logger.info(f"Created SMTP account '{account.name}' ({masked})")

    return _account_to_response(account)


@router.put("/accounts/{account_id}", response_model=SMTPAccountResponse)
def update_smtp_account(
    account_id: int,
    request: SMTPAccountUpdate,
    session: Session = Depends(get_session),
):
    """Update an existing SMTP account."""
    account = session.get(SMTPAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="SMTP account not found.")

    # Apply updates for provided fields
    update_data = request.model_dump(exclude_unset=True)

    # Handle password separately (encrypt if provided)
    if "password" in update_data:
        password_value = update_data.pop("password")
        if password_value:  # Only update if a new password is provided
            account.password_encrypted = encrypt_password(password_value)

    for field_name, value in update_data.items():
        setattr(account, field_name, value)

    # If warmup was just enabled and no start date, set it now
    if request.warmup_enabled and not account.warmup_start_date:
        account.warmup_start_date = date.today()

    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()
    session.refresh(account)

    logger.info(f"Updated SMTP account '{account.name}' (ID: {account.id})")

    return _account_to_response(account)


@router.delete("/accounts/{account_id}")
def delete_smtp_account(
    account_id: int,
    session: Session = Depends(get_session),
):
    """Delete an SMTP account from the pool."""
    account = session.get(SMTPAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="SMTP account not found.")

    name = account.name
    session.delete(account)
    session.commit()

    logger.info(f"Deleted SMTP account '{name}' (ID: {account_id})")

    return {"message": f"SMTP account '{name}' deleted successfully."}


@router.get("/stats", response_model=SMTPAccountStats)
def get_smtp_stats(session: Session = Depends(get_session)):
    """Get aggregate statistics for the SMTP pool."""
    stats = smtp_pool.get_pool_stats(session)
    return SMTPAccountStats(**stats)


@router.post("/test", response_model=SMTPTestResponse)
async def test_smtp_connection(
    request: SMTPTestRequest,
    session: Session = Depends(get_session),
):
    """
    Test an SMTP connection by attempting to connect and authenticate.
    Provide either an existing account ID, or inline credentials.
    """
    host = request.host
    port = request.port or 587
    email = request.email
    password = request.password
    use_tls = request.use_tls
    use_starttls = request.use_starttls

    # If testing an existing account, load its credentials
    if request.id is not None:
        account = session.get(SMTPAccount, request.id)
        if not account:
            raise HTTPException(status_code=404, detail="SMTP account not found.")
        host = account.host
        port = account.port
        email = account.email
        password = decrypt_password(account.password_encrypted)
        use_tls = account.use_tls
        use_starttls = account.use_starttls

    if not all([host, email, password]):
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: host, email, password.",
        )

    start_time = time.time()
    try:
        # Create a test SMTP connection
        smtp_client = aiosmtplib.SMTP(
            hostname=host,
            port=port,
            use_tls=use_tls,
            start_tls=use_starttls,
        )

        await smtp_client.connect()
        await smtp_client.login(email, password)
        await smtp_client.quit()

        latency_ms = round((time.time() - start_time) * 1000, 1)
        masked = mask_email(email)
        logger.info(f"SMTP test successful for {masked} ({host}:{port}) in {latency_ms}ms")

        return SMTPTestResponse(
            success=True,
            message=f"Connection successful! Authenticated as {masked}",
            latency_ms=latency_ms,
        )

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 1)
        error_msg = str(e)
        masked = mask_email(email)
        logger.warning(f"SMTP test failed for {masked} ({host}:{port}): {error_msg}")

        return SMTPTestResponse(
            success=False,
            message=f"Connection failed: {error_msg}",
            latency_ms=latency_ms,
        )


@router.post("/pause/{account_id}", response_model=SMTPAccountResponse)
def pause_smtp_account(
    account_id: int,
    session: Session = Depends(get_session),
):
    """Pause an SMTP account (temporarily remove from rotation)."""
    account = session.get(SMTPAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="SMTP account not found.")

    if account.status == "disabled":
        raise HTTPException(status_code=400, detail="Cannot pause a disabled account.")

    account.status = "paused"
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()
    session.refresh(account)

    logger.info(f"Paused SMTP account '{account.name}' (ID: {account.id})")

    return _account_to_response(account)


@router.post("/resume/{account_id}", response_model=SMTPAccountResponse)
def resume_smtp_account(
    account_id: int,
    session: Session = Depends(get_session),
):
    """Resume a paused or blocked SMTP account. Resets failure counter."""
    account = session.get(SMTPAccount, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="SMTP account not found.")

    if account.status == "disabled":
        raise HTTPException(status_code=400, detail="Cannot resume a disabled account. Edit it first.")

    account.status = "active"
    account.failure_count = 0
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()
    session.refresh(account)

    logger.info(f"Resumed SMTP account '{account.name}' (ID: {account.id})")

    return _account_to_response(account)
