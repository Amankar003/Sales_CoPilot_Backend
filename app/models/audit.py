"""
audit.py - Audit model for storing website and social audit results.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Audit(SQLModel, table=True):
    """Stores audit results for a business."""

    __tablename__ = "audits"

    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(index=True, foreign_key="businesses.id")

    # Website checks
    has_website: bool = Field(default=False)
    ssl_enabled: bool = Field(default=False)
    mobile_responsive: bool = Field(default=False)
    loading_speed_score: Optional[float] = None

    # Scores (0-100)
    seo_score: Optional[float] = None
    ux_score: Optional[float] = None
    social_score: Optional[float] = None

    # Website features
    has_contact_form: bool = Field(default=False)
    has_whatsapp: bool = Field(default=False)
    has_booking_system: bool = Field(default=False)
    has_crm_signals: bool = Field(default=False)

    # SEO details
    broken_links_count: int = Field(default=0)
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int = Field(default=0)
    image_alt_missing_count: int = Field(default=0)

    # Overall
    audit_score: Optional[float] = None

    # JSON fields stored as text
    pain_points_json: Optional[str] = None      # JSON array of pain points
    opportunities_json: Optional[str] = None     # JSON array of opportunities
    recommendations_json: Optional[str] = None   # JSON array of recommendations

    created_at: datetime = Field(default_factory=datetime.utcnow)
