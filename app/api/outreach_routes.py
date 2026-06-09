"""
outreach_routes.py - API routes for outreach content generation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
import asyncio

from app.database.session import get_session
from app.models.business import Business
from app.models.audit import Audit
from app.models.outreach import Outreach
from app.schemas.outreach_schema import OutreachResponse
from app.services.outreach.email_generator import generate_email_content
from app.services.outreach.whatsapp_generator import generate_whatsapp_content
from app.services.outreach.call_notes_generator import generate_call_script_notes
from app.services.outreach.pitch_generator import generate_pitch_content

router = APIRouter(prefix="/api/outreach", tags=["Outreach"])


@router.post("/generate/{business_id}", response_model=OutreachResponse)
async def generate_outreach(
    business_id: int,
    session: Session = Depends(get_session),
):
    """
    Generate customized outreach content (Email, WhatsApp, Call Notes, Pitch).
    Uses audit data if available for better personalization.
    """
    business = session.get(Business, business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    # Get latest audit if exists
    audit = session.exec(
        select(Audit)
        .where(Audit.business_id == business_id)
        .order_by(Audit.created_at.desc())
    ).first()
    
    # Check for existing outreach and delete
    existing = session.exec(
        select(Outreach).where(Outreach.business_id == business_id)
    ).first()
    if existing:
        session.delete(existing)
        session.commit()

    # Generate all content concurrently for speed
    email_task = generate_email_content(business, audit)
    whatsapp_task = generate_whatsapp_content(business)
    call_task = generate_call_script_notes(business, audit)
    pitch_task = generate_pitch_content(business, audit)
    
    email_content, whatsapp, call_notes, pitch = await asyncio.gather(
        email_task, whatsapp_task, call_task, pitch_task
    )
    
    # Save to database
    outreach = Outreach(
        business_id=business_id,
        audit_id=audit.id if audit else None,
        email_subject=email_content.get("subject"),
        email_body=email_content.get("body"),
        whatsapp_message=whatsapp,
        call_notes=call_notes,
        meeting_pitch=pitch,
    )
    
    session.add(outreach)
    session.commit()
    session.refresh(outreach)
    
    return outreach


@router.get("/{business_id}", response_model=OutreachResponse)
def get_outreach(
    business_id: int,
    session: Session = Depends(get_session),
):
    """Get the generated outreach content for a business."""
    outreach = session.exec(
        select(Outreach)
        .where(Outreach.business_id == business_id)
        .order_by(Outreach.created_at.desc())
    ).first()
    
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach content not found. Generate it first.")
        
    return outreach
