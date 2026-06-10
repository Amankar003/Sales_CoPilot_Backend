"""
maps_scraper.py - Real Google Maps scraper using async Playwright.

This scraper collects real business data from Google Maps.
No mock data. No generated data. No fake fallback.
"""

import time
import asyncio
import urllib.parse
import os
from typing import Callable, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _verify_chromium_installed() -> bool:
    """Verify that Playwright Chromium browser is installed before launching."""
    try:
        # Try to find the chromium executable via Playwright internals
        from playwright._impl._driver import compute_driver_executable
        driver = compute_driver_executable()
        if driver and os.path.exists(str(driver)):
            return True
    except Exception:
        pass

    # Secondary check: try to actually launch and immediately close
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            await browser.close()
            return True
    except Exception as exc:
        logger.error(f"Chromium verification failed: {repr(exc)}")
        return False


def _parse_reviews_count(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        cleaned = (
            value.replace("(", "")
            .replace(")", "")
            .replace(",", "")
            .replace("reviews", "")
            .replace("review", "")
            .strip()
        )
        return int(cleaned)
    except Exception:
        return None


def _parse_rating(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.strip().replace(",", "."))
    except Exception:
        return None


async def _async_scrape_google_maps_businesses(
    sector: str,
    location: str,
    campaign_id: int = None,
    limit: int | None = None,
    max_runtime_seconds: int = 120,
    should_stop: Optional[Callable[[], bool]] = None,
) -> list[dict]:
    """
    Scrape real businesses from Google Maps using async Playwright.

    Args:
        sector: Business sector, e.g. "Hospital"
        location: Location, e.g. "Noida"
        campaign_id: Campaign ID for logging.
        limit: Optional business limit. If None, scrape all loaded results.
        max_runtime_seconds: Runtime safety limit.
        should_stop: Optional external stop callback.

    Returns:
        List of real business dictionaries matching the Business model.
    """
    # Lazy import to avoid loading Playwright at module level
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

    search_query = f"{sector} in {location}".strip()
    encoded_query = urllib.parse.quote_plus(search_query)
    maps_url = f"https://www.google.com/maps/search/{encoded_query}"

    log_prefix = f"[Campaign {campaign_id}] " if campaign_id else ""
    logger.info(f"{log_prefix}Google Maps scrape starting | query='{search_query}' | url={maps_url}")

    results: list[dict] = []
    start_time = time.time()

    try:
        async with async_playwright() as p:
            logger.info(f"{log_prefix}Launching Chromium browser (headless)...")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            logger.info(f"{log_prefix}Chromium launched successfully.")

            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            page = await context.new_page()
            logger.info(f"{log_prefix}Navigating to Google Maps...")
            await page.goto(maps_url, wait_until="domcontentloaded", timeout=30000)

            try:
                await page.wait_for_selector('div[role="feed"]', timeout=15000)
                logger.info(f"{log_prefix}Google Maps results feed loaded.")
            except PlaywrightTimeoutError:
                logger.warning(f"{log_prefix}Google Maps results feed did not load within 15s.")
                await browser.close()
                return []

            scrollable_div = page.locator('div[role="feed"]').first

            previous_count = 0
            no_new_results_count = 0
            max_no_new_scrolls = 5

            logger.info(f"{log_prefix}Scrolling to load business cards...")

            while True:
                if should_stop and should_stop():
                    logger.info(f"{log_prefix}Scrape stopped by user.")
                    break

                if time.time() - start_time > max_runtime_seconds:
                    logger.info(f"{log_prefix}Scrape stopped: max runtime {max_runtime_seconds}s reached.")
                    break

                cards = await page.locator('a[href*="https://www.google.com/maps/place/"]').all()
                current_count = len(cards)

                if current_count != previous_count:
                    logger.info(f"{log_prefix}Loaded {current_count} business cards so far.")
                    previous_count = current_count
                    no_new_results_count = 0
                else:
                    no_new_results_count += 1

                if limit is not None and current_count >= limit:
                    logger.info(f"{log_prefix}Reached requested limit: {limit}")
                    break

                if no_new_results_count >= max_no_new_scrolls:
                    logger.info(f"{log_prefix}No more new results after {max_no_new_scrolls} scroll attempts. Total loaded: {current_count}")
                    break

                try:
                    await scrollable_div.hover(timeout=2000)
                    await page.mouse.wheel(0, 2500)
                except Exception:
                    await page.keyboard.press("PageDown")

                await asyncio.sleep(1.5)

            cards = await page.locator('a[href*="https://www.google.com/maps/place/"]').all()
            cards_to_process = cards[:limit] if limit is not None else cards

            logger.info(f"{log_prefix}Extracting details from {len(cards_to_process)} cards...")

            seen_names = set()

            for index, card in enumerate(cards_to_process, start=1):
                if should_stop and should_stop():
                    logger.info(f"{log_prefix}Extraction stopped by user.")
                    break

                if time.time() - start_time > max_runtime_seconds:
                    logger.info(f"{log_prefix}Extraction stopped: max runtime reached.")
                    break

                try:
                    await card.click(timeout=5000)
                    await asyncio.sleep(2)

                    business_name = ""
                    for selector in ["h1.DUwDvf", "h1.fontHeadlineLarge", "h1"]:
                        loc = page.locator(selector)
                        if await loc.count() > 0:
                            business_name = await loc.first.inner_text(timeout=2000)
                            business_name = business_name.strip()
                        if business_name:
                            break

                    if not business_name:
                        logger.warning(f"{log_prefix}Card {index}: missing business name, skipping.")
                        continue

                    normalized_name = business_name.strip().lower()
                    if normalized_name in seen_names:
                        continue
                    seen_names.add(normalized_name)

                    address = ""
                    address_loc = page.locator('button[data-item-id="address"]')
                    if await address_loc.count() > 0:
                        address = await address_loc.first.inner_text()
                    if "\n" in address:
                        address = address.split("\n")[-1].strip()

                    phone = ""
                    phone_loc = page.locator('button[data-item-id*="phone:tel:"]')
                    if await phone_loc.count() > 0:
                        phone = await phone_loc.first.inner_text()
                    if "\n" in phone:
                        phone = phone.split("\n")[-1].strip()

                    website = ""
                    website_loc = page.locator('a[data-item-id="authority"]')
                    if await website_loc.count() > 0:
                        website = await website_loc.first.get_attribute("href") or ""

                    rating_text = ""
                    rating_loc = page.locator("div.F7nice")
                    if await rating_loc.count() > 0:
                        rating_text = await rating_loc.first.inner_text()
                    rating = None
                    reviews_count = None

                    if rating_text:
                        parts = [part.strip() for part in rating_text.split("\n") if part.strip()]
                        if len(parts) >= 1:
                            rating = _parse_rating(parts[0])
                        if len(parts) >= 2:
                            reviews_count = _parse_reviews_count(parts[1])

                    category = sector.title()

                    business = {
                        "name": business_name,
                        "category": category,
                        "location": location,
                        "address": address or None,
                        "phone": phone or None,
                        "email": None,
                        "website": website or None,
                        "google_rating": rating,
                        "reviews_count": reviews_count,
                        "description": None,
                        "source": "google_maps",
                        "confidence_score": 0.9,
                    }

                    results.append(business)
                    logger.info(f"{log_prefix}Extracted [{index}]: {business_name} | phone={phone or 'N/A'} | website={'yes' if website else 'no'}")

                except Exception as exc:
                    logger.error(f"{log_prefix}Error extracting card {index}: {repr(exc)}")

            await browser.close()
            logger.info(f"{log_prefix}Browser closed.")

    except Exception as exc:
        logger.error(f"{log_prefix}Google Maps scraper FAILED: {repr(exc)}")
        raise  # Re-raise so caller can handle it properly

    elapsed = round(time.time() - start_time, 1)
    logger.info(f"{log_prefix}Google Maps scrape completed | businesses_found={len(results)} | elapsed={elapsed}s")
    return results


def _sync_run_scraper(
    sector: str,
    location: str,
    campaign_id: int = None,
    limit: int | None = None,
    max_runtime_seconds: int = 120,
) -> list[dict]:
    """
    Synchronous wrapper that creates a fresh event loop and runs the scraper.
    This guarantees a WindowsProactorEventLoopPolicy is used on Windows, bypassing uvicorn's override.
    """
    # Force Proactor loop on Windows in this thread
    import sys
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    return asyncio.run(
        _async_scrape_google_maps_businesses(
            sector=sector,
            location=location,
            campaign_id=campaign_id,
            limit=limit,
            max_runtime_seconds=max_runtime_seconds,
        )
    )


async def scrape_google_maps_businesses(
    sector: str,
    location: str,
    campaign_id: int = None,
    limit: int | None = None,
    max_runtime_seconds: int = 120,
    should_stop: Optional[Callable[[], bool]] = None,
) -> list[dict]:
    """
    Runs the Google Maps Playwright scraper in a separate thread.
    This prevents Playwright from crashing due to uvicorn's event loop policy
    and prevents blocking the main FastAPI thread.
    """
    return await asyncio.to_thread(
        _sync_run_scraper,
        sector,
        location,
        campaign_id,
        limit,
        max_runtime_seconds,
    )
