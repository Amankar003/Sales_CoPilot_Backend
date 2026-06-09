"""
session.py - Database session dependency for FastAPI.
"""

from sqlmodel import Session
from app.database.db import engine


def get_session():
    """
    FastAPI dependency that provides a database session.
    Session is automatically closed after the request.
    """
    with Session(engine) as session:
        yield session
