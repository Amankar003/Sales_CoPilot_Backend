"""
system_routes.py - System health and diagnostic endpoints.
"""

import sys
import asyncio
import os
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, text

from app.database.session import get_session
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/system", tags=["System"])
logger = get_logger(__name__)


@router.get("/health")
async def health_check(session: Session = Depends(get_session)):
    """
    System health check endpoint.
    Returns status of database, Playwright, and Chromium browser.
    """
    result = {
        "database": False,
        "chromium_installed": False,
        "playwright_ready": False,
        "event_loop_policy": str(asyncio.get_event_loop_policy().__class__.__name__),
        "platform": sys.platform,
    }

    # Check database
    try:
        session.exec(text("SELECT 1")).first()
        result["database"] = True
    except Exception as e:
        logger.warning(f"Health check: database failed: {repr(e)}")

    # Check Playwright availability
    try:
        from playwright.async_api import async_playwright
        result["playwright_ready"] = True
    except ImportError:
        logger.warning("Health check: playwright not installed")

    # Check Chromium browser
    if result["playwright_ready"]:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                await browser.close()
                result["chromium_installed"] = True
        except Exception as e:
            logger.warning(f"Health check: Chromium launch failed: {repr(e)}")
            result["chromium_installed"] = False

    return result
