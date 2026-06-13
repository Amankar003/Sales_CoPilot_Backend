"""
email_routes.py - API routes for sending emails and viewing logs.
Updated to use SMTP pool with automatic failover.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.database.session import get_session
from app.models.business import Business
from app.models.outreach import Outreach
from app.models.email_log import EmailLog
from app.schemas.email_schema import EmailSendRequest, EmailLogResponse
from app.services.email.smtp_sender import send_email
from app.services.email.email_logger import log_email_attempt

router = APIRouter(prefix="/api/email", tags=["Email"])


@router.post("/send/{outreach_id}")
async def send_outreach_email(
    outreach_id: int,
    request: EmailSendRequest,
    session: Session = Depends(get_session),
):
    """
    Send the generated email to a business or custom recipient.
    Uses the SMTP pool with automatic failover, falling back to .env config.
    """
    outreach = session.get(Outreach, outreach_id)
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach content not found")

    if not outreach.email_subject or not outreach.email_body:
        raise HTTPException(status_code=400, detail="Outreach is missing email subject or body")

    business = session.get(Business, outreach.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Associated business not found")

    # Determine recipient
    recipient = request.recipient_email or business.email
    if not recipient:
        raise HTTPException(status_code=400, detail="No email address available for this business")

    # Send email via SMTP pool (with failover)
    result = await send_email(
        to_email=recipient,
        subject=outreach.email_subject,
        body=outreach.email_body,
        is_html=False,
        session=session,
    )

    # Log attempt with pool attribution
    status = "sent" if result.success else "failed"
    error = None if result.success else (result.error or "Failed to send via SMTP.")

    log_email_attempt(
        session=session,
        business_id=business.id,
        outreach_id=outreach_id,
        recipient_email=recipient,
        subject=outreach.email_subject,
        status=status,
        error_message=error,
        smtp_account_id=result.smtp_account_id,
        provider=result.provider,
        message_id=result.message_id,
        delivery_status=status,
        retry_count=result.retry_count,
    )

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=result.error or "Failed to send email. Ensure SMTP is configured correctly.",
        )

    response = {"message": f"Email successfully sent to {recipient}"}
    if result.provider:
        response["provider"] = result.provider
    if result.retry_count > 0:
        response["retry_count"] = result.retry_count

    return response


@router.get("/logs", response_model=List[EmailLogResponse])
def get_email_logs(
    skip: int = 0,
    limit: int = 50,
    campaign_id: int = None,
    session: Session = Depends(get_session),
):
    """Get history of sent emails."""
    # Query with join to get business name
    query = (
        select(EmailLog, Business.name.label("business_name"))
        .join(Business, EmailLog.business_id == Business.id)
    )

    if campaign_id:
        query = query.where(Business.campaign_id == campaign_id)

    query = query.order_by(EmailLog.id.desc()).offset(skip).limit(limit)

    results = session.exec(query).all()

    # Format response
    logs = []
    for log, business_name in results:
        log_dict = log.model_dump()
        log_dict["business_name"] = business_name
        logs.append(log_dict)

    return logs
