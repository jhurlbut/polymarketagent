#!/usr/bin/env python3
"""
Database migration: Add scan_requested column to strategy_settings table.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.utils.database import db
from sqlalchemy import text

def migrate():
    """Add scan_requested column if it doesn't exist."""
    print("Running migration: Add scan_requested column...")

    session = db.get_session()
    try:
        # Check if column exists
        result = session.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='strategy_settings'
            AND column_name='scan_requested'
        """))

        if result.fetchone():
            print("✓ Column scan_requested already exists, skipping migration")
            return

        # Add the column
        print("Adding scan_requested column...")
        session.execute(text("""
            ALTER TABLE strategy_settings
            ADD COLUMN scan_requested BOOLEAN NOT NULL DEFAULT FALSE
        """))
        session.commit()
        print("✓ Migration completed successfully!")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
