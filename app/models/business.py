"""
business.py - Business model for storing lead information.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class Business(SQLModel, table=True):
    """Represents a business lead in the system."""

    __tablename__ = "businesses"

    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: Optional[int] = Field(default=None, foreign_key="campaigns.id", index=True)
    name: str = Field(index=True)
    category: str = Field(index=True)
    location: str = Field(index=True)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    linkedin: Optional[str] = None
    google_rating: Optional[float] = None
    reviews_count: Optional[int] = None
    description: Optional[str] = None
    source: str = Field(default="manual")  # manual, discovered, csv_import
    confidence_score: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
