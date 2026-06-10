"""
reset_db.py - Delete and recreate the SQLite database.

Usage:
    python scripts/reset_db.py

This script:
1. Deletes the existing leadpilot.db file
2. Recreates all tables via SQLModel.metadata.create_all()
"""

import os
import sys

# Add the backend directory to the Python path so we can import app modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.settings import settings
from app.database.db import engine, create_db_and_tables


def main():
    # Extract the file path from DATABASE_URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
    else:
        print(f"Non-SQLite database detected ({db_url}). Manual migration needed.")
        sys.exit(1)

    # Resolve relative path
    db_path = os.path.join(backend_dir, db_path) if not os.path.isabs(db_path) else db_path

    # Step 1: Delete existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[OK] Deleted existing database: {db_path}")
    else:
        print(f"[INFO] No existing database found at: {db_path}")

    # Step 2: Create fresh tables
    create_db_and_tables()
    print("[OK] Recreated all database tables.")
    print("[OK] Database reset complete. You can now start the backend.")


if __name__ == "__main__":
    main()
