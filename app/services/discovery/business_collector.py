"""
business_collector.py - Orchestrates business discovery, deduplication, and storage.

Discovery priority:
1. Google Maps (primary - real scraped data via Playwright)
2. JustDial (India-specific business directory scraping)
3. IndiaMART (India-specific B2B directory scraping)
4. DuckDuckGo (last resort - supplementary, heavily rate-limited)

DuckDuckGo is NEVER the primary source due to aggressive rate limits.
"""

from typing import List
import re
import time
from sqlmodel import Session, select
from app.models.business import Business
from app.services.discovery.maps_scraper import scrape_google_maps_businesses
from app.services.discovery.serp_search import search_businesses_ddg
from app.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_business_name(name: str) -> str:
    """Normalize business name for deduplication."""
    if not name:
        return ""
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)
    return " ".join(name.split())


def normalize_phone(phone: str) -> str:
    """Normalize phone number."""
    if not phone:
        return ""
    return re.sub(r'[^\d+]', '', phone)


def normalize_website(website: str) -> str:
    """Normalize website."""
    if not website:
        return ""
    website = website.lower()
    website = website.replace('http://', '').replace('https://', '').replace('www.', '')
    return website.rstrip('/')


def deduplicate_results(results: List[dict], location: str) -> List[dict]:
    """Deduplicate a list of business dictionaries."""
    seen_keys = set()
    unique_results = []

    for result in results:
        name = normalize_business_name(result.get("name", ""))
        if not name:
            continue

        normalized_loc = location.lower().strip()
        key = f"{name}|{normalized_loc}"

        if key not in seen_keys:
            seen_keys.add(key)
            unique_results.append(result)

    return unique_results


async def _scrape_justdial(sector: str, location: str, max_runtime_seconds: int = 60) -> List[dict]:
    """
    Scrape businesses from JustDial (India-specific directory).
    Uses HTTP requests, not Playwright, so no browser needed.
    """
    import asyncio
    results = []
    try:
        import httpx
        search_query = f"{sector} in {location}"
        jd_url = f"https://www.justdial.com/{location}/{sector.replace(' ', '-')}"

        logger.info(f"JustDial scraping: {jd_url}")

        async with httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        ) as client:
            resp = await client.get(jd_url)

            if resp.status_code == 200:
                from html.parser import HTMLParser
                html_content = resp.text

                # Simple extraction of business names from JustDial HTML
                # JustDial uses specific class names for business listings
                import re as regex
                # Look for business names in common JustDial patterns
                name_pattern = regex.compile(r'class="lng_cont_name[^"]*"[^>]*>([^<]+)<', regex.IGNORECASE)
                names_found = name_pattern.findall(html_content)

                for name in names_found:
                    name = name.strip()
                    if name and len(name) > 2:
                        results.append({
                            "name": name,
                            "category": sector.title(),
                            "location": location,
                            "source": "justdial",
                            "confidence_score": 0.7,
                        })

                logger.info(f"JustDial returned {len(results)} results.")
            else:
                logger.warning(f"JustDial returned HTTP {resp.status_code}")

    except ImportError:
        logger.warning("httpx not installed, skipping JustDial scrape.")
    except Exception as e:
        logger.warning(f"JustDial scraping failed: {repr(e)}")

    return results


async def _scrape_indiamart(sector: str, location: str, max_runtime_seconds: int = 60) -> List[dict]:
    """
    Scrape businesses from IndiaMART (India-specific B2B directory).
    Uses HTTP requests.
    """
    results = []
    try:
        import httpx
        search_query = f"{sector} in {location}"
        im_url = f"https://dir.indiamart.com/search.mp?ss={sector.replace(' ', '+')}&cq={location}"

        logger.info(f"IndiaMART scraping: {im_url}")

        async with httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
        ) as client:
            resp = await client.get(im_url)

            if resp.status_code == 200:
                import re as regex
                # IndiaMART uses specific patterns for company names
                name_pattern = regex.compile(r'class="lcname[^"]*"[^>]*>([^<]+)<', regex.IGNORECASE)
                names_found = name_pattern.findall(resp.text)

                for name in names_found:
                    name = name.strip()
                    if name and len(name) > 2:
                        results.append({
                            "name": name,
                            "category": sector.title(),
                            "location": location,
                            "source": "indiamart",
                            "confidence_score": 0.65,
                        })

                logger.info(f"IndiaMART returned {len(results)} results.")
            else:
                logger.warning(f"IndiaMART returned HTTP {resp.status_code}")

    except ImportError:
        logger.warning("httpx not installed, skipping IndiaMART scrape.")
    except Exception as e:
        logger.warning(f"IndiaMART scraping failed: {repr(e)}")

    return results


