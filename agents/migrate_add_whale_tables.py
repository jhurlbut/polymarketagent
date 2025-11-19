#!/usr/bin/env python3
"""
Database migration: Add whale tracking tables.

This migration adds four new tables for whale-following trading strategy:
- whales: Registry of tracked whale traders with performance metrics
- whale_positions: Current open positions for each whale
- whale_transactions: Historical transaction log
- whale_signals: Copy-trading signals generated from whale activity
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.utils.database import db
from sqlalchemy import text

def migrate():
    """Add whale tracking tables if they don't exist."""
    print("=" * 70)
    print("WHALE TRACKING TABLES MIGRATION")
    print("=" * 70)
    print()

    session = db.get_session()
    try:
        # Check if whale tables already exist
        result = session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            AND table_name IN ('whales', 'whale_positions', 'whale_transactions', 'whale_signals')
        """))

        existing_tables = [row[0] for row in result.fetchall()]

        if len(existing_tables) == 4:
            print("✓ All whale tables already exist, skipping migration")
            return

        if len(existing_tables) > 0:
            print(f"Found existing tables: {', '.join(existing_tables)}")
            print("Creating missing tables...")
        else:
            print("Creating whale tracking tables...")

        # Use db.create_tables() which will create all tables from models
        db.create_tables()

        print()
        print("=" * 70)
        print("✓ Migration completed successfully!")
        print("=" * 70)
        print()
        print("Created tables:")
        print("  - whales: Whale trader registry")
        print("  - whale_positions: Current whale positions")
        print("  - whale_transactions: Historical transactions")
        print("  - whale_signals: Copy-trading signals")
        print()

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
