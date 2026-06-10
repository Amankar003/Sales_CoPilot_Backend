"""
campaign_routes.py - API routes for campaigns.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from typing import List

from app.database.session import get_session
from app.models.campaign import Campaign
from app.models.business import Business
from app.schemas.campaign_schema import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignDiscoverRequest,
    CampaignDiscoverResponse
)
from app.services.campaign.campaign_pipeline import run_campaign_pipeline
from app.schemas.business_schema import BusinessResponse
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse)
def create_campaign(
    campaign_in: CampaignCreate,
    session: Session = Depends(get_session),
):
    """Create a new campaign."""
    campaign = Campaign.model_validate(campaign_in)
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


@router.get("", response_model=List[CampaignResponse])
def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """Get all campaigns."""
    campaigns = session.exec(select(Campaign).offset(skip).limit(limit).order_by(Campaign.created_at.desc())).all()
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific campaign by ID."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    session: Session = Depends(get_session),
):
    """Update a campaign."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign_data = campaign_in.model_dump(exclude_unset=True)
    for key, value in campaign_data.items():
        setattr(campaign, key, value)
        
    session.add(campaign)
    session.commit()
    session.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}")
def delete_campaign(
    campaign_id: int,
    session: Session = Depends(get_session),
):
    """Delete a campaign."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    session.delete(campaign)
    session.commit()
    return {"message": "Campaign deleted successfully"}


@router.post("/discover", response_model=CampaignDiscoverResponse)
async def discover_campaign_inline(
    request: CampaignDiscoverRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Create a campaign and immediately trigger automated background discovery pipeline."""
    # 1. Create campaign
    campaign = Campaign(
        name=request.name,
        sector=request.sector,
        location=request.location,
        status="discovering",
        leads_count=0,
        enriched_count=0,
        audited_count=0,
        reports_count=0,
        outreach_count=0,
        emails_sent_count=0,
    )
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    logger.info(
        f"[Campaign {campaign.id}] Discovery pipeline initiated | "
        f"name='{request.name}' | sector='{request.sector}' | "
        f"location='{request.location}'"
    )

    # 2. Trigger background pipeline task
    background_tasks.add_task(
        run_campaign_pipeline,
        campaign.id,
        request.model_dump()
    )

    return {
        "message": "Campaign discovery pipeline started in background.",
        "campaign": campaign,
        "count": 0,
        "businesses": []
    }


@router.post("/{campaign_id}/discover", response_model=CampaignDiscoverResponse)
async def discover_campaign_by_id(
    campaign_id: int,
    request: CampaignDiscoverRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Run discovery and automation pipeline for an existing campaign in the background."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = "discovering"
    campaign.pipeline_error = None
    campaign.leads_count = 0
    campaign.enriched_count = 0
    campaign.audited_count = 0
    campaign.reports_count = 0
    campaign.outreach_count = 0
    campaign.emails_sent_count = 0
    session.add(campaign)
    session.commit()
    session.refresh(campaign)

    logger.info(f"[Campaign {campaign.id}] Discovery pipeline restarted in background.")

    # Trigger background pipeline task
    background_tasks.add_task(
        run_campaign_pipeline,
        campaign.id,
        request.model_dump()
    )

    return {
        "message": "Campaign discovery pipeline restarted in background.",
        "campaign": campaign,
        "count": 0,
        "businesses": []
    }
