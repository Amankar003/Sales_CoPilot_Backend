"""
db.py - Database engine and table creation.
"""

from sqlmodel import SQLModel, create_engine
from app.core.settings import settings

# Create SQLite engine
# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables():
    """Create all database tables on startup."""
    # Import all models so SQLModel knows about them
    from app.models.business import Business  # noqa: F401
    from app.models.audit import Audit  # noqa: F401
    from app.models.report import Report  # noqa: F401
    from app.models.outreach import Outreach  # noqa: F401
    from app.models.email_log import EmailLog  # noqa: F401
    from app.models.campaign import Campaign  # noqa: F401
    from app.models.smtp_account import SMTPAccount  # noqa: F401

    SQLModel.metadata.create_all(engine)
