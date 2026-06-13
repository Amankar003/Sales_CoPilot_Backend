"""
add_smtp_tables.py - Migration script for the Multi SMTP Pool system.

Usage:
    python scripts/add_smtp_tables.py

This script:
1. Checks if the smtp_accounts table exists, creates if missing
2. Checks if email_logs has the new SMTP pool columns
3. Advises on database reset if column changes are needed
"""

import os
import sys
import sqlite3

# Add the backend directory to the Python path
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

    if not os.path.exists(db_path):
        print(f"[INFO] No existing database found at: {db_path}")
        print("[INFO] Creating fresh database with all tables...")
        create_db_and_tables()
        print("[OK] Database created with SMTP pool tables.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check 1: Does smtp_accounts table exist?
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='smtp_accounts'"
    )
    has_smtp_table = cursor.fetchone() is not None

    # Check 2: Does email_logs have the new columns?
    cursor.execute("PRAGMA table_info(email_logs)")
    email_log_columns = [row[1] for row in cursor.fetchall()]

    new_email_log_columns = [
        "smtp_account_id", "provider", "message_id",
        "delivery_status", "bounce_reason", "retry_count"
    ]
    missing_email_log_cols = [c for c in new_email_log_columns if c not in email_log_columns]

    conn.close()

    print("=" * 60)
    print("  SMTP Pool Migration Check")
    print("=" * 60)

    if has_smtp_table and not missing_email_log_cols:
        print("[OK] All SMTP pool tables and columns are present.")
        print("[OK] No migration needed.")
        return

    needs_reset = False

    if not has_smtp_table:
        print("[MISSING] smtp_accounts table does not exist.")
        print("  -> Will be created automatically on next startup.")

    if missing_email_log_cols:
        print(f"[MISSING] email_logs is missing columns: {missing_email_log_cols}")
        print("  -> SQLite cannot add columns to existing tables easily.")
        needs_reset = True

    print()

    if needs_reset:
        print("[ACTION REQUIRED] The email_logs table needs new columns.")
        print("Automatically altering the table to add missing columns...")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            for col in missing_email_log_cols:
                # Determine default value/type
                col_type = "INTEGER" if col in ["smtp_account_id", "retry_count"] else "VARCHAR"
                default_val = "0" if col == "retry_count" else "NULL"
                
                print(f"  Adding column {col}...")
                cursor.execute(f"ALTER TABLE email_logs ADD COLUMN {col} {col_type} DEFAULT {default_val}")
            
            conn.commit()
            conn.close()
            print("  [OK] Successfully added all missing columns.")
            
            # Now create any missing tables (like smtp_accounts)
            create_db_and_tables()
            print("  [OK] Created smtp_accounts table.")
        except Exception as e:
            print(f"  [ERROR] Failed to alter table: {e}")
            print("  Please stop the backend server and run scripts/reset_db.py manually.")
    else:
        # Only the smtp_accounts table is missing — it will auto-create
        print("[INFO] Starting backend will auto-create the smtp_accounts table.")
        create_db_and_tables()
        print("[OK] smtp_accounts table created successfully.")


if __name__ == "__main__":
    main()
