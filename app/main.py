"""
main.py - Main FastAPI application entry point.

IMPORTANT: The event loop policy MUST be set before any other imports
that might trigger Playwright or asyncio subprocess usage.
"""

import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.settings import settings
from app.database.db import create_db_and_tables, engine
from app.utils.logger import get_logger
from app.utils.file_manager import ensure_directory

# Import routers
from app.api.lead_routes import router as lead_router
from app.api.audit_routes import router as audit_router
from app.api.report_routes import router as report_router
from app.api.outreach_routes import router as outreach_router
from app.api.email_routes import router as email_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.campaign_routes import router as campaign_router
from app.api.system_routes import router as system_router

logger = get_logger(__name__)


def _check_playwright_browsers():
    """Check if Playwright Chromium browser is installed."""
    try:
        from playwright._impl._driver import compute_driver_executable
        driver_exe = compute_driver_executable()
        if driver_exe and os.path.exists(str(driver_exe)):
            logger.info("Playwright driver found.")
        else:
            logger.warning(
                "Chromium browser not installed. Run: playwright install chromium"
            )
    except Exception:
        logger.warning(
            "Chromium browser not installed. Run: playwright install chromium"
        )


def _check_and_migrate_db():
    """
    Check if the existing SQLite database has the required schema.
    If columns are missing (e.g. campaign_id), delete and recreate.
    """
    import sqlite3

    # Extract the file path from DATABASE_URL (sqlite:///./leadpilot.db)
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
    else:
        # Not SQLite, skip this check
        return

    if not os.path.exists(db_path):
        logger.info("No existing database file. Will create fresh.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if businesses table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='businesses'"
        )
        if not cursor.fetchone():
            conn.close()
            logger.info("businesses table not found. Will create fresh.")
            return

        # Check if campaign_id column exists in businesses
        cursor.execute("PRAGMA table_info(businesses)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        if "campaign_id" not in columns:
            logger.warning(
                "Outdated schema detected: businesses.campaign_id column missing. "
                "Deleting old database and recreating..."
            )
            os.remove(db_path)
            logger.info(f"Deleted old database: {db_path}")

        # Also check if campaigns table exists and contains new columns
        if "campaign_id" in columns:
            conn2 = sqlite3.connect(db_path)
            cursor2 = conn2.cursor()
            cursor2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='campaigns'"
            )
            has_campaigns = cursor2.fetchone()
            
            if has_campaigns:
                cursor2.execute("PRAGMA table_info(campaigns)")
                campaign_cols = [row[1] for row in cursor2.fetchall()]
                conn2.close()
                
                required_cols = ["enriched_count", "audited_count", "reports_count", "outreach_count", "pipeline_error"]
                missing_cols = [c for c in required_cols if c not in campaign_cols]
                if missing_cols:
                    logger.warning(
                        f"Outdated schema: campaigns table missing columns {missing_cols}. "
                        "Deleting old database and recreating..."
                    )
                    os.remove(db_path)
                    logger.info(f"Deleted old database: {db_path}")
            else:
                conn2.close()
                logger.warning(
                    "Outdated schema: campaigns table missing. "
                    "Deleting old database and recreating..."
                )
                os.remove(db_path)
                logger.info(f"Deleted old database: {db_path}")

    except Exception as e:
        logger.error(f"Schema check failed: {repr(e)}. Deleting database to be safe.")
        try:
            os.remove(db_path)
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    Runs startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")

    # Re-apply Proactor policy in case uvicorn overrode it during startup
    if sys.platform.startswith("win"):
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            logger.warning(
                f"Event loop policy was overridden to {type(current_policy).__name__}. "
                "Re-applying WindowsProactorEventLoopPolicy..."
            )
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info(f"Windows event loop policy: {type(asyncio.get_event_loop_policy()).__name__}")

    # Ensure reports directory exists
    reports_dir = os.path.join(os.getcwd(), settings.REPORTS_DIR)
    ensure_directory(reports_dir)

    # Check Playwright browsers
    _check_playwright_browsers()

    # Check and auto-migrate database schema
    _check_and_migrate_db()

    # Initialize database tables
    logger.info("Initializing database...")
    create_db_and_tables()

    logger.info("Application startup complete.")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered lead discovery and audit platform",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for reports
reports_dir = os.path.join(os.getcwd(), settings.REPORTS_DIR)
ensure_directory(reports_dir)
app.mount("/static/reports", StaticFiles(directory=reports_dir), name="reports")


# Include API routers
app.include_router(lead_router)
app.include_router(audit_router)
app.include_router(report_router)
app.include_router(outreach_router)
app.include_router(email_router)
app.include_router(dashboard_router)
app.include_router(campaign_router)
app.include_router(system_router)


@app.get("/")
def root():
    """Root endpoint to verify API is running."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "openai_configured": settings.has_groq_key,
        "smtp_configured": settings.has_smtp_config,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
