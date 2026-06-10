"""
lead_routes.py - API routes for business leads.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List
import csv
import io

from app.database.session import get_session
from app.models.business import Business
from app.schemas.business_schema import (
    BusinessCreate,
    BusinessUpdate,
    BusinessResponse,
    DiscoverRequest,
    DiscoverResponse,
)
from app.services.discovery.business_collector import (
    discover_businesses,
    import_businesses_from_csv,
)

router = APIRouter(prefix="/api/leads", tags=["Leads"])


@router.post("", response_model=BusinessResponse)
def create_lead(
    lead_in: BusinessCreate,
    session: Session = Depends(get_session),
):
    """Create a new business lead manually."""
    lead = Business.model_validate(lead_in)
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@router.get("", response_model=List[BusinessResponse])
def get_leads(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    campaign_id: int = None,
    session: Session = Depends(get_session),
):
    """Get all business leads with optional filtering."""
    query = select(Business)
    if category:
        query = query.where(Business.category == category)
    if campaign_id:
        query = query.where(Business.campaign_id == campaign_id)
    
    query = query.offset(skip).limit(limit)
    leads = session.exec(query).all()
    return leads


@router.get("/{business_id}", response_model=BusinessResponse)
def get_lead(
    business_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific business lead by ID."""
    lead = session.get(Business, business_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{business_id}", response_model=BusinessResponse)
def update_lead(
    business_id: int,
    lead_in: BusinessUpdate,
    session: Session = Depends(get_session),
):
    """Update a business lead."""
    lead = session.get(Business, business_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = lead_in.model_dump(exclude_unset=True)
    for key, value in lead_data.items():
        setattr(lead, key, value)
        
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead


@router.delete("/{business_id}")
def delete_lead(
    business_id: int,
    session: Session = Depends(get_session),
):
    """Delete a business lead."""
    lead = session.get(Business, business_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    session.delete(lead)
    session.commit()
    return {"message": "Lead deleted successfully"}


@router.post("/discover", deprecated=True)
async def discover_leads_deprecated():
    """DEPRECATED. Use /api/campaigns/discover instead."""
    return {"message": "Deprecated. Use /api/campaigns/discover instead."}
    
    if len(new_leads) > 0:
        message = f"Discovered real businesses successfully"
    else:
        message = "No real businesses found. Try another sector/location or use CSV import."
    
    return {
        "businesses": new_leads,
        "count": len(new_leads),
        "message": message
    }


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Import leads from a CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_text))
        
        # Convert keys to lowercase and strip whitespace
        rows = []
        for row in reader:
            clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            rows.append(clean_row)
            
        imported = import_businesses_from_csv(rows, session)
        
        return {
            "message": f"Successfully imported {len(imported)} leads",
            "imported_count": len(imported)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
