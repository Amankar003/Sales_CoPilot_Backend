"""
audit_schema.py - Pydantic schemas for audit endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AuditResponse(BaseModel):
    """Schema for audit response."""
    id: int
    business_id: int
    has_website: bool
    ssl_enabled: bool
    mobile_responsive: bool
    loading_speed_score: Optional[float] = None
    seo_score: Optional[float] = None
    ux_score: Optional[float] = None
    social_score: Optional[float] = None
    has_contact_form: bool
    has_whatsapp: bool
    has_booking_system: bool
    has_crm_signals: bool
    broken_links_count: int
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int
    image_alt_missing_count: int
    audit_score: Optional[float] = None
    pain_points: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditSummary(BaseModel):
    """Compact audit summary for dashboard/listing."""
    id: int
    business_id: int
    business_name: Optional[str] = None
    audit_score: Optional[float] = None
    has_website: bool
    seo_score: Optional[float] = None
    social_score: Optional[float] = None
    created_at: datetime
