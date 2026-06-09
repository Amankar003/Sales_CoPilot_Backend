"""
business_collector.py - Orchestrates business discovery, deduplication, and storage.
"""

from typing import List
from sqlmodel import Session, select
from app.models.business import Business
from app.services.discovery.maps_scraper import get_mock_businesses
from app.services.discovery.serp_search import search_businesses_ddg
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def discover_businesses(
    sector: str,
    location: str,
    limit: int = 10,
    session: Session = None,
) -> List[Business]:
    """
    Discover businesses by sector and location.
    
    Strategy:
    1. Try DuckDuckGo search for real results
    2. Fall back to mock data if search fails or returns too few results
    3. Deduplicate against existing database entries
    4. Save new businesses to database
    """
    logger.info(f"Discovering businesses: {sector} in {location}")

    # Step 1: Try real search
    search_results = []
    try:
        search_results = await search_businesses_ddg(sector, location, limit)
    except Exception as e:
        logger.warning(f"Search failed, using mock data: {e}")

    # Step 2: If search returned insufficient results, use mock data
    if len(search_results) < limit:
        logger.info("Using mock data to supplement results")
        mock_results = get_mock_businesses(sector, location, limit)

        # Merge search results with mock data
        existing_names = {r.get("name", "").lower() for r in search_results}
        for mock in mock_results:
            if mock["name"].lower() not in existing_names:
                search_results.append(mock)
            if len(search_results) >= limit:
                break

    # Step 3: Create Business objects and deduplicate
    new_businesses = []
    for result in search_results[:limit]:
        # Check if business already exists in database
        if session:
            existing = session.exec(
                select(Business).where(
                    Business.name == result.get("name", ""),
                    Business.location == location,
                )
            ).first()

            if existing:
                logger.info(f"Skipping duplicate: {result.get('name')}")
                new_businesses.append(existing)
                continue

        # Create new business
        business = Business(
            name=result.get("name", "Unknown Business"),
            category=result.get("category", sector.title()),
            location=location,
            address=result.get("address"),
            phone=result.get("phone"),
            email=result.get("email"),
            website=result.get("website"),
            google_rating=result.get("google_rating"),
            reviews_count=result.get("reviews_count"),
            description=result.get("description"),
            source=result.get("source", "discovered"),
            confidence_score=result.get("confidence_score"),
        )

        if session:
            session.add(business)
            session.commit()
            session.refresh(business)

        new_businesses.append(business)

    logger.info(f"Discovered {len(new_businesses)} businesses")
    return new_businesses


def import_businesses_from_csv(
    csv_data: List[dict],
    session: Session,
) -> List[Business]:
    """
    Import businesses from parsed CSV data.
    
    Expected CSV columns: name, category, location, address, phone, email, website
    """
    logger.info(f"Importing {len(csv_data)} businesses from CSV")

    imported = []
    for row in csv_data:
        # Skip rows without a name
        if not row.get("name"):
            continue

        # Check for duplicates
        existing = session.exec(
            select(Business).where(
                Business.name == row["name"],
                Business.location == row.get("location", "Unknown"),
            )
        ).first()

        if existing:
            logger.info(f"Skipping CSV duplicate: {row['name']}")
            imported.append(existing)
            continue

        business = Business(
            name=row["name"],
            category=row.get("category", "Other"),
            location=row.get("location", "Unknown"),
            address=row.get("address"),
            phone=row.get("phone"),
            email=row.get("email"),
            website=row.get("website"),
            instagram=row.get("instagram"),
            facebook=row.get("facebook"),
            linkedin=row.get("linkedin"),
            description=row.get("description"),
            source="csv_import",
        )

        session.add(business)
        session.commit()
        session.refresh(business)
        imported.append(business)

    logger.info(f"Imported {len(imported)} businesses from CSV")
    return imported
