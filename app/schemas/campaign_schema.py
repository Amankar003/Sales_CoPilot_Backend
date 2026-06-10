"""
campaign_schema.py - Pydantic schemas for campaigns.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.business_schema import BusinessResponse

class CampaignBase(BaseModel):
    name: str
    sector: str
    location: str

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    leads_count: Optional[int] = None
    enriched_count: Optional[int] = None
    audited_count: Optional[int] = None
    reports_count: Optional[int] = None
    outreach_count: Optional[int] = None
    emails_sent_count: Optional[int] = None
    pipeline_error: Optional[str] = None

class CampaignResponse(CampaignBase):
    id: int
    status: str
    leads_count: int
    enriched_count: int
    audited_count: int
    reports_count: int
    outreach_count: int
    emails_sent_count: int
    pipeline_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class CampaignDiscoverRequest(CampaignBase):
    max_runtime_seconds: int = 120
    auto_enrich: bool = True
    auto_audit: bool = True
    auto_generate_reports: bool = True
    auto_generate_outreach: bool = True

class CampaignDiscoverResponse(BaseModel):
    message: str
    campaign: CampaignResponse
    count: int
    businesses: List[BusinessResponse]
