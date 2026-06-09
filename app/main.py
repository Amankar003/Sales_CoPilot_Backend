"""
main.py - Main FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.settings import settings
from app.database.db import create_db_and_tables
from app.utils.logger import get_logger
from app.utils.file_manager import ensure_directory

# Import routers
from app.api.lead_routes import router as lead_router
from app.api.audit_routes import router as audit_router
from app.api.report_routes import router as report_router
from app.api.outreach_routes import router as outreach_router
from app.api.email_routes import router as email_router
from app.api.dashboard_routes import router as dashboard_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    Runs startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # Ensure reports directory exists
    reports_dir = os.path.join(os.getcwd(), settings.REPORTS_DIR)
    ensure_directory(reports_dir)
    
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
