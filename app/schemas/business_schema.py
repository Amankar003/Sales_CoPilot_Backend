"""
business_schema.py - Pydantic schemas for business/lead endpoints.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BusinessCreate(BaseModel):
    """Schema for creating a new business lead."""
    name: str
    category: str
    location: str
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
    source: str = "manual"


class BusinessUpdate(BaseModel):
    """Schema for updating a business lead."""
    name: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
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


class BusinessResponse(BaseModel):
    """Schema for business response."""
    id: int
    name: str
    category: str
    location: str
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
    source: str
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscoverRequest(BaseModel):
    """Schema for lead discovery request."""
    sector: str
    location: str
    limit: int = 10


class DiscoverResponse(BaseModel):
    """Schema for lead discovery response."""
    leads: List[BusinessResponse]
    total: int
    message: str
