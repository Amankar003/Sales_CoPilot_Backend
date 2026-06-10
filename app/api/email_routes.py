"""
email_routes.py - API routes for sending emails and viewing logs.
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
        
    # Send email
    success = await send_email(
        to_email=recipient,
        subject=outreach.email_subject,
        body=outreach.email_body,
        is_html=False
    )
    
    # Log attempt
    status = "sent" if success else "failed"
    error = None if success else "Failed to send via SMTP. Check configuration."
    
    log_email_attempt(
        session=session,
        business_id=business.id,
        outreach_id=outreach_id,
        recipient_email=recipient,
        subject=outreach.email_subject,
        status=status,
        error_message=error
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email. Ensure SMTP is configured correctly.")
        
    return {"message": f"Email successfully sent to {recipient}"}


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