async def discover_businesses(
    sector: str,
    location: str,
    campaign_id: int,
    max_runtime_seconds: int = 120,
    session: Session = None,
) -> List[Business]:
    """
    Discover businesses by sector and location.

    Discovery priority order:
    1. Google Maps (primary - real structured business data)
    2. JustDial (India-specific directory)
    3. IndiaMART (India-specific B2B directory)
    4. DuckDuckGo (last resort only - heavily rate-limited)
    """
    log_prefix = f"[Campaign {campaign_id}]"
    logger.info(f"{log_prefix} Discovery starting | sector='{sector}' | location='{location}' | max_runtime={max_runtime_seconds}s")

    combined_results = []
    errors = []
    discovery_start = time.time()

    # ----- Source 1 (Primary): Google Maps -----
    try:
        logger.info(f"{log_prefix} Source 1/4: Google Maps scraping...")
        maps_results = await scrape_google_maps_businesses(
            sector=sector,
            location=location,
            campaign_id=campaign_id,
            limit=None,
            max_runtime_seconds=max_runtime_seconds,
        )
        combined_results.extend(maps_results)
        logger.info(f"{log_prefix} Google Maps: {len(maps_results)} businesses found.")
    except Exception as e:
        logger.error(f"{log_prefix} Google Maps FAILED: {repr(e)}")
        errors.append(f"GoogleMaps: {repr(e)}")

    # ----- Source 2: JustDial -----
    if len(combined_results) < 5:
        try:
            remaining_time = max(30, max_runtime_seconds - int(time.time() - discovery_start))
            logger.info(f"{log_prefix} Source 2/4: JustDial scraping...")
            jd_results = await _scrape_justdial(sector, location, remaining_time)
            combined_results.extend(jd_results)
            logger.info(f"{log_prefix} JustDial: {len(jd_results)} businesses found.")
        except Exception as e:
            logger.warning(f"{log_prefix} JustDial failed: {repr(e)}")
            errors.append(f"JustDial: {repr(e)}")
    else:
        logger.info(f"{log_prefix} Skipping JustDial - Google Maps returned {len(combined_results)} results.")

    # ----- Source 3: IndiaMART -----
    if len(combined_results) < 5:
        try:
            remaining_time = max(30, max_runtime_seconds - int(time.time() - discovery_start))
            logger.info(f"{log_prefix} Source 3/4: IndiaMART scraping...")
            im_results = await _scrape_indiamart(sector, location, remaining_time)
            combined_results.extend(im_results)
            logger.info(f"{log_prefix} IndiaMART: {len(im_results)} businesses found.")
        except Exception as e:
            logger.warning(f"{log_prefix} IndiaMART failed: {repr(e)}")
            errors.append(f"IndiaMART: {repr(e)}")
    else:
        logger.info(f"{log_prefix} Skipping IndiaMART - already have {len(combined_results)} results.")

    # ----- Source 4 (Last Resort): DuckDuckGo -----
    if len(combined_results) < 3:
        try:
            remaining_time = max(20, max_runtime_seconds - int(time.time() - discovery_start))
            logger.info(f"{log_prefix} Source 4/4 (last resort): DuckDuckGo search...")
            ddg_results = await search_businesses_ddg(
                sector=sector,
                location=location,
                max_runtime_seconds=remaining_time,
            )
            combined_results.extend(ddg_results)
            logger.info(f"{log_prefix} DuckDuckGo: {len(ddg_results)} results.")
        except Exception as e:
            logger.warning(f"{log_prefix} DuckDuckGo failed (rate limited?): {repr(e)}")
            errors.append(f"DuckDuckGo: {repr(e)}")
    else:
        logger.info(f"{log_prefix} Skipping DuckDuckGo - already have {len(combined_results)} results.")

    # If ALL sources failed and we got nothing
    if errors and not combined_results:
        error_summary = " | ".join(errors)
        logger.error(f"{log_prefix} ALL discovery sources failed: {error_summary}")
        raise RuntimeError(f"All scrapers failed. Errors: {error_summary}")

    # Deduplicate
    unique_results = deduplicate_results(combined_results, location)
    logger.info(f"{log_prefix} Deduplication: {len(combined_results)} raw -> {len(unique_results)} unique")

    new_businesses = []

    if not unique_results:
        logger.info(f"{log_prefix} No real businesses found after deduplication.")
        return []

    # Create Business objects and deduplicate against DB
    for result in unique_results:
        if session:
            existing = session.exec(
                select(Business).where(
                    Business.name == result.get("name", ""),
                    Business.location == location,
                )
            ).first()

            if existing:
                logger.debug(f"{log_prefix} DB duplicate skipped: {result.get('name')}")
                new_businesses.append(existing)
                continue

        business = Business(
            campaign_id=campaign_id,
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
            confidence_score=result.get("confidence_score", 0.7),
        )

        if session:
            session.add(business)
            new_businesses.append(business)

    if session and new_businesses:
        session.commit()
        for b in new_businesses:
            if b.id is None:
                session.refresh(b)

    elapsed = round(time.time() - discovery_start, 1)
    logger.info(
        f"{log_prefix} Discovery COMPLETE | "
        f"businesses_saved={len(new_businesses)} | "
        f"sources_tried={4 - len([e for e in errors])} | "
        f"errors={len(errors)} | "
        f"elapsed={elapsed}s"
    )
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
        if not row.get("name"):
            continue

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
        imported.append(business)

    if session and imported:
        session.commit()
        for b in imported:
            session.refresh(b)

    logger.info(f"Imported {len(imported)} businesses from CSV")
    return imported
